"""
FastChat Plugin
Platform for training and serving LLM-based chatbots
"""

from typing import Dict, Any, Optional, List
import os


class FastChatPlugin:
    """Plugin for FastChat"""

    name = "fastchat"
    version = "1.0.0"
    description = "Integration with FastChat for LLM-based chatbots"
    author = "Windows AI Team"

    def __init__(self):
        self.base_url: str = "http://localhost:8000"
        self.client = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the FastChat plugin"""
        try:
            import requests

            self.base_url = (
                config.get("base_url") if config
                else os.getenv("FASTCHAT_HOST", "http://localhost:8000")
            )

            self.client = requests
            self._initialized = True
            return True

        except ImportError:
            print("requests package not installed. Install with: pip install requests")
            return False
        except Exception as e:
            print(f"Error initializing FastChat plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a FastChat action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "chat":
                return self._chat(params)
            elif action == "list_models":
                return self._list_models()
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate chat completion"""
        messages = params.get("messages", [])
        model = params.get("model", "vicuna-7b-v1.5")

        response = self.client.post(
            f"{self.base_url}/v1/chat/completions",
            json={
                "model": model,
                "messages": messages
            }
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "response": data.get("choices", [{}])[0].get("message", {}).get("content", "")
            }
        return {"success": False, "error": response.text}

    def _list_models(self) -> Dict[str, Any]:
        """List available models"""
        response = self.client.get(f"{self.base_url}/v1/models")

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "models": data.get("data", [])
            }
        return {"success": False, "error": response.text}

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.client = None
        return True
