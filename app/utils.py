from __future__ import annotations

import re
from pathlib import Path

from pypdf import PdfReader


SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx"}


def is_supported_document(filename: str) -> bool:
    return Path(filename).suffix.lower() in SUPPORTED_EXTENSIONS


def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 80) -> list[str]:
    if not text:
        return []
    clean_text = re.sub(r"\s+", " ", text).strip()
    if len(clean_text) <= chunk_size:
        return [clean_text]

    step = max(1, chunk_size - chunk_overlap)
    chunks: list[str] = []
    start = 0

    while start < len(clean_text):
        end = min(start + chunk_size, len(clean_text))
        chunk = clean_text[start:end].strip()
        if not chunk:
            break
        if end < len(clean_text):
            last_space = chunk.rfind(" ")
            if last_space > max(10, int(chunk_size * 0.6)):
                chunk = chunk[:last_space].strip()
        chunks.append(chunk)
        if end >= len(clean_text):
            break
        start += step

    return [item for item in chunks if item]


def load_document_text(file_path: str | Path) -> str:
    path = Path(file_path)
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        reader = PdfReader(str(path))
        pages = []
        for page in reader.pages:
            text = page.extract_text() or ""
            pages.append(text)
        return "\n".join(pages)
    if suffix == ".docx":
        try:
            from docx import Document
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(f"python-docx is required for .docx support: {exc}") from exc
        document = Document(str(path))
        return "\n".join(paragraph.text for paragraph in document.paragraphs)
    return path.read_text(encoding="utf-8", errors="ignore")
