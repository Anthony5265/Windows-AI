"""
Milvus Vector Database Plugin
Supports vector similarity search and storage operations
"""

from typing import Dict, Any, Optional, List
import os


class MilvusPlugin:
    """Plugin for Milvus vector database operations"""

    name = "milvus"
    version = "1.0.0"
    description = "Integration with Milvus vector database for vector similarity search"
    author = "Windows AI Team"

    def __init__(self):
        self.client = None
        self.uri = None
        self.token = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Milvus plugin"""
        try:
            from pymilvus import MilvusClient

            # Get configuration
            self.uri = (
                config.get("uri") if config
                else os.getenv("MILVUS_URI", "milvus_demo.db")
            )
            self.token = (
                config.get("token") if config
                else os.getenv("MILVUS_TOKEN")
            )

            # Initialize Milvus client
            if self.token:
                self.client = MilvusClient(uri=self.uri, token=self.token)
            else:
                self.client = MilvusClient(uri=self.uri)

            # Test connection by listing collections
            try:
                self.client.list_collections()
            except Exception as e:
                print(f"Warning: Could not verify Milvus connection: {e}")

            self._initialized = True
            return True

        except ImportError:
            print("pymilvus package not installed. Install with: pip install pymilvus")
            return False
        except Exception as e:
            print(f"Error initializing Milvus plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Milvus action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please provide valid URI and token."}

        try:
            if action == "connect":
                return self._connect(params)
            elif action == "create_collection":
                return self._create_collection(params)
            elif action == "insert_vectors":
                return self._insert_vectors(params)
            elif action == "search_vectors":
                return self._search_vectors(params)
            elif action == "query":
                return self._query(params)
            elif action == "delete_vectors":
                return self._delete_vectors(params)
            elif action == "list_collections":
                return self._list_collections()
            elif action == "drop_collection":
                return self._drop_collection(params)
            elif action == "has_collection":
                return self._has_collection(params)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {"error": str(e)}

    def _connect(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Reconnect to Milvus with new parameters"""
        try:
            from pymilvus import MilvusClient

            uri = params.get("uri", self.uri)
            token = params.get("token", self.token)

            if token:
                self.client = MilvusClient(uri=uri, token=token)
            else:
                self.client = MilvusClient(uri=uri)

            self.uri = uri
            self.token = token

            # Test connection
            collections = self.client.list_collections()
            return {
                "status": "connected",
                "uri": uri,
                "collections": collections
            }

        except Exception as e:
            return {"error": f"Failed to connect: {str(e)}"}

    def _create_collection(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new collection"""
        collection_name = params.get("collection_name")
        if not collection_name:
            return {"error": "collection_name is required"}

        dimension = params.get("dimension")
        if not dimension:
            return {"error": "dimension is required"}

        metric_type = params.get("metric_type", "COSINE")
        description = params.get("description", "")

        try:
            # Check if collection already exists
            if self.client.has_collection(collection_name=collection_name):
                return {"error": f"Collection '{collection_name}' already exists"}

            # Create collection
            self.client.create_collection(
                collection_name=collection_name,
                dimension=dimension,
                metric_type=metric_type,
                description=description
            )

            return {
                "status": "created",
                "collection_name": collection_name,
                "dimension": dimension,
                "metric_type": metric_type
            }

        except Exception as e:
            return {"error": f"Failed to create collection: {str(e)}"}

    def _insert_vectors(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Insert vectors into a collection"""
        collection_name = params.get("collection_name")
        if not collection_name:
            return {"error": "collection_name is required"}

        data = params.get("data")
        if not data:
            return {"error": "data is required"}

        try:
            # Ensure data is a list of dictionaries
            if not isinstance(data, list):
                data = [data]

            result = self.client.insert(
                collection_name=collection_name,
                data=data
            )

            return {
                "status": "inserted",
                "collection_name": collection_name,
                "insert_count": result.get("insert_count", 0),
                "ids": result.get("ids", [])
            }

        except Exception as e:
            return {"error": f"Failed to insert vectors: {str(e)}"}

    def _search_vectors(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search for similar vectors"""
        collection_name = params.get("collection_name")
        if not collection_name:
            return {"error": "collection_name is required"}

        query_vectors = params.get("query_vectors")
        if not query_vectors:
            return {"error": "query_vectors is required"}

        limit = params.get("limit", 10)
        output_fields = params.get("output_fields", [])
        filter_expr = params.get("filter")

        try:
            # Ensure query_vectors is a list
            if not isinstance(query_vectors, list):
                query_vectors = [query_vectors]

            search_params = {
                "collection_name": collection_name,
                "data": query_vectors,
                "limit": limit,
                "output_fields": output_fields
            }

            if filter_expr:
                search_params["filter"] = filter_expr

            results = self.client.search(**search_params)

            return {
                "status": "searched",
                "collection_name": collection_name,
                "results": results
            }

        except Exception as e:
            return {"error": f"Failed to search vectors: {str(e)}"}

    def _query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Query entities by filter or IDs"""
        collection_name = params.get("collection_name")
        if not collection_name:
            return {"error": "collection_name is required"}

        output_fields = params.get("output_fields", [])
        filter_expr = params.get("filter")
        ids = params.get("ids")

        if not filter_expr and not ids:
            return {"error": "Either filter or ids must be provided"}

        try:
            query_params = {
                "collection_name": collection_name,
                "output_fields": output_fields
            }

            if filter_expr:
                query_params["filter"] = filter_expr
            if ids:
                query_params["ids"] = ids

            results = self.client.query(**query_params)

            return {
                "status": "queried",
                "collection_name": collection_name,
                "results": results
            }

        except Exception as e:
            return {"error": f"Failed to query: {str(e)}"}

    def _delete_vectors(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete vectors from collection"""
        collection_name = params.get("collection_name")
        if not collection_name:
            return {"error": "collection_name is required"}

        ids = params.get("ids")
        filter_expr = params.get("filter")

        if not ids and not filter_expr:
            return {"error": "Either ids or filter must be provided"}

        try:
            delete_params = {"collection_name": collection_name}

            if ids:
                delete_params["ids"] = ids
            if filter_expr:
                delete_params["filter"] = filter_expr

            result = self.client.delete(**delete_params)

            return {
                "status": "deleted",
                "collection_name": collection_name,
                "deleted_ids": result
            }

        except Exception as e:
            return {"error": f"Failed to delete vectors: {str(e)}"}

    def _list_collections(self) -> Dict[str, Any]:
        """List all collections"""
        try:
            collections = self.client.list_collections()
            return {
                "collections": collections,
                "count": len(collections)
            }

        except Exception as e:
            return {"error": f"Failed to list collections: {str(e)}"}

    def _drop_collection(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Drop a collection"""
        collection_name = params.get("collection_name")
        if not collection_name:
            return {"error": "collection_name is required"}

        try:
            self.client.drop_collection(collection_name=collection_name)
            return {
                "status": "dropped",
                "collection_name": collection_name
            }

        except Exception as e:
            return {"error": f"Failed to drop collection: {str(e)}"}

    def _has_collection(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Check if collection exists"""
        collection_name = params.get("collection_name")
        if not collection_name:
            return {"error": "collection_name is required"}

        try:
            exists = self.client.has_collection(collection_name=collection_name)
            return {
                "collection_name": collection_name,
                "exists": exists
            }

        except Exception as e:
            return {"error": f"Failed to check collection: {str(e)}"}

    def cleanup(self):
        """Cleanup resources"""
        if self.client:
            # MilvusClient doesn't have explicit close method, just set to None
            self.client = None
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = MilvusPlugin
PLUGIN_NAME = "milvus"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with Milvus vector database"
PLUGIN_ACTIONS = ["connect", "create_collection", "insert_vectors", "search_vectors", "query", "delete_vectors", "list_collections", "drop_collection", "has_collection"]</content>
<parameter name="filePath">plugins/ai_models/milvus_plugin.py