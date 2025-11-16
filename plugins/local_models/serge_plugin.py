"""
Serge Plugin
Web interface for chatting with Alpaca models
"""

from typing import Dict, Any, Optional, List
import os


class SergePlugin:
    """Plugin for Serge local chat interface"""

    name = "serge"
    version = "1.0.0"
    description = "Integration with Serge for Alpaca-based chat"
    author = "Windows AI Team"

    def __init__(self):
        self.base_url: str = "http://localhost:8008"
        self.client = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Serge plugin"""
        try:
            import requests

            self.base_url = (
                config.get("base_url") if config
                else os.getenv("SERGE_HOST", "http://localhost:8008")
            )

            self.client = requests
            self._initialized = True
            return True

        except ImportError:
            print("requests package not installed. Install with: pip install requests")
            return False
        except Exception as e:
            print(f"Error initializing Serge plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Serge action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "chat":
                return self._chat(params)
            elif action == "models":
                return self._list_models()
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send chat message"""
        message = params.get("message", "")
        model = params.get("model", "alpaca-7b")

        response = self.client.post(
            f"{self.base_url}/api/chat",
            json={
                "prompt": message,
                "model": model
            }
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "response": data.get("response", "")
            }
        return {"success": False, "error": response.text}

    def _list_models(self) -> Dict[str, Any]:
        """List available models"""
        response = self.client.get(f"{self.base_url}/api/models")

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "models": data.get("models", [])
            }
        return {"success": False, "error": response.text}

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.client = None
        return True
