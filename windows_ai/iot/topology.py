"""
Network Topology Mapping
Maps and visualizes IoT device network topology
"""
from typing import Dict, Any, List, Optional, Set
import logging
import time
import json
from dataclasses import dataclass, asdict, field

logger = logging.getLogger(__name__)


@dataclass
class NetworkNode:
    """Network node representation"""
    node_id: str
    node_type: str  # device, gateway, hub, router
    name: str
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    parent_id: Optional[str] = None
    children: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_seen: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class NetworkLink:
    """Network link between nodes"""
    source_id: str
    target_id: str
    link_type: str  # wifi, ethernet, zigbee, zwave, ble
    strength: Optional[int] = None  # Signal strength
    latency: Optional[float] = None  # ms
    bandwidth: Optional[float] = None  # Mbps
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class NetworkTopology:
    """
    Network topology mapper
    Builds and maintains network topology graph
    """

    def __init__(self):
        self.nodes = {}
        self.links = []
        self.gateway_node = None

    def add_node(self, node_id: str, node_type: str, name: str,
                 **kwargs) -> Dict[str, Any]:
        """
        Add node to topology

        Args:
            node_id: Unique node identifier
            node_type: Type (device, gateway, hub, router)
            name: Node name
            ip_address: IP address
            mac_address: MAC address
            parent_id: Parent node ID
            metadata: Additional metadata

        Returns:
            Dict with status
        """
        try:
            node = NetworkNode(
                node_id=node_id,
                node_type=node_type,
                name=name,
                ip_address=kwargs.get('ip_address'),
                mac_address=kwargs.get('mac_address'),
                parent_id=kwargs.get('parent_id'),
                metadata=kwargs.get('metadata', {})
            )

            self.nodes[node_id] = node

            # Set as gateway if specified
            if node_type == 'gateway' and not self.gateway_node:
                self.gateway_node = node_id

            logger.info(f"Added node to topology: {name} ({node_type})")

            return {
                "status": "success",
                "message": "Node added",
                "node": node.to_dict()
            }

        except Exception as e:
            logger.error(f"Error adding node: {e}")
            return {"status": "error", "message": str(e)}

    def remove_node(self, node_id: str) -> Dict[str, Any]:
        """Remove node from topology"""
        if node_id not in self.nodes:
            return {
                "status": "error",
                "message": f"Node not found: {node_id}"
            }

        # Remove links involving this node
        self.links = [
            link for link in self.links
            if link.source_id != node_id and link.target_id != node_id
        ]

        # Remove node
        del self.nodes[node_id]

        return {
            "status": "success",
            "message": "Node removed",
            "node_id": node_id
        }

    def add_link(self, source_id: str, target_id: str, link_type: str,
                 **kwargs) -> Dict[str, Any]:
        """
        Add link between nodes

        Args:
            source_id: Source node ID
            target_id: Target node ID
            link_type: Link type (wifi, ethernet, zigbee, zwave, ble)
            strength: Signal strength
            latency: Link latency in ms
            bandwidth: Bandwidth in Mbps
            metadata: Additional metadata

        Returns:
            Dict with status
        """
        try:
            # Verify nodes exist
            if source_id not in self.nodes:
                return {
                    "status": "error",
                    "message": f"Source node not found: {source_id}"
                }
            if target_id not in self.nodes:
                return {
                    "status": "error",
                    "message": f"Target node not found: {target_id}"
                }

            link = NetworkLink(
                source_id=source_id,
                target_id=target_id,
                link_type=link_type,
                strength=kwargs.get('strength'),
                latency=kwargs.get('latency'),
                bandwidth=kwargs.get('bandwidth'),
                metadata=kwargs.get('metadata', {})
            )

            self.links.append(link)

            # Update parent-child relationships
            target_node = self.nodes[target_id]
            if not target_node.parent_id:
                target_node.parent_id = source_id
                self.nodes[source_id].children.append(target_id)

            logger.info(f"Added link: {source_id} -> {target_id} ({link_type})")

            return {
                "status": "success",
                "message": "Link added",
                "link": link.to_dict()
            }

        except Exception as e:
            logger.error(f"Error adding link: {e}")
            return {"status": "error", "message": str(e)}

    def get_topology(self) -> Dict[str, Any]:
        """Get complete topology"""
        return {
            "status": "success",
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "links": [link.to_dict() for link in self.links],
            "node_count": len(self.nodes),
            "link_count": len(self.links),
            "gateway": self.gateway_node
        }

    def get_node_hierarchy(self, root_id: str = None) -> Dict[str, Any]:
        """
        Get hierarchical tree structure

        Args:
            root_id: Root node ID (uses gateway if not specified)

        Returns:
            Dict with hierarchical tree
        """
        if root_id is None:
            root_id = self.gateway_node

        if not root_id or root_id not in self.nodes:
            return {
                "status": "error",
                "message": "Root node not found"
            }

        def build_tree(node_id: str) -> Dict[str, Any]:
            node = self.nodes[node_id]
            tree = {
                "id": node_id,
                "name": node.name,
                "type": node.node_type,
                "children": []
            }

            for child_id in node.children:
                if child_id in self.nodes:
                    tree["children"].append(build_tree(child_id))

            return tree

        return {
            "status": "success",
            "tree": build_tree(root_id)
        }

    def get_node_path(self, node_id: str) -> Dict[str, Any]:
        """
        Get path from gateway to node

        Args:
            node_id: Target node ID

        Returns:
            Dict with path
        """
        if node_id not in self.nodes:
            return {
                "status": "error",
                "message": f"Node not found: {node_id}"
            }

        path = []
        current_id = node_id

        # Traverse up to root
        visited = set()
        while current_id:
            if current_id in visited:
                return {
                    "status": "error",
                    "message": "Circular reference detected"
                }

            visited.add(current_id)
            path.insert(0, current_id)

            node = self.nodes[current_id]
            current_id = node.parent_id

        return {
            "status": "success",
            "path": path,
            "depth": len(path) - 1
        }

    def get_neighbors(self, node_id: str) -> Dict[str, Any]:
        """
        Get neighboring nodes

        Args:
            node_id: Node ID

        Returns:
            Dict with neighbors
        """
        if node_id not in self.nodes:
            return {
                "status": "error",
                "message": f"Node not found: {node_id}"
            }

        neighbors = set()

        # Find connected nodes
        for link in self.links:
            if link.source_id == node_id:
                neighbors.add(link.target_id)
            elif link.target_id == node_id:
                neighbors.add(link.source_id)

        neighbor_nodes = [
            self.nodes[nid].to_dict()
            for nid in neighbors
            if nid in self.nodes
        ]

        return {
            "status": "success",
            "neighbors": neighbor_nodes,
            "count": len(neighbor_nodes)
        }

    def detect_isolated_nodes(self) -> Dict[str, Any]:
        """Find nodes with no connections"""
        isolated = []

        for node_id, node in self.nodes.items():
            has_links = any(
                link.source_id == node_id or link.target_id == node_id
                for link in self.links
            )

            if not has_links:
                isolated.append(node.to_dict())

        return {
            "status": "success",
            "isolated_nodes": isolated,
            "count": len(isolated)
        }

    def calculate_network_statistics(self) -> Dict[str, Any]:
        """Calculate network statistics"""
        stats = {
            "total_nodes": len(self.nodes),
            "total_links": len(self.links),
            "nodes_by_type": {},
            "links_by_type": {},
            "average_connections": 0,
            "max_depth": 0,
            "isolated_nodes": 0
        }

        # Count by type
        for node in self.nodes.values():
            node_type = node.node_type
            stats["nodes_by_type"][node_type] = stats["nodes_by_type"].get(node_type, 0) + 1

        for link in self.links:
            link_type = link.link_type
            stats["links_by_type"][link_type] = stats["links_by_type"].get(link_type, 0) + 1

        # Calculate average connections
        if len(self.nodes) > 0:
            stats["average_connections"] = (len(self.links) * 2) / len(self.nodes)

        # Find max depth
        for node_id in self.nodes:
            path_result = self.get_node_path(node_id)
            if path_result["status"] == "success":
                depth = path_result["depth"]
                stats["max_depth"] = max(stats["max_depth"], depth)

        # Count isolated nodes
        isolated_result = self.detect_isolated_nodes()
        stats["isolated_nodes"] = isolated_result["count"]

        return {
            "status": "success",
            "statistics": stats
        }

    def export_topology(self, file_path: str = None,
                       format: str = "json") -> Dict[str, Any]:
        """
        Export topology to file

        Args:
            file_path: Output file path
            format: Export format (json, dot)

        Returns:
            Dict with status
        """
        try:
            if format == "json":
                data = self.get_topology()

                if file_path:
                    with open(file_path, 'w') as f:
                        json.dump(data, f, indent=2)

                    return {
                        "status": "success",
                        "message": "Topology exported",
                        "file_path": file_path,
                        "format": format
                    }
                else:
                    return data

            elif format == "dot":
                # GraphViz DOT format
                dot = self._export_dot()

                if file_path:
                    with open(file_path, 'w') as f:
                        f.write(dot)

                    return {
                        "status": "success",
                        "message": "Topology exported",
                        "file_path": file_path,
                        "format": "dot"
                    }
                else:
                    return {
                        "status": "success",
                        "data": dot
                    }

            else:
                return {
                    "status": "error",
                    "message": f"Unsupported format: {format}"
                }

        except Exception as e:
            logger.error(f"Export error: {e}")
            return {"status": "error", "message": str(e)}

    def _export_dot(self) -> str:
        """Export topology as GraphViz DOT"""
        lines = ["digraph NetworkTopology {"]
        lines.append("  rankdir=LR;")
        lines.append("  node [shape=box, style=rounded];")

        # Add nodes
        for node_id, node in self.nodes.items():
            label = f"{node.name}\\n({node.node_type})"
            lines.append(f'  "{node_id}" [label="{label}"];')

        # Add links
        for link in self.links:
            label = link.link_type
            lines.append(f'  "{link.source_id}" -> "{link.target_id}" [label="{label}"];')

        lines.append("}")
        return "\n".join(lines)

    def import_topology(self, file_path: str) -> Dict[str, Any]:
        """Import topology from JSON file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            # Clear existing topology
            self.nodes.clear()
            self.links = []

            # Import nodes
            for node_data in data.get("nodes", []):
                node = NetworkNode(**node_data)
                self.nodes[node.node_id] = node

            # Import links
            for link_data in data.get("links", []):
                link = NetworkLink(**link_data)
                self.links.append(link)

            return {
                "status": "success",
                "message": "Topology imported",
                "nodes": len(self.nodes),
                "links": len(self.links)
            }

        except Exception as e:
            logger.error(f"Import error: {e}")
            return {"status": "error", "message": str(e)}
