"""
E5 Embedding Model Plugin
Supports E5 family of embedding models from Microsoft
"""

from typing import Dict, Any, Optional, List
import os


class E5Plugin:
    """Plugin for E5 embedding models"""

    name = "e5"
    version = "1.0.0"
    description = "Integration with E5 embedding models from Microsoft"
    author = "Windows AI Team"

    def __init__(self):
        self.model = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the E5 plugin"""
        try:
            from sentence_transformers import SentenceTransformer

            # Get model name from config or use default
            model_name = (
                config.get("model", "intfloat/e5-large-v2")
                if config
                else "intfloat/e5-large-v2"
            )

            # Load the model
            self.model = SentenceTransformer(model_name)
            self._initialized = True
            return True

        except ImportError:
            print(
                "sentence-transformers package not installed. Install with: pip install sentence-transformers"
            )
            return False
        except Exception as e:
            print(f"Error initializing E5 plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an E5 action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Failed to load model."}

        try:
            if action == "embed":
                return self._embed(params)
            elif action == "embed_query":
                return self._embed_query(params)
            elif action == "embed_documents":
                return self._embed_documents(params)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {"error": str(e)}

    def _embed(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate embeddings for text(s)"""
        texts = params.get("texts", [])
        if isinstance(texts, str):
            texts = [texts]

        if not texts:
            return {"error": "No texts provided for embedding"}

        try:
            # E5 models expect "query: " or "passage: " prefixes
            prefix = params.get("prefix", "passage: ")
            prefixed_texts = [f"{prefix}{text}" for text in texts]

            embeddings = self.model.encode(prefixed_texts, convert_to_list=True)

            return {
                "embeddings": embeddings,
                "model": self.model.get_sentence_embedding_dimension(),
                "count": len(embeddings),
                "dimensions": len(embeddings[0]) if embeddings else 0,
            }

        except Exception as e:
            return {"error": f"Embedding generation failed: {str(e)}"}

    def _embed_query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate embedding for a query"""
        query = params.get("query", "")
        if not query:
            return {"error": "No query provided"}

        try:
            # Use "query: " prefix for queries
            prefixed_query = f"query: {query}"
            embedding = self.model.encode(prefixed_query, convert_to_list=True)

            return {
                "embedding": embedding,
                "model": self.model.get_sentence_embedding_dimension(),
                "dimensions": len(embedding),
            }

        except Exception as e:
            return {"error": f"Query embedding generation failed: {str(e)}"}

    def _embed_documents(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate embeddings for documents"""
        documents = params.get("documents", [])
        if not documents:
            return {"error": "No documents provided"}

        try:
            # Use "passage: " prefix for documents
            prefixed_docs = [f"passage: {doc}" for doc in documents]
            embeddings = self.model.encode(prefixed_docs, convert_to_list=True)

            return {
                "embeddings": embeddings,
                "model": self.model.get_sentence_embedding_dimension(),
                "count": len(embeddings),
                "dimensions": len(embeddings[0]) if embeddings else 0,
            }

        except Exception as e:
            return {"error": f"Document embedding generation failed: {str(e)}"}

    def cleanup(self):
        """Cleanup resources"""
        if self.model:
            del self.model
        self.model = None
        self._initialized = False


# Plugin metadata for registration
PLUGIN_CLASS = E5Plugin
PLUGIN_NAME = "e5"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with E5 embedding models from Microsoft"
PLUGIN_ACTIONS = ["embed", "embed_query", "embed_documents"]
