"""
Weaviate Vector Database Integration
Open-source vector search engine with GraphQL API
"""
from typing import Dict, Any, List, Optional
import logging
import os

try:
    import weaviate
    from weaviate.classes.config import Configure
    WEAVIATE_AVAILABLE = True
except ImportError:
    WEAVIATE_AVAILABLE = False

logger = logging.getLogger(__name__)

class WeaviateDB:
    """Weaviate vector database client"""

    def __init__(self):
        self.url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
        self.api_key = os.getenv("WEAVIATE_API_KEY", None)
        self.client = None

        if WEAVIATE_AVAILABLE:
            if self.api_key:
                self.client = weaviate.connect_to_weaviate_cloud(
                    cluster_url=self.url,
                    auth_credentials=weaviate.auth.AuthApiKey(self.api_key)
                )
            else:
                self.client = weaviate.connect_to_local(host=self.url)

    async def create_collection(self, name: str, properties: List[Dict],
                               vectorizer: str = "text2vec-openai") -> Dict[str, Any]:
        """Create a new collection (class in Weaviate)"""
        if not self.client:
            return {"status": "error", "message": "Weaviate not configured"}

        try:
            self.client.collections.create(
                name=name,
                properties=properties,
                vectorizer_config=Configure.Vectorizer.text2vec_openai()
            )
            return {"status": "success", "collection": name}
        except Exception as e:
            logger.error(f"Create collection error: {e}")
            return {"status": "error", "message": str(e)}

    async def add(self, collection_name: str, objects: List[Dict]) -> Dict[str, Any]:
        """Add objects to collection"""
        if not self.client:
            return {"status": "error", "message": "Weaviate not configured"}

        try:
            collection = self.client.collections.get(collection_name)
            with collection.batch.dynamic() as batch:
                for obj in objects:
                    batch.add_object(
                        properties=obj.get("properties", {}),
                        vector=obj.get("vector")
                    )

            return {"status": "success", "count": len(objects)}
        except Exception as e:
            logger.error(f"Add objects error: {e}")
            return {"status": "error", "message": str(e)}

    async def search(self, collection_name: str, query: str = None,
                     vector: List[float] = None, limit: int = 10) -> Dict[str, Any]:
        """Search collection"""
        if not self.client:
            return {"status": "error", "message": "Weaviate not configured"}

        try:
            collection = self.client.collections.get(collection_name)

            if query:
                results = collection.query.near_text(
                    query=query,
                    limit=limit
                )
            elif vector:
                results = collection.query.near_vector(
                    near_vector=vector,
                    limit=limit
                )
            else:
                return {"status": "error", "message": "Query or vector required"}

            matches = [
                {
                    "uuid": str(r.uuid),
                    "properties": r.properties,
                    "distance": r.metadata.distance if hasattr(r.metadata, 'distance') else None
                }
                for r in results.objects
            ]

            return {"status": "success", "matches": matches}
        except Exception as e:
            logger.error(f"Search error: {e}")
            return {"status": "error", "message": str(e)}

    async def delete(self, collection_name: str, uuids: List[str]) -> Dict[str, Any]:
        """Delete objects by UUID"""
        if not self.client:
            return {"status": "error", "message": "Weaviate not configured"}

        try:
            collection = self.client.collections.get(collection_name)
            for uuid in uuids:
                collection.data.delete_by_id(uuid)

            return {"status": "success", "deleted": len(uuids)}
        except Exception as e:
            logger.error(f"Delete error: {e}")
            return {"status": "error", "message": str(e)}

    async def list_collections(self) -> Dict[str, Any]:
        """List all collections"""
        if not self.client:
            return {"status": "error", "message": "Weaviate not configured"}

        try:
            collections = self.client.collections.list_all()
            return {"status": "success", "collections": list(collections.keys())}
        except Exception as e:
            logger.error(f"List collections error: {e}")
            return {"status": "error", "message": str(e)}
