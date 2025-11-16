"""
Sentence Transformers Plugin
Versatile sentence embeddings
"""

from typing import Dict, Any, Optional, List
import os


class SentenceTransformersPlugin:
    """Plugin for Sentence Transformers"""

    name = "sentence_transformers"
    version = "1.0.0"
    description = "Integration with Sentence Transformers for text embeddings"
    author = "Windows AI Team"

    def __init__(self):
        self.model = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Sentence Transformers plugin"""
        try:
            from sentence_transformers import SentenceTransformer

            model_name = config.get("model", "all-MiniLM-L6-v2") if config else "all-MiniLM-L6-v2"

            self.model = SentenceTransformer(model_name)
            self._initialized = True
            return True

        except ImportError:
            print("sentence-transformers package not installed. Install with: pip install sentence-transformers")
            return False
        except Exception as e:
            print(f"Error initializing Sentence Transformers plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Sentence Transformers action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "embed":
                return self._embed(params)
            elif action == "similarity":
                return self._compute_similarity(params)
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

    def _compute_similarity(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Compute semantic similarity"""
        from sentence_transformers import util

        texts1 = params.get("texts1", [])
        texts2 = params.get("texts2", [])

        embeddings1 = self.model.encode(texts1)
        embeddings2 = self.model.encode(texts2)

        similarities = util.cos_sim(embeddings1, embeddings2)

        return {
            "success": True,
            "similarities": similarities.tolist()
        }

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.model = None
        return True
