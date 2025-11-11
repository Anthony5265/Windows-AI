"""
Vector Database Integrations
Supports multiple vector database providers for RAG and semantic search
"""
from typing import Dict, Any, List, Optional
import logging

# Export base classes
from .base import (
    VectorDBInterface,
    VectorDBConfig,
    VectorDBType,
    MetricType,
    SearchResult,
    IndexStats
)

logger = logging.getLogger(__name__)


class VectorDBManager:
    """Manager for vector database operations"""

    def __init__(self):
        self.providers = {}
        self._load_providers()

    def _load_providers(self):
        """Load available vector database providers"""
        try:
            from .pinecone_db import PineconeDB
            self.providers["pinecone"] = PineconeDB
        except ImportError:
            logger.warning("Pinecone not available")

        try:
            from .chroma_db import ChromaDB
            self.providers["chroma"] = ChromaDB
        except ImportError:
            logger.warning("Chroma not available")

        try:
            from .faiss_db import FAISSDB
            self.providers["faiss"] = FAISSDB
        except ImportError:
            logger.warning("FAISS not available")

        try:
            from .qdrant_db import QdrantDB
            self.providers["qdrant"] = QdrantDB
        except ImportError:
            logger.warning("Qdrant not available")

        try:
            from .weaviate_db import WeaviateDB
            self.providers["weaviate"] = WeaviateDB
        except ImportError:
            logger.warning("Weaviate not available")

        try:
            from .milvus_db import MilvusDB
            self.providers["milvus"] = MilvusDB
        except ImportError:
            logger.warning("Milvus not available")

    def get_provider(self, provider_name: str, config: Optional[VectorDBConfig] = None):
        """
        Get a vector database provider instance.

        Args:
            provider_name: Name of the provider
            config: Optional configuration for the provider

        Returns:
            Initialized provider instance
        """
        if provider_name not in self.providers:
            raise ValueError(f"Provider {provider_name} not available. Available: {self.list_providers()}")

        if config:
            return self.providers[provider_name](config)
        return self.providers[provider_name]()

    def list_providers(self) -> List[str]:
        """List available providers"""
        return list(self.providers.keys())

    def create_config(
        self,
        db_type: str,
        dimension: int,
        **kwargs
    ) -> VectorDBConfig:
        """
        Create a vector database configuration.

        Args:
            db_type: Type of vector database
            dimension: Vector dimension
            **kwargs: Additional configuration options

        Returns:
            VectorDBConfig instance
        """
        db_type_enum = VectorDBType(db_type)
        metric = MetricType(kwargs.pop("metric", "cosine"))

        return VectorDBConfig(
            db_type=db_type_enum,
            dimension=dimension,
            metric=metric,
            **kwargs
        )


__all__ = [
    "VectorDBManager",
    "VectorDBInterface",
    "VectorDBConfig",
    "VectorDBType",
    "MetricType",
    "SearchResult",
    "IndexStats",
]
