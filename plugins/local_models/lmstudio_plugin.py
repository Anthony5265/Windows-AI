"""
LM Studio Plugin
Local AI model platform with GUI
"""

from typing import Dict, Any, Optional, List
import os


class LMStudioPlugin:
    """Plugin for LM Studio local model platform"""

    name = "lmstudio"
    version = "1.0.0"
    description = "Integration with LM Studio for local AI models"
    author = "Windows AI Team"

    def __init__(self):
        self.base_url: str = "http://localhost:1234"
        self.client = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the LM Studio plugin"""
        try:
            import requests

            self.base_url = (
                config.get("base_url") if config
                else os.getenv("LMSTUDIO_HOST", "http://localhost:1234")
            )

            self.client = requests
            self._initialized = True
            return True

        except ImportError:
            print("requests package not installed. Install with: pip install requests")
            return False
        except Exception as e:
            print(f"Error initializing LM Studio plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an LM Studio action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "chat":
                return self._chat(params)
            elif action == "completion":
                return self._completion(params)
            elif action == "list_models":
                return self._list_models()
            elif action == "embeddings":
                return self._get_embeddings(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate chat completion"""
        messages = params.get("messages", [])
        temperature = params.get("temperature", 0.7)
        max_tokens = params.get("max_tokens", 2000)

        response = self.client.post(
            f"{self.base_url}/v1/chat/completions",
            json={
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "response": data.get("choices", [{}])[0].get("message", {}).get("content", ""),
                "usage": data.get("usage", {})
            }
        return {"success": False, "error": response.text}

    def _completion(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate text completion"""
        prompt = params.get("prompt", "")
        temperature = params.get("temperature", 0.7)

        response = self.client.post(
            f"{self.base_url}/v1/completions",
            json={
                "prompt": prompt,
                "temperature": temperature
            }
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "response": data.get("choices", [{}])[0].get("text", "")
            }
        return {"success": False, "error": response.text}

    def _list_models(self) -> Dict[str, Any]:
        """List loaded models"""
        response = self.client.get(f"{self.base_url}/v1/models")

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "models": data.get("data", [])
            }
        return {"success": False, "error": response.text}

    def _get_embeddings(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get text embeddings"""
        text = params.get("text", "")

        response = self.client.post(
            f"{self.base_url}/v1/embeddings",
            json={
                "input": text
            }
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "embedding": data.get("data", [{}])[0].get("embedding", [])
            }
        return {"success": False, "error": response.text}

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.client = None
        return True
