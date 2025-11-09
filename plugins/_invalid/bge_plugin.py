"""
BGE Embedding Model Plugin
Supports BGE family of embedding models from BAAI
"""

from typing import Dict, Any, Optional, List
import os


class BGEPlugin:
    """Plugin for BGE embedding models"""

    name = "bge"
    version = "1.0.0"
    description = "Integration with BGE embedding models from BAAI"
    author = "Windows AI Team"

    def __init__(self):
        self.model = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the BGE plugin"""
        try:
            from sentence_transformers import SentenceTransformer

            # Get model name from config or use default
            model_name = (
                config.get("model", "BAAI/bge-large-en-v1.5") if config
                else "BAAI/bge-large-en-v1.5"
            )

            # Load the model
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
            # BGE models work well without prefixes, but can use instruction prefixes for better performance
            instruction = params.get("instruction", "")
            if instruction:
                processed_texts = [f"{instruction}{text}" for text in texts]
            else:
                processed_texts = texts

            embeddings = self.model.encode(processed_texts, convert_to_list=True)

            return {
                "embeddings": embeddings,
                "model": self.model.get_sentence_embedding_dimension(),
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
            # Use instruction for queries if provided, otherwise use default
            instruction = params.get("instruction", "Represent this sentence for searching relevant passages: ")
            processed_query = f"{instruction}{query}"
            embedding = self.model.encode(processed_query, convert_to_list=True)

            return {
                "embedding": embedding,
                "model": self.model.get_sentence_embedding_dimension(),
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
            # Use instruction for documents if provided, otherwise use default
            instruction = params.get("instruction", "Represent this sentence for retrieval: ")
            processed_docs = [f"{instruction}{doc}" for doc in documents]
            embeddings = self.model.encode(processed_docs, convert_to_list=True)

            return {
                "embeddings": embeddings,
                "model": self.model.get_sentence_embedding_dimension(),
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
PLUGIN_CLASS = BGEPlugin
PLUGIN_NAME = "bge"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with BGE embedding models from BAAI"
PLUGIN_ACTIONS = ["embed", "embed_query", "embed_documents"]</content>
<parameter name="filePath">plugins/ai_models/bge_plugin.py