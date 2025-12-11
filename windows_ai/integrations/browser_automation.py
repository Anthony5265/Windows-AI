"""
Browser Automation Manager
Playwright, Puppeteer, and AI-powered browser automation
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional
from windows_ai.config.unified_config import WindowsAIConfig

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)

class BrowserType(Enum):
    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"

class BrowserAutomationManager:
    """Manages browser automation with Playwright and AI capabilities"""

    def __init__(self):
        self._config: Optional[WindowsAIConfig] = None
        self._initialized = False
        self._browser = None
        self._context = None
        self._page = None
        self.screenshots_dir = Path.home() / ".windowsai" / "browser_screenshots"

    async def initialize(self, config: Optional[WindowsAIConfig] = None):
        """Initialize browser automation"""
        if self._initialized:
            return
        
        self._config = config

        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self._initialized = True
        logger.info("Browser Automation Manager initialized")

    async def cleanup(self):
        """Cleanup resources before shutdown"""
        try:
            # Close any open connections
            if hasattr(self, '_clients'):
                for client in self._clients.values():
                    if hasattr(client, 'close'):
                        await client.close() if asyncio.iscoroutinefunction(client.close) else client.close()
            
            # Reset initialization flag
            self._initialized = False
            logger.info(f"{self.__class__.__name__} cleanup completed")
            
        except Exception as e:
            logger.error(f"{self.__class__.__name__} cleanup failed: {e}")

    async def launch_browser(
        self,
        browser_type: BrowserType = BrowserType.CHROMIUM,
        headless: bool = True,
        **kwargs
    ):
        """Launch a browser instance"""
        from playwright.async_api import async_playwright

        self._playwright = await async_playwright().start()

        if browser_type == BrowserType.CHROMIUM:
            self._browser = await self._playwright.chromium.launch(headless=headless, **kwargs)
        elif browser_type == BrowserType.FIREFOX:
            self._browser = await self._playwright.firefox.launch(headless=headless, **kwargs)
        elif browser_type == BrowserType.WEBKIT:
            self._browser = await self._playwright.webkit.launch(headless=headless, **kwargs)

        self._context = await self._browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=kwargs.get("user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        )
        self._page = await self._context.new_page()

        logger.info(f"Launched {browser_type.value} browser")
        return self._page

    async def close_browser(self):
        """Close the browser"""
        if self._page:
            await self._page.close()
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if hasattr(self, '_playwright'):
            await self._playwright.stop()

    async def navigate(self, url: str, wait_until: str = "domcontentloaded") -> Dict[str, Any]:
        """Navigate to a URL"""
        if not self._page:
            await self.launch_browser()

        response = await self._page.goto(url, wait_until=wait_until)

        return {
            "url": self._page.url,
            "title": await self._page.title(),
            "status": response.status if response else None
        }

    async def click(self, selector: str, **kwargs):
        """Click an element"""
        await self._page.click(selector, **kwargs)

    async def fill(self, selector: str, text: str, **kwargs):
        """Fill a text input"""
        await self._page.fill(selector, text, **kwargs)

    async def type_text(self, selector: str, text: str, delay: int = 50):
        """Type text with delay (simulates human typing)"""
        await self._page.type(selector, text, delay=delay)

    async def press(self, key: str):
        """Press a key"""
        await self._page.keyboard.press(key)

    async def select(self, selector: str, value: str):
        """Select from dropdown"""
        await self._page.select_option(selector, value)

    async def wait_for_selector(self, selector: str, timeout: int = 30000):
        """Wait for an element"""
        await self._page.wait_for_selector(selector, timeout=timeout)

    async def wait_for_navigation(self, timeout: int = 30000):
        """Wait for navigation"""
        await self._page.wait_for_load_state("networkidle", timeout=timeout)

    async def get_text(self, selector: str) -> str:
        """Get text content of an element"""
        element = await self._page.query_selector(selector)
        if element:
            return await element.text_content()
        return ""

    async def get_attribute(self, selector: str, attribute: str) -> Optional[str]:
        """Get attribute of an element"""
        element = await self._page.query_selector(selector)
        if element:
            return await element.get_attribute(attribute)
        return None

    async def get_html(self, selector: str = None) -> str:
        """Get HTML content"""
        if selector:
            element = await self._page.query_selector(selector)
            if element:
                return await element.inner_html()
            return ""
        return await self._page.content()

    async def screenshot(self, path: str = None, full_page: bool = False) -> str:
        """Take a screenshot"""
        if not path:
            from datetime import datetime
            path = str(self.screenshots_dir / f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")

        await self._page.screenshot(path=path, full_page=full_page)
        return path

    async def pdf(self, path: str = None) -> str:
        """Generate PDF of the page"""
        if not path:
            from datetime import datetime
            path = str(self.screenshots_dir / f"page_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")

        await self._page.pdf(path=path)
        return path

    async def evaluate(self, script: str) -> Any:
        """Execute JavaScript in the page"""
        return await self._page.evaluate(script)

    async def query_selector_all(self, selector: str) -> List[Any]:
        """Query all matching elements"""
        return await self._page.query_selector_all(selector)

    async def extract_links(self) -> List[Dict[str, str]]:
        """Extract all links from the page"""
        links = await self._page.evaluate("""
            () => Array.from(document.querySelectorAll('a')).map(a => ({
                href: a.href,
                text: a.innerText.trim()
            }))
        """)
        return links

    async def extract_text(self) -> str:
        """Extract all text from the page"""
        return await self._page.evaluate("() => document.body.innerText")

    async def extract_tables(self) -> List[List[List[str]]]:
        """Extract all tables from the page"""
        return await self._page.evaluate("""
            () => Array.from(document.querySelectorAll('table')).map(table =>
                Array.from(table.querySelectorAll('tr')).map(row =>
                    Array.from(row.querySelectorAll('td, th')).map(cell => cell.innerText.trim())
                )
            )
        """)

    async def extract_images(self) -> List[Dict[str, str]]:
        """Extract all images from the page"""
        return await self._page.evaluate("""
            () => Array.from(document.querySelectorAll('img')).map(img => ({
                src: img.src,
                alt: img.alt
            }))
        """)

    async def scroll_to_bottom(self):
        """Scroll to the bottom of the page"""
        await self._page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(0.5)

    async def scroll_to_element(self, selector: str):
        """Scroll to an element"""
        await self._page.evaluate(f"document.querySelector('{selector}').scrollIntoView()")

    async def set_cookies(self, cookies: List[Dict]):
        """Set cookies"""
        await self._context.add_cookies(cookies)

    async def get_cookies(self) -> List[Dict]:
        """Get cookies"""
        return await self._context.cookies()

    async def clear_cookies(self):
        """Clear cookies"""
        await self._context.clear_cookies()

    # ==================== AI-POWERED AUTOMATION ====================

    async def ai_extract(self, prompt: str, llm_provider: str = "openai") -> Any:
        """Use AI to extract structured data from the page"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        # Get page content
        html = await self.get_html()
        text = await self.extract_text()

        # Use AI to extract
        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": "You are a web scraping assistant. Extract the requested information from the webpage content. Return JSON when structured data is requested."},
            {"role": "user", "content": f"Page content:\n{text[:8000]}\n\nExtract: {prompt}"}
        ]

        provider = Provider(llm_provider)
        response = await ai.chat(provider, messages)

        return response["content"]

    async def ai_action(self, instruction: str, llm_provider: str = "openai") -> Dict[str, Any]:
        """Use AI to perform an action on the page"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        # Get page state
        html = await self.get_html()
        screenshot_path = await self.screenshot()

        # Get AI to determine action
        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": """You are a browser automation assistant. Given a webpage and an instruction, determine the action to take.
            Return a JSON object with:
            - action: "click", "fill", "select", "scroll", "navigate", "wait"
            - selector: CSS selector for the element (if applicable)
            - value: value to fill or select (if applicable)
            - url: URL to navigate to (if applicable)
            """},
            {"role": "user", "content": f"Page HTML (truncated):\n{html[:5000]}\n\nInstruction: {instruction}"}
        ]

        provider = Provider(llm_provider)
        response = await ai.chat(provider, messages)

        # Parse and execute action
        import json
        try:
            action = json.loads(response["content"])

            if action.get("action") == "click":
                await self.click(action["selector"])
            elif action.get("action") == "fill":
                await self.fill(action["selector"], action["value"])
            elif action.get("action") == "select":
                await self.select(action["selector"], action["value"])
            elif action.get("action") == "navigate":
                await self.navigate(action["url"])
            elif action.get("action") == "scroll":
                if action.get("selector"):
                    await self.scroll_to_element(action["selector"])
                else:
                    await self.scroll_to_bottom()

            return {"success": True, "action": action}
        except Exception as e:
            return {"success": False, "error": str(e), "raw_response": response["content"]}

    async def scrape_with_ai(
        self,
        url: str,
        extraction_prompt: str,
        llm_provider: str = "openai"
    ) -> Any:
        """Complete AI-powered scraping workflow"""
        await self.navigate(url)
        await asyncio.sleep(2)  # Wait for dynamic content

        return await self.ai_extract(extraction_prompt, llm_provider)

    # ==================== CLOUD BROWSER SERVICES ====================

    async def use_browserbase(self, api_key: str = None):
        """Use Browserbase cloud browser"""
        api_key = api_key or os.environ.get("BROWSERBASE_API_KEY")

        from playwright.async_api import async_playwright

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.connect_over_cdp(
            f"wss://connect.browserbase.com?apiKey={api_key}"
        )
        self._context = self._browser.contexts[0]
        self._page = self._context.pages[0]

    async def use_browserless(self, api_key: str = None):
        """Use Browserless cloud browser"""
        api_key = api_key or os.environ.get("BROWSERLESS_API_KEY")

        from playwright.async_api import async_playwright

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.connect_over_cdp(
            f"wss://chrome.browserless.io?token={api_key}"
        )
        self._context = await self._browser.new_context()
        self._page = await self._context.new_page()
