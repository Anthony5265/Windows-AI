"""
Playwright Browser Automation Plugin
Supports modern browser testing across Chrome, Firefox, Safari
"""

from typing import Dict, Any, Optional, List
import asyncio
import os


class PlaywrightPlugin:
    """Plugin for browser automation using Playwright"""

    name = "playwright"
    version = "1.0.0"
    description = "Modern browser automation using Playwright (Chrome, Firefox, Safari)"
    author = "Windows AI Team"

    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.pages: List[Any] = []
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Playwright plugin"""
        try:
            from playwright.async_api import async_playwright
            self.async_playwright = async_playwright
            self._initialized = True
            return True
        except ImportError:
            print("playwright not installed. Please install with: pip install playwright")
            return False
        except Exception as e:
            print(f"Error initializing Playwright plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Playwright automation action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please install playwright."}

        try:
            # Run async actions in event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._execute_async(action, params))
            loop.close()
            return result
        except Exception as e:
            return {"error": str(e)}

    async def _execute_async(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute async Playwright actions"""
        if action == "launch_browser":
            return await self._launch_browser(params)
        elif action == "close_browser":
            return await self._close_browser()
        elif action == "new_page":
            return await self._new_page(params)
        elif action == "close_page":
            return await self._close_page(params)
        elif action == "navigate":
            return await self._navigate(params)
        elif action == "get_current_url":
            return await self._get_current_url(params)
        elif action == "get_page_content":
            return await self._get_page_content(params)
        elif action == "execute_script":
            return await self._execute_script(params)
        elif action == "take_screenshot":
            return await self._take_screenshot(params)
        elif action == "get_pages":
            return await self._get_pages()
        else:
            return {"error": f"Unknown action: {action}"}

    async def _launch_browser(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Launch browser with Playwright"""
        if self.browser:
            return {"error": "Browser already launched"}

        try:
            browser_type = params.get("browser", "chromium")  # chromium, firefox, webkit
            headless = params.get("headless", False)
            args = params.get("args", [])

            self.playwright = await self.async_playwright().start()

            if browser_type == "chromium":
                self.browser = await self.playwright.chromium.launch(headless=headless, args=args)
            elif browser_type == "firefox":
                self.browser = await self.playwright.firefox.launch(headless=headless, args=args)
            elif browser_type == "webkit":
                self.browser = await self.playwright.webkit.launch(headless=headless, args=args)
            else:
                return {"error": f"Unsupported browser type: {browser_type}"}

            # Create browser context
            self.context = await self.browser.new_context()

            # Create initial page
            page = await self.context.new_page()
            self.pages.append(page)

            return {
                "success": True,
                "message": f"{browser_type.capitalize()} browser launched successfully",
                "browser": browser_type,
                "pages": len(self.pages)
            }
        except Exception as e:
            return {"error": f"Failed to launch browser: {str(e)}"}

    async def _close_browser(self) -> Dict[str, Any]:
        """Close browser"""
        if not self.browser:
            return {"error": "No browser instance running"}

        try:
            await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            self.browser = None
            self.context = None
            self.pages = []
            return {"success": True, "message": "Browser closed successfully"}
        except Exception as e:
            return {"error": f"Failed to close browser: {str(e)}"}

    async def _new_page(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new page"""
        if not self.context:
            return {"error": "Browser not launched"}

        try:
            page = await self.context.new_page()
            self.pages.append(page)
            page_id = len(self.pages) - 1

            url = params.get("url")
            if url:
                await page.goto(url)

            return {
                "success": True,
                "page_id": page_id,
                "url": url or "about:blank",
                "total_pages": len(self.pages)
            }
        except Exception as e:
            return {"error": f"Failed to create new page: {str(e)}"}

    async def _close_page(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Close a page"""
        if not self.context:
            return {"error": "Browser not launched"}

        page_id = params.get("page_id", 0)
        if page_id >= len(self.pages) or page_id < 0:
            return {"error": f"Invalid page_id: {page_id}"}

        try:
            page = self.pages[page_id]
            await page.close()
            self.pages.pop(page_id)

            return {
                "success": True,
                "closed_page_id": page_id,
                "remaining_pages": len(self.pages)
            }
        except Exception as e:
            return {"error": f"Failed to close page: {str(e)}"}

    async def _navigate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Navigate to a URL"""
        if not self.context:
            return {"error": "Browser not launched"}

        page_id = params.get("page_id", 0)
        url = params.get("url")

        if not url:
            return {"error": "URL parameter required"}

        if page_id >= len(self.pages) or page_id < 0:
            return {"error": f"Invalid page_id: {page_id}"}

        try:
            page = self.pages[page_id]
            await page.goto(url)

            return {
                "success": True,
                "page_id": page_id,
                "url": url
            }
        except Exception as e:
            return {"error": f"Failed to navigate: {str(e)}"}

    async def _get_current_url(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get current URL of a page"""
        if not self.context:
            return {"error": "Browser not launched"}

        page_id = params.get("page_id", 0)
        if page_id >= len(self.pages) or page_id < 0:
            return {"error": f"Invalid page_id: {page_id}"}

        try:
            page = self.pages[page_id]
            url = page.url

            return {
                "page_id": page_id,
                "url": url
            }
        except Exception as e:
            return {"error": f"Failed to get URL: {str(e)}"}

    async def _get_page_content(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get page content"""
        if not self.context:
            return {"error": "Browser not launched"}

        page_id = params.get("page_id", 0)
        if page_id >= len(self.pages) or page_id < 0:
            return {"error": f"Invalid page_id: {page_id}"}

        try:
            page = self.pages[page_id]
            content = await page.content()

            return {
                "page_id": page_id,
                "content": content
            }
        except Exception as e:
            return {"error": f"Failed to get page content: {str(e)}"}

    async def _execute_script(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute JavaScript in a page"""
        if not self.context:
            return {"error": "Browser not launched"}

        page_id = params.get("page_id", 0)
        script = params.get("script")

        if not script:
            return {"error": "script parameter required"}

        if page_id >= len(self.pages) or page_id < 0:
            return {"error": f"Invalid page_id: {page_id}"}

        try:
            page = self.pages[page_id]
            result = await page.evaluate(script)

            return {
                "page_id": page_id,
                "result": result
            }
        except Exception as e:
            return {"error": f"Failed to execute script: {str(e)}"}

    async def _take_screenshot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Take screenshot of a page"""
        if not self.context:
            return {"error": "Browser not launched"}

        page_id = params.get("page_id", 0)
        path = params.get("path", "screenshot.png")

        if page_id >= len(self.pages) or page_id < 0:
            return {"error": f"Invalid page_id: {page_id}"}

        try:
            page = self.pages[page_id]
            await page.screenshot(path=path)

            return {
                "success": True,
                "page_id": page_id,
                "path": path
            }
        except Exception as e:
            return {"error": f"Failed to take screenshot: {str(e)}"}

    async def _get_pages(self) -> Dict[str, Any]:
        """Get list of pages"""
        if not self.context:
            return {"error": "Browser not launched"}

        try:
            pages = []
            for i, page in enumerate(self.pages):
                try:
                    url = page.url
                    title = await page.title()
                except:
                    url = "unknown"
                    title = "unknown"

                pages.append({
                    "page_id": i,
                    "url": url,
                    "title": title
                })

            return {
                "pages": pages,
                "count": len(pages)
            }
        except Exception as e:
            return {"error": f"Failed to get pages: {str(e)}"}

    def cleanup(self):
        """Cleanup resources"""
        if self.browser:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self._close_browser())
                loop.close()
            except:
                pass
        self.playwright = None
        self.browser = None
        self.context = None
        self.pages = []
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = PlaywrightPlugin
PLUGIN_NAME = "playwright"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Modern browser automation using Playwright (Chrome, Firefox, Safari)"
PLUGIN_ACTIONS = [
    "launch_browser", "close_browser", "new_page", "close_page",
    "navigate", "get_current_url", "get_page_content", "execute_script",
    "take_screenshot", "get_pages"
]