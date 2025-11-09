"""
Pinecone Vector Database Plugin
Provides vector database operations for Retrieval-Augmented Generation
"""

from typing import Dict, Any, Optional, List
import os


class PineconePlugin:
    """Plugin for Pinecone vector database operations"""

    name = "pinecone"
    version = "1.0.0"
    description = "Integration with Pinecone vector database for RAG applications"
    author = "Windows AI Team"

    def __init__(self):
        self.client = None
        self.index = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Pinecone plugin"""
        try:
            from pinecone import Pinecone

            # Get API key from config or environment
            api_key = (
                config.get("api_key") if config
                else os.getenv("PINECONE_API_KEY")
            )

            if not api_key:
                print("Pinecone API key not found. Please set PINECONE_API_KEY environment variable or provide it in config.")
                return False

            # Initialize Pinecone client
            self.client = Pinecone(api_key=api_key)

            # Test connection by listing indexes
            try:
                self.client.list_indexes()
            except Exception as e:
                print(f"Failed to connect to Pinecone: {e}")
                return False

            self._initialized = True
            return True

        except ImportError:
            print("pinecone package not installed. Install with: pip install pinecone-client")
            return False
        except Exception as e:
            print(f"Error initializing Pinecone plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Pinecone action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please provide Pinecone API key."}

        try:
            if action == "create_index":
                return self._create_index(params)
            elif action == "delete_index":
                return self._delete_index(params)
            elif action == "list_indexes":
                return self._list_indexes(params)
            elif action == "describe_index":
                return self._describe_index(params)
            elif action == "upsert_vectors":
                return self._upsert_vectors(params)
            elif action == "query_vectors":
                return self._query_vectors(params)
            elif action == "delete_vectors":
                return self._delete_vectors(params)
            elif action == "fetch_vectors":
                return self._fetch_vectors(params)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {"error": str(e)}

    def _create_index(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new Pinecone index"""
        name = params.get("name")
        dimension = params.get("dimension", 1536)  # Default for OpenAI embeddings
        metric = params.get("metric", "cosine")
        spec = params.get("spec", {"serverless": {"cloud": "aws", "region": "us-east-1"}})

        if not name:
            return {"error": "Index name is required"}

        try:
            self.client.create_index(
                name=name,
                dimension=dimension,
                metric=metric,
                spec=spec
            )

            return {
                "success": True,
                "index_name": name,
                "dimension": dimension,
                "metric": metric,
                "spec": spec
            }

        except Exception as e:
            return {"error": f"Failed to create index: {str(e)}"}

    def _delete_index(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a Pinecone index"""
        name = params.get("name")

        if not name:
            return {"error": "Index name is required"}

        try:
            self.client.delete_index(name)
            return {"success": True, "index_name": name}

        except Exception as e:
            return {"error": f"Failed to delete index: {str(e)}"}

    def _list_indexes(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List all Pinecone indexes"""
        try:
            indexes = self.client.list_indexes()
            return {
                "indexes": indexes,
                "count": len(indexes) if indexes else 0
            }

        except Exception as e:
            return {"error": f"Failed to list indexes: {str(e)}"}

    def _describe_index(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Describe a Pinecone index"""
        name = params.get("name")

        if not name:
            return {"error": "Index name is required"}

        try:
            description = self.client.describe_index(name)
            return {"index": description}

        except Exception as e:
            return {"error": f"Failed to describe index: {str(e)}"}

    def _upsert_vectors(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Upsert vectors to a Pinecone index"""
        index_name = params.get("index_name")
        vectors = params.get("vectors", [])
        namespace = params.get("namespace", "")

        if not index_name:
            return {"error": "Index name is required"}

        if not vectors:
            return {"error": "Vectors are required"}

        try:
            # Get or create index connection
            index = self.client.Index(index_name)

            # Prepare vectors in Pinecone format
            # Each vector should be a tuple: (id, values, metadata)
            pinecone_vectors = []
            for vector in vectors:
                if isinstance(vector, dict):
                    vector_id = vector.get("id")
                    values = vector.get("values")
                    metadata = vector.get("metadata", {})

                    if not vector_id or not values:
                        continue

                    pinecone_vectors.append((vector_id, values, metadata))
                elif isinstance(vector, tuple) and len(vector) >= 2:
                    pinecone_vectors.append(vector)

            if not pinecone_vectors:
                return {"error": "No valid vectors provided"}

            # Upsert vectors
            response = index.upsert(
                vectors=pinecone_vectors,
                namespace=namespace
            )

            return {
                "success": True,
                "index_name": index_name,
                "namespace": namespace,
                "upserted_count": response.get("upserted_count", len(pinecone_vectors))
            }

        except Exception as e:
            return {"error": f"Failed to upsert vectors: {str(e)}"}

    def _query_vectors(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Query vectors from a Pinecone index"""
        index_name = params.get("index_name")
        query_vector = params.get("query_vector")
        top_k = params.get("top_k", 10)
        namespace = params.get("namespace", "")
        include_metadata = params.get("include_metadata", True)
        include_values = params.get("include_values", False)

        if not index_name:
            return {"error": "Index name is required"}

        if not query_vector:
            return {"error": "Query vector is required"}

        try:
            # Get index connection
            index = self.client.Index(index_name)

            # Query vectors
            response = index.query(
                vector=query_vector,
                top_k=top_k,
                namespace=namespace,
                include_metadata=include_metadata,
                include_values=include_values
            )

            # Format results
            matches = []
            for match in response.get("matches", []):
                match_data = {
                    "id": match.get("id"),
                    "score": match.get("score")
                }
                if include_values and "values" in match:
                    match_data["values"] = match["values"]
                if include_metadata and "metadata" in match:
                    match_data["metadata"] = match["metadata"]
                matches.append(match_data)

            return {
                "matches": matches,
                "count": len(matches),
                "namespace": namespace
            }

        except Exception as e:
            return {"error": f"Failed to query vectors: {str(e)}"}

    def _delete_vectors(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete vectors from a Pinecone index"""
        index_name = params.get("index_name")
        ids = params.get("ids", [])
        namespace = params.get("namespace", "")
        delete_all = params.get("delete_all", False)

        if not index_name:
            return {"error": "Index name is required"}

        if not delete_all and not ids:
            return {"error": "Either ids or delete_all=True must be provided"}

        try:
            # Get index connection
            index = self.client.Index(index_name)

            if delete_all:
                # Delete all vectors in namespace
                index.delete(delete_all=True, namespace=namespace)
                return {
                    "success": True,
                    "index_name": index_name,
                    "namespace": namespace,
                    "deleted_all": True
                }
            else:
                # Delete specific vectors
                index.delete(ids=ids, namespace=namespace)
                return {
                    "success": True,
                    "index_name": index_name,
                    "namespace": namespace,
                    "deleted_ids": ids,
                    "deleted_count": len(ids)
                }

        except Exception as e:
            return {"error": f"Failed to delete vectors: {str(e)}"}

    def _fetch_vectors(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch vectors by IDs from a Pinecone index"""
        index_name = params.get("index_name")
        ids = params.get("ids", [])
        namespace = params.get("namespace", "")

        if not index_name:
            return {"error": "Index name is required"}

        if not ids:
            return {"error": "Vector IDs are required"}

        try:
            # Get index connection
            index = self.client.Index(index_name)

            # Fetch vectors
            response = index.fetch(ids=ids, namespace=namespace)

            # Format results
            vectors = {}
            for vector_id, vector_data in response.get("vectors", {}).items():
                vectors[vector_id] = {
                    "id": vector_id,
                    "values": vector_data.get("values"),
                    "metadata": vector_data.get("metadata", {})
                }

            return {
                "vectors": vectors,
                "count": len(vectors),
                "namespace": namespace
            }

        except Exception as e:
            return {"error": f"Failed to fetch vectors: {str(e)}"}

    def cleanup(self):
        """Cleanup resources"""
        self.client = None
        self.index = None
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = PineconePlugin
PLUGIN_NAME = "pinecone"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Pinecone vector database integration for RAG applications"
PLUGIN_ACTIONS = ["create_index", "delete_index", "list_indexes", "describe_index", "upsert_vectors", "query_vectors", "delete_vectors", "fetch_vectors"]