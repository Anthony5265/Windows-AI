"""
Tabnine AI Plugin
Supports AI-powered code completion
"""

from typing import Dict, Any, Optional, List
import os


class TabninePlugin:
    """Plugin for Tabnine AI code completion"""

    name = "tabnine"
    version = "1.0.0"
    description = "Integration with Tabnine AI for code completion"
    author = "Windows AI Team"

    def __init__(self):
        self.api_key: Optional[str] = None
        self.client = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Tabnine plugin"""
        try:
            import requests

            # Get API key from config or environment
            self.api_key = (
                config.get("api_key") if config
                else os.getenv("TABNINE_API_KEY")
            )

            if not self.api_key:
                return False

            self.client = requests
            self.base_url = "https://api.tabnine.com/v1"
            self._initialized = True
            return True

        except ImportError:
            print("requests package not installed. Install with: pip install requests")
            return False
        except Exception as e:
            print(f"Error initializing Tabnine plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Tabnine action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "complete":
                return self._complete(params)
            elif action == "chat":
                return self._chat(params)
            elif action == "generate":
                return self._generate(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _complete(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code completion"""
        before = params.get("before", "")
        after = params.get("after", "")
        filename = params.get("filename", "untitled.py")
        language = params.get("language", "python")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        response = self.client.post(
            f"{self.base_url}/completions",
            headers=headers,
            json={
                "before": before,
                "after": after,
                "filename": filename,
                "language": language
            }
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "completions": data.get("results", [])
            }
        return {"success": False, "error": response.text}

    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Chat with Tabnine AI"""
        messages = params.get("messages", [])
        context = params.get("context", {})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        response = self.client.post(
            f"{self.base_url}/chat",
            headers=headers,
            json={
                "messages": messages,
                "context": context
            }
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "response": data.get("message", "")
            }
        return {"success": False, "error": response.text}

    def _generate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code from description"""
        description = params.get("description", "")
        language = params.get("language", "python")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        response = self.client.post(
            f"{self.base_url}/generate",
            headers=headers,
            json={
                "prompt": description,
                "language": language
            }
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "code": data.get("code", "")
            }
        return {"success": False, "error": response.text}

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.client = None
        return True
