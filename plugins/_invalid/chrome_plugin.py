"""
Chrome Browser Automation Plugin
Supports Chrome automation via Chrome DevTools Protocol (CDP)
"""

from typing import Dict, Any, Optional, List
import asyncio
import os


class ChromePlugin:
    """Plugin for Chrome browser automation via CDP"""

    name = "chrome"
    version = "1.0.0"
    description = "Chrome browser automation using Chrome DevTools Protocol"
    author = "Windows AI Team"

    def __init__(self):
        self.browser = None
        self.pages: List[Any] = []
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Chrome plugin"""
        try:
            # Check if pyppeteer is available
            import pyppeteer
            self.pyppeteer = pyppeteer
            self._initialized = True
            return True
        except ImportError:
            print("pyppeteer not installed. Please install with: pip install pyppeteer")
            return False
        except Exception as e:
            print(f"Error initializing Chrome plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Chrome automation action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please install pyppeteer."}

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
        """Execute async Chrome actions"""
        if action == "launch_browser":
            return await self._launch_browser(params)
        elif action == "close_browser":
            return await self._close_browser()
        elif action == "new_tab":
            return await self._new_tab(params)
        elif action == "close_tab":
            return await self._close_tab(params)
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
        elif action == "get_tabs":
            return await self._get_tabs()
        else:
            return {"error": f"Unknown action: {action}"}

    async def _launch_browser(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Launch Chrome browser"""
        if self.browser:
            return {"error": "Browser already launched"}

        try:
            headless = params.get("headless", False)
            args = params.get("args", ["--no-sandbox", "--disable-setuid-sandbox"])

            self.browser = await self.pyppeteer.launch(
                headless=headless,
                args=args
            )

            # Create initial page
            page = await self.browser.newPage()
            self.pages.append(page)

            return {
                "success": True,
                "message": "Browser launched successfully",
                "tabs": len(self.pages)
            }
        except Exception as e:
            return {"error": f"Failed to launch browser: {str(e)}"}

    async def _close_browser(self) -> Dict[str, Any]:
        """Close Chrome browser"""
        if not self.browser:
            return {"error": "No browser instance running"}

        try:
            await self.browser.close()
            self.browser = None
            self.pages = []
            return {"success": True, "message": "Browser closed successfully"}
        except Exception as e:
            return {"error": f"Failed to close browser: {str(e)}"}

    async def _new_tab(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new tab"""
        if not self.browser:
            return {"error": "Browser not launched"}

        try:
            page = await self.browser.newPage()
            self.pages.append(page)
            tab_id = len(self.pages) - 1

            url = params.get("url")
            if url:
                await page.goto(url)

            return {
                "success": True,
                "tab_id": tab_id,
                "url": url or "about:blank",
                "total_tabs": len(self.pages)
            }
        except Exception as e:
            return {"error": f"Failed to create new tab: {str(e)}"}

    async def _close_tab(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Close a tab"""
        if not self.browser:
            return {"error": "Browser not launched"}

        tab_id = params.get("tab_id", 0)
        if tab_id >= len(self.pages) or tab_id < 0:
            return {"error": f"Invalid tab_id: {tab_id}"}

        try:
            page = self.pages[tab_id]
            await page.close()
            self.pages.pop(tab_id)

            return {
                "success": True,
                "closed_tab_id": tab_id,
                "remaining_tabs": len(self.pages)
            }
        except Exception as e:
            return {"error": f"Failed to close tab: {str(e)}"}

    async def _navigate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Navigate to a URL"""
        if not self.browser:
            return {"error": "Browser not launched"}

        tab_id = params.get("tab_id", 0)
        url = params.get("url")

        if not url:
            return {"error": "URL parameter required"}

        if tab_id >= len(self.pages) or tab_id < 0:
            return {"error": f"Invalid tab_id: {tab_id}"}

        try:
            page = self.pages[tab_id]
            await page.goto(url)

            return {
                "success": True,
                "tab_id": tab_id,
                "url": url
            }
        except Exception as e:
            return {"error": f"Failed to navigate: {str(e)}"}

    async def _get_current_url(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get current URL of a tab"""
        if not self.browser:
            return {"error": "Browser not launched"}

        tab_id = params.get("tab_id", 0)
        if tab_id >= len(self.pages) or tab_id < 0:
            return {"error": f"Invalid tab_id: {tab_id}"}

        try:
            page = self.pages[tab_id]
            url = page.url

            return {
                "tab_id": tab_id,
                "url": url
            }
        except Exception as e:
            return {"error": f"Failed to get URL: {str(e)}"}

    async def _get_page_content(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get page content"""
        if not self.browser:
            return {"error": "Browser not launched"}

        tab_id = params.get("tab_id", 0)
        if tab_id >= len(self.pages) or tab_id < 0:
            return {"error": f"Invalid tab_id: {tab_id}"}

        try:
            page = self.pages[tab_id]
            content = await page.content()

            return {
                "tab_id": tab_id,
                "content": content
            }
        except Exception as e:
            return {"error": f"Failed to get page content: {str(e)}"}

    async def _execute_script(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute JavaScript in a tab"""
        if not self.browser:
            return {"error": "Browser not launched"}

        tab_id = params.get("tab_id", 0)
        script = params.get("script")

        if not script:
            return {"error": "script parameter required"}

        if tab_id >= len(self.pages) or tab_id < 0:
            return {"error": f"Invalid tab_id: {tab_id}"}

        try:
            page = self.pages[tab_id]
            result = await page.evaluate(script)

            return {
                "tab_id": tab_id,
                "result": result
            }
        except Exception as e:
            return {"error": f"Failed to execute script: {str(e)}"}

    async def _take_screenshot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Take screenshot of a tab"""
        if not self.browser:
            return {"error": "Browser not launched"}

        tab_id = params.get("tab_id", 0)
        path = params.get("path", "screenshot.png")

        if tab_id >= len(self.pages) or tab_id < 0:
            return {"error": f"Invalid tab_id: {tab_id}"}

        try:
            page = self.pages[tab_id]
            await page.screenshot({'path': path})

            return {
                "success": True,
                "tab_id": tab_id,
                "path": path
            }
        except Exception as e:
            return {"error": f"Failed to take screenshot: {str(e)}"}

    async def _get_tabs(self) -> Dict[str, Any]:
        """Get list of tabs"""
        if not self.browser:
            return {"error": "Browser not launched"}

        try:
            tabs = []
            for i, page in enumerate(self.pages):
                try:
                    url = page.url
                    title = await page.title()
                except:
                    url = "unknown"
                    title = "unknown"

                tabs.append({
                    "tab_id": i,
                    "url": url,
                    "title": title
                })

            return {
                "tabs": tabs,
                "count": len(tabs)
            }
        except Exception as e:
            return {"error": f"Failed to get tabs: {str(e)}"}

    def cleanup(self):
        """Cleanup resources"""
        if self.browser:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.browser.close())
                loop.close()
            except:
                pass
        self.browser = None
        self.pages = []
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = ChromePlugin
PLUGIN_NAME = "chrome"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Chrome browser automation via CDP"
PLUGIN_ACTIONS = [
    "launch_browser", "close_browser", "new_tab", "close_tab",
    "navigate", "get_current_url", "get_page_content", "execute_script",
    "take_screenshot", "get_tabs"
]