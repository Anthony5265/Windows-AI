"""
Pinecone Vector Database Integration
Cloud-native vector database for production applications
"""
from typing import Dict, Any, List, Optional
import logging
import os

try:
    from pinecone import Pinecone, ServerlessSpec
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False

logger = logging.getLogger(__name__)

class PineconeDB:
    """Pinecone vector database client"""

    def __init__(self):
        self.api_key = os.getenv("PINECONE_API_KEY", "")
        self.environment = os.getenv("PINECONE_ENVIRONMENT", "us-east-1-aws")
        self.client = None

        if PINECONE_AVAILABLE and self.api_key:
            self.client = Pinecone(api_key=self.api_key)

    async def create_index(self, name: str, dimension: int, metric: str = "cosine") -> Dict[str, Any]:
        """Create a new index"""
        if not self.client:
            return {"status": "error", "message": "Pinecone not configured"}

        try:
            self.client.create_index(
                name=name,
                dimension=dimension,
                metric=metric,
                spec=ServerlessSpec(cloud="aws", region=self.environment)
            )
            return {"status": "success", "index": name}
        except Exception as e:
            logger.error(f"Create index error: {e}")
            return {"status": "error", "message": str(e)}

    async def upsert(self, index_name: str, vectors: List[Dict]) -> Dict[str, Any]:
        """Insert or update vectors"""
        if not self.client:
            return {"status": "error", "message": "Pinecone not configured"}

        try:
            index = self.client.Index(index_name)
            index.upsert(vectors=vectors)
            return {"status": "success", "count": len(vectors)}
        except Exception as e:
            logger.error(f"Upsert error: {e}")
            return {"status": "error", "message": str(e)}

    async def query(self, index_name: str, vector: List[float], top_k: int = 10,
                    filter: Optional[Dict] = None, include_metadata: bool = True) -> Dict[str, Any]:
        """Query for similar vectors"""
        if not self.client:
            return {"status": "error", "message": "Pinecone not configured"}

        try:
            index = self.client.Index(index_name)
            results = index.query(
                vector=vector,
                top_k=top_k,
                filter=filter,
                include_metadata=include_metadata
            )
            return {"status": "success", "matches": results.matches}
        except Exception as e:
            logger.error(f"Query error: {e}")
            return {"status": "error", "message": str(e)}

    async def delete(self, index_name: str, ids: List[str]) -> Dict[str, Any]:
        """Delete vectors by ID"""
        if not self.client:
            return {"status": "error", "message": "Pinecone not configured"}

        try:
            index = self.client.Index(index_name)
            index.delete(ids=ids)
            return {"status": "success", "deleted": len(ids)}
        except Exception as e:
            logger.error(f"Delete error: {e}")
            return {"status": "error", "message": str(e)}

    async def list_indexes(self) -> Dict[str, Any]:
        """List all indexes"""
        if not self.client:
            return {"status": "error", "message": "Pinecone not configured"}

        try:
            indexes = self.client.list_indexes()
            return {"status": "success", "indexes": indexes}
        except Exception as e:
            logger.error(f"List indexes error: {e}")
            return {"status": "error", "message": str(e)}
