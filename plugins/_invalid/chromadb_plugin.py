"""
ChromaDB Vector Store Plugin
Provides vector storage and retrieval capabilities using ChromaDB
"""

from typing import Dict, Any, Optional, List
import os


class ChromaDBPlugin:
    """Plugin for ChromaDB vector database operations"""

    name = "chromadb"
    version = "1.0.0"
    description = "Integration with ChromaDB vector database for RAG applications"
    author = "Windows AI Team"

    def __init__(self):
        self.client = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the ChromaDB plugin"""
        try:
            import chromadb

            # Get configuration
            persist_directory = (
                config.get("persist_directory") if config
                else os.getenv("CHROMADB_PERSIST_DIR")
            )

            # Initialize ChromaDB client
            if persist_directory:
                self.client = chromadb.PersistentClient(path=persist_directory)
            else:
                self.client = chromadb.EphemeralClient()

            # Test connection by listing collections
            self.client.list_collections()
            self._initialized = True
            return True

        except ImportError:
            print("chromadb package not installed. Install with: pip install chromadb")
            return False
        except Exception as e:
            print(f"Error initializing ChromaDB plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a ChromaDB action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please check ChromaDB configuration."}

        try:
            if action == "create_collection":
                return self._create_collection(params)
            elif action == "get_collection":
                return self._get_collection(params)
            elif action == "delete_collection":
                return self._delete_collection(params)
            elif action == "list_collections":
                return self._list_collections()
            elif action == "add_documents":
                return self._add_documents(params)
            elif action == "query":
                return self._query(params)
            elif action == "update_documents":
                return self._update_documents(params)
            elif action == "delete_documents":
                return self._delete_documents(params)
            elif action == "get_collection_count":
                return self._get_collection_count(params)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {"error": str(e)}

    def _create_collection(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new collection"""
        collection_name = params.get("collection_name")
        if not collection_name:
            return {"error": "collection_name is required"}

        metadata = params.get("metadata", {})
        embedding_function = params.get("embedding_function")

        try:
            # Get or create embedding function if specified
            ef = None
            if embedding_function:
                ef = self._get_embedding_function(embedding_function)

            collection = self.client.create_collection(
                name=collection_name,
                metadata=metadata if metadata else None,
                embedding_function=ef
            )

            return {
                "success": True,
                "collection_name": collection_name,
                "collection_id": collection.id if hasattr(collection, 'id') else None
            }

        except Exception as e:
            return {"error": f"Failed to create collection: {str(e)}"}

    def _get_collection(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get an existing collection"""
        collection_name = params.get("collection_name")
        if not collection_name:
            return {"error": "collection_name is required"}

        try:
            collection = self.client.get_collection(name=collection_name)

            return {
                "success": True,
                "collection_name": collection.name,
                "collection_id": collection.id if hasattr(collection, 'id') else None,
                "document_count": collection.count() if hasattr(collection, 'count') else 0
            }

        except Exception as e:
            return {"error": f"Failed to get collection: {str(e)}"}

    def _delete_collection(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a collection"""
        collection_name = params.get("collection_name")
        if not collection_name:
            return {"error": "collection_name is required"}

        try:
            self.client.delete_collection(name=collection_name)
            return {"success": True, "collection_name": collection_name}

        except Exception as e:
            return {"error": f"Failed to delete collection: {str(e)}"}

    def _list_collections(self) -> Dict[str, Any]:
        """List all collections"""
        try:
            collections = self.client.list_collections()
            collection_names = [col.name for col in collections]

            return {
                "collections": collection_names,
                "count": len(collection_names)
            }

        except Exception as e:
            return {"error": f"Failed to list collections: {str(e)}"}

    def _add_documents(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add documents to a collection"""
        collection_name = params.get("collection_name")
        if not collection_name:
            return {"error": "collection_name is required"}

        documents = params.get("documents", [])
        metadatas = params.get("metadatas", [])
        ids = params.get("ids", [])

        if not documents:
            return {"error": "documents array is required"}

        try:
            collection = self.client.get_collection(name=collection_name)

            # Generate IDs if not provided
            if not ids:
                import uuid
                ids = [str(uuid.uuid4()) for _ in range(len(documents))]

            # Ensure metadatas is the same length as documents
            if metadatas and len(metadatas) != len(documents):
                return {"error": "metadatas length must match documents length"}
            elif not metadatas:
                metadatas = [{}] * len(documents)

            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )

            return {
                "success": True,
                "collection_name": collection_name,
                "added_count": len(documents),
                "ids": ids
            }

        except Exception as e:
            return {"error": f"Failed to add documents: {str(e)}"}

    def _query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Query a collection for similar documents"""
        collection_name = params.get("collection_name")
        if not collection_name:
            return {"error": "collection_name is required"}

        query_texts = params.get("query_texts", [])
        query_embeddings = params.get("query_embeddings", [])
        n_results = params.get("n_results", 10)
        where = params.get("where", {})
        where_document = params.get("where_document", {})
        include = params.get("include", ["documents", "metadatas", "distances"])

        if not query_texts and not query_embeddings:
            return {"error": "Either query_texts or query_embeddings is required"}

        try:
            collection = self.client.get_collection(name=collection_name)

            results = collection.query(
                query_texts=query_texts if query_texts else None,
                query_embeddings=query_embeddings if query_embeddings else None,
                n_results=n_results,
                where=where if where else None,
                where_document=where_document if where_document else None,
                include=include
            )

            # Format results
            formatted_results = {
                "ids": results.get("ids", []),
                "distances": results.get("distances", []),
                "documents": results.get("documents", []),
                "metadatas": results.get("metadatas", []),
                "n_results": n_results
            }

            return formatted_results

        except Exception as e:
            return {"error": f"Failed to query collection: {str(e)}"}

    def _update_documents(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing documents in a collection"""
        collection_name = params.get("collection_name")
        if not collection_name:
            return {"error": "collection_name is required"}

        ids = params.get("ids", [])
        documents = params.get("documents", [])
        metadatas = params.get("metadatas", [])

        if not ids:
            return {"error": "ids array is required"}

        try:
            collection = self.client.get_collection(name=collection_name)

            # Prepare update parameters
            update_params = {"ids": ids}

            if documents:
                update_params["documents"] = documents
            if metadatas:
                update_params["metadatas"] = metadatas

            collection.update(**update_params)

            return {
                "success": True,
                "collection_name": collection_name,
                "updated_count": len(ids)
            }

        except Exception as e:
            return {"error": f"Failed to update documents: {str(e)}"}

    def _delete_documents(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete documents from a collection"""
        collection_name = params.get("collection_name")
        if not collection_name:
            return {"error": "collection_name is required"}

        ids = params.get("ids", [])
        where = params.get("where", {})

        if not ids and not where:
            return {"error": "Either ids or where filter is required"}

        try:
            collection = self.client.get_collection(name=collection_name)

            if ids:
                collection.delete(ids=ids)
                deleted_count = len(ids)
            else:
                # For where clause, we need to query first to get count
                results = collection.get(where=where)
                collection.delete(where=where)
                deleted_count = len(results.get("ids", []))

            return {
                "success": True,
                "collection_name": collection_name,
                "deleted_count": deleted_count
            }

        except Exception as e:
            return {"error": f"Failed to delete documents: {str(e)}"}

    def _get_collection_count(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get the count of documents in a collection"""
        collection_name = params.get("collection_name")
        if not collection_name:
            return {"error": "collection_name is required"}

        try:
            collection = self.client.get_collection(name=collection_name)
            count = collection.count()

            return {
                "collection_name": collection_name,
                "count": count
            }

        except Exception as e:
            return {"error": f"Failed to get collection count: {str(e)}"}

    def _get_embedding_function(self, embedding_config: Dict[str, Any]):
        """Get embedding function based on configuration"""
        try:
            provider = embedding_config.get("provider", "openai")

            if provider == "openai":
                import chromadb.utils.embedding_functions as embedding_functions
                api_key = embedding_config.get("api_key") or os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OpenAI API key required for OpenAI embeddings")
                return embedding_functions.OpenAIEmbeddingFunction(api_key=api_key)

            elif provider == "sentence_transformers":
                import chromadb.utils.embedding_functions as embedding_functions
                model_name = embedding_config.get("model_name", "all-MiniLM-L6-v2")
                return embedding_functions.SentenceTransformerEmbeddingFunction(model_name=model_name)

            else:
                raise ValueError(f"Unsupported embedding provider: {provider}")

        except Exception as e:
            raise ValueError(f"Failed to initialize embedding function: {str(e)}")

    def cleanup(self):
        """Cleanup resources"""
        # ChromaDB clients don't need explicit cleanup
        self.client = None
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = ChromaDBPlugin
PLUGIN_NAME = "chromadb"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with ChromaDB vector database for RAG applications"
PLUGIN_ACTIONS = [
    "create_collection", "get_collection", "delete_collection", "list_collections",
    "add_documents", "query", "update_documents", "delete_documents", "get_collection_count"
]