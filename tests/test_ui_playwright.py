from playwright.sync_api import sync_playwright


def _launch_browser():
    pw = sync_playwright().start()
    browser = pw.chromium.launch(
        headless=True,
        args=["--disable-dev-shm-usage", "--no-sandbox", "--disable-gpu", "--disable-software-rasterizer"],
    )
    return pw, browser


def test_homepage_loads_and_has_app_shell():
    pw, browser = _launch_browser()
    try:
        page = browser.new_page()
        page.goto("http://localhost:8000", wait_until="domcontentloaded", timeout=30000)
        assert page.locator("h1").text_content().strip() == "Newpage Docs"
        assert page.get_by_role("button", name="Ask question").is_visible()
    finally:
        browser.close()
        pw.stop()


def test_question_flow_answers_using_documents():
    pw, browser = _launch_browser()
    try:
        page = browser.new_page()
        page.goto("http://localhost:8000", wait_until="domcontentloaded", timeout=30000)
        page.get_by_role("button", name="Load demo docs").click()
        page.locator("#question-input").fill("What are the pricing tiers?")
        page.get_by_role("button", name="Ask question").click()
        for _ in range(20):
            text = page.locator("#chat-output").text_content()
            if "Starter" in text:
                break
            page.wait_for_timeout(500)
        assert "Starter" in page.locator("#chat-output").text_content()
    finally:
        browser.close()
        pw.stop()
