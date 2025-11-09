"""
Qdrant Vector Database Integration
High-performance vector search engine
"""
from typing import Dict, Any, List, Optional
import logging
import os

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

logger = logging.getLogger(__name__)

class QdrantDB:
    """Qdrant vector database client"""

    def __init__(self):
        self.url = os.getenv("QDRANT_URL", "localhost")
        self.port = int(os.getenv("QDRANT_PORT", "6333"))
        self.api_key = os.getenv("QDRANT_API_KEY", None)
        self.client = None

        if QDRANT_AVAILABLE:
            if self.api_key:
                self.client = QdrantClient(url=self.url, api_key=self.api_key)
            else:
                self.client = QdrantClient(host=self.url, port=self.port)

    async def create_collection(self, name: str, dimension: int,
                               distance: str = "Cosine") -> Dict[str, Any]:
        """Create a new collection"""
        if not self.client:
            return {"status": "error", "message": "Qdrant not configured"}

        try:
            distance_map = {
                "Cosine": Distance.COSINE,
                "Euclidean": Distance.EUCLID,
                "Dot": Distance.DOT
            }

            self.client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(
                    size=dimension,
                    distance=distance_map.get(distance, Distance.COSINE)
                )
            )
            return {"status": "success", "collection": name}
        except Exception as e:
            logger.error(f"Create collection error: {e}")
            return {"status": "error", "message": str(e)}

    async def upsert(self, collection_name: str, points: List[Dict]) -> Dict[str, Any]:
        """Insert or update points"""
        if not self.client:
            return {"status": "error", "message": "Qdrant not configured"}

        try:
            point_structs = [
                PointStruct(
                    id=p["id"],
                    vector=p["vector"],
                    payload=p.get("payload", {})
                )
                for p in points
            ]

            self.client.upsert(
                collection_name=collection_name,
                points=point_structs
            )
            return {"status": "success", "count": len(points)}
        except Exception as e:
            logger.error(f"Upsert error: {e}")
            return {"status": "error", "message": str(e)}

    async def search(self, collection_name: str, vector: List[float],
                     limit: int = 10, filter: Optional[Dict] = None) -> Dict[str, Any]:
        """Search for similar vectors"""
        if not self.client:
            return {"status": "error", "message": "Qdrant not configured"}

        try:
            results = self.client.search(
                collection_name=collection_name,
                query_vector=vector,
                limit=limit,
                query_filter=filter
            )

            matches = [
                {
                    "id": r.id,
                    "score": r.score,
                    "payload": r.payload
                }
                for r in results
            ]

            return {"status": "success", "matches": matches}
        except Exception as e:
            logger.error(f"Search error: {e}")
            return {"status": "error", "message": str(e)}

    async def delete(self, collection_name: str, ids: List[str]) -> Dict[str, Any]:
        """Delete points by ID"""
        if not self.client:
            return {"status": "error", "message": "Qdrant not configured"}

        try:
            self.client.delete(
                collection_name=collection_name,
                points_selector=ids
            )
            return {"status": "success", "deleted": len(ids)}
        except Exception as e:
            logger.error(f"Delete error: {e}")
            return {"status": "error", "message": str(e)}

    async def list_collections(self) -> Dict[str, Any]:
        """List all collections"""
        if not self.client:
            return {"status": "error", "message": "Qdrant not configured"}

        try:
            collections = self.client.get_collections()
            return {
                "status": "success",
                "collections": [c.name for c in collections.collections]
            }
        except Exception as e:
            logger.error(f"List collections error: {e}")
            return {"status": "error", "message": str(e)}
