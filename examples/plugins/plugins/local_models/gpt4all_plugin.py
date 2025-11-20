"""
GPT4All Plugin
Local AI models for CPU inference
"""

from typing import Dict, Any, Optional, List
import os


class GPT4AllPlugin:
    """Plugin for GPT4All local models"""

    name = "gpt4all"
    version = "1.0.0"
    description = "Integration with GPT4All for CPU-based local AI models"
    author = "Windows AI Team"

    def __init__(self):
        self.model = None
        self.client = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the GPT4All plugin"""
        try:
            from gpt4all import GPT4All

            model_name = (
                config.get("model") if config
                else os.getenv("GPT4ALL_MODEL", "mistral-7b-openorca.Q4_0.gguf")
            )

            self.model = GPT4All(model_name)
            self._initialized = True
            return True

        except ImportError:
            print("gpt4all package not installed. Install with: pip install gpt4all")
            return False
        except Exception as e:
            print(f"Error initializing GPT4All plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a GPT4All action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "chat":
                return self._chat(params)
            elif action == "generate":
                return self._generate(params)
            elif action == "embed":
                return self._get_embeddings(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate chat completion"""
        messages = params.get("messages", [])
        max_tokens = params.get("max_tokens", 200)

        with self.model.chat_session():
            # Get last message
            if messages:
                last_message = messages[-1].get("content", "")
                response = self.model.generate(last_message, max_tokens=max_tokens)

                return {
                    "success": True,
                    "response": response
                }

        return {"success": False, "error": "No messages provided"}

    def _generate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate text completion"""
        prompt = params.get("prompt", "")
        max_tokens = params.get("max_tokens", 200)
        temp = params.get("temperature", 0.7)

        response = self.model.generate(
            prompt,
            max_tokens=max_tokens,
            temp=temp
        )

        return {
            "success": True,
            "response": response
        }

    def _get_embeddings(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get text embeddings"""
        text = params.get("text", "")

        try:
            embedding = self.model.embed(text)
            return {
                "success": True,
                "embedding": embedding
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.model = None
        return True
