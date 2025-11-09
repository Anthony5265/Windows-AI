"""
GTE Embedding Model Plugin
Supports GTE family of embedding models from Alibaba
"""

from typing import Dict, Any, Optional, List
import os


class GTEPlugin:
    """Plugin for GTE embedding models"""

    name = "gte"
    version = "1.0.0"
    description = "Integration with GTE embedding models from Alibaba"
    author = "Windows AI Team"

    def __init__(self):
        self.model = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the GTE plugin"""
        try:
            from sentence_transformers import SentenceTransformer

            # Get model name from config or use default
            model_name = (
                config.get("model", "Alibaba-NLP/gte-large-en-v1.5") if config
                else "Alibaba-NLP/gte-large-en-v1.5"
            )

            # Load the model
            self.model = SentenceTransformer(model_name)
            self._initialized = True
            return True

        except ImportError:
            print("sentence-transformers package not installed. Install with: pip install sentence-transformers")
            return False
        except Exception as e:
            print(f"Error initializing GTE plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a GTE action"""
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
            # Encode texts to get embeddings
            embeddings = self.model.encode(texts, convert_to_list=True)

            return {
                "embeddings": embeddings,
                "model": getattr(self.model, 'get_sentence_embedding_dimension', lambda: len(embeddings[0]) if embeddings else 0)(),
                "count": len(embeddings),
                "dimensions": len(embeddings[0]) if embeddings else 0
            }

        except Exception as e:
            return {"error": f"Embedding generation failed: {str(e)}"}

    def _embed_query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate embedding for a query"""
        query = params.get("query", "")
        if not query:
            return {"error": "No query provided"}

        try:
            # Encode query
            embedding = self.model.encode(query, convert_to_list=True)

            return {
                "embedding": embedding,
                "model": getattr(self.model, 'get_sentence_embedding_dimension', lambda: len(embedding))(),
                "dimensions": len(embedding)
            }

        except Exception as e:
            return {"error": f"Query embedding generation failed: {str(e)}"}

    def _embed_documents(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate embeddings for documents"""
        documents = params.get("documents", [])
        if not documents:
            return {"error": "No documents provided"}

        try:
            # Encode documents
            embeddings = self.model.encode(documents, convert_to_list=True)

            return {
                "embeddings": embeddings,
                "model": getattr(self.model, 'get_sentence_embedding_dimension', lambda: len(embeddings[0]) if embeddings else 0)(),
                "count": len(embeddings),
                "dimensions": len(embeddings[0]) if embeddings else 0
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
PLUGIN_CLASS = GTEPlugin
PLUGIN_NAME = "gte"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with GTE embedding models from Alibaba"
PLUGIN_ACTIONS = ["embed", "embed_query", "embed_documents"]