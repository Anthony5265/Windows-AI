"""
Selenium Web Automation Plugin
Supports multi-browser testing with Chrome, Firefox, Edge, and Safari
"""

from typing import Dict, Any, Optional, List
import os
import time
import base64
from io import BytesIO


class SeleniumPlugin:
    """Plugin for web automation using Selenium WebDriver"""

    name = "selenium"
    version = "1.0.0"
    description = "Web automation and multi-browser testing with Selenium"
    author = "Windows AI Team"

    def __init__(self):
        self.drivers = {}  # Store multiple browser instances
        self._initialized = False

        # Supported browsers
        self.supported_browsers = {
            "chrome": "Chrome",
            "firefox": "Firefox",
            "edge": "Microsoft Edge",
            "safari": "Safari"
        }

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Selenium plugin"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options as ChromeOptions
            from selenium.webdriver.firefox.options import Options as FirefoxOptions
            from selenium.webdriver.edge.options import Options as EdgeOptions
            from selenium.webdriver.safari.options import Options as SafariOptions

            # Store options classes for dynamic instantiation
            self.webdriver_options = {
                "chrome": ChromeOptions,
                "firefox": FirefoxOptions,
                "edge": EdgeOptions,
                "safari": SafariOptions
            }

            self._initialized = True
            return True

        except ImportError:
            print("selenium package not installed. Install with: pip install selenium")
            return False
        except Exception as e:
            print(f"Error initializing Selenium plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Selenium action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please install selenium: pip install selenium"}

        try:
            if action == "start_browser":
                return self._start_browser(params)
            elif action == "close_browser":
                return self._close_browser(params)
            elif action == "navigate":
                return self._navigate(params)
            elif action == "click":
                return self._click(params)
            elif action == "type_text":
                return self._type_text(params)
            elif action == "get_text":
                return self._get_text(params)
            elif action == "get_attribute":
                return self._get_attribute(params)
            elif action == "screenshot":
                return self._screenshot(params)
            elif action == "wait_for_element":
                return self._wait_for_element(params)
            elif action == "execute_script":
                return self._execute_script(params)
            elif action == "list_browsers":
                return self._list_browsers(params)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {"error": str(e)}

    def _start_browser(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Start a new browser instance"""
        browser = params.get("browser", "chrome").lower()
        session_id = params.get("session_id", f"{browser}_{int(time.time())}")
        headless = params.get("headless", False)
        window_size = params.get("window_size", "1920x1080")

        if browser not in self.supported_browsers:
            return {"error": f"Unsupported browser: {browser}. Supported: {list(self.supported_browsers.keys())}"}

        if session_id in self.drivers:
            return {"error": f"Session {session_id} already exists"}

        try:
            from selenium import webdriver

            # Configure browser options
            options_class = self.webdriver_options[browser]
            options = options_class()

            if headless:
                if browser == "chrome" or browser == "edge":
                    options.add_argument("--headless")
                elif browser == "firefox":
                    options.add_argument("--headless")

            # Set window size
            width, height = window_size.split('x')
            options.add_argument(f"--window-size={width},{height}")

            # Additional options for stability
            if browser == "chrome" or browser == "edge":
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--disable-gpu")
                options.add_argument("--disable-extensions")
            elif browser == "firefox":
                options.add_argument("--disable-gpu")

            # Create driver instance
            if browser == "chrome":
                driver = webdriver.Chrome(options=options)
            elif browser == "firefox":
                driver = webdriver.Firefox(options=options)
            elif browser == "edge":
                driver = webdriver.Edge(options=options)
            elif browser == "safari":
                driver = webdriver.Safari(options=options)

            # Store driver
            self.drivers[session_id] = {
                "driver": driver,
                "browser": browser,
                "start_time": time.time()
            }

            return {
                "session_id": session_id,
                "browser": browser,
                "status": "started",
                "window_size": window_size,
                "headless": headless
            }

        except Exception as e:
            return {"error": f"Failed to start {browser} browser: {str(e)}"}

    def _close_browser(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Close a browser instance"""
        session_id = params.get("session_id")
        if not session_id:
            return {"error": "session_id parameter required"}

        if session_id not in self.drivers:
            return {"error": f"Session {session_id} not found"}

        try:
            driver_info = self.drivers[session_id]
            driver = driver_info["driver"]
            driver.quit()

            # Remove from storage
            del self.drivers[session_id]

            return {
                "session_id": session_id,
                "browser": driver_info["browser"],
                "status": "closed",
                "duration": time.time() - driver_info["start_time"]
            }

        except Exception as e:
            return {"error": f"Failed to close browser: {str(e)}"}

    def _navigate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Navigate to a URL"""
        session_id = params.get("session_id")
        url = params.get("url")

        if not session_id or not url:
            return {"error": "session_id and url parameters required"}

        if session_id not in self.drivers:
            return {"error": f"Session {session_id} not found"}

        try:
            driver = self.drivers[session_id]["driver"]
            driver.get(url)

            return {
                "session_id": session_id,
                "url": url,
                "title": driver.title,
                "current_url": driver.current_url
            }

        except Exception as e:
            return {"error": f"Failed to navigate to {url}: {str(e)}"}

    def _click(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Click on an element"""
        session_id = params.get("session_id")
        selector = params.get("selector")
        selector_type = params.get("selector_type", "css_selector")  # css_selector, xpath, id, class_name, etc.

        if not session_id or not selector:
            return {"error": "session_id and selector parameters required"}

        if session_id not in self.drivers:
            return {"error": f"Session {session_id} not found"}

        try:
            from selenium.webdriver.common.by import By

            driver = self.drivers[session_id]["driver"]

            # Map selector type to Selenium By
            by_map = {
                "css_selector": By.CSS_SELECTOR,
                "xpath": By.XPATH,
                "id": By.ID,
                "class_name": By.CLASS_NAME,
                "name": By.NAME,
                "tag_name": By.TAG_NAME,
                "link_text": By.LINK_TEXT,
                "partial_link_text": By.PARTIAL_LINK_TEXT
            }

            if selector_type not in by_map:
                return {"error": f"Unsupported selector_type: {selector_type}"}

            element = driver.find_element(by_map[selector_type], selector)
            element.click()

            return {
                "session_id": session_id,
                "selector": selector,
                "selector_type": selector_type,
                "status": "clicked"
            }

        except Exception as e:
            return {"error": f"Failed to click element: {str(e)}"}

    def _type_text(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Type text into an element"""
        session_id = params.get("session_id")
        selector = params.get("selector")
        text = params.get("text", "")
        selector_type = params.get("selector_type", "css_selector")
        clear_first = params.get("clear_first", True)

        if not session_id or not selector:
            return {"error": "session_id and selector parameters required"}

        if session_id not in self.drivers:
            return {"error": f"Session {session_id} not found"}

        try:
            from selenium.webdriver.common.by import By

            driver = self.drivers[session_id]["driver"]

            by_map = {
                "css_selector": By.CSS_SELECTOR,
                "xpath": By.XPATH,
                "id": By.ID,
                "class_name": By.CLASS_NAME,
                "name": By.NAME,
                "tag_name": By.TAG_NAME,
                "link_text": By.LINK_TEXT,
                "partial_link_text": By.PARTIAL_LINK_TEXT
            }

            element = driver.find_element(by_map[selector_type], selector)

            if clear_first:
                element.clear()

            element.send_keys(text)

            return {
                "session_id": session_id,
                "selector": selector,
                "selector_type": selector_type,
                "text": text,
                "status": "typed"
            }

        except Exception as e:
            return {"error": f"Failed to type text: {str(e)}"}

    def _get_text(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get text from an element"""
        session_id = params.get("session_id")
        selector = params.get("selector")
        selector_type = params.get("selector_type", "css_selector")

        if not session_id or not selector:
            return {"error": "session_id and selector parameters required"}

        if session_id not in self.drivers:
            return {"error": f"Session {session_id} not found"}

        try:
            from selenium.webdriver.common.by import By

            driver = self.drivers[session_id]["driver"]

            by_map = {
                "css_selector": By.CSS_SELECTOR,
                "xpath": By.XPATH,
                "id": By.ID,
                "class_name": By.CLASS_NAME,
                "name": By.NAME,
                "tag_name": By.TAG_NAME,
                "link_text": By.LINK_TEXT,
                "partial_link_text": By.PARTIAL_LINK_TEXT
            }

            element = driver.find_element(by_map[selector_type], selector)
            text = element.text

            return {
                "session_id": session_id,
                "selector": selector,
                "selector_type": selector_type,
                "text": text
            }

        except Exception as e:
            return {"error": f"Failed to get text: {str(e)}"}

    def _get_attribute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get attribute value from an element"""
        session_id = params.get("session_id")
        selector = params.get("selector")
        attribute = params.get("attribute")
        selector_type = params.get("selector_type", "css_selector")

        if not session_id or not selector or not attribute:
            return {"error": "session_id, selector, and attribute parameters required"}

        if session_id not in self.drivers:
            return {"error": f"Session {session_id} not found"}

        try:
            from selenium.webdriver.common.by import By

            driver = self.drivers[session_id]["driver"]

            by_map = {
                "css_selector": By.CSS_SELECTOR,
                "xpath": By.XPATH,
                "id": By.ID,
                "class_name": By.CLASS_NAME,
                "name": By.NAME,
                "tag_name": By.TAG_NAME,
                "link_text": By.LINK_TEXT,
                "partial_link_text": By.PARTIAL_LINK_TEXT
            }

            element = driver.find_element(by_map[selector_type], selector)
            value = element.get_attribute(attribute)

            return {
                "session_id": session_id,
                "selector": selector,
                "selector_type": selector_type,
                "attribute": attribute,
                "value": value
            }

        except Exception as e:
            return {"error": f"Failed to get attribute: {str(e)}"}

    def _screenshot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Take a screenshot"""
        session_id = params.get("session_id")
        selector = params.get("selector", None)  # Optional: screenshot specific element
        selector_type = params.get("selector_type", "css_selector")

        if not session_id:
            return {"error": "session_id parameter required"}

        if session_id not in self.drivers:
            return {"error": f"Session {session_id} not found"}

        try:
            driver = self.drivers[session_id]["driver"]

            if selector:
                # Screenshot specific element
                from selenium.webdriver.common.by import By

                by_map = {
                    "css_selector": By.CSS_SELECTOR,
                    "xpath": By.XPATH,
                    "id": By.ID,
                    "class_name": By.CLASS_NAME,
                    "name": By.NAME,
                    "tag_name": By.TAG_NAME,
                    "link_text": By.LINK_TEXT,
                    "partial_link_text": By.PARTIAL_LINK_TEXT
                }

                element = driver.find_element(by_map[selector_type], selector)
                screenshot_data = element.screenshot_as_png
            else:
                # Full page screenshot
                screenshot_data = driver.get_screenshot_as_png()

            # Convert to base64 for JSON serialization
            screenshot_b64 = base64.b64encode(screenshot_data).decode('utf-8')

            return {
                "session_id": session_id,
                "selector": selector,
                "screenshot": screenshot_b64,
                "format": "base64"
            }

        except Exception as e:
            return {"error": f"Failed to take screenshot: {str(e)}"}

    def _wait_for_element(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Wait for an element to be present"""
        session_id = params.get("session_id")
        selector = params.get("selector")
        selector_type = params.get("selector_type", "css_selector")
        timeout = params.get("timeout", 10)
        condition = params.get("condition", "presence")  # presence, visibility, clickable

        if not session_id or not selector:
            return {"error": "session_id and selector parameters required"}

        if session_id not in self.drivers:
            return {"error": f"Session {session_id} not found"}

        try:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC

            driver = self.drivers[session_id]["driver"]

            by_map = {
                "css_selector": By.CSS_SELECTOR,
                "xpath": By.XPATH,
                "id": By.ID,
                "class_name": By.CLASS_NAME,
                "name": By.NAME,
                "tag_name": By.TAG_NAME,
                "link_text": By.LINK_TEXT,
                "partial_link_text": By.PARTIAL_LINK_TEXT
            }

            wait = WebDriverWait(driver, timeout)

            condition_map = {
                "presence": EC.presence_of_element_located,
                "visibility": EC.visibility_of_element_located,
                "clickable": EC.element_to_be_clickable
            }

            if condition not in condition_map:
                return {"error": f"Unsupported condition: {condition}"}

            element = wait.until(condition_map[condition]((by_map[selector_type], selector)))

            return {
                "session_id": session_id,
                "selector": selector,
                "selector_type": selector_type,
                "condition": condition,
                "timeout": timeout,
                "status": "found"
            }

        except Exception as e:
            return {"error": f"Failed to wait for element: {str(e)}"}

    def _execute_script(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute JavaScript code"""
        session_id = params.get("session_id")
        script = params.get("script")
        args = params.get("args", [])

        if not session_id or not script:
            return {"error": "session_id and script parameters required"}

        if session_id not in self.drivers:
            return {"error": f"Session {session_id} not found"}

        try:
            driver = self.drivers[session_id]["driver"]
            result = driver.execute_script(script, *args)

            return {
                "session_id": session_id,
                "script": script,
                "result": result
            }

        except Exception as e:
            return {"error": f"Failed to execute script: {str(e)}"}

    def _list_browsers(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List active browser sessions"""
        sessions = []
        for session_id, info in self.drivers.items():
            sessions.append({
                "session_id": session_id,
                "browser": info["browser"],
                "start_time": info["start_time"],
                "duration": time.time() - info["start_time"]
            })

        return {
            "sessions": sessions,
            "count": len(sessions),
            "supported_browsers": list(self.supported_browsers.keys())
        }

    def cleanup(self):
        """Cleanup all browser instances"""
        for session_id, info in self.drivers.items():
            try:
                info["driver"].quit()
            except:
                pass  # Ignore errors during cleanup

        self.drivers.clear()
        self._initialized = False


# Plugin metadata for registration
PLUGIN_CLASS = SeleniumPlugin
PLUGIN_NAME = "selenium"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Web automation and multi-browser testing with Selenium"
PLUGIN_ACTIONS = [
    "start_browser", "close_browser", "navigate", "click", "type_text",
    "get_text", "get_attribute", "screenshot", "wait_for_element",
    "execute_script", "list_browsers"
]