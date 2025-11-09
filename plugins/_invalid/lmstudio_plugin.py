"""
LM Studio Local Model Provider Plugin
Supports local model chat, model listing, and server control
"""

from typing import Dict, Any, Optional, List
import os
import requests


class LMStudioPlugin:
    """Plugin for LM Studio local models"""

    name = "lmstudio"
    version = "1.0.0"
    description = "Integration with LM Studio local models"
    author = "Windows AI Team"

    def __init__(self):
        self.base_url: Optional[str] = None
        self.client = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the LM Studio plugin"""
        try:
            # Get base URL from config or use default
            self.base_url = (
                config.get("base_url") if config
                else os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234")
            )

            # Test connection
            if self._test_connection():
                self._initialized = True
                return True
            else:
                print(f"Could not connect to LM Studio server at {self.base_url}")
                return False

        except Exception as e:
            print(f"Error initializing LM Studio plugin: {e}")
            return False

    def _test_connection(self) -> bool:
        """Test connection to LM Studio server"""
        try:
            response = requests.get(f"{self.base_url}/v1/models", timeout=5)
            return response.status_code == 200
        except:
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an LM Studio action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please ensure LM Studio server is running."}

        try:
            if action == "chat":
                return self._chat(params)
            elif action == "list_models":
                return self._list_models(params)
            elif action == "server_status":
                return self._server_status(params)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {"error": str(e)}

    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Chat completion using local LM Studio model"""
        messages = params.get("messages", [])
        model = params.get("model", "")
        temperature = params.get("temperature", 0.7)
        max_tokens = params.get("max_tokens", 256)
        stream = params.get("stream", False)

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }

        response = requests.post(
            f"{self.base_url}/v1/chat/completions",
            json=payload,
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            return {
                "response": result["choices"][0]["message"]["content"],
                "model": result.get("model", model),
                "usage": result.get("usage", {}),
                "finish_reason": result["choices"][0].get("finish_reason")
            }
        else:
            return {"error": f"LM Studio API error: {response.status_code} - {response.text}"}

    def _list_models(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List available models in LM Studio"""
        response = requests.get(f"{self.base_url}/v1/models", timeout=10)

        if response.status_code == 200:
            result = response.json()
            models = [
                {
                    "id": model["id"],
                    "object": model.get("object", "model"),
                    "owned_by": model.get("owned_by", "lmstudio")
                }
                for model in result.get("data", [])
            ]
            return {
                "models": models,
                "count": len(models)
            }
        else:
            return {"error": f"Failed to list models: {response.status_code} - {response.text}"}

    def _server_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Check LM Studio server status"""
        try:
            response = requests.get(f"{self.base_url}/v1/models", timeout=5)
            if response.status_code == 200:
                return {
                    "status": "running",
                    "base_url": self.base_url,
                    "message": "LM Studio server is running and accessible"
                }
            else:
                return {
                    "status": "error",
                    "base_url": self.base_url,
                    "message": f"Server responded with status {response.status_code}"
                }
        except requests.exceptions.RequestException as e:
            return {
                "status": "not_running",
                "base_url": self.base_url,
                "message": f"Could not connect to LM Studio server: {str(e)}"
            }

    def cleanup(self):
        """Cleanup resources"""
        self._initialized = False


# Plugin metadata for registration
PLUGIN_CLASS = LMStudioPlugin
PLUGIN_NAME = "lmstudio"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with LM Studio local models"
PLUGIN_ACTIONS = ["chat", "list_models", "server_status"]