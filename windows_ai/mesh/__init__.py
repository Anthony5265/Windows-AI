"""
Mesh Networking Module
Distributed AI agent coordination across local network
"""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

try:
    from .mesh_node import MeshNode
    from .peer_discovery import PeerDiscovery
    from .task_queue import DistributedTaskQueue
    from .state_sync import StateSync
    from .agent_coordinator import AgentCoordinator
except ImportError as e:
    logger.warning(f"Mesh networking components not fully available: {e}")

__all__ = ['MeshNode', 'PeerDiscovery', 'DistributedTaskQueue', 'StateSync', 'AgentCoordinator']
