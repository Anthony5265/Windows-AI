"""
Pinecone Vector Database Integration
Cloud-native vector database for production applications
"""
from typing import Dict, Any, List, Optional
import logging
import os
import asyncio
from datetime import datetime

try:
    from pinecone import Pinecone, ServerlessSpec, PodSpec
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False

from .base import (
    VectorDBInterface,
    VectorDBConfig,
    VectorDBType,
    MetricType,
    SearchResult,
    IndexStats
)

logger = logging.getLogger(__name__)


class PineconeDB(VectorDBInterface):
    """Pinecone vector database client with connection pooling and error handling"""

    def __init__(self, config: Optional[VectorDBConfig] = None):
        """Initialize Pinecone client"""
        if not config:
            # Create default config from environment
            config = VectorDBConfig(
                db_type=VectorDBType.PINECONE,
                dimension=1536,  # Default for OpenAI embeddings
                metric=MetricType.COSINE,
                api_key=os.getenv("PINECONE_API_KEY"),
                url=os.getenv("PINECONE_ENVIRONMENT", "us-east-1-aws")
            )

        super().__init__(config)

        if not PINECONE_AVAILABLE:
            self.logger.error("Pinecone library not installed. Install with: pip install pinecone-client")
            return

        if not self.config.api_key:
            self.logger.warning("PINECONE_API_KEY not set")
            return

        self._connected = False
        self._indexes_cache = {}
        self._cache_timestamp = None

    async def connect(self) -> Dict[str, Any]:
        """Establish connection to Pinecone"""
        try:
            if not PINECONE_AVAILABLE or not self.config.api_key:
                return {
                    "status": "error",
                    "message": "Pinecone not configured properly"
                }

            # Initialize Pinecone client
            self._client = Pinecone(api_key=self.config.api_key)
            self._connected = True

            # Test connection by listing indexes
            result = await self.list_indexes()

            if result.get("status") == "success":
                return {
                    "status": "success",
                    "message": "Connected to Pinecone",
                    "indexes": len(result.get("indexes", []))
                }
            else:
                return result

        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            return {"status": "error", "message": str(e)}

    async def disconnect(self) -> Dict[str, Any]:
        """Close connection to Pinecone"""
        try:
            self._client = None
            self._connected = False
            self._indexes_cache.clear()
            return {"status": "success", "message": "Disconnected from Pinecone"}
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
        """Create a new Pinecone index"""
        if not self._client:
            return {"status": "error", "message": "Pinecone not connected"}

        try:
            # Map MetricType to Pinecone metric
            metric_map = {
                MetricType.COSINE: "cosine",
                MetricType.EUCLIDEAN: "euclidean",
                MetricType.DOT_PRODUCT: "dotproduct"
            }

            pinecone_metric = metric_map.get(metric, "cosine")

            # Determine spec type (serverless vs pod)
            use_serverless = kwargs.get("serverless", True)

            if use_serverless:
                cloud = kwargs.get("cloud", "aws")
                region = kwargs.get("region", self.config.url or "us-east-1")
                spec = ServerlessSpec(cloud=cloud, region=region)
            else:
                environment = kwargs.get("environment", self.config.url)
                pod_type = kwargs.get("pod_type", "p1.x1")
                spec = PodSpec(environment=environment, pod_type=pod_type)

            # Create index
            self._client.create_index(
                name=name,
                dimension=dimension,
                metric=pinecone_metric,
                spec=spec
            )

            # Wait for index to be ready
            timeout = kwargs.get("timeout", 60)
            start_time = datetime.now()

            while (datetime.now() - start_time).seconds < timeout:
                try:
                    index_desc = self._client.describe_index(name)
                    if index_desc.status.get("ready", False):
                        break
                except:
                    pass
                await asyncio.sleep(2)

            # Invalidate cache
            self._indexes_cache.clear()

            return {
                "status": "success",
                "index": name,
                "dimension": dimension,
                "metric": pinecone_metric
            }

        except Exception as e:
            self.logger.error(f"Create index error: {e}")
            return {"status": "error", "message": str(e)}

    async def delete_index(self, name: str) -> Dict[str, Any]:
        """Delete a Pinecone index"""
        if not self._client:
            return {"status": "error", "message": "Pinecone not connected"}

        try:
            self._client.delete_index(name)
            self._indexes_cache.pop(name, None)
            return {"status": "success", "index": name}
        except Exception as e:
            self.logger.error(f"Delete index error: {e}")
            return {"status": "error", "message": str(e)}

    async def list_indexes(self) -> Dict[str, Any]:
        """List all Pinecone indexes"""
        if not self._client:
            return {"status": "error", "message": "Pinecone not connected"}

        try:
            indexes = self._client.list_indexes()
            index_names = [idx.name for idx in indexes]

            return {
                "status": "success",
                "indexes": index_names,
                "count": len(index_names)
            }
        except Exception as e:
            self.logger.error(f"List indexes error: {e}")
            return {"status": "error", "message": str(e)}

    async def get_index_stats(self, name: str) -> Dict[str, Any]:
        """Get statistics about a Pinecone index"""
        if not self._client:
            return {"status": "error", "message": "Pinecone not connected"}

        try:
            # Get index description
            index_desc = self._client.describe_index(name)

            # Get index stats
            index = self._client.Index(name)
            stats = index.describe_index_stats()

            return {
                "status": "success",
                "stats": IndexStats(
                    name=name,
                    dimension=index_desc.dimension,
                    total_vectors=stats.total_vector_count,
                    metric=MetricType.COSINE,  # Would need to parse from index_desc
                    metadata={
                        "namespaces": stats.namespaces,
                        "index_fullness": stats.index_fullness
                    }
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
        """Insert or update vectors in Pinecone"""
        if not self._client:
            return {"status": "error", "message": "Pinecone not connected"}

        try:
            index = self._client.Index(index_name)

            # Prepare vectors for upsert
            upsert_data = []
            for i, (id_, vec) in enumerate(zip(ids, vectors)):
                item = {"id": id_, "values": vec}

                # Add metadata if provided
                if metadata and i < len(metadata):
                    item_metadata = metadata[i].copy()
                    # Add document text to metadata if provided
                    if documents and i < len(documents):
                        item_metadata["text"] = documents[i]
                    item["metadata"] = item_metadata
                elif documents and i < len(documents):
                    item["metadata"] = {"text": documents[i]}

                upsert_data.append(item)

            # Upsert vectors
            namespace = kwargs.get("namespace", "")
            response = index.upsert(vectors=upsert_data, namespace=namespace)

            return {
                "status": "success",
                "count": response.upserted_count,
                "namespace": namespace
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
        """Search for similar vectors in Pinecone"""
        if not self._client:
            return {"status": "error", "message": "Pinecone not connected"}

        try:
            index = self._client.Index(index_name)

            namespace = kwargs.get("namespace", "")

            # Execute query
            response = index.query(
                vector=query_vector,
                top_k=top_k,
                filter=filter,
                include_metadata=include_metadata,
                include_values=include_vectors,
                namespace=namespace
            )

            # Convert to SearchResult format
            results = []
            for match in response.matches:
                result = SearchResult(
                    id=match.id,
                    score=match.score,
                    vector=match.values if include_vectors else None,
                    metadata=match.metadata if include_metadata else None,
                    document=match.metadata.get("text") if (include_metadata and match.metadata) else None
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
        """Delete vectors from Pinecone"""
        if not self._client:
            return {"status": "error", "message": "Pinecone not connected"}

        try:
            index = self._client.Index(index_name)
            namespace = kwargs.get("namespace", "")

            if delete_all:
                # Delete all vectors in namespace
                index.delete(delete_all=True, namespace=namespace)
                return {"status": "success", "deleted": "all", "namespace": namespace}

            elif ids:
                # Delete specific IDs
                index.delete(ids=ids, namespace=namespace)
                return {"status": "success", "deleted": len(ids), "namespace": namespace}

            elif filter:
                # Delete by filter
                index.delete(filter=filter, namespace=namespace)
                return {"status": "success", "deleted": "filtered", "namespace": namespace}

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
        """Update metadata for a vector in Pinecone"""
        if not self._client:
            return {"status": "error", "message": "Pinecone not connected"}

        try:
            index = self._client.Index(index_name)
            namespace = kwargs.get("namespace", "")

            # Update requires set_metadata parameter
            index.update(
                id=id,
                set_metadata=metadata,
                namespace=namespace
            )

            return {"status": "success", "id": id, "namespace": namespace}

        except Exception as e:
            self.logger.error(f"Update metadata error: {e}")
            return {"status": "error", "message": str(e)}

    async def fetch(
        self,
        index_name: str,
        ids: List[str],
        namespace: str = ""
    ) -> Dict[str, Any]:
        """Fetch vectors by ID from Pinecone"""
        if not self._client:
            return {"status": "error", "message": "Pinecone not connected"}

        try:
            index = self._client.Index(index_name)
            response = index.fetch(ids=ids, namespace=namespace)

            vectors = []
            for id_, vec_data in response.vectors.items():
                vectors.append({
                    "id": id_,
                    "values": vec_data.values,
                    "metadata": vec_data.metadata
                })

            return {"status": "success", "vectors": vectors, "count": len(vectors)}

        except Exception as e:
            self.logger.error(f"Fetch error: {e}")
            return {"status": "error", "message": str(e)}
