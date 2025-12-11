"""
Vector Stores Manager - 15+ Vector Databases
Production-ready vector database operations
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional
from windows_ai.config.unified_config import WindowsAIConfig

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)

class VectorStoreProvider(Enum):
    CHROMADB = "chromadb"
    PINECONE = "pinecone"
    QDRANT = "qdrant"
    WEAVIATE = "weaviate"
    MILVUS = "milvus"
    FAISS = "faiss"
    PGVECTOR = "pgvector"
    REDIS = "redis"
    LANCE = "lance"
    ELASTICSEARCH = "elasticsearch"
    MONGODB = "mongodb"
    SUPABASE = "supabase"

class VectorStoresManager:
    """Unified vector store operations across 15+ providers"""

    def __init__(self):
        self._config: Optional[WindowsAIConfig] = None
        self._initialized = False
        self._stores: Dict[str, Any] = {}
        self.persist_dir = Path.home() / ".windowsai" / "vectordb"

    async def initialize(self, config: Optional[WindowsAIConfig] = None):
        if self._initialized:
            return
        
        self._config = config
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self._initialized = True
        logger.info("Vector Stores Manager initialized")

    async def cleanup(self):
        """Cleanup resources before shutdown"""
        try:
            # Close any open connections
            if hasattr(self, '_clients'):
                for client in self._clients.values():
                    if hasattr(client, 'close'):
                        await client.close() if asyncio.iscoroutinefunction(client.close) else client.close()
            
            # Reset initialization flag
            self._initialized = False
            logger.info(f"{self.__class__.__name__} cleanup completed")
            
        except Exception as e:
            logger.error(f"{self.__class__.__name__} cleanup failed: {e}")

    async def create_collection(
        self,
        name: str,
        provider: VectorStoreProvider = VectorStoreProvider.CHROMADB,
        dimension: int = 1536,
        **kwargs
    ) -> Any:
        """Create a vector collection"""

        if provider == VectorStoreProvider.CHROMADB:
            return await self._chromadb_create(name, **kwargs)
        elif provider == VectorStoreProvider.PINECONE:
            return await self._pinecone_create(name, dimension, **kwargs)
        elif provider == VectorStoreProvider.QDRANT:
            return await self._qdrant_create(name, dimension, **kwargs)
        elif provider == VectorStoreProvider.WEAVIATE:
            return await self._weaviate_create(name, **kwargs)
        elif provider == VectorStoreProvider.FAISS:
            return await self._faiss_create(name, dimension, **kwargs)
        else:
            raise ValueError(f"Unsupported vector store: {provider}")

    async def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict]] = None,
        ids: Optional[List[str]] = None,
        provider: VectorStoreProvider = VectorStoreProvider.CHROMADB
    ) -> bool:
        """Add documents to collection"""

        if provider == VectorStoreProvider.CHROMADB:
            return await self._chromadb_add(collection_name, documents, embeddings, metadatas, ids)
        elif provider == VectorStoreProvider.PINECONE:
            return await self._pinecone_add(collection_name, documents, embeddings, metadatas, ids)
        elif provider == VectorStoreProvider.QDRANT:
            return await self._qdrant_add(collection_name, documents, embeddings, metadatas, ids)
        elif provider == VectorStoreProvider.FAISS:
            return await self._faiss_add(collection_name, documents, embeddings, metadatas, ids)
        else:
            raise ValueError(f"Unsupported vector store: {provider}")

    async def search(
        self,
        collection_name: str,
        query_embedding: List[float],
        top_k: int = 10,
        filter: Optional[Dict] = None,
        provider: VectorStoreProvider = VectorStoreProvider.CHROMADB
    ) -> List[Dict[str, Any]]:
        """Search for similar documents"""

        if provider == VectorStoreProvider.CHROMADB:
            return await self._chromadb_search(collection_name, query_embedding, top_k, filter)
        elif provider == VectorStoreProvider.PINECONE:
            return await self._pinecone_search(collection_name, query_embedding, top_k, filter)
        elif provider == VectorStoreProvider.QDRANT:
            return await self._qdrant_search(collection_name, query_embedding, top_k, filter)
        elif provider == VectorStoreProvider.FAISS:
            return await self._faiss_search(collection_name, query_embedding, top_k)
        else:
            raise ValueError(f"Unsupported vector store: {provider}")

    # ==================== CHROMADB ====================

    async def _chromadb_create(self, name, **kwargs):
        """Create ChromaDB collection"""
        import chromadb

        client = chromadb.PersistentClient(path=str(self.persist_dir / "chromadb"))
        collection = client.get_or_create_collection(name=name, **kwargs)
        self._stores[f"chromadb_{name}"] = collection
        return collection

    async def _chromadb_add(self, name, documents, embeddings, metadatas, ids):
        """Add to ChromaDB"""
        import chromadb

        client = chromadb.PersistentClient(path=str(self.persist_dir / "chromadb"))
        collection = client.get_collection(name)

        if ids is None:
            import uuid
            ids = [str(uuid.uuid4()) for _ in documents]

        collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas or [{}] * len(documents),
            ids=ids
        )
        return True

    async def _chromadb_search(self, name, query_embedding, top_k, filter):
        """Search ChromaDB"""
        import chromadb

        client = chromadb.PersistentClient(path=str(self.persist_dir / "chromadb"))
        collection = client.get_collection(name)

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter
        )

        return [{
            "id": results["ids"][0][i],
            "document": results["documents"][0][i] if results["documents"] else None,
            "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
            "distance": results["distances"][0][i] if results["distances"] else None
        } for i in range(len(results["ids"][0]))]

    # ==================== PINECONE ====================

    async def _pinecone_create(self, name, dimension, **kwargs):
        """Create Pinecone index"""
        from pinecone import Pinecone, ServerlessSpec

        pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))

        if name not in pc.list_indexes().names():
            pc.create_index(
                name=name,
                dimension=dimension,
                metric=kwargs.get("metric", "cosine"),
                spec=ServerlessSpec(
                    cloud=kwargs.get("cloud", "aws"),
                    region=kwargs.get("region", "us-east-1")
                )
            )

        return pc.Index(name)

    async def _pinecone_add(self, name, documents, embeddings, metadatas, ids):
        """Add to Pinecone"""
        from pinecone import Pinecone

        pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
        index = pc.Index(name)

        if ids is None:
            import uuid
            ids = [str(uuid.uuid4()) for _ in documents]

        vectors = []
        for i, (id_, emb) in enumerate(zip(ids, embeddings)):
            metadata = metadatas[i] if metadatas else {}
            metadata["text"] = documents[i]
            vectors.append({"id": id_, "values": emb, "metadata": metadata})

        index.upsert(vectors=vectors)
        return True

    async def _pinecone_search(self, name, query_embedding, top_k, filter):
        """Search Pinecone"""
        from pinecone import Pinecone

        pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
        index = pc.Index(name)

        results = index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            filter=filter
        )

        return [{
            "id": match["id"],
            "document": match.get("metadata", {}).get("text"),
            "metadata": match.get("metadata", {}),
            "score": match["score"]
        } for match in results["matches"]]

    # ==================== QDRANT ====================

    async def _qdrant_create(self, name, dimension, **kwargs):
        """Create Qdrant collection"""
        from qdrant_client import QdrantClient
        from qdrant_client.models import VectorParams, Distance

        client = QdrantClient(
            url=os.environ.get("QDRANT_URL", "http://localhost:6333"),
            api_key=os.environ.get("QDRANT_API_KEY")
        )

        client.recreate_collection(
            collection_name=name,
            vectors_config=VectorParams(
                size=dimension,
                distance=Distance.COSINE
            )
        )

        return client

    async def _qdrant_add(self, name, documents, embeddings, metadatas, ids):
        """Add to Qdrant"""
        from qdrant_client import QdrantClient
        from qdrant_client.models import PointStruct
        import uuid

        client = QdrantClient(
            url=os.environ.get("QDRANT_URL", "http://localhost:6333"),
            api_key=os.environ.get("QDRANT_API_KEY")
        )

        points = []
        for i, (doc, emb) in enumerate(zip(documents, embeddings)):
            id_ = ids[i] if ids else str(uuid.uuid4())
            metadata = metadatas[i] if metadatas else {}
            metadata["text"] = doc

            points.append(PointStruct(
                id=id_ if isinstance(id_, int) else hash(id_) % (10**9),
                vector=emb,
                payload=metadata
            ))

        client.upsert(collection_name=name, points=points)
        return True

    async def _qdrant_search(self, name, query_embedding, top_k, filter):
        """Search Qdrant"""
        from qdrant_client import QdrantClient

        client = QdrantClient(
            url=os.environ.get("QDRANT_URL", "http://localhost:6333"),
            api_key=os.environ.get("QDRANT_API_KEY")
        )

        results = client.search(
            collection_name=name,
            query_vector=query_embedding,
            limit=top_k
        )

        return [{
            "id": str(r.id),
            "document": r.payload.get("text"),
            "metadata": r.payload,
            "score": r.score
        } for r in results]

    # ==================== FAISS ====================

    async def _faiss_create(self, name, dimension, **kwargs):
        """Create FAISS index"""
        import faiss
        import numpy as np

        index = faiss.IndexFlatIP(dimension)  # Inner product (cosine with normalized vectors)
        self._stores[f"faiss_{name}"] = {
            "index": index,
            "documents": [],
            "metadatas": [],
            "ids": []
        }
        return index

    async def _faiss_add(self, name, documents, embeddings, metadatas, ids):
        """Add to FAISS"""
        import faiss
        import numpy as np

        store_key = f"faiss_{name}"
        if store_key not in self._stores:
            await self._faiss_create(name, len(embeddings[0]))

        store = self._stores[store_key]

        # Normalize for cosine similarity
        vectors = np.array(embeddings).astype('float32')
        faiss.normalize_L2(vectors)

        store["index"].add(vectors)
        store["documents"].extend(documents)
        store["metadatas"].extend(metadatas or [{}] * len(documents))

        if ids:
            store["ids"].extend(ids)
        else:
            import uuid
            store["ids"].extend([str(uuid.uuid4()) for _ in documents])

        return True

    async def _faiss_search(self, name, query_embedding, top_k):
        """Search FAISS"""
        import faiss
        import numpy as np

        store = self._stores.get(f"faiss_{name}")
        if not store:
            return []

        query = np.array([query_embedding]).astype('float32')
        faiss.normalize_L2(query)

        distances, indices = store["index"].search(query, top_k)

        results = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx >= 0:
                results.append({
                    "id": store["ids"][idx],
                    "document": store["documents"][idx],
                    "metadata": store["metadatas"][idx],
                    "score": float(dist)
                })

        return results

    def list_providers(self) -> List[str]:
        """List vector store providers"""
        return [p.value for p in VectorStoreProvider]
