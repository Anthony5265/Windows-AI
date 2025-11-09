"""
FAISS Vector Database Integration
Facebook AI Similarity Search for efficient similarity search
"""
from typing import Dict, Any, List, Optional
import logging
import os
import pickle
import numpy as np

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

logger = logging.getLogger(__name__)

class FAISSDB:
    """FAISS vector database client"""

    def __init__(self):
        self.persist_directory = os.getenv("FAISS_PERSIST_DIR", "./faiss_db")
        self.indexes = {}
        self.metadatas = {}

        os.makedirs(self.persist_directory, exist_ok=True)

    async def create_index(self, name: str, dimension: int, index_type: str = "Flat") -> Dict[str, Any]:
        """Create a new FAISS index"""
        if not FAISS_AVAILABLE:
            return {"status": "error", "message": "FAISS not available"}

        try:
            if index_type == "Flat":
                index = faiss.IndexFlatL2(dimension)
            elif index_type == "IVF":
                quantizer = faiss.IndexFlatL2(dimension)
                index = faiss.IndexIVFFlat(quantizer, dimension, 100)
            elif index_type == "HNSW":
                index = faiss.IndexHNSWFlat(dimension, 32)
            else:
                return {"status": "error", "message": f"Unknown index type: {index_type}"}

            self.indexes[name] = index
            self.metadatas[name] = {}
            return {"status": "success", "index": name, "dimension": dimension}
        except Exception as e:
            logger.error(f"Create index error: {e}")
            return {"status": "error", "message": str(e)}

    async def add(self, index_name: str, vectors: np.ndarray, ids: List[str],
                  metadatas: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Add vectors to index"""
        if index_name not in self.indexes:
            return {"status": "error", "message": f"Index {index_name} not found"}

        try:
            index = self.indexes[index_name]

            # Train index if needed (for IVF)
            if isinstance(index, faiss.IndexIVFFlat) and not index.is_trained:
                index.train(vectors)

            # Add vectors
            index.add(vectors)

            # Store metadata
            if metadatas:
                for i, (id_, metadata) in enumerate(zip(ids, metadatas)):
                    self.metadatas[index_name][id_] = metadata

            return {"status": "success", "count": len(vectors)}
        except Exception as e:
            logger.error(f"Add vectors error: {e}")
            return {"status": "error", "message": str(e)}

    async def search(self, index_name: str, query_vectors: np.ndarray,
                     k: int = 10) -> Dict[str, Any]:
        """Search for similar vectors"""
        if index_name not in self.indexes:
            return {"status": "error", "message": f"Index {index_name} not found"}

        try:
            index = self.indexes[index_name]
            distances, indices = index.search(query_vectors, k)

            results = []
            for dist_row, idx_row in zip(distances, indices):
                matches = []
                for distance, idx in zip(dist_row, idx_row):
                    if idx >= 0:  # -1 means no match found
                        matches.append({
                            "index": int(idx),
                            "distance": float(distance),
                            "metadata": self.metadatas[index_name].get(str(idx), {})
                        })
                results.append(matches)

            return {"status": "success", "results": results}
        except Exception as e:
            logger.error(f"Search error: {e}")
            return {"status": "error", "message": str(e)}

    async def save(self, index_name: str) -> Dict[str, Any]:
        """Save index to disk"""
        if index_name not in self.indexes:
            return {"status": "error", "message": f"Index {index_name} not found"}

        try:
            index_path = os.path.join(self.persist_directory, f"{index_name}.index")
            metadata_path = os.path.join(self.persist_directory, f"{index_name}.meta")

            faiss.write_index(self.indexes[index_name], index_path)

            with open(metadata_path, "wb") as f:
                pickle.dump(self.metadatas[index_name], f)

            return {"status": "success", "path": index_path}
        except Exception as e:
            logger.error(f"Save index error: {e}")
            return {"status": "error", "message": str(e)}

    async def load(self, index_name: str) -> Dict[str, Any]:
        """Load index from disk"""
        try:
            index_path = os.path.join(self.persist_directory, f"{index_name}.index")
            metadata_path = os.path.join(self.persist_directory, f"{index_name}.meta")

            if not os.path.exists(index_path):
                return {"status": "error", "message": f"Index file not found: {index_path}"}

            self.indexes[index_name] = faiss.read_index(index_path)

            if os.path.exists(metadata_path):
                with open(metadata_path, "rb") as f:
                    self.metadatas[index_name] = pickle.load(f)
            else:
                self.metadatas[index_name] = {}

            return {"status": "success", "index": index_name}
        except Exception as e:
            logger.error(f"Load index error: {e}")
            return {"status": "error", "message": str(e)}

    async def list_indexes(self) -> Dict[str, Any]:
        """List all indexes"""
        return {"status": "success", "indexes": list(self.indexes.keys())}
