# Assessment Coverage Checklist

This document maps the assessment criteria to the implemented application, tests, and supporting documentation.

## Core functionality

**Requirement:** Answer questions based on uploaded or provided documents using RAG or a similar retrieval mechanism.

**Implemented:**

- Demo documents can be selected individually before loading.
- Users can upload TXT, Markdown, PDF, and DOCX files.
- Documents are normalized, chunked with overlap, indexed, and ranked against the question.
- Uploading replaces the active session context, so old demo documents cannot silently influence uploaded-document questions.
- Answers return source names, retrieval scores, retrieved chunk counts, provider, and grounded status.
- Gemini mode uses LangChain to send retrieved context to Gemini for final generation.
- No-key mode uses local deterministic fallback generation.

**Evidence:** `tests/test_rag.py`, `tests/test_ui_playwright.py`, `tests/test-runs/`.

## Creativity and product UX

**Requirement:** Demonstrate thoughtful UI/UX and product innovation.

**Implemented:**

- Single active document list avoids duplicating selected and loaded files.
- Clickable highlighted document rows, visible selected/not-selected states, selected count, Select all, Clear all, and Load selected actions.
- RAG trace is shown directly in the chat experience.
- Gemini-only executive brief converts the active document set into an executive summary, key facts, risks or gaps, suggested questions, and citations.
- Responsive layout handles long filenames and narrow screens.

**Evidence:** `tests/test-runs/2026-08-15_16-42-47/`.

## RAG and LLM decisions

### Chunking

Documents are normalized and split into approximately 500-character chunks with 80-character overlap. This keeps retrieved context compact while preserving continuity across chunk boundaries.

### Embeddings

This assessment build intentionally does not use an embedding model. It uses transparent token-vector similarity instead. That trade-off avoids model downloads and makes the retrieval behavior deterministic, inspectable, cheap, and easy to test. A production version would evaluate Gemini Embedding, another hosted embedding model, or a local embedding model against a representative question set.

### LLM selection

Gemini was selected because it provides a practical hosted LLM option with an accessible developer tier. LangChain provides the orchestration boundary, prompt composition, and model integration. The model is configured through `GEMINI_MODEL` and the API key through `GEMINI_API_KEY` or `GOOGLE_API_KEY`.

### Retrieval approach

The system tokenizes the query and chunks, builds normalized sparse term vectors, calculates cosine-style similarity, and returns the highest-ranked matching chunks. The active document session is explicit and can be scoped through the demo picker or upload replacement behavior.

### Prompt engineering and context management

LangChain builds a system prompt that instructs Gemini to use only retrieved context, avoid outside knowledge, state when context is insufficient, answer concisely, and cite supporting passages using `[1]`, `[2]` markers. Only the top retrieved chunks are sent to the LLM.

### Guardrails

- API keys remain server-side in `.env` and are ignored by Git.
- Gemini receives retrieved context rather than unrestricted application state.
- Source names and retrieval metadata are returned to the UI.
- No-match queries receive an explicit insufficient-context response.
- Quota, model, and general Gemini failures are surfaced clearly.
- Uploads replace the active session to prevent cross-document contamination.

### Quality controls

- Unit tests cover ingestion, retrieval, fallback answers, session replacement, prompt context, and executive brief composition.
- Playwright tests cover the real browser shell, document selection, loading, question flow, and upload session transition.
- GitHub Actions installs dependencies, installs Chromium, starts the service, waits for health, and runs the full suite.
- Timestamped screenshot evidence records the user-facing flows.

### Observability

- `/api/health` reports status, document count, chunk count, provider, and configured model.
- Query responses expose provider, sources, retrieval count, best score, and grounded status.
- The UI displays a retrieval trace after each answer.
- Gemini failures are classified as quota, model availability, or general request errors.

## Engineering excellence

- FastAPI backend, lightweight browser frontend, separated retrieval and parsing utilities.
- Dockerfile for repeatable container execution.
- Pinned core dependencies and CI automation.
- Clear local setup and end-user instructions.
- Tests run against real behavior and a real browser rather than mocked production methods.

## AI-assisted development approach

The implementation used GitHub Copilot as a collaborative coding assistant, with GPT models and Claude used for targeted reasoning, design exploration, and implementation feedback. The workflow kept the developer in control:

1. Define behavior and acceptance criteria.
2. Give the assistant a narrow code slice and relevant context.
3. Review generated changes for security, simplicity, and design consistency.
4. Run focused tests, full regression tests, and browser checks.
5. Keep secrets, prompts, architectural choices, and trade-offs explicit.

The do's are using AI for acceleration, exploration, boilerplate, tests, and review support while validating meaningful changes. The don'ts are sharing secrets, accepting broad unreviewed rewrites, trusting generated code without execution, or delegating product and architecture decisions without human direction.

## Known trade-offs

- Lexical retrieval is easier to explain but less semantically powerful than embeddings.
- Uploads are in-memory and not persistent.
- There is no authentication or multi-tenant isolation in the assessment build.
- Gemini access depends on the reviewer’s account, quota, model availability, and key restrictions.

These trade-offs are intentional and documented so the solution remains simple, testable, and honest about its productionization path.
