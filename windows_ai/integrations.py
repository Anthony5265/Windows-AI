"""
Windows AI - Integration Layer
Connects all subsystems (IoT, Mesh, Model Discovery, Cloud Sync, etc.) to the main backend
"""

import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .search.search_orchestrator import SearchOrchestrator

# Import subsystems
try:
    from iot.mqtt import MQTTAdapter
    from iot.home_assistant import HomeAssistantAdapter
    from iot.automation import IoTAutomation
    IOT_AVAILABLE = True
except ImportError:
    IOT_AVAILABLE = False
    logging.warning("IoT modules not available")

try:
    from mesh.hub import MeshHub
    from mesh.node import MeshNode
    MESH_AVAILABLE = True
except ImportError:
    MESH_AVAILABLE = False
    logging.warning("Mesh networking modules not available")

try:
    from model_discovery.discovery import ModelDiscovery
    MODEL_DISCOVERY_AVAILABLE = True
except ImportError:
    MODEL_DISCOVERY_AVAILABLE = False
    logging.warning("Model discovery not available")

try:
    from cloud_sync.provider import CloudSyncProvider
    CLOUD_SYNC_AVAILABLE = True
except ImportError:
    CLOUD_SYNC_AVAILABLE = False
    logging.warning("Cloud sync not available")

SEARCH_AVAILABLE = True

logger = logging.getLogger(__name__)

# =====================================================================
# IoT Integration
# =====================================================================

router = APIRouter(prefix="/integrations", tags=["integrations"])

# Global instances
iot_automation: Optional[Any] = None
mesh_hub: Optional[Any] = None
model_discovery: Optional[Any] = None
cloud_sync: Optional[Any] = None
search_orchestrator: Optional[SearchOrchestrator] = None

async def initialize_integrations():
    """Initialize all integration subsystems"""
    global iot_automation, mesh_hub, model_discovery, cloud_sync, search_orchestrator, SEARCH_AVAILABLE

    logger.info("Initializing Windows AI integrations...")

    # Initialize IoT
    if IOT_AVAILABLE:
        try:
            logger.info("Initializing IoT subsystem...")
            iot_automation = IoTAutomation()
            logger.info("✓ IoT subsystem initialized")
        except Exception as e:
            logger.error(f"Failed to initialize IoT: {e}")

    # Initialize Mesh Network
    if MESH_AVAILABLE:
        try:
            logger.info("Initializing mesh networking...")
            mesh_hub = MeshHub()
            logger.info("✓ Mesh networking initialized")
        except Exception as e:
            logger.error(f"Failed to initialize mesh: {e}")

    # Initialize Model Discovery
    if MODEL_DISCOVERY_AVAILABLE:
        try:
            logger.info("Initializing model discovery...")
            model_discovery = ModelDiscovery()
            logger.info("✓ Model discovery initialized")
        except Exception as e:
            logger.error(f"Failed to initialize model discovery: {e}")

    # Initialize Cloud Sync
    if CLOUD_SYNC_AVAILABLE:
        try:
            logger.info("Initializing cloud sync...")
            cloud_sync = CloudSyncProvider()
            logger.info("✓ Cloud sync initialized")
        except Exception as e:
            logger.error(f"Failed to initialize cloud sync: {e}")

    # Initialize Search
    try:
        logger.info("Initializing search orchestrator...")
        search_orchestrator = SearchOrchestrator()
        SEARCH_AVAILABLE = await search_orchestrator.setup()
        if SEARCH_AVAILABLE:
            logger.info("✓ Search orchestrator initialized")
        else:
            logger.error("Search orchestrator failed to initialize")
    except Exception as e:
        SEARCH_AVAILABLE = False
        logger.error(f"Failed to initialize search orchestrator: {e}")

    logger.info("All integrations initialized")

# =====================================================================
# IoT API Endpoints
# =====================================================================

class IoTDeviceModel(BaseModel):
    id: str
    name: str
    type: str
    protocol: str
    status: str = "unknown"

@router.get("/iot/devices")
async def list_iot_devices():
    """List all discovered IoT devices"""
    if not IOT_AVAILABLE or not iot_automation:
        raise HTTPException(status_code=503, detail="IoT not available")

    try:
        devices = iot_automation.get_devices()
        return {"devices": devices, "count": len(devices)}
    except Exception as e:
        logger.error(f"Error listing IoT devices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/iot/devices/discover")
async def discover_iot_devices():
    """Trigger IoT device discovery"""
    if not IOT_AVAILABLE or not iot_automation:
        raise HTTPException(status_code=503, detail="IoT not available")

    try:
        devices = iot_automation.discover_devices()
        return {"discovered": len(devices), "devices": devices}
    except Exception as e:
        logger.error(f"Error discovering devices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/iot/devices/{device_id}/control")
async def control_iot_device(device_id: str, command: Dict[str, Any]):
    """Send command to IoT device"""
    if not IOT_AVAILABLE or not iot_automation:
        raise HTTPException(status_code=503, detail="IoT not available")

    try:
        result = iot_automation.control_device(device_id, command)
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Error controlling device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =====================================================================
# Mesh Networking API Endpoints
# =====================================================================

@router.get("/mesh/status")
async def get_mesh_status():
    """Get mesh network status"""
    if not MESH_AVAILABLE or not mesh_hub:
        raise HTTPException(status_code=503, detail="Mesh networking not available")

    try:
        status = {
            "running": mesh_hub._running,
            "host": mesh_hub.host,
            "port": mesh_hub.port,
            "discovery_port": mesh_hub.discovery_port,
            "connected_nodes": len(mesh_hub._nodes),
            "heartbeat_timeout": mesh_hub.heartbeat_timeout
        }
        return status
    except Exception as e:
        logger.error(f"Error getting mesh status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mesh/nodes")
async def list_mesh_nodes():
    """List all mesh nodes"""
    if not MESH_AVAILABLE or not mesh_hub:
        raise HTTPException(status_code=503, detail="Mesh networking not available")

    try:
        with mesh_hub._lock:
            node_list = [
                {
                    "address": str(node.getpeername() if node else "unknown"),
                    "last_heartbeat": mesh_hub._last_heartbeat.get(node, 0)
                }
                for node in mesh_hub._nodes
            ]
        return {"nodes": node_list, "count": len(node_list)}
    except Exception as e:
        logger.error(f"Error listing mesh nodes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class MeshTaskRequest(BaseModel):
    task: str
    metadata: Optional[Dict[str, Any]] = None

@router.post("/mesh/task/distribute")
async def distribute_mesh_task(request: MeshTaskRequest):
    """Distribute AI task across mesh network"""
    if not MESH_AVAILABLE or not mesh_hub:
        raise HTTPException(status_code=503, detail="Mesh networking not available")

    try:
        mesh_hub.distribute_task(request.task)
        return {
            "success": True,
            "task": request.task,
            "distributed_to": len(mesh_hub._nodes),
            "metadata": request.metadata
        }
    except Exception as e:
        logger.error(f"Error distributing task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =====================================================================
# Model Discovery API Endpoints
# =====================================================================

@router.get("/models/discover")
async def discover_models():
    """Discover available AI models (local + cloud)"""
    if not MODEL_DISCOVERY_AVAILABLE or not model_discovery:
        raise HTTPException(status_code=503, detail="Model discovery not available")

    try:
        models = model_discovery.discover_all()
        return {"models": models, "count": len(models)}
    except Exception as e:
        logger.error(f"Error discovering models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/models/download")
async def download_model(model_id: str, model_source: str = "huggingface"):
    """Download a model from HuggingFace or other source"""
    if not MODEL_DISCOVERY_AVAILABLE or not model_discovery:
        raise HTTPException(status_code=503, detail="Model discovery not available")

    try:
        result = model_discovery.download_model(model_id, model_source)
        return {"success": True, "model": result}
    except Exception as e:
        logger.error(f"Error downloading model {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =====================================================================
# Cloud Sync API Endpoints
# =====================================================================

@router.post("/sync/upload")
async def upload_to_cloud(data: Dict[str, Any]):
    """Upload data to cloud"""
    if not CLOUD_SYNC_AVAILABLE or not cloud_sync:
        raise HTTPException(status_code=503, detail="Cloud sync not available")

    try:
        result = cloud_sync.upload(data)
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Error uploading to cloud: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sync/download")
async def download_from_cloud():
    """Download data from cloud"""
    if not CLOUD_SYNC_AVAILABLE or not cloud_sync:
        raise HTTPException(status_code=503, detail="Cloud sync not available")

    try:
        data = cloud_sync.download()
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"Error downloading from cloud: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =====================================================================
# Search API Endpoints
# =====================================================================

class SearchRequest(BaseModel):
    query: str
    filters: Optional[Dict[str, Any]] = None
    limit: int = 10
    offset: int = 0
    backends: Optional[List[str]] = None
    timeout: int = 30
    expected_results: Optional[List[str]] = None
    persist_cache: bool = False

@router.post("/search")
async def search(request: SearchRequest):
    """Universal search across files, apps, web"""
    if not SEARCH_AVAILABLE or not search_orchestrator or not search_orchestrator.initialized:
        raise HTTPException(status_code=503, detail="Search orchestrator not available")

    try:
        results = await search_orchestrator.search(
            request.query,
            filters=request.filters,
            limit=request.limit,
            offset=request.offset,
            backends=request.backends,
            timeout=request.timeout,
            expected_results=request.expected_results,
            persist_cache=request.persist_cache,
        )
        return {"results": results, "count": len(results)}
    except Exception as e:
        logger.error(f"Error searching: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =====================================================================
# Context Menu Integration
# =====================================================================

class ContextMenuRequest(BaseModel):
    action: str
    file_info: Optional[Dict[str, Any]] = None
    file_path: Optional[str] = None
    content: Optional[str] = None
    path: Optional[str] = None
    is_folder: Optional[bool] = False

@router.post("/context_menu")
async def handle_context_menu(request: ContextMenuRequest):
    """Handle context menu actions from Windows Explorer"""
    try:
        action = request.action
        logger.info(f"Context menu action: {action}")

        if action == "analyze_file":
            # File analysis request
            file_info = request.file_info or {}
            content = request.content

            response = {
                "message": f"File analysis queued: {file_info.get('name', 'Unknown')}",
                "file_info": file_info,
                "has_content": content is not None,
                "action": "open_gui_with_context"
            }

            # Notify the GUI via a lightweight IPC event if the GUI server is running
            try:
                import urllib.request as _ur, json as _j
                _payload = _j.dumps({"event": "file_analysis", "data": response}).encode()
                _req = _ur.Request(
                    "http://127.0.0.1:8010/api/v1/events",
                    data=_payload,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                _ur.urlopen(_req, timeout=1)
            except Exception:
                pass  # GUI not running — analysis result returned inline to caller
            return response

        elif action == "summarize_file":
            # File summarization request
            file_path = request.file_path
            content = request.content

            if not content:
                raise HTTPException(status_code=400, detail="No content to summarize")

            response = {
                "message": f"Summarization queued for: {file_path}",
                "action": "open_gui_with_context",
                "context_type": "summarize"
            }

            return response

        elif action == "ask_about":
            # Open GUI with file/folder context
            path = request.path
            is_folder = request.is_folder

            response = {
                "message": f"Opening chat with context: {path}",
                "path": path,
                "is_folder": is_folder,
                "action": "open_gui_with_context"
            }

            return response

        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {action}")

    except Exception as e:
        logger.error(f"Context menu error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =====================================================================
# Status Endpoint
# =====================================================================

@router.get("/status")
async def integration_status():
    """Get status of all integrations"""
    return {
        "iot": {
            "available": IOT_AVAILABLE,
            "initialized": iot_automation is not None,
            "status": "active" if (IOT_AVAILABLE and iot_automation) else "unavailable"
        },
        "mesh": {
            "available": MESH_AVAILABLE,
            "initialized": mesh_hub is not None,
            "status": "active" if (MESH_AVAILABLE and mesh_hub) else "unavailable"
        },
        "model_discovery": {
            "available": MODEL_DISCOVERY_AVAILABLE,
            "initialized": model_discovery is not None,
            "status": "active" if (MODEL_DISCOVERY_AVAILABLE and model_discovery) else "unavailable"
        },
        "cloud_sync": {
            "available": CLOUD_SYNC_AVAILABLE,
            "initialized": cloud_sync is not None,
            "status": "active" if (CLOUD_SYNC_AVAILABLE and cloud_sync) else "unavailable"
        },
        "search": {
            "available": SEARCH_AVAILABLE,
            "initialized": search_orchestrator is not None and search_orchestrator.initialized,
            "status": "active" if (SEARCH_AVAILABLE and search_orchestrator and search_orchestrator.initialized) else "unavailable"
        }
    }
