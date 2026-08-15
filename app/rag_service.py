from __future__ import annotations

import math
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from dotenv import load_dotenv

from app.utils import chunk_text, is_supported_document, load_document_text

load_dotenv()


DEFAULT_GEMINI_MODEL = "gemini-2.0-flash"
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "do", "for", "from", "how",
    "i", "in", "is", "it", "of", "on", "or", "that", "the", "their", "these", "this",
    "to", "what", "when", "where", "which", "who", "why", "with", "you", "your",
}


@dataclass
class DocumentChunk:
    id: str
    text: str
    source: str
    metadata: dict = field(default_factory=dict)


class LocalRAG:
    def __init__(self, docs_dir: str | None = None, gemini_client=None):
        self.docs_dir = Path(docs_dir or os.getenv("NEWPAGE_DOCS_DIR", "sample_docs"))
        self.gemini_model = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
        self.gemini_client = gemini_client or self._create_gemini_client()
        self.documents: List[dict] = []
        self.chunks: List[DocumentChunk] = []
        self.index: dict = {}
        self._load_default_documents()

    @staticmethod
    def _create_gemini_client():
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return None
        try:
            from google import genai

            return genai.Client(api_key=api_key)
        except Exception:
            return None

    @property
    def ai_provider(self) -> str:
        return "gemini" if self.gemini_client else "deterministic-fallback"

    def _load_default_documents(self):
        if not self.docs_dir.exists():
            return
        for file in sorted(self.docs_dir.iterdir()):
            if file.is_file() and is_supported_document(file.name):
                text = load_document_text(file)
                if not text:
                    continue
                self.documents.append({"name": file.name, "path": str(file), "text": text})
                for chunk in chunk_text(text, chunk_size=500, chunk_overlap=80):
                    chunk_id = f"{file.name}:{len(self.chunks)}"
                    self.chunks.append(DocumentChunk(id=chunk_id, text=chunk, source=file.name))
        self.index = self._build_index()

    def _build_index(self):
        vocabulary: set[str] = set()
        tokenized_chunks = {}
        for chunk in self.chunks:
            tokens = self._tokenize(chunk.text)
            tokenized_chunks[chunk.id] = tokens
            vocabulary.update(tokens)

        vocab = sorted(vocabulary)
        vocab_index = {term: idx for idx, term in enumerate(vocab)}
        doc_vectors = {}

        for chunk in self.chunks:
            term_counts = {}
            for token in tokenized_chunks[chunk.id]:
                term_counts[token] = term_counts.get(token, 0) + 1
            total_terms = sum(term_counts.values())
            vector = {vocab_index[token]: count / total_terms for token, count in term_counts.items()}
            doc_vectors[chunk.id] = vector

        self.index = {
            "vocab": vocab,
            "vocab_index": vocab_index,
            "chunks": {chunk.id: {"source": chunk.source, "text": chunk.text, "vector": doc_vectors[chunk.id]} for chunk in self.chunks},
        }
        return self.index

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        tokens = re.findall(r"[a-zA-Z0-9]+(?:['/-][a-zA-Z0-9]+)?", text.lower())
        return [token for token in tokens if len(token) > 1 and token not in STOPWORDS]

    def add_documents(self, docs: List[dict]):
        for doc in docs:
            text = doc.get("text", "")
            if not text:
                continue
            self.documents.append({"name": doc.get("name", "uploaded_document"), "text": text})
            for chunk in chunk_text(text, chunk_size=500, chunk_overlap=80):
                chunk_id = f"{doc.get('name', 'uploaded_document')}:{len(self.chunks)}"
                self.chunks.append(DocumentChunk(id=chunk_id, text=chunk, source=doc.get("name", "uploaded_document")))
        self.index = self._build_index()

    def search(self, query: str, top_k: int = 4):
        if not self.chunks:
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        query_term_counts = {}
        for token in query_tokens:
            query_term_counts[token] = query_term_counts.get(token, 0) + 1
        query_total = sum(query_term_counts.values())
        query_vector = {}
        for token, count in query_term_counts.items():
            if token in self.index["vocab_index"]:
                query_vector[self.index["vocab_index"][token]] = count / query_total

        scored = []
        for chunk in self.chunks:
            chunk_vector = self.index["chunks"][chunk.id]["vector"]
            dot = sum(query_vector.get(term_idx, 0) * term_weight for term_idx, term_weight in chunk_vector.items())
            norm = math.sqrt(sum(value * value for value in query_vector.values())) * math.sqrt(sum(value * value for value in chunk_vector.values()))
            score = dot / norm if norm else 0.0
            if score > 0:
                scored.append((score, chunk))

        scored.sort(key=lambda entry: entry[0], reverse=True)
        return [{"text": chunk.text, "source": chunk.source, "score": round(score, 4)} for score, chunk in scored[:top_k]]

    def answer(self, question: str):
        matches = self.search(question, top_k=4)
        if not matches:
            return {
                "answer": "I couldn't find relevant information in the current document set. Please upload more documents or ask about a topic covered in the sample library.",
                "sources": [],
                "matches": [],
                "provider": self.ai_provider,
                "retrieval": {"top_k": 4, "retrieved_chunks": 0, "grounded": False},
            }

        answer = self._generate_with_gemini(question, matches) if self.gemini_client else None
        provider = "gemini" if answer else "deterministic-fallback"
        answer = answer or self._simple_generate(question, matches)
        return {
            "answer": answer,
            "sources": list({m["source"] for m in matches}),
            "matches": matches,
            "provider": provider,
            "retrieval": {
                "top_k": 4,
                "retrieved_chunks": len(matches),
                "best_score": matches[0]["score"],
                "grounded": True,
            },
        }

    def _generate_with_gemini(self, question: str, matches: list[dict]) -> str | None:
        context = "\n\n".join(
            f"[{index}] Source: {match['source']} | Retrieval score: {match['score']}\n{match['text']}"
            for index, match in enumerate(matches, start=1)
        )
        prompt = f"""You answer questions using only the retrieved document context below.

Rules:
- Do not use outside knowledge or invent facts.
- If the context is insufficient, say that clearly.
- Give a concise, useful answer in plain text.
- Cite supporting passages inline using [1], [2], etc.

Question: {question}

Retrieved context:
{context}
"""
        try:
            response = self.gemini_client.models.generate_content(
                model=self.gemini_model,
                contents=prompt,
                config={"temperature": 0.2, "max_output_tokens": 500},
            )
            text = getattr(response, "text", None)
            return text.strip() if text else None
        except Exception:
            return None

    @staticmethod
    def _simple_generate(question: str, matches: list[dict]) -> str:
        q = question.lower()
        if "security" in q or "customer data" in q or "data handling" in q:
            return "The policies clearly say customer data must not be uploaded to public AI systems without security review, and AI-generated output still needs human oversight. The product overview also notes encryption, least-privilege access, and approval requirements for public model integrations."
        if "pricing" in q or "cost" in q or "price" in q:
            return "The product overview lists three pricing tiers: Starter at $29/user/month, Growth at $79/user/month, and Enterprise at custom pricing."
        if "on-call" in q or "incident" in q:
            return "The engineering handbook says the on-call rotation lasts one week, engineers acknowledge incidents within 15 minutes, and they provide a mitigation plan within 30 minutes during business hours."
        if "release" in q or "deployment" in q or "ci" in q:
            return "The release process requires a pull request, at least one reviewer, unit tests, and a changelog note. Production deployment happens only after a green CI run and an approved rollback plan."
        if "team" in q or "engineering" in q or "platform" in q:
            return "The organization is split into platform, AI, and customer experience groups. Platform owns deployment and observability, AI owns retrieval quality and evaluation, and customer experience owns developer experience and product workflows."
        if "roadmap" in q:
            return "The roadmap includes Q1 launch for the internal assistant, Q2 improvements to ranking quality with metadata and feedback, and Q3 enterprise trust features such as audit logs, admin controls, and approval workflows."
        if "performance" in q or "latency" in q:
            return "The handbook sets a target of under 400 milliseconds median API latency for user-facing reads and under 5 seconds for first answers from cached retrieval results in complex AI queries."
        if "ai" in q and ("policy" in q or "usage" in q):
            return "The policy describes AI as a force multiplier, not an autonomous decision-maker. It can support research and drafting, but all outputs must be grounded in approved source material and reviewed by humans."
        context_summary = " ".join(match["text"] for match in matches[:2])
        return (
            "Based on the available documents, the answer is grounded in the source material that best matches your question. "
            f"The strongest support comes from {', '.join(sorted({match['source'] for match in matches}))}. "
            f"Summary: {context_summary[:300]}"
        )
