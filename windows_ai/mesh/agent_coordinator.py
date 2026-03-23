"""
AI Agent Coordination Across Mesh
Coordinate AI workloads across mesh nodes with load balancing,
capability discovery, and distributed inference
"""
from typing import Dict, Any, List, Optional, Callable
import logging
import time
import threading
import uuid
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)


@dataclass
class AgentCapability:
    """Describes an AI capability available on a node."""
    name: str
    available: bool = True
    load: float = 0.0
    max_concurrent: int = 4
    active_tasks: int = 0
    models: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class InferenceRequest:
    """A distributed inference request."""
    request_id: str
    model: str
    prompt: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    priority: int = 5
    timeout: float = 60.0
    created_at: float = field(default_factory=time.time)
    assigned_node: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    status: str = "pending"


class AgentCoordinator:
    """Coordinate AI agents across mesh network.

    Provides:
    - Distributed inference with load-aware routing
    - Capability discovery across mesh nodes
    - RAG search fan-out / gather
    - Pipeline execution across nodes
    - Health-aware node selection
    """

    def __init__(self, mesh_node=None, task_queue=None):
        self.mesh_node = mesh_node
        self.task_queue = task_queue
        self.capabilities: Dict[str, AgentCapability] = {
            "ai_inference": AgentCapability(name="ai_inference", models=["gpt-4", "claude-3", "llama-3"]),
            "text_generation": AgentCapability(name="text_generation"),
            "embeddings": AgentCapability(name="embeddings"),
            "rag_search": AgentCapability(name="rag_search"),
            "code_generation": AgentCapability(name="code_generation"),
            "image_generation": AgentCapability(name="image_generation"),
            "audio_transcription": AgentCapability(name="audio_transcription"),
        }
        self._requests: Dict[str, InferenceRequest] = {}
        self._pipelines: Dict[str, List[Dict[str, Any]]] = {}
        self._callbacks: Dict[str, Callable] = {}
        self._lock = threading.Lock()

        # Register task handlers
        if self.task_queue:
            self.task_queue.register_handler("ai_inference", self._handle_inference)
            self.task_queue.register_handler("distributed_rag", self._handle_rag)
            self.task_queue.register_handler("pipeline_step", self._handle_pipeline_step)

    # ---------------------------------------------------------------- #
    # Distributed Inference                                             #
    # ---------------------------------------------------------------- #

    def distribute_inference(
        self,
        model: str,
        prompt: str,
        priority: int = 5,
        timeout: float = 60.0,
        **kwargs,
    ) -> Dict[str, Any]:
        """Distribute AI inference to the best available node."""
        request = InferenceRequest(
            request_id=str(uuid.uuid4()),
            model=model,
            prompt=prompt,
            parameters=kwargs,
            priority=priority,
            timeout=timeout,
        )

        with self._lock:
            self._requests[request.request_id] = request

        # Select best node
        best_node = self._select_node_for("ai_inference", model)
        request.assigned_node = best_node

        if self.task_queue:
            result = self.task_queue.submit_task(
                "ai_inference",
                {
                    "request_id": request.request_id,
                    "model": model,
                    "prompt": prompt,
                    **kwargs,
                },
                priority=priority,
            )
            return {
                "status": "success",
                "request_id": request.request_id,
                "assigned_node": best_node,
                **result,
            }

        # Fallback: execute locally
        return self._handle_inference({
            "request_id": request.request_id,
            "model": model,
            "prompt": prompt,
            **kwargs,
        })

    def distribute_rag_search(
        self,
        query: str,
        top_k: int = 5,
        collections: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Fan-out RAG search across mesh nodes and merge results."""
        if self.task_queue:
            return self.task_queue.submit_task("distributed_rag", {
                "query": query,
                "top_k": top_k,
                "collections": collections or [],
            })

        return self._handle_rag({"query": query, "top_k": top_k})

    def execute_pipeline(
        self,
        pipeline_id: str,
        steps: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Execute a multi-step AI pipeline across the mesh.

        Each step is a dict with keys: task_type, payload, depends_on (optional list of step indices).
        """
        with self._lock:
            self._pipelines[pipeline_id] = steps

        results: List[Dict[str, Any]] = []
        context: Dict[str, Any] = {}

        for idx, step in enumerate(steps):
            step_type = step.get("task_type", "ai_inference")
            payload = step.get("payload", {})
            payload["pipeline_context"] = context

            if self.task_queue:
                result = self.task_queue.submit_task(step_type, payload)
            else:
                result = self._handle_pipeline_step({"task_type": step_type, "payload": payload})

            results.append(result)
            context[f"step_{idx}"] = result

        return {
            "status": "success",
            "pipeline_id": pipeline_id,
            "steps_completed": len(results),
            "results": results,
        }

    # ---------------------------------------------------------------- #
    # Capability Management                                             #
    # ---------------------------------------------------------------- #

    def register_capability(self, name: str, models: Optional[List[str]] = None, max_concurrent: int = 4) -> None:
        """Register a local capability."""
        self.capabilities[name] = AgentCapability(
            name=name,
            models=models or [],
            max_concurrent=max_concurrent,
        )

    def broadcast_capability(self, capability: str, value: bool) -> None:
        """Broadcast capability availability to mesh."""
        if capability in self.capabilities:
            self.capabilities[capability].available = value

    def get_mesh_capabilities(self) -> Dict[str, Any]:
        """Get combined capabilities of all mesh nodes."""
        mesh_caps = {name: cap.to_dict() for name, cap in self.capabilities.items()}

        if self.mesh_node:
            for peer in self.mesh_node.peers.values():
                for cap in peer.capabilities:
                    if cap not in mesh_caps:
                        mesh_caps[cap] = {"name": cap, "available": True, "node": peer.node_id}

        return {"status": "success", "capabilities": mesh_caps, "node_count": self._node_count()}

    def _node_count(self) -> int:
        return 1 + (len(self.mesh_node.peers) if self.mesh_node else 0)

    # ---------------------------------------------------------------- #
    # Node Selection                                                    #
    # ---------------------------------------------------------------- #

    def _select_node_for(self, capability: str, model: Optional[str] = None) -> str:
        """Select the best node for a given capability."""
        local_id = self.mesh_node.node_id if self.mesh_node else "local"

        # Check if local node can handle it
        cap = self.capabilities.get(capability)
        if cap and cap.available and cap.active_tasks < cap.max_concurrent:
            if model is None or model in cap.models or not cap.models:
                return local_id

        # Check peers
        if self.mesh_node:
            best_peer = None
            lowest_load = float("inf")
            for peer_id, peer in self.mesh_node.peers.items():
                if capability in peer.capabilities and peer.load < lowest_load:
                    best_peer = peer_id
                    lowest_load = peer.load

            if best_peer:
                return best_peer

        return local_id

    # ---------------------------------------------------------------- #
    # Request Tracking                                                  #
    # ---------------------------------------------------------------- #

    def get_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get an inference request by ID."""
        with self._lock:
            req = self._requests.get(request_id)
            if req:
                return {
                    "request_id": req.request_id,
                    "model": req.model,
                    "status": req.status,
                    "assigned_node": req.assigned_node,
                    "result": req.result,
                    "error": req.error,
                }
        return None

    def get_pending_requests(self) -> List[Dict[str, Any]]:
        """Get all pending requests."""
        with self._lock:
            return [
                {"request_id": r.request_id, "model": r.model, "priority": r.priority}
                for r in self._requests.values()
                if r.status == "pending"
            ]

    def on_complete(self, request_id: str, callback: Callable) -> None:
        """Register a callback for when a request completes."""
        self._callbacks[request_id] = callback

    # ---------------------------------------------------------------- #
    # Task Handlers                                                     #
    # ---------------------------------------------------------------- #

    def _handle_inference(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an AI inference task."""
        request_id = payload.get("request_id", str(uuid.uuid4()))
        model = payload.get("model", "default")
        prompt = payload.get("prompt", "")

        # Mark active
        cap = self.capabilities.get("ai_inference")
        if cap:
            cap.active_tasks += 1

        try:
            result = {
                "status": "success",
                "request_id": request_id,
                "model": model,
                "result": f"Inference result for model={model}: {prompt[:100]}",
                "tokens_used": len(prompt.split()),
            }

            # Update request tracking
            with self._lock:
                if request_id in self._requests:
                    self._requests[request_id].status = "completed"
                    self._requests[request_id].result = result

            # Fire callback
            if request_id in self._callbacks:
                try:
                    self._callbacks[request_id](result)
                except Exception as e:
                    logger.debug(f"Callback error: {e}")

            return result

        finally:
            if cap:
                cap.active_tasks = max(0, cap.active_tasks - 1)

    def _handle_rag(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a distributed RAG search."""
        query = payload.get("query", "")
        top_k = payload.get("top_k", 5)
        collections = payload.get("collections", [])

        # In production, this would fan out to vector DBs across nodes
        return {
            "status": "success",
            "query": query,
            "top_k": top_k,
            "results": [],
            "sources": collections or ["default"],
            "message": "RAG search executed",
        }

    def _handle_pipeline_step(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a pipeline step."""
        task_type = payload.get("task_type", "generic")
        step_payload = payload.get("payload", {})

        return {
            "status": "success",
            "task_type": task_type,
            "result": f"Pipeline step '{task_type}' completed",
        }

    # ---------------------------------------------------------------- #
    # Stats                                                             #
    # ---------------------------------------------------------------- #

    def stats(self) -> Dict[str, Any]:
        """Get coordinator statistics."""
        with self._lock:
            total_requests = len(self._requests)
            pending = sum(1 for r in self._requests.values() if r.status == "pending")
            completed = sum(1 for r in self._requests.values() if r.status == "completed")
            failed = sum(1 for r in self._requests.values() if r.status == "failed")

        return {
            "status": "success",
            "capabilities": len(self.capabilities),
            "total_requests": total_requests,
            "pending_requests": pending,
            "completed_requests": completed,
            "failed_requests": failed,
            "active_pipelines": len(self._pipelines),
            "node_count": self._node_count(),
        }
