# Newpage: Chat With Your Docs

This project is a lightweight document Q&A application built for a tech assessment. It lets a user upload documents or use a preloaded demo library and ask natural-language questions grounded in the source material. When configured, Gemini provides the final answer; without a key, the app uses a deterministic local fallback.

## Why this approach

The goal was to build a working, well-engineered baseline rather than a complex, fragile system. I chose a local retrieval-first design because it is fast to run, simple to explain, and easy to test in a short interview-friendly timeline.

### RAG and retrieval decisions

- Retrieval approach: lexical retrieval with chunking over a small document library.
- Why this choice: the project prioritizes reliability, speed, and maintainability over huge model dependencies. It works well for a demo and is easy to swap for a vector DB or embeddings model later.
- Chunking: documents are split into overlapping text chunks of about 500 characters to preserve context without overloading the prompt.
- LLM/orchestration: LangChain composes a grounded prompt chain and invokes Gemini only after retrieval. The prompt includes ranked chunks, source names, retrieval scores, and strict instructions to answer only from that context.
- Prompting: generated answers cite retrieved passages using `[1]`, `[2]` markers. If Gemini is unavailable or fails, the deterministic fallback keeps the demo usable.
- Guardrails: answers are limited to retrieved content, source names are surfaced, and the app avoids confidently answering when the document set has no relevant match.
- Quality control: the system is intentionally simple but testable.

### Architecture

- Frontend: a lightweight HTML/CSS/JavaScript UI
- Backend: FastAPI service
- Document ingestion: text/PDF support via local parsing
- Retrieval layer: token-based similarity over chunked content
- Response layer: grounded answer composition using retrieved chunk text

The UI exposes the RAG trace after each answer: provider used, number of retrieved chunks, and source document names. The API also returns retrieval scores and a `grounded` flag, making the retrieval-to-generation boundary inspectable during a demo.

## Gemini setup

GitHub Copilot access cannot be used as a server-side API key for this application. Copilot can help write and review the code, but the running app needs a model API such as Gemini. LangChain is the orchestration layer; Gemini is the LLM provider. The Gemini key stays server-side and is never placed in frontend JavaScript.

1. Copy `.env.example` to `.env`.
2. Set `GEMINI_API_KEY` to your own Gemini API key.
3. Use the default `gemini-flash-latest`, or set `GEMINI_MODEL` to a model available to your key.

Google also supports `GOOGLE_API_KEY`; if both variables are set, this app uses `GOOGLE_API_KEY` first.

For PowerShell, the equivalent session-only setup is:

```powershell
$env:GEMINI_API_KEY = "your-key"
$env:GEMINI_MODEL = "gemini-flash-latest"
uvicorn app.main:app --reload
```

The answer trace reports `langchain-gemini` when Gemini generation succeeds. Without a key, it reports `deterministic-fallback`. If the key is present but the configured model is unavailable, the app reports the AI feature as unavailable instead of pretending the request used an LLM. Never commit `.env` or paste the key into GitHub.

## Two ways to run the app

### Mode 1: local retrieval, no AI key

This mode is useful for reviewers who want a zero-cost, offline-friendly demo. The app still performs real document ingestion, chunking, token-based retrieval, ranking, source tracing, and deterministic answers for the sample topics. No external request is made.

```text
Question -> chunk retrieval -> ranked sources -> deterministic response
```

### Mode 2: LangChain + Gemini AI

This mode demonstrates the full LLM application layer. The app retrieves the most relevant chunks first, then LangChain sends only that context to Gemini with a grounded prompt. Gemini writes the final response and cites source passages.

```text
Question -> chunk retrieval -> LangChain prompt chain -> Gemini -> cited answer
```

Gemini-only showcase features include:

- **Grounded answer generation:** natural-language synthesis over retrieved chunks rather than fixed topic responses.
- **Executive brief:** the **Generate AI brief** button turns the document library into a concise brief with an executive summary, key facts, risks or gaps, suggested questions, and citations.
- **RAG observability:** every answer shows the provider, retrieved chunk count, source files, retrieval score, and grounded status.
- **Graceful degradation:** if Gemini is not configured or the selected model is unavailable, the core retrieval experience remains usable and explains that AI mode is unavailable.

For a strong assessment demonstration, run one question in both modes and compare the deterministic response with the Gemini-written response. Then use **Generate AI brief** to show a capability that depends on the LLM layer.

The current Gemini model catalog is maintained by Google. Prefer a stable or latest model available to your account; `gemini-flash-latest` is the default so the sample does not depend on a retired model ID. Model availability and free-tier access can vary by account, project, region, and date.

## Quick start

1. Create a virtual environment
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

2. Install dependencies
   ```bash
   python -m pip install -r requirements.txt
   ```

3. Run the app
   ```bash
   uvicorn app.main:app --reload
   ```

4. Open the app at http://localhost:8000

5. Run tests
   ```bash
   pytest -q
   ```

## Demo documents

The repo includes sample docs in the sample_docs folder:

- company_policy.txt
- product_overview.md
- engineering_handbook.txt

These allow the app to answer questions about policy, pricing, roadmap, engineering practices, and security.

## Productionization roadmap

To make this production-ready for AWS/GCP/Azure/Cloudflare, I would add:

1. A managed vector database such as Pinecone, Weaviate, or Azure AI Search
2. Hosted embedding model and LLM via Azure OpenAI / OpenAI / Bedrock / Vertex AI
3. Background ingestion pipeline with async job processing
4. Auth and RBAC
5. Audit logs and observability with Prometheus, Grafana, and structured logs
6. Rate limiting, request throttling, and secrets management
7. Separate indexing and retrieval services behind a queue
8. Evaluation metrics for answer quality and retrieval precision

## Key technical decisions

- I prioritized a simple, explainable “retrieval-first” pattern for the interview use case.
- I kept the architecture modular so the retrieval layer can be swapped with vector DB + embeddings later.
- I avoided heavy model-download dependencies during the initial build because they increase setup friction and failure risk.
- I added automatic chunking and overlapping contexts to improve answer quality without a lot of system complexity.

## Engineering standards followed

- Clear separation of concerns: UI, retrieval logic, document parsing, and tests
- Small, testable functions
- Minimal dependencies to support quick setup
- Basic observability through health endpoints and structured responses
- Easy local development via FastAPI + static frontend

The project intentionally skips some enterprise features such as full multi-tenant auth, persistent vector storage, and remote model orchestration because the main goal is a solid, understandable demo.

## AI-assisted development workflow

I used AI tools as a speed multiplier for code scaffolding, issue diagnosis, and iterative refinement. The main value was in generating boilerplate, suggesting UI structure, and helping me iterate on code quickly while keeping the final decisions grounded in project goals and testing.

My principles with AI assistants:

- Use them to accelerate boilerplate and reduce repetitive work
- Verify every generated change with tests and local execution
- Prefer small, readable edits over large AI-generated rewrites
- Keep the final architecture understandable to a human reviewer
- Treat the README and technical decisions as my own reasoning, not a model-generated summary

## What I would do with more time

- Add a real embeddings model and vector DB for semantic retrieval
- Add multi-document upload parsing and better PDF cleanup
- Add broader answer quality tests and evaluation checks
- Add a deployment pipeline with Docker and CI
- Add more robust source citation and observability

## Notes

This project is intentionally simple and pragmatic. It demonstrates the core idea of document Q&A, retrieval grounding, and a clean interface without overengineering the stack.
