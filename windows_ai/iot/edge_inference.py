"""IoT Edge Inference — Run small AI models on IoT and edge devices.

Provides a lightweight inference runtime that can be deployed to edge
devices (Raspberry Pi, Jetson Nano, ESP32, etc.) for local AI processing
without cloud connectivity.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class EdgeDeviceType(str, Enum):
    """Types of edge devices."""
    RASPBERRY_PI = "raspberry_pi"
    JETSON_NANO = "jetson_nano"
    CORAL = "coral"
    ESP32 = "esp32"
    ARDUINO = "arduino"
    GENERIC_ARM = "generic_arm"
    GENERIC_X86 = "generic_x86"


class ModelFormat(str, Enum):
    """Supported model formats for edge deployment."""
    ONNX = "onnx"
    TFLITE = "tflite"
    OPENVINO = "openvino"
    TENSORRT = "tensorrt"
    GGUF = "gguf"
    COREML = "coreml"


class InferenceStatus(str, Enum):
    """Status of an edge inference node."""
    OFFLINE = "offline"
    IDLE = "idle"
    LOADING = "loading"
    READY = "ready"
    PROCESSING = "processing"
    ERROR = "error"


@dataclass
class EdgeModel:
    """A model deployed to an edge device."""
    model_id: str
    name: str
    format: ModelFormat
    size_mb: float
    task: str  # e.g., "classification", "detection", "nlp"
    quantized: bool = False
    max_batch_size: int = 1


@dataclass
class EdgeNode:
    """An edge device running inference."""
    node_id: str
    device_type: EdgeDeviceType
    hostname: str
    status: InferenceStatus = InferenceStatus.OFFLINE
    models: List[EdgeModel] = field(default_factory=list)
    capabilities: Dict[str, Any] = field(default_factory=dict)
    last_heartbeat: float = 0.0
    inference_count: int = 0
    avg_latency_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "device_type": self.device_type.value,
            "hostname": self.hostname,
            "status": self.status.value,
            "model_count": len(self.models),
            "inference_count": self.inference_count,
            "avg_latency_ms": round(self.avg_latency_ms, 2),
        }


@dataclass
class InferenceResult:
    """Result from an edge inference request."""
    node_id: str
    model_id: str
    success: bool
    result: Any = None
    latency_ms: float = 0.0
    error: Optional[str] = None


class EdgeInferenceManager:
    """Manages edge inference across IoT devices.

    Usage::

        manager = EdgeInferenceManager()
        node = manager.register_node("node-1", EdgeDeviceType.RASPBERRY_PI, "raspi.local")
        manager.deploy_model(node.node_id, EdgeModel(...))
        result = await manager.infer(node.node_id, "model-1", {"input": data})
    """

    def __init__(self):
        self._nodes: Dict[str, EdgeNode] = {}
        self._model_registry: Dict[str, EdgeModel] = {}
        self._inference_history: List[InferenceResult] = []
        logger.info("EdgeInferenceManager initialized")

    # ------------------------------------------------------------------
    # Node Management
    # ------------------------------------------------------------------

    def register_node(
        self,
        node_id: str,
        device_type: EdgeDeviceType,
        hostname: str,
        capabilities: Optional[Dict[str, Any]] = None,
    ) -> EdgeNode:
        """Register a new edge device."""
        node = EdgeNode(
            node_id=node_id,
            device_type=device_type,
            hostname=hostname,
            status=InferenceStatus.IDLE,
            capabilities=capabilities or {},
            last_heartbeat=time.time(),
        )
        self._nodes[node_id] = node
        logger.info("Registered edge node %s (%s) at %s", node_id, device_type.value, hostname)
        return node

    def unregister_node(self, node_id: str) -> bool:
        """Remove an edge node."""
        if node_id in self._nodes:
            del self._nodes[node_id]
            return True
        return False

    def get_node(self, node_id: str) -> Optional[EdgeNode]:
        return self._nodes.get(node_id)

    def list_nodes(self) -> List[Dict[str, Any]]:
        return [n.to_dict() for n in self._nodes.values()]

    def heartbeat(self, node_id: str) -> bool:
        """Update heartbeat timestamp for a node."""
        node = self._nodes.get(node_id)
        if not node:
            return False
        node.last_heartbeat = time.time()
        if node.status == InferenceStatus.OFFLINE:
            node.status = InferenceStatus.IDLE
        return True

    # ------------------------------------------------------------------
    # Model Deployment
    # ------------------------------------------------------------------

    def register_model(self, model: EdgeModel) -> None:
        """Register a model in the central registry."""
        self._model_registry[model.model_id] = model
        logger.info("Registered edge model %s (%s, %.1fMB)",
                     model.model_id, model.format.value, model.size_mb)

    def deploy_model(self, node_id: str, model: EdgeModel) -> Dict[str, Any]:
        """Deploy a model to an edge node."""
        node = self._nodes.get(node_id)
        if not node:
            return {"status": "error", "message": f"Node {node_id} not found"}

        # Check if model is compatible with device
        compatibility = self._check_compatibility(node, model)
        if not compatibility["compatible"]:
            return {"status": "error", "message": compatibility["reason"]}

        node.models.append(model)
        node.status = InferenceStatus.READY
        self._model_registry[model.model_id] = model
        logger.info("Deployed model %s to node %s", model.model_id, node_id)
        return {"status": "success", "node_id": node_id, "model_id": model.model_id}

    def undeploy_model(self, node_id: str, model_id: str) -> Dict[str, Any]:
        """Remove a model from an edge node."""
        node = self._nodes.get(node_id)
        if not node:
            return {"status": "error", "message": f"Node {node_id} not found"}

        node.models = [m for m in node.models if m.model_id != model_id]
        if not node.models:
            node.status = InferenceStatus.IDLE
        return {"status": "success"}

    def _check_compatibility(self, node: EdgeNode, model: EdgeModel) -> Dict[str, Any]:
        """Check if a model is compatible with a device."""
        # ESP32 can only run tiny TFLite models
        if node.device_type == EdgeDeviceType.ESP32:
            if model.format != ModelFormat.TFLITE:
                return {"compatible": False, "reason": "ESP32 only supports TFLite models"}
            if model.size_mb > 4:
                return {"compatible": False, "reason": "Model too large for ESP32 (max 4MB)"}

        # Coral requires TFLite or OpenVINO
        if node.device_type == EdgeDeviceType.CORAL:
            if model.format not in (ModelFormat.TFLITE, ModelFormat.OPENVINO):
                return {"compatible": False, "reason": "Coral only supports TFLite/OpenVINO"}

        # Jetson supports TensorRT and ONNX
        if node.device_type == EdgeDeviceType.JETSON_NANO:
            if model.format not in (ModelFormat.TENSORRT, ModelFormat.ONNX, ModelFormat.TFLITE):
                return {"compatible": False, "reason": "Jetson supports TensorRT/ONNX/TFLite only"}

        return {"compatible": True}

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    async def infer(
        self,
        node_id: str,
        model_id: str,
        input_data: Dict[str, Any],
        timeout: float = 10.0,
    ) -> InferenceResult:
        """Run inference on an edge node."""
        node = self._nodes.get(node_id)
        if not node:
            return InferenceResult(
                node_id=node_id, model_id=model_id, success=False,
                error=f"Node {node_id} not found"
            )

        if node.status == InferenceStatus.OFFLINE:
            return InferenceResult(
                node_id=node_id, model_id=model_id, success=False,
                error="Node is offline"
            )

        model_ids = [m.model_id for m in node.models]
        if model_id not in model_ids:
            return InferenceResult(
                node_id=node_id, model_id=model_id, success=False,
                error=f"Model {model_id} not deployed on node {node_id}"
            )

        start = time.perf_counter()
        node.status = InferenceStatus.PROCESSING

        try:
            # Simulated inference — in production, sends request to edge device
            result = {"prediction": "simulated", "confidence": 0.95, "input_keys": list(input_data.keys())}
            latency = (time.perf_counter() - start) * 1000

            # Update stats
            node.inference_count += 1
            node.avg_latency_ms = (
                (node.avg_latency_ms * (node.inference_count - 1) + latency) / node.inference_count
            )
            node.status = InferenceStatus.READY

            inference_result = InferenceResult(
                node_id=node_id, model_id=model_id, success=True,
                result=result, latency_ms=round(latency, 2)
            )
            self._inference_history.append(inference_result)
            return inference_result

        except Exception as e:
            node.status = InferenceStatus.ERROR
            return InferenceResult(
                node_id=node_id, model_id=model_id, success=False,
                error=str(e), latency_ms=round((time.perf_counter() - start) * 1000, 2)
            )

    async def infer_best_node(
        self,
        model_id: str,
        input_data: Dict[str, Any],
    ) -> InferenceResult:
        """Find the best available node and run inference."""
        best_node = None
        for node in self._nodes.values():
            if node.status in (InferenceStatus.READY, InferenceStatus.IDLE):
                if any(m.model_id == model_id for m in node.models):
                    if best_node is None or node.avg_latency_ms < best_node.avg_latency_ms:
                        best_node = node

        if not best_node:
            return InferenceResult(
                node_id="", model_id=model_id, success=False,
                error="No available node with this model"
            )

        return await self.infer(best_node.node_id, model_id, input_data)

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Get edge inference statistics."""
        nodes = list(self._nodes.values())
        return {
            "total_nodes": len(nodes),
            "online_nodes": sum(1 for n in nodes if n.status != InferenceStatus.OFFLINE),
            "total_models_deployed": sum(len(n.models) for n in nodes),
            "total_inferences": sum(n.inference_count for n in nodes),
            "registered_models": len(self._model_registry),
        }

    def get_available_formats(self) -> List[str]:
        """List supported model formats."""
        return [f.value for f in ModelFormat]

    def get_supported_devices(self) -> List[str]:
        """List supported device types."""
        return [d.value for d in EdgeDeviceType]
