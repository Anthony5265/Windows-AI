"""
Hierarchical Memory Plugin
Organize memories in hierarchical structures with parent-child relationships
"""

from typing import Dict, Any, Optional, List


class HierarchicalMemoryPlugin:
    """Plugin for hierarchical memory organization"""

    name = "hierarchical_memory"
    version = "1.0.0"
    description = "Organize memories in tree-like hierarchical structures"
    author = "Windows AI Team"

    def __init__(self):
        self.nodes = {}
        self.root_nodes = []
        self.hierarchies = {}
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Hierarchical Memory plugin"""
        try:
            self._initialized = True
            return True
        except Exception as e:
            print(f"Error initializing Hierarchical Memory plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Hierarchical Memory action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "create_node":
                return self._create_node(params)
            elif action == "add_child":
                return self._add_child(params)
            elif action == "get_children":
                return self._get_children(params)
            elif action == "get_ancestors":
                return self._get_ancestors(params)
            elif action == "get_descendants":
                return self._get_descendants(params)
            elif action == "get_siblings":
                return self._get_siblings(params)
            elif action == "move_node":
                return self._move_node(params)
            elif action == "get_path":
                return self._get_path(params)
            elif action == "get_level":
                return self._get_level(params)
            elif action == "search_hierarchy":
                return self._search_hierarchy(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _create_node(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new memory node"""
        node_id = params.get("node_id", f"node_{len(self.nodes)}")
        content = params.get("content", "")
        node_type = params.get("type", "general")
        metadata = params.get("metadata", {})
        parent_id = params.get("parent_id", None)

        node = {
            "id": node_id,
            "content": content,
            "type": node_type,
            "metadata": metadata,
            "parent_id": parent_id,
            "children": [],
            "level": 0,
            "created_at": "now"
        }

        # If has parent, add as child and calculate level
        if parent_id:
            if parent_id not in self.nodes:
                return {"success": False, "error": f"Parent node {parent_id} not found"}

            parent = self.nodes[parent_id]
            parent["children"].append(node_id)
            node["level"] = parent["level"] + 1
        else:
            # Root node
            self.root_nodes.append(node_id)

        self.nodes[node_id] = node

        return {
            "success": True,
            "node": node,
            "total_nodes": len(self.nodes),
            "is_root": parent_id is None
        }

    def _add_child(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add a child node to a parent"""
        parent_id = params.get("parent_id", "")
        child_id = params.get("child_id", "")

        if parent_id not in self.nodes:
            return {"success": False, "error": f"Parent node {parent_id} not found"}
        if child_id not in self.nodes:
            return {"success": False, "error": f"Child node {child_id} not found"}

        parent = self.nodes[parent_id]
        child = self.nodes[child_id]

        # Remove from old parent if exists
        if child["parent_id"]:
            old_parent = self.nodes[child["parent_id"]]
            if child_id in old_parent["children"]:
                old_parent["children"].remove(child_id)
        else:
            # Remove from root nodes
            if child_id in self.root_nodes:
                self.root_nodes.remove(child_id)

        # Add to new parent
        if child_id not in parent["children"]:
            parent["children"].append(child_id)

        child["parent_id"] = parent_id

        # Update level recursively
        self._update_levels(child_id, parent["level"] + 1)

        return {
            "success": True,
            "parent_id": parent_id,
            "child_id": child_id,
            "new_level": child["level"],
            "parent_children_count": len(parent["children"])
        }

    def _update_levels(self, node_id: str, new_level: int):
        """Recursively update levels for a node and its descendants"""
        if node_id not in self.nodes:
            return

        node = self.nodes[node_id]
        node["level"] = new_level

        # Update all children
        for child_id in node["children"]:
            self._update_levels(child_id, new_level + 1)

    def _get_children(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get all children of a node"""
        node_id = params.get("node_id", "")
        recursive = params.get("recursive", False)

        if node_id not in self.nodes:
            return {"success": False, "error": f"Node {node_id} not found"}

        node = self.nodes[node_id]

        if recursive:
            # Get all descendants
            children = self._get_all_descendants(node_id)
        else:
            # Get direct children only
            children = [self.nodes[child_id] for child_id in node["children"] if child_id in self.nodes]

        return {
            "success": True,
            "node_id": node_id,
            "children": children,
            "num_children": len(children),
            "recursive": recursive
        }

    def _get_all_descendants(self, node_id: str) -> List[Dict[str, Any]]:
        """Recursively get all descendants"""
        descendants = []

        if node_id not in self.nodes:
            return descendants

        node = self.nodes[node_id]

        for child_id in node["children"]:
            if child_id in self.nodes:
                child = self.nodes[child_id]
                descendants.append(child)
                # Recursively get children's descendants
                descendants.extend(self._get_all_descendants(child_id))

        return descendants

    def _get_ancestors(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get all ancestors of a node (path to root)"""
        node_id = params.get("node_id", "")

        if node_id not in self.nodes:
            return {"success": False, "error": f"Node {node_id} not found"}

        ancestors = []
        current_id = node_id

        while current_id in self.nodes:
            node = self.nodes[current_id]
            parent_id = node["parent_id"]

            if parent_id and parent_id in self.nodes:
                ancestors.append(self.nodes[parent_id])
                current_id = parent_id
            else:
                break

        return {
            "success": True,
            "node_id": node_id,
            "ancestors": ancestors,
            "num_ancestors": len(ancestors),
            "depth": len(ancestors)
        }

    def _get_descendants(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get all descendants of a node"""
        node_id = params.get("node_id", "")
        max_depth = params.get("max_depth", None)

        if node_id not in self.nodes:
            return {"success": False, "error": f"Node {node_id} not found"}

        descendants = self._get_descendants_with_depth(node_id, max_depth, 0)

        return {
            "success": True,
            "node_id": node_id,
            "descendants": descendants,
            "num_descendants": len(descendants),
            "max_depth": max_depth
        }

    def _get_descendants_with_depth(self, node_id: str, max_depth: Optional[int], current_depth: int) -> List[Dict[str, Any]]:
        """Get descendants up to a certain depth"""
        descendants = []

        if node_id not in self.nodes:
            return descendants

        if max_depth is not None and current_depth >= max_depth:
            return descendants

        node = self.nodes[node_id]

        for child_id in node["children"]:
            if child_id in self.nodes:
                child = self.nodes[child_id]
                descendants.append(child)
                # Recursively get deeper descendants
                descendants.extend(self._get_descendants_with_depth(child_id, max_depth, current_depth + 1))

        return descendants

    def _get_siblings(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get sibling nodes (nodes with same parent)"""
        node_id = params.get("node_id", "")

        if node_id not in self.nodes:
            return {"success": False, "error": f"Node {node_id} not found"}

        node = self.nodes[node_id]
        parent_id = node["parent_id"]

        siblings = []

        if parent_id and parent_id in self.nodes:
            parent = self.nodes[parent_id]
            siblings = [self.nodes[sibling_id] for sibling_id in parent["children"]
                       if sibling_id != node_id and sibling_id in self.nodes]
        elif not parent_id:
            # Root node - siblings are other root nodes
            siblings = [self.nodes[root_id] for root_id in self.root_nodes
                       if root_id != node_id and root_id in self.nodes]

        return {
            "success": True,
            "node_id": node_id,
            "siblings": siblings,
            "num_siblings": len(siblings),
            "same_parent": parent_id
        }

    def _move_node(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Move a node to a new parent"""
        node_id = params.get("node_id", "")
        new_parent_id = params.get("new_parent_id", None)

        if node_id not in self.nodes:
            return {"success": False, "error": f"Node {node_id} not found"}

        if new_parent_id and new_parent_id not in self.nodes:
            return {"success": False, "error": f"New parent {new_parent_id} not found"}

        # Check for circular reference
        if new_parent_id:
            ancestors = self._get_ancestors({"node_id": new_parent_id})["ancestors"]
            if any(anc["id"] == node_id for anc in ancestors):
                return {"success": False, "error": "Cannot move node to its own descendant"}

        node = self.nodes[node_id]
        old_parent_id = node["parent_id"]

        # Remove from old parent
        if old_parent_id and old_parent_id in self.nodes:
            old_parent = self.nodes[old_parent_id]
            if node_id in old_parent["children"]:
                old_parent["children"].remove(node_id)
        elif not old_parent_id and node_id in self.root_nodes:
            self.root_nodes.remove(node_id)

        # Add to new parent
        if new_parent_id:
            new_parent = self.nodes[new_parent_id]
            new_parent["children"].append(node_id)
            node["parent_id"] = new_parent_id
            self._update_levels(node_id, new_parent["level"] + 1)
        else:
            # Move to root
            self.root_nodes.append(node_id)
            node["parent_id"] = None
            self._update_levels(node_id, 0)

        return {
            "success": True,
            "node_id": node_id,
            "old_parent_id": old_parent_id,
            "new_parent_id": new_parent_id,
            "new_level": node["level"]
        }

    def _get_path(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get the full path from root to node"""
        node_id = params.get("node_id", "")

        if node_id not in self.nodes:
            return {"success": False, "error": f"Node {node_id} not found"}

        path = [self.nodes[node_id]]
        current_id = node_id

        while current_id in self.nodes:
            node = self.nodes[current_id]
            parent_id = node["parent_id"]

            if parent_id and parent_id in self.nodes:
                path.insert(0, self.nodes[parent_id])
                current_id = parent_id
            else:
                break

        # Create path string
        path_string = " -> ".join([node["id"] for node in path])

        return {
            "success": True,
            "node_id": node_id,
            "path": path,
            "path_string": path_string,
            "depth": len(path) - 1
        }

    def _get_level(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get all nodes at a specific level"""
        level = params.get("level", 0)

        nodes_at_level = [node for node in self.nodes.values() if node["level"] == level]

        return {
            "success": True,
            "level": level,
            "nodes": nodes_at_level,
            "num_nodes": len(nodes_at_level)
        }

    def _search_hierarchy(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search for nodes in the hierarchy"""
        query = params.get("query", "")
        search_field = params.get("field", "content")  # content, type, id
        start_node = params.get("start_node", None)

        results = []

        # Determine search scope
        if start_node:
            if start_node not in self.nodes:
                return {"success": False, "error": f"Start node {start_node} not found"}
            # Search in descendants only
            search_nodes = [self.nodes[start_node]] + self._get_all_descendants(start_node)
        else:
            # Search all nodes
            search_nodes = list(self.nodes.values())

        # Perform search
        for node in search_nodes:
            field_value = str(node.get(search_field, ""))
            if query.lower() in field_value.lower():
                results.append(node)

        return {
            "success": True,
            "query": query,
            "search_field": search_field,
            "start_node": start_node,
            "results": results,
            "num_results": len(results)
        }

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.nodes = {}
        self.root_nodes = []
        self.hierarchies = {}
        return True
