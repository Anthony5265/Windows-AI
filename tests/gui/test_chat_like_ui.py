import pathlib
import subprocess
import sys

import pytest

try:  # pragma: no cover - optional dependency
    from playwright.sync_api import sync_playwright
except Exception:  # pragma: no cover
    sync_playwright = None  # type: ignore


@pytest.fixture(scope="module")
def page():
    """Provide a Playwright page connected to headless Chromium.

    The fixture attempts to install the browser at runtime.  If Playwright or
    the browser cannot be initialised, the test is skipped instead of failing.
    """

    if sync_playwright is None:
        pytest.skip("playwright not installed")

    subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch()
        except Exception:
            pytest.skip("chromium browser not available")
        page = browser.new_page()
        yield page
        browser.close()


def test_chat_ui_layout(page):
    html_path = (
        pathlib.Path(__file__).resolve().parents[2]
        / "installer"
        / "web"
        / "chat_ui.html"
    )
    page.goto(f"file://{html_path}")
    page.wait_for_selector("#chat-container")

    assert page.query_selector(".message.user") is not None
    assert page.query_selector(".message.assistant") is not None

    bg1 = page.evaluate(
        "getComputedStyle(document.documentElement).getPropertyValue('--background')"
    )
    page.click("#theme-toggle")
    bg2 = page.evaluate(
        "getComputedStyle(document.documentElement).getPropertyValue('--background')"
    )
    assert bg1.strip() != bg2.strip()

    page.set_viewport_size({"width": 400, "height": 800})
    width = page.evaluate(
        "document.getElementById('chat-container').offsetWidth"
    )
    assert width <= 400
