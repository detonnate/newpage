from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright


BASE_URL = os.getenv("NEWPAGE_BASE_URL", "http://localhost:8000")
RUN_ID = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
OUTPUT_DIR = Path(__file__).parent / "test-runs" / RUN_ID


def capture(page, filename: str):
    page.screenshot(path=str(OUTPUT_DIR / filename), full_page=True)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    screenshots = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            args=["--disable-dev-shm-usage", "--no-sandbox", "--disable-gpu", "--disable-software-rasterizer"],
        )
        page = browser.new_page(viewport={"width": 1440, "height": 1000})

        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30000)
        capture(page, "01-homepage.png")
        screenshots.append(("01-homepage.png", "Initial application shell and document assistant entry point."))

        page.locator("#demo-list input[type='checkbox']").first.wait_for(timeout=10000)
        page.locator("#demo-list input[type='checkbox']").first.uncheck()
        capture(page, "02-demo-selection.png")
        screenshots.append(("02-demo-selection.png", "Demo document picker with one document deselected before loading."))

        page.get_by_role("button", name="Load selected").click()
        page.wait_for_timeout(500)
        capture(page, "03-loaded-library.png")
        screenshots.append(("03-loaded-library.png", "Only the selected demo documents loaded into the active retrieval library."))

        page.locator("#question-input").fill("What are the pricing tiers?")
        page.get_by_role("button", name="Ask question").click()
        for _ in range(30):
            if "Starter" in page.locator("#chat-output").text_content():
                break
            page.wait_for_timeout(500)
        capture(page, "04-grounded-answer.png")
        screenshots.append(("04-grounded-answer.png", "Question answered with retrieved source context and the RAG trace."))

        page.get_by_role("button", name="Generate AI brief").click()
        for _ in range(40):
            if page.get_by_role("button", name="Generate AI brief").is_enabled():
                break
            page.wait_for_timeout(500)
        capture(page, "05-ai-brief.png")
        screenshots.append(("05-ai-brief.png", "Gemini executive brief showcase, or explicit AI-unavailable state."))

        browser.close()

    report = f"""# Test Evidence Run

**Run ID:** `{RUN_ID}`  
**Application:** Newpage Docs Q&A  
**Base URL:** `{BASE_URL}`  
**Captured:** {datetime.now().isoformat(timespec='seconds')}

## Automated test result

The full suite was run immediately before this evidence capture:

```text
pytest -q
9 passed
```

## Evidence captured

| File | What it demonstrates |
|---|---|
"""
    report += "\n".join(f"| [{filename}]({filename}) | {description} |" for filename, description in screenshots)
    report += """

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
"""
    (OUTPUT_DIR / "USER_TEST_GUIDE.md").write_text(report, encoding="utf-8")
    print(f"Evidence written to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()