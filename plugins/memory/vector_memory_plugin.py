"""
Vector Memory Plugin
Long-term semantic memory using vector embeddings
"""

from typing import Dict, Any, Optional, List


class VectorMemoryPlugin:
    """Plugin for semantic memory with vector search"""

    name = "vector_memory"
    version = "1.0.0"
    description = "Long-term semantic memory using vector embeddings"
    author = "Windows AI Team"

    def __init__(self):
        self.memories = []
        self.embeddings = []
        self.embedding_model = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Vector Memory plugin"""
        try:
            from sentence_transformers import SentenceTransformer

            model_name = config.get("model", "all-MiniLM-L6-v2") if config else "all-MiniLM-L6-v2"
            self.embedding_model = SentenceTransformer(model_name)
            self._initialized = True
            return True
        except ImportError:
            print("sentence-transformers package not installed")
            return False
        except Exception as e:
            print(f"Error initializing Vector Memory plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a vector memory action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "store":
                return self._store(params)
            elif action == "recall":
                return self._recall(params)
            elif action == "search":
                return self._search(params)
            elif action == "clear":
                return self._clear()
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _store(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Store a memory"""
        content = params.get("content", "")
        metadata = params.get("metadata", {})

        # Generate embedding
        embedding = self.embedding_model.encode(content)

        memory = {
            "content": content,
            "metadata": metadata,
            "id": len(self.memories)
        }

        self.memories.append(memory)
        self.embeddings.append(embedding)

        return {
            "success": True,
            "memory_id": memory["id"],
            "total_memories": len(self.memories)
        }

    def _recall(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Recall most similar memories"""
        import numpy as np
        from sklearn.metrics.pairwise import cosine_similarity

        query = params.get("query", "")
        top_k = params.get("top_k", 5)

        if not self.memories:
            return {
                "success": True,
                "memories": [],
                "count": 0
            }

        # Generate query embedding
        query_embedding = self.embedding_model.encode(query)

        # Calculate similarities
        similarities = cosine_similarity(
            [query_embedding],
            self.embeddings
        )[0]

        # Get top-k indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]

        recalled_memories = [
            {
                **self.memories[idx],
                "similarity": float(similarities[idx])
            }
            for idx in top_indices
        ]

        return {
            "success": True,
            "memories": recalled_memories,
            "count": len(recalled_memories)
        }

    def _search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search memories by metadata"""
        metadata_filter = params.get("metadata_filter", {})

        filtered_memories = [
            mem for mem in self.memories
            if all(mem["metadata"].get(k) == v for k, v in metadata_filter.items())
        ]

        return {
            "success": True,
            "memories": filtered_memories,
            "count": len(filtered_memories)
        }

    def _clear(self) -> Dict[str, Any]:
        """Clear all memories"""
        self.memories = []
        self.embeddings = []

        return {
            "success": True,
            "message": "All memories cleared"
        }

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.memories = []
        self.embeddings = []
        return True
