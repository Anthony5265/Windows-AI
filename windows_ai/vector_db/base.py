"""
Base Interface for Vector Database Implementations
Provides a unified API for all vector database providers
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class VectorDBType(Enum):
    """Supported vector database types"""
    PINECONE = "pinecone"
    CHROMA = "chroma"
    FAISS = "faiss"
    WEAVIATE = "weaviate"
    QDRANT = "qdrant"
    MILVUS = "milvus"


class MetricType(Enum):
    """Distance metrics for similarity search"""
    COSINE = "cosine"
    EUCLIDEAN = "euclidean"
    DOT_PRODUCT = "dot_product"
    L2 = "l2"


@dataclass
class VectorDBConfig:
    """Configuration for vector database"""
    db_type: VectorDBType
    dimension: int
    metric: MetricType = MetricType.COSINE
    index_name: str = "default"

    # Connection settings
    api_key: Optional[str] = None
    url: Optional[str] = None
    persist_directory: Optional[str] = None

    # Performance settings
    batch_size: int = 100
    connection_pool_size: int = 10
    timeout: int = 30

    # Index settings
    index_config: Optional[Dict[str, Any]] = None


@dataclass
class SearchResult:
    """Result from similarity search"""
    id: str
    score: float
    vector: Optional[List[float]] = None
    metadata: Optional[Dict[str, Any]] = None
    document: Optional[str] = None


@dataclass
class IndexStats:
    """Statistics about an index"""
    name: str
    dimension: int
    total_vectors: int
    metric: MetricType
    metadata: Optional[Dict[str, Any]] = None


class VectorDBInterface(ABC):
    """
    Abstract base class for vector database implementations.
    All vector database providers must implement this interface.
    """

    def __init__(self, config: VectorDBConfig):
        """Initialize vector database with configuration"""
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._client = None
        self._connection_pool = []

    @abstractmethod
    async def connect(self) -> Dict[str, Any]:
        """
        Establish connection to the vector database.

        Returns:
            Dict with status and connection info
        """
        pass

    @abstractmethod
    async def disconnect(self) -> Dict[str, Any]:
        """
        Close connection to the vector database.

        Returns:
            Dict with status
        """
        pass

    @abstractmethod
    async def create_index(
        self,
        name: str,
        dimension: int,
        metric: MetricType = MetricType.COSINE,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a new index/collection.

        Args:
            name: Index name
            dimension: Vector dimension
            metric: Distance metric
            **kwargs: Additional provider-specific options

        Returns:
            Dict with status and index info
        """
        pass

    @abstractmethod
    async def delete_index(self, name: str) -> Dict[str, Any]:
        """
        Delete an index/collection.

        Args:
            name: Index name

        Returns:
            Dict with status
        """
        pass

    @abstractmethod
    async def list_indexes(self) -> Dict[str, Any]:
        """
        List all indexes/collections.

        Returns:
            Dict with status and list of indexes
        """
        pass

    @abstractmethod
    async def get_index_stats(self, name: str) -> Dict[str, Any]:
        """
        Get statistics about an index.

        Args:
            name: Index name

        Returns:
            Dict with IndexStats
        """
        pass

    @abstractmethod
    async def upsert(
        self,
        index_name: str,
        vectors: List[List[float]],
        ids: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None,
        documents: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Insert or update vectors.

        Args:
            index_name: Index name
            vectors: List of vectors
            ids: List of vector IDs
            metadata: Optional metadata for each vector
            documents: Optional document text for each vector
            **kwargs: Additional provider-specific options

        Returns:
            Dict with status and count
        """
        pass

    @abstractmethod
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
        """
        Search for similar vectors.

        Args:
            index_name: Index name
            query_vector: Query vector
            top_k: Number of results to return
            filter: Optional metadata filter
            include_metadata: Include metadata in results
            include_vectors: Include vectors in results
            **kwargs: Additional provider-specific options

        Returns:
            Dict with status and list of SearchResults
        """
        pass

    @abstractmethod
    async def delete(
        self,
        index_name: str,
        ids: Optional[List[str]] = None,
        filter: Optional[Dict[str, Any]] = None,
        delete_all: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Delete vectors by ID or filter.

        Args:
            index_name: Index name
            ids: Optional list of IDs to delete
            filter: Optional metadata filter for deletion
            delete_all: If True, delete all vectors in index
            **kwargs: Additional provider-specific options

        Returns:
            Dict with status and count of deleted vectors
        """
        pass

    @abstractmethod
    async def update_metadata(
        self,
        index_name: str,
        id: str,
        metadata: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Update metadata for a vector.

        Args:
            index_name: Index name
            id: Vector ID
            metadata: New metadata
            **kwargs: Additional provider-specific options

        Returns:
            Dict with status
        """
        pass

    async def batch_upsert(
        self,
        index_name: str,
        vectors: List[List[float]],
        ids: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None,
        documents: Optional[List[str]] = None,
        batch_size: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Insert vectors in batches for efficiency.

        Args:
            index_name: Index name
            vectors: List of vectors
            ids: List of vector IDs
            metadata: Optional metadata
            documents: Optional documents
            batch_size: Batch size (uses config default if not provided)
            **kwargs: Additional options

        Returns:
            Dict with status and total count
        """
        batch_size = batch_size or self.config.batch_size
        total_vectors = len(vectors)
        total_upserted = 0

        try:
            for i in range(0, total_vectors, batch_size):
                batch_vectors = vectors[i:i + batch_size]
                batch_ids = ids[i:i + batch_size]
                batch_metadata = metadata[i:i + batch_size] if metadata else None
                batch_documents = documents[i:i + batch_size] if documents else None

                result = await self.upsert(
                    index_name=index_name,
                    vectors=batch_vectors,
                    ids=batch_ids,
                    metadata=batch_metadata,
                    documents=batch_documents,
                    **kwargs
                )

                if result.get("status") == "success":
                    total_upserted += result.get("count", 0)
                else:
                    self.logger.warning(f"Batch {i//batch_size} failed: {result.get('message')}")

            return {
                "status": "success",
                "total": total_vectors,
                "upserted": total_upserted,
                "batches": (total_vectors + batch_size - 1) // batch_size
            }
        except Exception as e:
            self.logger.error(f"Batch upsert error: {e}")
            return {
                "status": "error",
                "message": str(e),
                "upserted": total_upserted
            }

    async def health_check(self) -> Dict[str, Any]:
        """
        Check if the vector database is healthy and accessible.

        Returns:
            Dict with status and health info
        """
        try:
            result = await self.list_indexes()
            if result.get("status") == "success":
                return {
                    "status": "healthy",
                    "db_type": self.config.db_type.value,
                    "indexes": len(result.get("indexes", []))
                }
            else:
                return {
                    "status": "unhealthy",
                    "message": result.get("message", "Unknown error")
                }
        except Exception as e:
            self.logger.error(f"Health check error: {e}")
            return {
                "status": "unhealthy",
                "message": str(e)
            }

    def __enter__(self):
        """Context manager support"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup"""
        # Async cleanup would need to be handled separately
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(type={self.config.db_type.value}, index={self.config.index_name})"
