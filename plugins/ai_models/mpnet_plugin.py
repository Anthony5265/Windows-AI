"""
MPNet Plugin
High-quality sentence embeddings
"""

from typing import Dict, Any, Optional, List
import os


class MPNetPlugin:
    """Plugin for all-mpnet-base-v2 embeddings"""

    name = "mpnet"
    version = "1.0.0"
    description = "Integration with all-mpnet-base-v2 for high-quality embeddings"
    author = "Windows AI Team"

    def __init__(self):
        self.model = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the MPNet plugin"""
        try:
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer("all-mpnet-base-v2")
            self._initialized = True
            return True

        except ImportError:
            print("sentence-transformers package not installed. Install with: pip install sentence-transformers")
            return False
        except Exception as e:
            print(f"Error initializing MPNet plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an MPNet action"""
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
