"""
OpenAI Embeddings Plugin
Text embeddings using ada-002
"""

from typing import Dict, Any, Optional, List
import os


class OpenAIEmbeddingsPlugin:
    """Plugin for OpenAI Embeddings"""

    name = "openai_embeddings"
    version = "1.0.0"
    description = "Integration with OpenAI Embeddings (ada-002)"
    author = "Windows AI Team"

    def __init__(self):
        self.api_key: Optional[str] = None
        self.client = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the OpenAI Embeddings plugin"""
        try:
            import openai

            self.api_key = (
                config.get("api_key") if config
                else os.getenv("OPENAI_API_KEY")
            )

            if not self.api_key:
                return False

            openai.api_key = self.api_key
            self.client = openai
            self._initialized = True
            return True

        except ImportError:
            print("openai package not installed. Install with: pip install openai")
            return False
        except Exception as e:
            print(f"Error initializing OpenAI Embeddings plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an OpenAI Embeddings action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "embed":
                return self._embed(params)
            elif action == "embed_batch":
                return self._embed_batch(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _embed(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Embed single text"""
        text = params.get("text", "")
        model = params.get("model", "text-embedding-ada-002")

        response = self.client.Embedding.create(
            input=text,
            model=model
        )

        return {
            "success": True,
            "embedding": response.data[0].embedding,
            "usage": response.usage
        }

    def _embed_batch(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Embed multiple texts"""
        texts = params.get("texts", [])
        model = params.get("model", "text-embedding-ada-002")

        response = self.client.Embedding.create(
            input=texts,
            model=model
        )

        embeddings = [item.embedding for item in response.data]

        return {
            "success": True,
            "embeddings": embeddings,
            "usage": response.usage
        }

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.client = None
        return True
