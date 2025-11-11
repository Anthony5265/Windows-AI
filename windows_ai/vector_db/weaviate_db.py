"""
Weaviate Vector Database Integration
Open-source vector search engine with GraphQL API for production scale
"""
from typing import Dict, Any, List, Optional
import logging
import os
import asyncio

try:
    import weaviate
    from weaviate.classes.config import Configure, Property, DataType
    from weaviate.classes.query import Filter
    WEAVIATE_AVAILABLE = True
except ImportError:
    WEAVIATE_AVAILABLE = False

from .base import (
    VectorDBInterface,
    VectorDBConfig,
    VectorDBType,
    MetricType,
    SearchResult,
    IndexStats
)

logger = logging.getLogger(__name__)


class WeaviateDB(VectorDBInterface):
    """Weaviate vector database client for production-scale applications"""

    def __init__(self, config: Optional[VectorDBConfig] = None):
        """Initialize Weaviate client"""
        if not config:
            config = VectorDBConfig(
                db_type=VectorDBType.WEAVIATE,
                dimension=1536,
                metric=MetricType.COSINE,
                url=os.getenv("WEAVIATE_URL", "http://localhost:8080"),
                api_key=os.getenv("WEAVIATE_API_KEY")
            )

        super().__init__(config)

        if not WEAVIATE_AVAILABLE:
            self.logger.error("Weaviate library not installed. Install with: pip install weaviate-client")
            return

        self._connected = False

    async def connect(self) -> Dict[str, Any]:
        """Establish connection to Weaviate"""
        try:
            if not WEAVIATE_AVAILABLE:
                return {"status": "error", "message": "Weaviate not installed"}

            # Connect based on configuration
            if self.config.api_key:
                # Cloud connection
                self._client = weaviate.connect_to_weaviate_cloud(
                    cluster_url=self.config.url,
                    auth_credentials=weaviate.auth.AuthApiKey(self.config.api_key)
                )
            else:
                # Local connection
                host = self.config.url.replace("http://", "").replace("https://", "")
                self._client = weaviate.connect_to_local(host=host)

            self._connected = True

            # Test connection
            if self._client.is_ready():
                collections = self._client.collections.list_all()
                return {
                    "status": "success",
                    "message": "Connected to Weaviate",
                    "url": self.config.url,
                    "collections": len(collections)
                }
            else:
                return {"status": "error", "message": "Weaviate not ready"}

        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            return {"status": "error", "message": str(e)}

    async def disconnect(self) -> Dict[str, Any]:
        """Close connection to Weaviate"""
        try:
            if self._client:
                self._client.close()
            self._client = None
            self._connected = False
            return {"status": "success", "message": "Disconnected from Weaviate"}
        except Exception as e:
            self.logger.error(f"Disconnect error: {e}")
            return {"status": "error", "message": str(e)}

    async def create_index(
        self,
        name: str,
        dimension: int,
        metric: MetricType = MetricType.COSINE,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a new collection (class in Weaviate)"""
        if not self._client:
            return {"status": "error", "message": "Weaviate not connected"}

        try:
            # Map MetricType to Weaviate distance metric
            metric_map = {
                MetricType.COSINE: "cosine",
                MetricType.EUCLIDEAN: "l2-squared",
                MetricType.DOT_PRODUCT: "dot"
            }

            weaviate_metric = metric_map.get(metric, "cosine")

            # Define properties for the collection
            properties = [
                Property(name="text", data_type=DataType.TEXT),
                Property(name="metadata", data_type=DataType.OBJECT),
            ]

            # Add custom properties if provided
            custom_properties = kwargs.get("properties", [])
            if custom_properties:
                properties.extend(custom_properties)

            # Create collection
            vectorizer_config = kwargs.get("vectorizer_config")
            if not vectorizer_config:
                # Use none vectorizer - we'll provide vectors manually
                vectorizer_config = Configure.Vectorizer.none()

            self._client.collections.create(
                name=name,
                properties=properties,
                vectorizer_config=vectorizer_config,
                vector_index_config=Configure.VectorIndex.hnsw(
                    distance_metric=weaviate_metric
                )
            )

            return {
                "status": "success",
                "index": name,
                "dimension": dimension,
                "metric": weaviate_metric
            }

        except Exception as e:
            self.logger.error(f"Create index error: {e}")
            return {"status": "error", "message": str(e)}

    async def delete_index(self, name: str) -> Dict[str, Any]:
        """Delete a collection"""
        if not self._client:
            return {"status": "error", "message": "Weaviate not connected"}

        try:
            self._client.collections.delete(name)
            return {"status": "success", "index": name}
        except Exception as e:
            self.logger.error(f"Delete index error: {e}")
            return {"status": "error", "message": str(e)}

    async def list_indexes(self) -> Dict[str, Any]:
        """List all collections"""
        if not self._client:
            return {"status": "error", "message": "Weaviate not connected"}

        try:
            collections = self._client.collections.list_all()
            collection_names = list(collections.keys())

            return {
                "status": "success",
                "indexes": collection_names,
                "count": len(collection_names)
            }
        except Exception as e:
            self.logger.error(f"List indexes error: {e}")
            return {"status": "error", "message": str(e)}

    async def get_index_stats(self, name: str) -> Dict[str, Any]:
        """Get statistics about a collection"""
        if not self._client:
            return {"status": "error", "message": "Weaviate not connected"}

        try:
            collection = self._client.collections.get(name)

            # Get collection info
            aggregate_result = collection.aggregate.over_all(total_count=True)
            total_vectors = aggregate_result.total_count

            return {
                "status": "success",
                "stats": IndexStats(
                    name=name,
                    dimension=0,  # Weaviate doesn't expose this easily
                    total_vectors=total_vectors,
                    metric=MetricType.COSINE,
                    metadata={}
                )
            }

        except Exception as e:
            self.logger.error(f"Get index stats error: {e}")
            return {"status": "error", "message": str(e)}

    async def upsert(
        self,
        index_name: str,
        vectors: List[List[float]],
        ids: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None,
        documents: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Insert or update vectors"""
        if not self._client:
            return {"status": "error", "message": "Weaviate not connected"}

        try:
            collection = self._client.collections.get(index_name)

            # Use batch insert for efficiency
            with collection.batch.dynamic() as batch:
                for i, (id_, vec) in enumerate(zip(ids, vectors)):
                    properties = {
                        "text": documents[i] if documents and i < len(documents) else "",
                        "metadata": metadata[i] if metadata and i < len(metadata) else {}
                    }

                    batch.add_object(
                        properties=properties,
                        vector=vec,
                        uuid=id_ if len(id_) == 36 else None  # UUID format check
                    )

            return {
                "status": "success",
                "count": len(ids)
            }

        except Exception as e:
            self.logger.error(f"Upsert error: {e}")
            return {"status": "error", "message": str(e)}

    async def search(
        self,
        index_name: str,
        query_vector: List[float],
        top_k: int = 10,
        filter: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True,
        include_vectors: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Search for similar vectors"""
        if not self._client:
            return {"status": "error", "message": "Weaviate not connected"}

        try:
            collection = self._client.collections.get(index_name)

            # Build query
            query_builder = collection.query.near_vector(
                near_vector=query_vector,
                limit=top_k,
                return_metadata=["distance"] if not include_vectors else ["distance", "vector"]
            )

            # Add filter if provided
            if filter:
                # Convert filter dict to Weaviate filter
                # This is a simple implementation - can be extended
                pass

            # Execute query
            response = query_builder

            # Convert to SearchResult format
            results = []
            for obj in response.objects:
                # Weaviate returns distance, convert to score
                distance = obj.metadata.distance if hasattr(obj.metadata, 'distance') else 0
                score = 1.0 / (1.0 + distance)

                result = SearchResult(
                    id=str(obj.uuid),
                    score=score,
                    vector=obj.vector.get("default") if include_vectors and hasattr(obj, 'vector') else None,
                    metadata=obj.properties.get("metadata") if include_metadata else None,
                    document=obj.properties.get("text")
                )
                results.append(result)

            return {
                "status": "success",
                "results": results,
                "count": len(results)
            }

        except Exception as e:
            self.logger.error(f"Search error: {e}")
            return {"status": "error", "message": str(e)}

    async def delete(
        self,
        index_name: str,
        ids: Optional[List[str]] = None,
        filter: Optional[Dict[str, Any]] = None,
        delete_all: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Delete vectors"""
        if not self._client:
            return {"status": "error", "message": "Weaviate not connected"}

        try:
            collection = self._client.collections.get(index_name)

            if delete_all:
                # Delete all objects in collection
                collection.data.delete_many(where=Filter.by_id().exists())
                return {"status": "success", "deleted": "all"}

            elif ids:
                # Delete specific IDs
                for id_ in ids:
                    collection.data.delete_by_id(id_)
                return {"status": "success", "deleted": len(ids)}

            elif filter:
                # Delete by filter
                # Convert filter dict to Weaviate where clause
                collection.data.delete_many(where=filter)
                return {"status": "success", "deleted": "filtered"}

            else:
                return {"status": "error", "message": "Must specify ids, filter, or delete_all"}

        except Exception as e:
            self.logger.error(f"Delete error: {e}")
            return {"status": "error", "message": str(e)}

    async def update_metadata(
        self,
        index_name: str,
        id: str,
        metadata: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Update metadata for a vector"""
        if not self._client:
            return {"status": "error", "message": "Weaviate not connected"}

        try:
            collection = self._client.collections.get(index_name)

            # Update object properties
            collection.data.update(
                uuid=id,
                properties={"metadata": metadata}
            )

            return {"status": "success", "id": id}

        except Exception as e:
            self.logger.error(f"Update metadata error: {e}")
            return {"status": "error", "message": str(e)}

    async def search_hybrid(
        self,
        index_name: str,
        query_text: str,
        query_vector: Optional[List[float]] = None,
        top_k: int = 10,
        alpha: float = 0.5
    ) -> Dict[str, Any]:
        """
        Hybrid search combining vector and keyword search.
        Alpha controls the weight: 0.0 = pure keyword, 1.0 = pure vector
        """
        if not self._client:
            return {"status": "error", "message": "Weaviate not connected"}

        try:
            collection = self._client.collections.get(index_name)

            # Perform hybrid search
            response = collection.query.hybrid(
                query=query_text,
                vector=query_vector,
                alpha=alpha,
                limit=top_k
            )

            results = []
            for obj in response.objects:
                score = obj.metadata.score if hasattr(obj.metadata, 'score') else 0.0

                result = SearchResult(
                    id=str(obj.uuid),
                    score=score,
                    vector=None,
                    metadata=obj.properties.get("metadata"),
                    document=obj.properties.get("text")
                )
                results.append(result)

            return {
                "status": "success",
                "results": results,
                "count": len(results)
            }

        except Exception as e:
            self.logger.error(f"Hybrid search error: {e}")
            return {"status": "error", "message": str(e)}
