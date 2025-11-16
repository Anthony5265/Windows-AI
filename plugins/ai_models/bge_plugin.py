"""
BGE (BAAI General Embedding) Plugin
State-of-the-art Chinese and English embeddings
"""

from typing import Dict, Any, Optional, List
import os


class BGEPlugin:
    """Plugin for BGE embeddings"""

    name = "bge"
    version = "1.0.0"
    description = "Integration with BGE models (M3, large, base) for embeddings"
    author = "Windows AI Team"

    def __init__(self):
        self.model = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the BGE plugin"""
        try:
            from sentence_transformers import SentenceTransformer

            model_name = config.get("model", "BAAI/bge-large-en-v1.5") if config else "BAAI/bge-large-en-v1.5"

            self.model = SentenceTransformer(model_name)
            self._initialized = True
            return True

        except ImportError:
            print("sentence-transformers package not installed. Install with: pip install sentence-transformers")
            return False
        except Exception as e:
            print(f"Error initializing BGE plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a BGE action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "embed":
                return self._embed(params)
            elif action == "embed_query":
                return self._embed_query(params)
            elif action == "embed_documents":
                return self._embed_documents(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _embed(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Embed text(s)"""
        texts = params.get("texts", [])

        if isinstance(texts, str):
            texts = [texts]

        embeddings = self.model.encode(texts, normalize_embeddings=True)

        return {
            "success": True,
            "embeddings": embeddings.tolist()
        }

    def _embed_query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Embed query with instruction"""
        query = params.get("query", "")

        # Add query instruction for BGE
        query_with_instruction = f"Represent this sentence for searching relevant passages: {query}"

        embedding = self.model.encode(query_with_instruction, normalize_embeddings=True)

        return {
            "success": True,
            "embedding": embedding.tolist()
        }

    def _embed_documents(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Embed documents"""
        documents = params.get("documents", [])

        embeddings = self.model.encode(documents, normalize_embeddings=True)

        return {
            "success": True,
            "embeddings": embeddings.tolist()
        }

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.model = None
        return True
