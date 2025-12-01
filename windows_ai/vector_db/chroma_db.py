"""
Chroma Vector Database Integration
Open-source embeddings database for LLM applications
"""
from typing import Dict, Any, List, Optional
import logging
import os
import uuid

try:
    import chromadb
    from chromadb.config import Settings
    from chromadb.api.types import EmbeddingFunction
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

from .base import (
    VectorDBInterface,
    VectorDBConfig,
    VectorDBType,
    MetricType,
    SearchResult,
    IndexStats
)

logger = logging.getLogger(__name__)


class ChromaDB(VectorDBInterface):
    """Chroma vector database client with persistent storage"""

    def __init__(self, config: Optional[VectorDBConfig] = None):
        """Initialize Chroma client"""
        if not config:
            config = VectorDBConfig(
                db_type=VectorDBType.CHROMA,
                dimension=1536,
                metric=MetricType.COSINE,
                persist_directory=os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
            )

        super().__init__(config)

        if not CHROMA_AVAILABLE:
            self.logger.error("Chroma library not installed. Install with: pip install chromadb")
            return

        self._connected = False

    async def connect(self) -> Dict[str, Any]:
        """Establish connection to Chroma"""
        try:
            if not CHROMA_AVAILABLE:
                return {"status": "error", "message": "Chroma not installed"}

            # Create persist directory if needed
            os.makedirs(self.config.persist_directory, exist_ok=True)

            # Initialize Chroma client
            self._client = chromadb.PersistentClient(
                path=self.config.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )

            self._connected = True

            # Test connection by listing collections
            collections = self._client.list_collections()

            return {
                "status": "success",
                "message": "Connected to Chroma",
                "persist_directory": self.config.persist_directory,
                "collections": len(collections)
            }

        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            return {"status": "error", "message": str(e)}

    async def disconnect(self) -> Dict[str, Any]:
        """Close connection to Chroma"""
        try:
            self._client = None
            self._connected = False
            return {"status": "success", "message": "Disconnected from Chroma"}
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
        """Create a new collection (index)"""
        if not self._client:
            return {"status": "error", "message": "Chroma not connected"}

        try:
            # Map MetricType to Chroma distance
            metric_map = {
                MetricType.COSINE: "cosine",
                MetricType.EUCLIDEAN: "l2",
                MetricType.DOT_PRODUCT: "ip"
            }

            chroma_metric = metric_map.get(metric, "cosine")

            # Create collection with metadata
            metadata = kwargs.get("metadata", {})
            metadata["dimension"] = dimension
            metadata["metric"] = chroma_metric

            collection = self._client.create_collection(
                name=name,
                metadata=metadata,
                embedding_function=None  # We'll provide embeddings directly
            )

            return {
                "status": "success",
                "index": name,
                "dimension": dimension,
                "metric": chroma_metric
            }

        except Exception as e:
            self.logger.error(f"Create index error: {e}")
            return {"status": "error", "message": str(e)}

    async def delete_index(self, name: str) -> Dict[str, Any]:
        """Delete a collection"""
        if not self._client:
            return {"status": "error", "message": "Chroma not connected"}

        try:
            self._client.delete_collection(name=name)
            return {"status": "success", "index": name}
        except Exception as e:
            self.logger.error(f"Delete index error: {e}")
            return {"status": "error", "message": str(e)}

    async def list_indexes(self) -> Dict[str, Any]:
        """List all collections"""
        if not self._client:
            return {"status": "error", "message": "Chroma not connected"}

        try:
            collections = self._client.list_collections()
            collection_names = [c.name for c in collections]

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
            return {"status": "error", "message": "Chroma not connected"}

        try:
            collection = self._client.get_collection(name=name)
            count = collection.count()
            metadata = collection.metadata

            return {
                "status": "success",
                "stats": IndexStats(
                    name=name,
                    dimension=metadata.get("dimension", 0),
                    total_vectors=count,
                    metric=MetricType.COSINE,
                    metadata=metadata
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
            return {"status": "error", "message": "Chroma not connected"}

        try:
            collection = self._client.get_collection(name=index_name)

            # Prepare data
            add_ids = ids
            add_embeddings = vectors
            add_documents = documents if documents else [f"doc_{id_}" for id_ in ids]
            add_metadatas = metadata if metadata else [{"id": id_} for id_ in ids]

            # Add or update
            collection.upsert(
                ids=add_ids,
                embeddings=add_embeddings,
                documents=add_documents,
                metadatas=add_metadatas
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
            return {"status": "error", "message": "Chroma not connected"}

        try:
            collection = self._client.get_collection(name=index_name)

            # Execute query
            query_results = collection.query(
                query_embeddings=[query_vector],
                n_results=top_k,
                where=filter,
                include=["metadatas", "documents", "distances"] +
                        (["embeddings"] if include_vectors else [])
            )

            # Convert to SearchResult format
            results = []
            if query_results["ids"] and len(query_results["ids"][0]) > 0:
                for i, result_id in enumerate(query_results["ids"][0]):
                    distance = query_results["distances"][0][i]
                    # Chroma returns distance, convert to similarity score
                    score = 1.0 / (1.0 + distance) if distance is not None else 0.0

                    result = SearchResult(
                        id=result_id,
                        score=score,
                        vector=query_results["embeddings"][0][i] if include_vectors and "embeddings" in query_results else None,
                        metadata=query_results["metadatas"][0][i] if include_metadata else None,
                        document=query_results["documents"][0][i] if "documents" in query_results else None
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
            return {"status": "error", "message": "Chroma not connected"}

        try:
            collection = self._client.get_collection(name=index_name)

            if delete_all:
                # Delete entire collection
                count = collection.count()
                self._client.delete_collection(name=index_name)
                # Recreate empty collection with same metadata
                metadata = collection.metadata
                self._client.create_collection(
                    name=index_name,
                    metadata=metadata,
                    embedding_function=None
                )
                return {"status": "success", "deleted": count}

            elif ids:
                collection.delete(ids=ids)
                return {"status": "success", "deleted": len(ids)}

            elif filter:
                collection.delete(where=filter)
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
            return {"status": "error", "message": "Chroma not connected"}

        try:
            collection = self._client.get_collection(name=index_name)

            # Update metadata
            collection.update(
                ids=[id],
                metadatas=[metadata]
            )

            return {"status": "success", "id": id}

        except Exception as e:
            self.logger.error(f"Update metadata error: {e}")
            return {"status": "error", "message": str(e)}

    async def get_collection(
        self,
        index_name: str,
        ids: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        filter: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get items from collection"""
        if not self._client:
            return {"status": "error", "message": "Chroma not connected"}

        try:
            collection = self._client.get_collection(name=index_name)

            result = collection.get(
                ids=ids,
                where=filter,
                limit=limit,
                offset=offset,
                include=["metadatas", "documents", "embeddings"]
            )

            return {"status": "success", "items": result}

        except Exception as e:
            self.logger.error(f"Get collection error: {e}")
            return {"status": "error", "message": str(e)}
