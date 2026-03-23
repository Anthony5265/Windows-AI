"""
Mesh Network API Routes
Manage distributed mesh nodes, peers, state sync, and task distribution
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/mesh", tags=["Mesh Network"])

# --- Singleton instances (created lazily) ---
_mesh_node = None
_state_sync = None
_task_queue = None
_coordinator = None


def _get_node():
    global _mesh_node
    if _mesh_node is None:
        from windows_ai.mesh.mesh_node import MeshNode
        _mesh_node = MeshNode()
    return _mesh_node


def _get_state_sync():
    global _state_sync
    if _state_sync is None:
        from windows_ai.mesh.state_sync import StateSync
        _state_sync = StateSync(_get_node())
    return _state_sync


def _get_task_queue():
    global _task_queue
    if _task_queue is None:
        from windows_ai.mesh.task_queue import DistributedTaskQueue
        _task_queue = DistributedTaskQueue(_get_node())
    return _task_queue


def _get_coordinator():
    global _coordinator
    if _coordinator is None:
        from windows_ai.mesh.agent_coordinator import AgentCoordinator
        _coordinator = AgentCoordinator(_get_node(), _get_task_queue())
    return _coordinator


# ---------------------------------------------------------------------- #
# Node Management                                                         #
# ---------------------------------------------------------------------- #

@router.get("/status")
async def get_mesh_status():
    """Get current mesh node status."""
    return _get_node().get_status()


class AddPeerRequest(BaseModel):
    node_id: str
    address: str
    port: int
    capabilities: List[str] = []


@router.post("/peers")
async def add_peer(req: AddPeerRequest):
    """Add a peer to the mesh."""
    return _get_node().add_peer(req.node_id, req.address, req.port, req.capabilities)


@router.get("/peers")
async def get_peers(max_age: int = Query(default=30, ge=1)):
    """List known peers."""
    node = _get_node()
    peers = [
        {
            "node_id": p.node_id,
            "address": p.address,
            "port": p.port,
            "role": p.role,
            "capabilities": p.capabilities,
            "load": p.load,
        }
        for p in node.peers.values()
    ]
    return {"status": "success", "peers": peers, "count": len(peers)}


# ---------------------------------------------------------------------- #
# State Synchronization                                                    #
# ---------------------------------------------------------------------- #

class StateSetRequest(BaseModel):
    key: str
    value: Any


@router.post("/state")
async def set_state(req: StateSetRequest):
    """Set a distributed state value."""
    return _get_state_sync().set(req.key, req.value)


@router.get("/state/{key}")
async def get_state(key: str):
    """Get a distributed state value."""
    result = _get_state_sync().get(key)
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result.get("message", "Key not found"))
    return result


@router.get("/state")
async def get_all_state():
    """Get all distributed state."""
    return _get_state_sync().get_all()


@router.delete("/state/{key}")
async def delete_state(key: str):
    """Delete a distributed state key."""
    result = _get_state_sync().delete(key)
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result.get("message", "Key not found"))
    return result


@router.get("/state/status")
async def get_sync_status():
    """Get state sync status."""
    return _get_state_sync().get_status()


# ---------------------------------------------------------------------- #
# Task Queue                                                               #
# ---------------------------------------------------------------------- #

class TaskSubmitRequest(BaseModel):
    task_type: str
    payload: Dict[str, Any] = {}
    priority: int = 0


@router.post("/tasks")
async def submit_task(req: TaskSubmitRequest):
    """Submit a distributed task."""
    return _get_task_queue().submit_task(req.task_type, req.payload, req.priority)


@router.get("/tasks/{task_id}")
async def get_task(task_id: str):
    """Get task status."""
    result = _get_task_queue().get_task_status(task_id)
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result.get("message", "Task not found"))
    return result


@router.get("/tasks/queue/status")
async def get_queue_status():
    """Get task queue status."""
    return _get_task_queue().get_queue_status()


# ---------------------------------------------------------------------- #
# Agent Coordination                                                       #
# ---------------------------------------------------------------------- #

class InferenceRequest(BaseModel):
    model: str = "default"
    prompt: str
    priority: int = 5
    timeout: float = 60.0


@router.post("/inference")
async def distribute_inference(req: InferenceRequest):
    """Distribute AI inference to best available node."""
    return _get_coordinator().distribute_inference(
        model=req.model,
        prompt=req.prompt,
        priority=req.priority,
        timeout=req.timeout,
    )


class RAGSearchRequest(BaseModel):
    query: str
    top_k: int = 5
    collections: List[str] = []


@router.post("/rag/search")
async def distribute_rag_search(req: RAGSearchRequest):
    """Fan-out RAG search across mesh nodes."""
    return _get_coordinator().distribute_rag_search(req.query, req.top_k, req.collections)


class PipelineRequest(BaseModel):
    pipeline_id: str
    steps: List[Dict[str, Any]]


@router.post("/pipeline")
async def execute_pipeline(req: PipelineRequest):
    """Execute a multi-step pipeline across the mesh."""
    return _get_coordinator().execute_pipeline(req.pipeline_id, req.steps)


@router.get("/capabilities")
async def get_capabilities():
    """Get mesh capabilities across all nodes."""
    return _get_coordinator().get_mesh_capabilities()


@router.get("/coordinator/stats")
async def get_coordinator_stats():
    """Get agent coordinator statistics."""
    return _get_coordinator().stats()
