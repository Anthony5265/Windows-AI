"""
Qdrant Plugin
High-performance vector similarity search engine
"""

from typing import Dict, Any, Optional, List
import os


class QdrantPlugin:
    """Plugin for Qdrant vector database"""

    name = "qdrant"
    version = "1.0.0"
    description = "Integration with Qdrant for high-performance vector search"
    author = "Windows AI Team"

    def __init__(self):
        self.client = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Qdrant plugin"""
        try:
            from qdrant_client import QdrantClient

            url = config.get("url", "localhost") if config else "localhost"
            port = config.get("port", 6333) if config else 6333
            api_key = config.get("api_key") if config else os.getenv("QDRANT_API_KEY")

            if api_key:
                self.client = QdrantClient(url=url, port=port, api_key=api_key)
            else:
                self.client = QdrantClient(url=url, port=port)

            self._initialized = True
            return True
        except ImportError:
            print("qdrant-client package not installed. Install with: pip install qdrant-client")
            return False
        except Exception as e:
            print(f"Error initializing Qdrant plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Qdrant action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "create_collection":
                return self._create_collection(params)
            elif action == "upsert":
                return self._upsert(params)
            elif action == "search":
                return self._search(params)
            elif action == "delete":
                return self._delete(params)
            elif action == "list_collections":
                return self._list_collections()
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _create_collection(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new collection"""
        from qdrant_client.models import Distance, VectorParams

        collection_name = params.get("collection_name", "")
        vector_size = params.get("vector_size", 1536)
        distance = params.get("distance", "Cosine")

        distance_map = {
            "Cosine": Distance.COSINE,
            "Euclidean": Distance.EUCLID,
            "Dot": Distance.DOT
        }

        self.client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=distance_map[distance])
        )

        return {
            "success": True,
            "collection_name": collection_name
        }

    def _upsert(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Upsert points"""
        from qdrant_client.models import PointStruct

        collection_name = params.get("collection_name", "")
        points = params.get("points", [])

        # Convert to PointStruct
        point_structs = [
            PointStruct(
                id=p.get("id"),
                vector=p.get("vector"),
                payload=p.get("payload", {})
            )
            for p in points
        ]

        self.client.upsert(
            collection_name=collection_name,
            points=point_structs
        )

        return {
            "success": True,
            "upserted": len(points)
        }

    def _search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search for similar vectors"""
        collection_name = params.get("collection_name", "")
        query_vector = params.get("query_vector", [])
        limit = params.get("limit", 5)
        filter_dict = params.get("filter", None)

        results = self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            query_filter=filter_dict
        )

        return {
            "success": True,
            "results": [
                {
                    "id": r.id,
                    "score": r.score,
                    "payload": r.payload
                }
                for r in results
            ]
        }

    def _delete(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete points"""
        collection_name = params.get("collection_name", "")
        point_ids = params.get("point_ids", [])

        self.client.delete(
            collection_name=collection_name,
            points_selector=point_ids
        )

        return {
            "success": True,
            "deleted": len(point_ids)
        }

    def _list_collections(self) -> Dict[str, Any]:
        """List all collections"""
        collections = self.client.get_collections()

        return {
            "success": True,
            "collections": [col.name for col in collections.collections]
        }

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.client = None
        return True
