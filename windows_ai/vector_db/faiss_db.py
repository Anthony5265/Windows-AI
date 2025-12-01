"""
FAISS Vector Database Integration
Facebook AI Similarity Search for efficient local similarity search
"""
from typing import Dict, Any, List, Optional, Tuple
import logging
import os
import pickle
import json
import numpy as np
from pathlib import Path

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

from .base import (
    VectorDBInterface,
    VectorDBConfig,
    VectorDBType,
    MetricType,
    SearchResult,
    IndexStats
)

logger = logging.getLogger(__name__)


class FAISSDB(VectorDBInterface):
    """FAISS vector database client for local-first vector search"""

    def __init__(self, config: Optional[VectorDBConfig] = None):
        """Initialize FAISS client"""
        if not config:
            config = VectorDBConfig(
                db_type=VectorDBType.FAISS,
                dimension=1536,
                metric=MetricType.L2,
                persist_directory=os.getenv("FAISS_PERSIST_DIR", "./faiss_db")
            )

        super().__init__(config)

        if not FAISS_AVAILABLE:
            self.logger.error("FAISS library not installed. Install with: pip install faiss-cpu or faiss-gpu")
            return

        # Storage for indexes and metadata
        self._indexes = {}
        self._metadatas = {}  # {index_name: {id: metadata}}
        self._id_mappings = {}  # {index_name: {id_str: internal_idx}}
        self._documents = {}  # {index_name: {id: document_text}}
        self._connected = False

        # Create persist directory
        os.makedirs(self.config.persist_directory, exist_ok=True)

    async def connect(self) -> Dict[str, Any]:
        """Establish connection (load existing indexes)"""
        try:
            if not FAISS_AVAILABLE:
                return {"status": "error", "message": "FAISS not installed"}

            # Load existing indexes from disk
            persist_path = Path(self.config.persist_directory)
            loaded_indexes = []

            for index_file in persist_path.glob("*.index"):
                index_name = index_file.stem
                result = await self.load(index_name)
                if result.get("status") == "success":
                    loaded_indexes.append(index_name)

            self._connected = True

            return {
                "status": "success",
                "message": "Connected to FAISS",
                "persist_directory": self.config.persist_directory,
                "loaded_indexes": loaded_indexes
            }

        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            return {"status": "error", "message": str(e)}

    async def disconnect(self) -> Dict[str, Any]:
        """Close connection (save all indexes)"""
        try:
            # Save all indexes
            saved = []
            for index_name in list(self._indexes.keys()):
                result = await self.save(index_name)
                if result.get("status") == "success":
                    saved.append(index_name)

            self._indexes.clear()
            self._metadatas.clear()
            self._id_mappings.clear()
            self._documents.clear()
            self._connected = False

            return {
                "status": "success",
                "message": "Disconnected from FAISS",
                "saved_indexes": saved
            }

        except Exception as e:
            self.logger.error(f"Disconnect error: {e}")
            return {"status": "error", "message": str(e)}

    async def create_index(
        self,
        name: str,
        dimension: int,
        metric: MetricType = MetricType.L2,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a new FAISS index"""
        if not FAISS_AVAILABLE:
            return {"status": "error", "message": "FAISS not available"}

        try:
            index_type = kwargs.get("index_type", "Flat")

            # Map MetricType to FAISS index type
            if metric == MetricType.COSINE:
                # For cosine similarity, we normalize vectors and use L2
                if index_type == "Flat":
                    index = faiss.IndexFlatIP(dimension)  # Inner product for normalized vectors
                elif index_type == "IVF":
                    quantizer = faiss.IndexFlatIP(dimension)
                    nlist = kwargs.get("nlist", 100)
                    index = faiss.IndexIVFFlat(quantizer, dimension, nlist)
                elif index_type == "HNSW":
                    M = kwargs.get("M", 32)
                    index = faiss.IndexHNSWFlat(dimension, M)
                else:
                    return {"status": "error", "message": f"Unknown index type: {index_type}"}

            elif metric in [MetricType.L2, MetricType.EUCLIDEAN]:
                if index_type == "Flat":
                    index = faiss.IndexFlatL2(dimension)
                elif index_type == "IVF":
                    quantizer = faiss.IndexFlatL2(dimension)
                    nlist = kwargs.get("nlist", 100)
                    index = faiss.IndexIVFFlat(quantizer, dimension, nlist)
                elif index_type == "HNSW":
                    M = kwargs.get("M", 32)
                    index = faiss.IndexHNSWFlat(dimension, M)
                else:
                    return {"status": "error", "message": f"Unknown index type: {index_type}"}

            else:
                # Default to L2
                index = faiss.IndexFlatL2(dimension)

            self._indexes[name] = index
            self._metadatas[name] = {}
            self._id_mappings[name] = {}
            self._documents[name] = {}

            return {
                "status": "success",
                "index": name,
                "dimension": dimension,
                "metric": metric.value,
                "index_type": index_type
            }

        except Exception as e:
            self.logger.error(f"Create index error: {e}")
            return {"status": "error", "message": str(e)}

    async def delete_index(self, name: str) -> Dict[str, Any]:
        """Delete an index"""
        try:
            if name in self._indexes:
                del self._indexes[name]
                del self._metadatas[name]
                del self._id_mappings[name]
                del self._documents[name]

            # Delete files from disk
            index_path = Path(self.config.persist_directory) / f"{name}.index"
            meta_path = Path(self.config.persist_directory) / f"{name}.meta"
            mappings_path = Path(self.config.persist_directory) / f"{name}.mappings"
            docs_path = Path(self.config.persist_directory) / f"{name}.docs"

            for path in [index_path, meta_path, mappings_path, docs_path]:
                if path.exists():
                    path.unlink()

            return {"status": "success", "index": name}

        except Exception as e:
            self.logger.error(f"Delete index error: {e}")
            return {"status": "error", "message": str(e)}

    async def list_indexes(self) -> Dict[str, Any]:
        """List all indexes"""
        try:
            indexes = list(self._indexes.keys())
            return {
                "status": "success",
                "indexes": indexes,
                "count": len(indexes)
            }
        except Exception as e:
            self.logger.error(f"List indexes error: {e}")
            return {"status": "error", "message": str(e)}

    async def get_index_stats(self, name: str) -> Dict[str, Any]:
        """Get statistics about an index"""
        try:
            if name not in self._indexes:
                return {"status": "error", "message": f"Index {name} not found"}

            index = self._indexes[name]
            total_vectors = index.ntotal

            return {
                "status": "success",
                "stats": IndexStats(
                    name=name,
                    dimension=index.d,
                    total_vectors=total_vectors,
                    metric=MetricType.L2,
                    metadata={
                        "index_type": type(index).__name__,
                        "is_trained": index.is_trained if hasattr(index, 'is_trained') else True
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
        """Insert or update vectors"""
        try:
            if index_name not in self._indexes:
                return {"status": "error", "message": f"Index {index_name} not found"}

            index = self._indexes[index_name]
            vectors_array = np.array(vectors, dtype=np.float32)

            # Normalize for cosine similarity if needed
            normalize = kwargs.get("normalize", False)
            if normalize:
                faiss.normalize_L2(vectors_array)

            # Train index if needed (for IVF indexes)
            if hasattr(index, 'is_trained') and not index.is_trained:
                if vectors_array.shape[0] >= 100:  # Need enough vectors for training
                    index.train(vectors_array)
                else:
                    self.logger.warning(f"Not enough vectors for training IVF index (need >=100, got {vectors_array.shape[0]})")

            # Get current index size
            current_size = index.ntotal

            # Add vectors to index
            index.add(vectors_array)

            # Store metadata and mappings
            for i, id_ in enumerate(ids):
                internal_idx = current_size + i
                self._id_mappings[index_name][id_] = internal_idx

                if metadata and i < len(metadata):
                    self._metadatas[index_name][id_] = metadata[i]

                if documents and i < len(documents):
                    self._documents[index_name][id_] = documents[i]

            return {
                "status": "success",
                "count": len(ids),
                "total_vectors": index.ntotal
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
        try:
            if index_name not in self._indexes:
                return {"status": "error", "message": f"Index {index_name} not found"}

            index = self._indexes[index_name]
            query_array = np.array([query_vector], dtype=np.float32)

            # Normalize for cosine similarity if needed
            normalize = kwargs.get("normalize", False)
            if normalize:
                faiss.normalize_L2(query_array)

            # Search
            distances, indices = index.search(query_array, top_k)

            # Convert to SearchResult format
            results = []
            id_mapping_reverse = {v: k for k, v in self._id_mappings[index_name].items()}

            for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
                if idx < 0:  # -1 means no match found
                    continue

                # Get ID from internal index
                result_id = id_mapping_reverse.get(int(idx), f"vec_{idx}")

                # Convert distance to similarity score (higher is better)
                # For L2 distance, smaller is better, so invert it
                score = 1.0 / (1.0 + float(dist))

                result = SearchResult(
                    id=result_id,
                    score=score,
                    vector=None,  # FAISS doesn't easily retrieve vectors
                    metadata=self._metadatas[index_name].get(result_id) if include_metadata else None,
                    document=self._documents[index_name].get(result_id)
                )

                # Apply metadata filter if provided
                if filter:
                    if result.metadata:
                        matches_filter = all(
                            result.metadata.get(k) == v
                            for k, v in filter.items()
                        )
                        if not matches_filter:
                            continue

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
        """Delete vectors (note: FAISS doesn't support efficient deletion)"""
        try:
            if index_name not in self._indexes:
                return {"status": "error", "message": f"Index {index_name} not found"}

            if delete_all:
                # Reset the index
                index = self._indexes[index_name]
                dimension = index.d
                index_type = type(index).__name__

                # Recreate index
                if "Flat" in index_type:
                    if "IP" in index_type:
                        self._indexes[index_name] = faiss.IndexFlatIP(dimension)
                    else:
                        self._indexes[index_name] = faiss.IndexFlatL2(dimension)

                self._metadatas[index_name].clear()
                self._id_mappings[index_name].clear()
                self._documents[index_name].clear()

                return {"status": "success", "deleted": "all"}

            elif ids:
                # Remove metadata only (FAISS doesn't support efficient vector deletion)
                for id_ in ids:
                    self._metadatas[index_name].pop(id_, None)
                    self._id_mappings[index_name].pop(id_, None)
                    self._documents[index_name].pop(id_, None)

                return {
                    "status": "success",
                    "deleted": len(ids),
                    "note": "Metadata deleted. For full deletion, recreate index."
                }

            else:
                return {"status": "error", "message": "Must specify ids or delete_all"}

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
        try:
            if index_name not in self._indexes:
                return {"status": "error", "message": f"Index {index_name} not found"}

            if id not in self._id_mappings[index_name]:
                return {"status": "error", "message": f"ID {id} not found"}

            self._metadatas[index_name][id] = metadata

            return {"status": "success", "id": id}

        except Exception as e:
            self.logger.error(f"Update metadata error: {e}")
            return {"status": "error", "message": str(e)}

    async def save(self, index_name: str) -> Dict[str, Any]:
        """Save index and metadata to disk"""
        try:
            if index_name not in self._indexes:
                return {"status": "error", "message": f"Index {index_name} not found"}

            persist_path = Path(self.config.persist_directory)
            index_path = persist_path / f"{index_name}.index"
            meta_path = persist_path / f"{index_name}.meta"
            mappings_path = persist_path / f"{index_name}.mappings"
            docs_path = persist_path / f"{index_name}.docs"

            # Save FAISS index
            faiss.write_index(self._indexes[index_name], str(index_path))

            # Save metadata
            with open(meta_path, "wb") as f:
                pickle.dump(self._metadatas[index_name], f)

            # Save ID mappings
            with open(mappings_path, "wb") as f:
                pickle.dump(self._id_mappings[index_name], f)

            # Save documents
            with open(docs_path, "wb") as f:
                pickle.dump(self._documents[index_name], f)

            return {
                "status": "success",
                "index": index_name,
                "path": str(index_path)
            }

        except Exception as e:
            self.logger.error(f"Save error: {e}")
            return {"status": "error", "message": str(e)}

    async def load(self, index_name: str) -> Dict[str, Any]:
        """Load index and metadata from disk"""
        try:
            persist_path = Path(self.config.persist_directory)
            index_path = persist_path / f"{index_name}.index"
            meta_path = persist_path / f"{index_name}.meta"
            mappings_path = persist_path / f"{index_name}.mappings"
            docs_path = persist_path / f"{index_name}.docs"

            if not index_path.exists():
                return {"status": "error", "message": f"Index file not found: {index_path}"}

            # Load FAISS index
            self._indexes[index_name] = faiss.read_index(str(index_path))

            # Load metadata
            if meta_path.exists():
                with open(meta_path, "rb") as f:
                    self._metadatas[index_name] = pickle.load(f)
            else:
                self._metadatas[index_name] = {}

            # Load ID mappings
            if mappings_path.exists():
                with open(mappings_path, "rb") as f:
                    self._id_mappings[index_name] = pickle.load(f)
            else:
                self._id_mappings[index_name] = {}

            # Load documents
            if docs_path.exists():
                with open(docs_path, "rb") as f:
                    self._documents[index_name] = pickle.load(f)
            else:
                self._documents[index_name] = {}

            return {
                "status": "success",
                "index": index_name,
                "vectors": self._indexes[index_name].ntotal
            }

        except Exception as e:
            self.logger.error(f"Load error: {e}")
            return {"status": "error", "message": str(e)}
