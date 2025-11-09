"""
Forefront AI Model Provider Plugin
Supports Phi-2, Mistral-7B, Mixtral-7Bx8 models
"""

from typing import Dict, Any, Optional, List
import os


class ForefrontPlugin:
    """Plugin for Forefront AI models"""

    name = "forefront"
    version = "1.0.0"
    description = "Integration with Forefront AI (Phi-2, Mistral, Mixtral)"
    author = "Windows AI Team"

    def __init__(self):
        self.api_key: Optional[str] = None
        self.base_url = "https://api.forefront.ai/v1"
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Forefront AI plugin"""
        try:
            # Get API key from config or environment
            self.api_key = (
                config.get("api_key") if config
                else os.getenv("FOREFRONT_API_KEY")
            )

            if not self.api_key:
                return False

            self._initialized = True
            return True

        except Exception as e:
            print(f"Error initializing Forefront AI plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Forefront AI action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please provide API key."}

        try:
            if action == "chat":
                return self._chat(params)
            elif action == "complete":
                return self._complete(params)
            elif action == "list_models":
                return self._list_models()
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {"error": str(e)}

    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Chat completion"""
        import requests

        messages = params.get("messages", [])
        model = params.get("model", "mistralai/Mistral-7B-Instruct-v0.1")
        # Popular models:
        # - microsoft/phi-2
        # - mistralai/Mistral-7B-Instruct-v0.1
        # - mistralai/Mixtral-8x7B-Instruct-v0.1 (coming soon)

        max_tokens = params.get("max_tokens", 512)
        temperature = params.get("temperature", 0.7)
        stop = params.get("stop", [])

        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stop": stop
            },
            timeout=60
        )
        response.raise_for_status()
        data = response.json()

        return {
            "response": data["choices"][0]["message"]["content"],
            "model": data.get("model", model),
            "finish_reason": data["choices"][0]["finish_reason"],
            "usage": data.get("usage", {})
        }

    def _complete(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Text completion"""
        import requests

        prompt = params.get("prompt", "")
        model = params.get("model", "mistralai/Mistral-7B-Instruct-v0.1")
        # Popular completion models:
        # - microsoft/phi-2
        # - mistralai/Mistral-7B-Instruct-v0.1
        # - mistralai/Mixtral-8x7B-Instruct-v0.1 (coming soon)

        max_tokens = params.get("max_tokens", 512)
        temperature = params.get("temperature", 0.7)
        stop = params.get("stop", [])

        response = requests.post(
            f"{self.base_url}/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stop": stop
            },
            timeout=60
        )
        response.raise_for_status()
        data = response.json()

        return {
            "text": data["choices"][0]["text"],
            "model": data.get("model", model),
            "finish_reason": data["choices"][0]["finish_reason"],
            "usage": data.get("usage", {})
        }

    def _list_models(self) -> Dict[str, Any]:
        """List available models"""
        # Forefront doesn't seem to have a models endpoint in their docs
        # Return known models based on documentation
        models = [
            {
                "id": "microsoft/phi-2",
                "name": "Phi-2",
                "creator": "Microsoft",
                "parameters": "3 billion",
                "context_length": 4096
            },
            {
                "id": "mistralai/Mistral-7B-Instruct-v0.1",
                "name": "Mistral-7B",
                "creator": "Mistral",
                "parameters": "7 billion",
                "context_length": 4096
            },
            {
                "id": "mistralai/Mixtral-8x7B-Instruct-v0.1",
                "name": "Mixtral-7Bx8",
                "creator": "Mistral",
                "parameters": "46.7 billion",
                "context_length": 4096,
                "status": "coming soon"
            }
        ]

        return {
            "models": models,
            "count": len(models)
        }

    def cleanup(self):
        """Cleanup resources"""
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = ForefrontPlugin
PLUGIN_NAME = "forefront"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with Forefront AI models"
PLUGIN_ACTIONS = ["chat", "complete", "list_models"]