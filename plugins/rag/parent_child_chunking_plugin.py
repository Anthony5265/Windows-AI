"""
Parent-Child Chunking Plugin
Hierarchical document chunking with parent-child relationships
"""

from typing import Dict, Any, Optional, List
import hashlib


class ParentChildChunkingPlugin:
    """Plugin for parent-child hierarchical chunking"""

    name = "parent_child_chunking"
    version = "1.0.0"
    description = "Create hierarchical chunks with parent-child relationships"
    author = "Windows AI Team"

    def __init__(self):
        self.chunks = {}
        self.parent_map = {}
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Parent-Child Chunking plugin"""
        try:
            self._initialized = True
            return True
        except Exception as e:
            print(f"Error initializing Parent-Child Chunking plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Parent-Child Chunking action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "create_hierarchy":
                return self._create_hierarchy(params)
            elif action == "retrieve_with_context":
                return self._retrieve_with_context(params)
            elif action == "expand_chunks":
                return self._expand_chunks(params)
            elif action == "get_children":
                return self._get_children(params)
            elif action == "get_parent":
                return self._get_parent(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _create_hierarchy(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create parent-child chunk hierarchy"""
        document = params.get("document", "")
        parent_size = params.get("parent_size", 2000)  # chars
        child_size = params.get("child_size", 500)     # chars
        overlap = params.get("overlap", 100)           # chars

        # Generate document ID
        doc_id = hashlib.md5(document.encode()).hexdigest()[:12]

        # Create parent chunks
        parents = []
        parent_start = 0

        while parent_start < len(document):
            parent_end = min(parent_start + parent_size, len(document))
            parent_text = document[parent_start:parent_end]

            parent_id = f"{doc_id}_p{len(parents)}"
            parents.append({
                "id": parent_id,
                "text": parent_text,
                "start": parent_start,
                "end": parent_end,
                "level": "parent"
            })

            parent_start = parent_end - overlap

            if parent_end >= len(document):
                break

        # Create child chunks for each parent
        all_chunks = []
        for parent in parents:
            parent_text = parent["text"]
            child_start = 0
            children = []

            while child_start < len(parent_text):
                child_end = min(child_start + child_size, len(parent_text))
                child_text = parent_text[child_start:child_end]

                child_id = f"{parent['id']}_c{len(children)}"
                child_chunk = {
                    "id": child_id,
                    "text": child_text,
                    "start": parent["start"] + child_start,
                    "end": parent["start"] + child_end,
                    "level": "child",
                    "parent_id": parent["id"]
                }

                children.append(child_chunk)
                all_chunks.append(child_chunk)

                # Store mapping
                self.chunks[child_id] = child_chunk
                self.parent_map[child_id] = parent["id"]

                child_start = child_end - overlap

                if child_end >= len(parent_text):
                    break

            # Store parent with children
            parent["children"] = [c["id"] for c in children]
            self.chunks[parent["id"]] = parent
            all_chunks.append(parent)

        return {
            "success": True,
            "document_id": doc_id,
            "parents": parents,
            "total_chunks": len(all_chunks),
            "parent_count": len(parents),
            "child_count": len(all_chunks) - len(parents)
        }

    def _retrieve_with_context(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve child chunks with parent context

        When a child chunk matches a query, return it along with
        its parent chunk for additional context.
        """
        matched_chunks = params.get("matched_chunks", [])  # List of chunk IDs

        results = []
        for chunk_id in matched_chunks:
            if chunk_id not in self.chunks:
                continue

            chunk = self.chunks[chunk_id]
            result = {
                "chunk": chunk,
                "context": None
            }

            # If this is a child, get parent for context
            if chunk.get("level") == "child" and chunk_id in self.parent_map:
                parent_id = self.parent_map[chunk_id]
                if parent_id in self.chunks:
                    result["context"] = self.chunks[parent_id]

            results.append(result)

        return {
            "success": True,
            "results": results,
            "count": len(results)
        }

    def _expand_chunks(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Expand child chunks to include siblings and parent"""
        chunk_ids = params.get("chunk_ids", [])
        include_siblings = params.get("include_siblings", True)
        include_parent = params.get("include_parent", True)

        expanded = []
        for chunk_id in chunk_ids:
            if chunk_id not in self.chunks:
                continue

            chunk = self.chunks[chunk_id]
            expansion = {
                "chunk": chunk,
                "parent": None,
                "siblings": []
            }

            # Get parent if requested and if this is a child
            if include_parent and chunk.get("level") == "child" and chunk_id in self.parent_map:
                parent_id = self.parent_map[chunk_id]
                if parent_id in self.chunks:
                    parent = self.chunks[parent_id]
                    expansion["parent"] = parent

                    # Get siblings if requested
                    if include_siblings:
                        for child_id in parent.get("children", []):
                            if child_id != chunk_id and child_id in self.chunks:
                                expansion["siblings"].append(self.chunks[child_id])

            expanded.append(expansion)

        return {
            "success": True,
            "expanded_chunks": expanded,
            "count": len(expanded)
        }

    def _get_children(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get all children of a parent chunk"""
        parent_id = params.get("parent_id", "")

        if parent_id not in self.chunks:
            return {"success": False, "error": f"Parent chunk {parent_id} not found"}

        parent = self.chunks[parent_id]
        children = []

        for child_id in parent.get("children", []):
            if child_id in self.chunks:
                children.append(self.chunks[child_id])

        return {
            "success": True,
            "parent_id": parent_id,
            "children": children,
            "count": len(children)
        }

    def _get_parent(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get parent of a child chunk"""
        child_id = params.get("child_id", "")

        if child_id not in self.parent_map:
            return {"success": False, "error": f"Child chunk {child_id} not found or has no parent"}

        parent_id = self.parent_map[child_id]

        if parent_id not in self.chunks:
            return {"success": False, "error": f"Parent chunk {parent_id} not found"}

        return {
            "success": True,
            "child_id": child_id,
            "parent": self.chunks[parent_id]
        }

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.chunks = {}
        self.parent_map = {}
        return True
