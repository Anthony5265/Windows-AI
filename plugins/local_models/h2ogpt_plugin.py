"""
h2oGPT Plugin
Enterprise-grade local LLM platform
"""

from typing import Dict, Any, Optional, List
import os


class H2OGPTPlugin:
    """Plugin for h2oGPT"""

    name = "h2ogpt"
    version = "1.0.0"
    description = "Integration with h2oGPT for enterprise local AI"
    author = "Windows AI Team"

    def __init__(self):
        self.base_url: str = "http://localhost:7860"
        self.client = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the h2oGPT plugin"""
        try:
            import requests

            self.base_url = (
                config.get("base_url") if config
                else os.getenv("H2OGPT_HOST", "http://localhost:7860")
            )

            self.client = requests
            self._initialized = True
            return True

        except ImportError:
            print("requests package not installed. Install with: pip install requests")
            return False
        except Exception as e:
            print(f"Error initializing h2oGPT plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an h2oGPT action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "chat":
                return self._chat(params)
            elif action == "summarize":
                return self._summarize(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Chat with h2oGPT"""
        message = params.get("message", "")

        response = self.client.post(
            f"{self.base_url}/api/predict",
            json={
                "data": [message]
            }
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "response": data.get("data", [""])[0]
            }
        return {"success": False, "error": response.text}

    def _summarize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize text or documents"""
        text = params.get("text", "")

        prompt = f"Summarize the following text:\n\n{text}"

        return self._chat({"message": prompt})

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.client = None
        return True
