"""
Jan AI Local LLM Plugin
Supports local LLM chat via Jan AI's OpenAI-compatible API
"""

from typing import Dict, Any, Optional, List
import os


class JanPlugin:
    """Plugin for Jan AI local models"""

    name = "jan"
    version = "1.0.0"
    description = "Integration with Jan AI local models"
    author = "Windows AI Team"

    def __init__(self):
        self.api_key: Optional[str] = None
        self.client = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Jan plugin"""
        try:
            from openai import OpenAI

            # Jan uses OpenAI-compatible API at localhost:1337
            # No API key required for local instance
            self.api_key = config.get("api_key", "jan-local") if config else "jan-local"

            self.client = OpenAI(
                api_key=self.api_key,
                base_url="http://localhost:1337/v1"
            )
            self._initialized = True
            return True

        except ImportError:
            print("openai package not installed. Install with: pip install openai")
            return False
        except Exception as e:
            print(f"Error initializing Jan plugin: {e}")
            print("Make sure Jan AI is running locally on port 1337")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Jan action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Make sure Jan AI is running locally."}

        try:
            if action == "chat":
                return self._chat(params)
            elif action == "stream_chat":
                return self._stream_chat(params)
            elif action == "list_models":
                return self._list_models()
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {"error": str(e)}

    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Chat completion"""
        messages = params.get("messages", [])
        model = params.get("model", "")  # Jan will use the active model
        temperature = params.get("temperature", 0.7)
        max_tokens = params.get("max_tokens", None)
        top_p = params.get("top_p", 1.0)

        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p
        )

        return {
            "response": response.choices[0].message.content,
            "model": response.model,
            "finish_reason": response.choices[0].finish_reason,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }

    def _stream_chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Stream chat completion"""
        messages = params.get("messages", [])
        model = params.get("model", "")
        temperature = params.get("temperature", 0.7)
        max_tokens = params.get("max_tokens", None)

        # Collect streamed response
        full_response = ""
        for chunk in self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        ):
            if chunk.choices[0].delta.content:
                full_response += chunk.choices[0].delta.content

        return {
            "response": full_response,
            "model": model,
            "streamed": True
        }

    def _list_models(self) -> Dict[str, Any]:
        """List available models"""
        try:
            response = self.client.models.list()
            models = [{"id": model.id, "owned_by": "jan"} for model in response.data]

            return {
                "models": models,
                "count": len(models)
            }
        except Exception as e:
            # Fallback to empty list if API doesn't support models endpoint
            return {
                "models": [],
                "count": 0,
                "error": str(e)
            }

    def cleanup(self):
        """Cleanup resources"""
        self.client = None
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = JanPlugin
PLUGIN_NAME = "jan"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with Jan AI local models"
PLUGIN_ACTIONS = ["chat", "stream_chat", "list_models"]