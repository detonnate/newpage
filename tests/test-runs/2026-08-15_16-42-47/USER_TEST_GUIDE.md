# Test Evidence Run

**Run ID:** `2026-08-15_16-42-47`  
**Application:** Newpage Docs Q&A  
**Base URL:** `http://localhost:8000`  
**Captured:** 2026-08-15T16:42:52

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
| [02-demo-selection.png](02-demo-selection.png) | Demo document picker with one document deselected before loading. |
| [03-loaded-library.png](03-loaded-library.png) | Only the selected demo documents loaded into the active retrieval library. |
| [04-grounded-answer.png](04-grounded-answer.png) | Question answered with retrieved source context and the RAG trace. |
| [05-ai-brief.png](05-ai-brief.png) | Gemini executive brief showcase, or explicit AI-unavailable state. |

## User-facing test protocol

1. Open the application shell and confirm the document assistant controls are visible.
2. Choose a subset of demo documents, load them, and confirm only those files appear in Loaded docs.
3. Ask a question about pricing and confirm the response includes grounded content and a retrieval trace.
4. Run the Gemini-only executive brief workflow and confirm either a generated brief or an explicit AI-unavailable message.

## Quality and engineering practices demonstrated

- Browser tests exercise real UI behavior rather than mocked DOM assertions.
- Backend tests cover document loading, retrieval, grounded fallback behavior, and LangChain prompt composition.
- The RAG trace makes retrieval count, source documents, provider, and grounded status inspectable.
- AI mode is optional and fails visibly when the key or model is unavailable.
- Screenshot evidence is timestamped and reproducible with `python tests/capture_evidence.py`.
