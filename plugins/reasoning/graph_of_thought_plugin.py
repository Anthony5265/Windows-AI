"""
Graph of Thought Plugin
Graph-based reasoning with nodes and edges representing thoughts and relationships
"""

from typing import Dict, Any, Optional, List
import hashlib


class GraphOfThoughtPlugin:
    """Plugin for Graph of Thought reasoning"""

    name = "graph_of_thought"
    version = "1.0.0"
    description = "Graph-based reasoning combining ideas from multiple paths"
    author = "Windows AI Team"

    def __init__(self):
        self.graph = {
            "nodes": {},
            "edges": []
        }
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Graph of Thought plugin"""
        try:
            self._initialized = True
            return True
        except Exception as e:
            print(f"Error initializing Graph of Thought plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Graph of Thought action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "add_thought":
                return self._add_thought(params)
            elif action == "connect_thoughts":
                return self._connect_thoughts(params)
            elif action == "aggregate":
                return self._aggregate(params)
            elif action == "find_path":
                return self._find_path(params)
            elif action == "get_neighbors":
                return self._get_neighbors(params)
            elif action == "get_graph":
                return self._get_graph()
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _add_thought(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add a thought node to the graph"""
        thought_id = params.get("id")
        content = params.get("content", "")
        metadata = params.get("metadata", {})

        if not thought_id:
            # Generate ID from content
            thought_id = hashlib.md5(content.encode()).hexdigest()[:12]

        if thought_id in self.graph["nodes"]:
            return {"success": False, "error": f"Thought {thought_id} already exists"}

        node = {
            "id": thought_id,
            "content": content,
            "metadata": metadata,
            "score": params.get("score", 0.5),
            "depth": params.get("depth", 0)
        }

        self.graph["nodes"][thought_id] = node

        return {
            "success": True,
            "thought_id": thought_id,
            "node": node
        }

    def _connect_thoughts(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Connect two thoughts with a labeled edge"""
        from_id = params.get("from", "")
        to_id = params.get("to", "")
        relationship = params.get("relationship", "leads_to")
        weight = params.get("weight", 1.0)

        if from_id not in self.graph["nodes"]:
            return {"success": False, "error": f"Source thought {from_id} not found"}

        if to_id not in self.graph["nodes"]:
            return {"success": False, "error": f"Target thought {to_id} not found"}

        edge = {
            "from": from_id,
            "to": to_id,
            "relationship": relationship,
            "weight": weight
        }

        self.graph["edges"].append(edge)

        return {
            "success": True,
            "edge": edge,
            "total_edges": len(self.graph["edges"])
        }

    def _aggregate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate multiple reasoning paths into a coherent solution"""
        target_thought = params.get("target")
        aggregation_method = params.get("method", "voting")  # voting, weighted, consensus

        if target_thought and target_thought not in self.graph["nodes"]:
            return {"success": False, "error": f"Target thought {target_thought} not found"}

        # Find all paths leading to target (or all leaf nodes if no target)
        if target_thought:
            paths = self._find_all_paths_to(target_thought)
        else:
            leaf_nodes = self._find_leaf_nodes()
            paths = [self._find_path({"start": "root", "end": leaf})["path"]
                    for leaf in leaf_nodes
                    if self._find_path({"start": "root", "end": leaf})["success"]]

        if aggregation_method == "voting":
            # Count frequency of thoughts across paths
            thought_votes = {}
            for path in paths:
                for thought_id in path:
                    thought_votes[thought_id] = thought_votes.get(thought_id, 0) + 1

            # Select most voted thoughts
            sorted_thoughts = sorted(thought_votes.items(),
                                   key=lambda x: x[1],
                                   reverse=True)

            aggregated = {
                "method": "voting",
                "top_thoughts": [
                    {
                        "id": t_id,
                        "content": self.graph["nodes"][t_id]["content"],
                        "votes": votes
                    }
                    for t_id, votes in sorted_thoughts[:5]
                ],
                "paths_considered": len(paths)
            }

        elif aggregation_method == "weighted":
            # Weight by node scores and edge weights
            thought_scores = {}
            for path in paths:
                path_weight = 1.0
                for i, thought_id in enumerate(path):
                    node_score = self.graph["nodes"][thought_id]["score"]

                    # Find edge weight if not first node
                    if i > 0:
                        prev_id = path[i-1]
                        edge = next((e for e in self.graph["edges"]
                                   if e["from"] == prev_id and e["to"] == thought_id),
                                  {"weight": 1.0})
                        path_weight *= edge["weight"]

                    thought_scores[thought_id] = thought_scores.get(thought_id, 0) + (node_score * path_weight)

            sorted_thoughts = sorted(thought_scores.items(),
                                   key=lambda x: x[1],
                                   reverse=True)

            aggregated = {
                "method": "weighted",
                "top_thoughts": [
                    {
                        "id": t_id,
                        "content": self.graph["nodes"][t_id]["content"],
                        "weighted_score": score
                    }
                    for t_id, score in sorted_thoughts[:5]
                ],
                "paths_considered": len(paths)
            }

        else:  # consensus
            # Find thoughts that appear in all paths
            if not paths:
                consensus_thoughts = []
            else:
                consensus_set = set(paths[0])
                for path in paths[1:]:
                    consensus_set &= set(path)

                consensus_thoughts = [
                    {
                        "id": t_id,
                        "content": self.graph["nodes"][t_id]["content"]
                    }
                    for t_id in consensus_set
                ]

            aggregated = {
                "method": "consensus",
                "consensus_thoughts": consensus_thoughts,
                "paths_considered": len(paths),
                "agreement_level": len(consensus_thoughts) / max(len(paths[0]), 1) if paths else 0
            }

        return {
            "success": True,
            "aggregation": aggregated
        }

    def _find_all_paths_to(self, target_id: str) -> List[List[str]]:
        """Find all paths from root to target"""
        paths = []

        def dfs(current, path):
            path.append(current)

            if current == target_id:
                paths.append(path.copy())
            else:
                # Find outgoing edges
                for edge in self.graph["edges"]:
                    if edge["from"] == current and edge["to"] not in path:
                        dfs(edge["to"], path)

            path.pop()

        # Find root nodes (nodes with no incoming edges)
        incoming = {e["to"] for e in self.graph["edges"]}
        roots = [n for n in self.graph["nodes"].keys() if n not in incoming]

        for root in roots:
            dfs(root, [])

        return paths

    def _find_leaf_nodes(self) -> List[str]:
        """Find leaf nodes (no outgoing edges)"""
        outgoing = {e["from"] for e in self.graph["edges"]}
        return [n for n in self.graph["nodes"].keys() if n not in outgoing]

    def _find_path(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Find shortest path between two thoughts"""
        start_id = params.get("start", "")
        end_id = params.get("end", "")

        if start_id not in self.graph["nodes"]:
            return {"success": False, "error": f"Start thought {start_id} not found"}

        if end_id not in self.graph["nodes"]:
            return {"success": False, "error": f"End thought {end_id} not found"}

        # BFS to find shortest path
        queue = [(start_id, [start_id])]
        visited = {start_id}

        while queue:
            current, path = queue.pop(0)

            if current == end_id:
                # Reconstruct path with details
                path_details = []
                for i, thought_id in enumerate(path):
                    node = self.graph["nodes"][thought_id]
                    detail = {
                        "id": thought_id,
                        "content": node["content"],
                        "score": node["score"]
                    }

                    if i > 0:
                        # Find edge
                        prev_id = path[i-1]
                        edge = next((e for e in self.graph["edges"]
                                   if e["from"] == prev_id and e["to"] == thought_id),
                                  None)
                        if edge:
                            detail["relationship_from_prev"] = edge["relationship"]

                    path_details.append(detail)

                return {
                    "success": True,
                    "path": path,
                    "path_details": path_details,
                    "length": len(path)
                }

            # Explore neighbors
            for edge in self.graph["edges"]:
                if edge["from"] == current and edge["to"] not in visited:
                    visited.add(edge["to"])
                    queue.append((edge["to"], path + [edge["to"]]))

        return {
            "success": False,
            "error": f"No path found from {start_id} to {end_id}"
        }

    def _get_neighbors(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get neighboring thoughts"""
        thought_id = params.get("thought_id", "")
        direction = params.get("direction", "both")  # incoming, outgoing, both

        if thought_id not in self.graph["nodes"]:
            return {"success": False, "error": f"Thought {thought_id} not found"}

        neighbors = {
            "incoming": [],
            "outgoing": []
        }

        for edge in self.graph["edges"]:
            if edge["to"] == thought_id and direction in ["incoming", "both"]:
                neighbors["incoming"].append({
                    "id": edge["from"],
                    "content": self.graph["nodes"][edge["from"]]["content"],
                    "relationship": edge["relationship"]
                })

            if edge["from"] == thought_id and direction in ["outgoing", "both"]:
                neighbors["outgoing"].append({
                    "id": edge["to"],
                    "content": self.graph["nodes"][edge["to"]]["content"],
                    "relationship": edge["relationship"]
                })

        return {
            "success": True,
            "thought_id": thought_id,
            "neighbors": neighbors,
            "incoming_count": len(neighbors["incoming"]),
            "outgoing_count": len(neighbors["outgoing"])
        }

    def _get_graph(self) -> Dict[str, Any]:
        """Get the entire thought graph"""
        return {
            "success": True,
            "graph": self.graph,
            "node_count": len(self.graph["nodes"]),
            "edge_count": len(self.graph["edges"])
        }

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.graph = {"nodes": {}, "edges": []}
        return True
