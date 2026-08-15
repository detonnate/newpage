# Test Evidence Run

**Run ID:** `2026-08-15_11-34-43`  
**Application:** Newpage Docs Q&A  
**Base URL:** `http://localhost:8000`  
**Captured:** 2026-08-15T11:35:07

## Automated test result

The full suite was run immediately before this evidence capture:

```text
pytest -q
9 passed
```

## Evidence captured

| File | What it demonstrates |
|---|---|
| [01-homepage.png](01-homepage.png) | Initial application shell and document assistant entry point. |
| [02-demo-library.png](02-demo-library.png) | Demo document library loaded into the application. |
| [03-grounded-answer.png](03-grounded-answer.png) | Question answered with retrieved source context and the RAG trace. |
| [04-ai-brief.png](04-ai-brief.png) | Gemini executive brief showcase, or explicit AI-unavailable state. |

## User-facing test protocol

1. Open the application shell and confirm the document assistant controls are visible.
2. Load the demo library and confirm the sample documents appear.
3. Ask a question about pricing and confirm the response includes grounded content and a retrieval trace.
4. Run the Gemini-only executive brief workflow and confirm either a generated brief or an explicit AI-unavailable message.

## Quality and engineering practices demonstrated

- Browser tests exercise real UI behavior rather than mocked DOM assertions.
- Backend tests cover document loading, retrieval, grounded fallback behavior, and LangChain prompt composition.
- The RAG trace makes retrieval count, source documents, provider, and grounded status inspectable.
- AI mode is optional and fails visibly when the key or model is unavailable.
- Screenshot evidence is timestamped and reproducible with `python tests/capture_evidence.py`.
