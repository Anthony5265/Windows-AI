"""
Vector Database Integrations
Supports multiple vector database providers for RAG and semantic search
"""
from typing import Dict, Any, List, Optional
import logging

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

    def get_provider(self, provider_name: str):
        """Get a vector database provider"""
        if provider_name not in self.providers:
            raise ValueError(f"Provider {provider_name} not available")
        return self.providers[provider_name]()

    def list_providers(self) -> List[str]:
        """List available providers"""
        return list(self.providers.keys())
