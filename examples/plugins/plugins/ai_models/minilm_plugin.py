"""
MiniLM Plugin
Lightweight and fast sentence embeddings
"""

from typing import Dict, Any, Optional, List
import os


class MiniLMPlugin:
    """Plugin for all-MiniLM-L6-v2 embeddings"""

    name = "minilm"
    version = "1.0.0"
    description = "Integration with all-MiniLM-L6-v2 for fast embeddings"
    author = "Windows AI Team"

    def __init__(self):
        self.model = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the MiniLM plugin"""
        try:
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer("all-MiniLM-L6-v2")
            self._initialized = True
            return True

        except ImportError:
            print("sentence-transformers package not installed. Install with: pip install sentence-transformers")
            return False
        except Exception as e:
            print(f"Error initializing MiniLM plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a MiniLM action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "embed":
                return self._embed(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _embed(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Embed text(s)"""
        texts = params.get("texts", [])

        if isinstance(texts, str):
            texts = [texts]

        embeddings = self.model.encode(texts)

        return {
            "success": True,
            "embeddings": embeddings.tolist()
        }

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.model = None
        return True
