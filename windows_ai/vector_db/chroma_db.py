"""
Chroma Vector Database Integration
Open-source embeddings database for LLM applications
"""
from typing import Dict, Any, List, Optional
import logging
import os

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

logger = logging.getLogger(__name__)

class ChromaDB:
    """Chroma vector database client"""

    def __init__(self):
        self.persist_directory = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
        self.client = None

        if CHROMA_AVAILABLE:
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )

    async def create_collection(self, name: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Create a new collection"""
        if not self.client:
            return {"status": "error", "message": "Chroma not configured"}

        try:
            collection = self.client.create_collection(
                name=name,
                metadata=metadata or {}
            )
            return {"status": "success", "collection": name}
        except Exception as e:
            logger.error(f"Create collection error: {e}")
            return {"status": "error", "message": str(e)}

    async def add(self, collection_name: str, documents: List[str],
                  embeddings: Optional[List[List[float]]] = None,
                  metadatas: Optional[List[Dict]] = None,
                  ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Add documents to collection"""
        if not self.client:
            return {"status": "error", "message": "Chroma not configured"}

        try:
            collection = self.client.get_collection(name=collection_name)
            collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids or [f"doc_{i}" for i in range(len(documents))]
            )
            return {"status": "success", "count": len(documents)}
        except Exception as e:
            logger.error(f"Add documents error: {e}")
            return {"status": "error", "message": str(e)}

    async def query(self, collection_name: str, query_texts: Optional[List[str]] = None,
                    query_embeddings: Optional[List[List[float]]] = None,
                    n_results: int = 10, where: Optional[Dict] = None) -> Dict[str, Any]:
        """Query collection"""
        if not self.client:
            return {"status": "error", "message": "Chroma not configured"}

        try:
            collection = self.client.get_collection(name=collection_name)
            results = collection.query(
                query_texts=query_texts,
                query_embeddings=query_embeddings,
                n_results=n_results,
                where=where
            )
            return {"status": "success", "results": results}
        except Exception as e:
            logger.error(f"Query error: {e}")
            return {"status": "error", "message": str(e)}

    async def delete(self, collection_name: str, ids: List[str]) -> Dict[str, Any]:
        """Delete documents by ID"""
        if not self.client:
            return {"status": "error", "message": "Chroma not configured"}

        try:
            collection = self.client.get_collection(name=collection_name)
            collection.delete(ids=ids)
            return {"status": "success", "deleted": len(ids)}
        except Exception as e:
            logger.error(f"Delete error: {e}")
            return {"status": "error", "message": str(e)}

    async def list_collections(self) -> Dict[str, Any]:
        """List all collections"""
        if not self.client:
            return {"status": "error", "message": "Chroma not configured"}

        try:
            collections = self.client.list_collections()
            return {"status": "success", "collections": [c.name for c in collections]}
        except Exception as e:
            logger.error(f"List collections error: {e}")
            return {"status": "error", "message": str(e)}
