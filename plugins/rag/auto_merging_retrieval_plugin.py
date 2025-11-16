"""
Auto-Merging Retrieval Plugin
Automatically merge smaller chunks into larger context when needed
"""

from typing import Dict, Any, Optional, List


class AutoMergingRetrievalPlugin:
    """Plugin for auto-merging retrieval with hierarchical chunks"""

    name = "auto_merging_retrieval"
    version = "1.0.0"
    description = "Automatically merge child chunks into parent chunks for better context"
    author = "Windows AI Team"

    def __init__(self):
        self.chunks = {}
        self.hierarchy = {}
        self.retrieved_cache = {}
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Auto-Merging Retrieval plugin"""
        try:
            self._initialized = True
            return True
        except Exception as e:
            print(f"Error initializing Auto-Merging Retrieval plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an Auto-Merging Retrieval action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "create_hierarchy":
                return self._create_hierarchy(params)
            elif action == "retrieve_and_merge":
                return self._retrieve_and_merge(params)
            elif action == "should_merge":
                return self._should_merge(params)
            elif action == "merge_chunks":
                return self._merge_chunks(params)
            elif action == "get_context":
                return self._get_context(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _create_hierarchy(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create hierarchical chunk structure"""
        document_id = params.get("document_id", f"doc_{len(self.hierarchy)}")
        text = params.get("text", "")
        chunk_sizes = params.get("chunk_sizes", [128, 512, 2048])  # Small, medium, large

        # Create chunks at different levels
        hierarchy = {
            "document_id": document_id,
            "levels": []
        }

        current_text = text
        for level, size in enumerate(chunk_sizes):
            # Simulate chunking
            num_chunks = max(1, len(text) // size)
            chunks_at_level = []

            for i in range(num_chunks):
                chunk_id = f"{document_id}_L{level}_C{i}"
                chunk = {
                    "id": chunk_id,
                    "level": level,
                    "text": f"Chunk {i} at level {level} (size {size})",
                    "start_pos": i * size,
                    "end_pos": min((i + 1) * size, len(text)),
                    "parent_id": None,
                    "children": []
                }

                # Link to children from previous level
                if level > 0:
                    # Children are chunks from previous level that overlap
                    prev_level_chunks = hierarchy["levels"][level - 1]
                    for prev_chunk in prev_level_chunks:
                        if (prev_chunk["start_pos"] >= chunk["start_pos"] and
                            prev_chunk["start_pos"] < chunk["end_pos"]):
                            chunk["children"].append(prev_chunk["id"])
                            prev_chunk["parent_id"] = chunk_id

                chunks_at_level.append(chunk)
                self.chunks[chunk_id] = chunk

            hierarchy["levels"].append(chunks_at_level)

        self.hierarchy[document_id] = hierarchy

        return {
            "success": True,
            "document_id": document_id,
            "num_levels": len(hierarchy["levels"]),
            "total_chunks": sum(len(level) for level in hierarchy["levels"]),
            "hierarchy": hierarchy
        }

    def _retrieve_and_merge(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve chunks and automatically merge if needed"""
        query = params.get("query", "")
        top_k = params.get("top_k", 5)
        merge_threshold = params.get("merge_threshold", 3)
        target_level = params.get("target_level", 0)  # Start with smallest chunks

        # Simulate retrieval at target level
        retrieved_chunks = []
        for chunk_id, chunk in self.chunks.items():
            if chunk["level"] == target_level:
                # Simulate similarity score
                score = 0.9 - len(retrieved_chunks) * 0.1
                retrieved_chunks.append({
                    "chunk_id": chunk_id,
                    "score": score,
                    "chunk": chunk
                })

        retrieved_chunks.sort(key=lambda x: x["score"], reverse=True)
        retrieved_chunks = retrieved_chunks[:top_k]

        # Check if we should merge
        should_merge_result = self._should_merge({
            "chunks": [c["chunk"] for c in retrieved_chunks],
            "threshold": merge_threshold
        })

        if should_merge_result["should_merge"]:
            # Merge to parent level
            merged = self._merge_chunks({
                "chunk_ids": [c["chunk_id"] for c in retrieved_chunks]
            })

            final_chunks = merged["merged_chunks"]
            merge_performed = True
        else:
            final_chunks = [c["chunk"] for c in retrieved_chunks]
            merge_performed = False

        return {
            "success": True,
            "query": query,
            "retrieved_chunks": final_chunks,
            "num_chunks": len(final_chunks),
            "merge_performed": merge_performed,
            "original_level": target_level
        }

    def _should_merge(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Determine if chunks should be merged based on heuristics"""
        chunks = params.get("chunks", [])
        threshold = params.get("threshold", 3)

        # Check if many chunks come from same parent
        parent_counts = {}
        for chunk in chunks:
            parent_id = chunk.get("parent_id")
            if parent_id:
                parent_counts[parent_id] = parent_counts.get(parent_id, 0) + 1

        # If many chunks share a parent, merge
        max_siblings = max(parent_counts.values()) if parent_counts else 0
        should_merge = max_siblings >= threshold

        merge_reasons = []
        if should_merge:
            merge_reasons.append(f"{max_siblings} chunks from same parent (threshold: {threshold})")

        # Additional heuristics
        if len(chunks) > 5:
            merge_reasons.append("Too many small chunks retrieved")
            should_merge = True

        return {
            "success": True,
            "should_merge": should_merge,
            "max_siblings": max_siblings,
            "threshold": threshold,
            "reasons": merge_reasons
        }

    def _merge_chunks(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Merge child chunks into their parents"""
        chunk_ids = params.get("chunk_ids", [])

        # Group chunks by parent
        parent_groups = {}
        for chunk_id in chunk_ids:
            if chunk_id not in self.chunks:
                continue

            chunk = self.chunks[chunk_id]
            parent_id = chunk.get("parent_id")

            if parent_id:
                if parent_id not in parent_groups:
                    parent_groups[parent_id] = []
                parent_groups[parent_id].append(chunk_id)
            else:
                # No parent, keep as is
                if "no_parent" not in parent_groups:
                    parent_groups["no_parent"] = []
                parent_groups["no_parent"].append(chunk_id)

        # Create merged chunks
        merged_chunks = []
        for parent_id, child_ids in parent_groups.items():
            if parent_id == "no_parent":
                # Add original chunks
                for child_id in child_ids:
                    merged_chunks.append(self.chunks[child_id])
            else:
                # Add parent chunk
                if parent_id in self.chunks:
                    parent_chunk = self.chunks[parent_id]
                    merged_chunks.append({
                        **parent_chunk,
                        "merged_from": child_ids,
                        "num_children_merged": len(child_ids)
                    })

        return {
            "success": True,
            "merged_chunks": merged_chunks,
            "num_merged": len(merged_chunks),
            "original_count": len(chunk_ids)
        }

    def _get_context(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get full context for a chunk (including siblings and parent)"""
        chunk_id = params.get("chunk_id", "")
        include_siblings = params.get("include_siblings", True)
        include_parent = params.get("include_parent", True)

        if chunk_id not in self.chunks:
            return {"success": False, "error": "Chunk not found"}

        chunk = self.chunks[chunk_id]
        context_chunks = [chunk]

        # Add parent
        if include_parent and chunk.get("parent_id"):
            parent_id = chunk["parent_id"]
            if parent_id in self.chunks:
                context_chunks.insert(0, self.chunks[parent_id])

        # Add siblings
        if include_siblings and chunk.get("parent_id"):
            parent = self.chunks[chunk["parent_id"]]
            for sibling_id in parent.get("children", []):
                if sibling_id != chunk_id and sibling_id in self.chunks:
                    context_chunks.append(self.chunks[sibling_id])

        # Sort by position
        context_chunks.sort(key=lambda c: c.get("start_pos", 0))

        return {
            "success": True,
            "chunk_id": chunk_id,
            "context_chunks": context_chunks,
            "num_chunks": len(context_chunks),
            "includes_parent": include_parent and chunk.get("parent_id") is not None,
            "includes_siblings": include_siblings
        }

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.chunks = {}
        self.hierarchy = {}
        self.retrieved_cache = {}
        return True
