"""
Milvus Vector Database Integration
High-performance, scalable vector database
"""
from typing import Dict, Any, List, Optional
import logging
import os

try:
    from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
    MILVUS_AVAILABLE = True
except ImportError:
    MILVUS_AVAILABLE = False

logger = logging.getLogger(__name__)

class MilvusDB:
    """Milvus vector database client"""

    def __init__(self):
        self.host = os.getenv("MILVUS_HOST", "localhost")
        self.port = os.getenv("MILVUS_PORT", "19530")
        self.user = os.getenv("MILVUS_USER", "")
        self.password = os.getenv("MILVUS_PASSWORD", "")
        self.connected = False

        if MILVUS_AVAILABLE:
            try:
                if self.user and self.password:
                    connections.connect(
                        alias="default",
                        host=self.host,
                        port=self.port,
                        user=self.user,
                        password=self.password
                    )
                else:
                    connections.connect(
                        alias="default",
                        host=self.host,
                        port=self.port
                    )
                self.connected = True
            except Exception as e:
                logger.error(f"Milvus connection error: {e}")

    async def create_collection(self, name: str, dimension: int,
                               description: str = "") -> Dict[str, Any]:
        """Create a new collection"""
        if not self.connected:
            return {"status": "error", "message": "Milvus not connected"}

        try:
            fields = [
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dimension),
                FieldSchema(name="metadata", dtype=DataType.JSON)
            ]

            schema = CollectionSchema(fields=fields, description=description)
            collection = Collection(name=name, schema=schema)

            # Create index for vector field
            index_params = {
                "index_type": "IVF_FLAT",
                "metric_type": "L2",
                "params": {"nlist": 128}
            }
            collection.create_index(field_name="embedding", index_params=index_params)

            return {"status": "success", "collection": name}
        except Exception as e:
            logger.error(f"Create collection error: {e}")
            return {"status": "error", "message": str(e)}

    async def insert(self, collection_name: str, embeddings: List[List[float]],
                     metadatas: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Insert vectors into collection"""
        if not self.connected:
            return {"status": "error", "message": "Milvus not connected"}

        try:
            collection = Collection(collection_name)

            data = [
                embeddings,
                metadatas or [{} for _ in range(len(embeddings))]
            ]

            collection.insert(data)
            collection.flush()

            return {"status": "success", "count": len(embeddings)}
        except Exception as e:
            logger.error(f"Insert error: {e}")
            return {"status": "error", "message": str(e)}

    async def search(self, collection_name: str, vectors: List[List[float]],
                     limit: int = 10, expr: Optional[str] = None) -> Dict[str, Any]:
        """Search for similar vectors"""
        if not self.connected:
            return {"status": "error", "message": "Milvus not connected"}

        try:
            collection = Collection(collection_name)
            collection.load()

            search_params = {
                "metric_type": "L2",
                "params": {"nprobe": 10}
            }

            results = collection.search(
                data=vectors,
                anns_field="embedding",
                param=search_params,
                limit=limit,
                expr=expr,
                output_fields=["metadata"]
            )

            matches = []
            for hits in results:
                hit_list = [
                    {
                        "id": hit.id,
                        "distance": hit.distance,
                        "metadata": hit.entity.get("metadata", {})
                    }
                    for hit in hits
                ]
                matches.append(hit_list)

            return {"status": "success", "results": matches}
        except Exception as e:
            logger.error(f"Search error: {e}")
            return {"status": "error", "message": str(e)}

    async def delete(self, collection_name: str, ids: List[int]) -> Dict[str, Any]:
        """Delete vectors by ID"""
        if not self.connected:
            return {"status": "error", "message": "Milvus not connected"}

        try:
            collection = Collection(collection_name)
            expr = f"id in {ids}"
            collection.delete(expr)

            return {"status": "success", "deleted": len(ids)}
        except Exception as e:
            logger.error(f"Delete error: {e}")
            return {"status": "error", "message": str(e)}

    async def list_collections(self) -> Dict[str, Any]:
        """List all collections"""
        if not self.connected:
            return {"status": "error", "message": "Milvus not connected"}

        try:
            collections = utility.list_collections()
            return {"status": "success", "collections": collections}
        except Exception as e:
            logger.error(f"List collections error: {e}")
            return {"status": "error", "message": str(e)}
