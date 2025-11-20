"""API route definitions"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
import time
import asyncio
from datetime import datetime

from windows_ai.api.models import (
    PluginExecuteRequest, PluginExecuteResponse, PluginConnectRequest,
    PluginListResponse, PluginInfo, HealthResponse, ErrorResponse,
    AgentCreateRequest, AgentExecuteRequest, AgentInfo, AgentExecuteResponse,
    PluginStatus, PluginType
)
from windows_ai.api.auth import get_current_user
from windows_ai.core.plugin_manager import PluginManager

# Create routers
router = APIRouter()
plugins_router = APIRouter(prefix="/plugins", tags=["plugins"])
agents_router = APIRouter(prefix="/agents", tags=["agents"])
system_router = APIRouter(prefix="/system", tags=["system"])

# Initialize plugin manager (will be set by server)
plugin_manager: Optional[PluginManager] = None

def set_plugin_manager(manager: PluginManager):
    """Set the plugin manager instance"""
    global plugin_manager
    plugin_manager = manager

# Plugin endpoints
@plugins_router.get("/", response_model=PluginListResponse)
async def list_plugins(
    category: Optional[str] = Query(None, description="Filter by category"),
    plugin_type: Optional[PluginType] = Query(None, description="Filter by plugin type"),
    search: Optional[str] = Query(None, description="Search in name/description"),
    user=Depends(get_current_user)
):
    """List all available plugins"""
    if not plugin_manager:
        raise HTTPException(status_code=503, detail="Plugin manager not initialized")

    # Get all plugins
    all_plugins = plugin_manager.get_all_plugins()

    # Apply filters
    filtered = all_plugins
    if category:
        filtered = [p for p in filtered if category.lower() in [t.lower() for t in p.get('tags', [])]]
    if plugin_type:
        filtered = [p for p in filtered if p.get('plugin_type') == plugin_type.value]
    if search:
        search_lower = search.lower()
        filtered = [
            p for p in filtered
            if search_lower in p.get('name', '').lower() or search_lower in p.get('description', '').lower()
        ]

    # Convert to PluginInfo models
    plugin_infos = [
        PluginInfo(
            id=p.get('id', ''),
            name=p.get('name', ''),
            description=p.get('description', ''),
            version=p.get('version', '1.0.0'),
            author=p.get('author', 'Unknown'),
            plugin_type=PluginType(p.get('plugin_type', 'integration')),
            tags=p.get('tags', []),
            status=PluginStatus.ACTIVE,
            enabled=True
        )
        for p in filtered
    ]

    # Calculate categories
    categories = {}
    for p in all_plugins:
        for tag in p.get('tags', []):
            categories[tag] = categories.get(tag, 0) + 1

    return PluginListResponse(
        plugins=plugin_infos,
        total=len(plugin_infos),
        categories=categories
    )

@plugins_router.get("/{plugin_id}", response_model=PluginInfo)
async def get_plugin(
    plugin_id: str,
    user=Depends(get_current_user)
):
    """Get detailed information about a specific plugin"""
    if not plugin_manager:
        raise HTTPException(status_code=503, detail="Plugin manager not initialized")

    plugin = plugin_manager.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Plugin '{plugin_id}' not found")

    metadata = plugin.metadata
    return PluginInfo(
        id=metadata.id,
        name=metadata.name,
        description=metadata.description,
        version=metadata.version,
        author=metadata.author,
        plugin_type=PluginType(metadata.plugin_type.value),
        tags=metadata.tags,
        status=PluginStatus.ACTIVE,
        enabled=True
    )

@plugins_router.post("/{plugin_id}/connect")
async def connect_plugin(
    plugin_id: str,
    request: PluginConnectRequest,
    user=Depends(get_current_user)
):
    """Connect a plugin with credentials"""
    if not plugin_manager:
        raise HTTPException(status_code=503, detail="Plugin manager not initialized")

    plugin = plugin_manager.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Plugin '{plugin_id}' not found")

    try:
        success = await plugin.connect(request.credentials)
        if success:
            return {"success": True, "message": f"Plugin '{plugin_id}' connected successfully"}
        else:
            raise HTTPException(status_code=400, detail=f"Failed to connect plugin '{plugin_id}'")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error connecting plugin: {str(e)}")

@plugins_router.post("/{plugin_id}/execute", response_model=PluginExecuteResponse)
async def execute_plugin(
    plugin_id: str,
    request: PluginExecuteRequest,
    user=Depends(get_current_user)
):
    """Execute a plugin action"""
    if not plugin_manager:
        raise HTTPException(status_code=503, detail="Plugin manager not initialized")

    plugin = plugin_manager.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Plugin '{plugin_id}' not found")

    start_time = time.time()
    try:
        # Execute with timeout
        result = await asyncio.wait_for(
            plugin.execute(request.action, request.params),
            timeout=request.timeout
        )
        execution_time = time.time() - start_time

        return PluginExecuteResponse(
            success=True,
            result=result,
            error=None,
            execution_time=execution_time,
            plugin_id=plugin_id,
            action=request.action
        )
    except asyncio.TimeoutError:
        execution_time = time.time() - start_time
        return PluginExecuteResponse(
            success=False,
            result=None,
            error=f"Execution timed out after {request.timeout} seconds",
            execution_time=execution_time,
            plugin_id=plugin_id,
            action=request.action
        )
    except Exception as e:
        execution_time = time.time() - start_time
        return PluginExecuteResponse(
            success=False,
            result=None,
            error=str(e),
            execution_time=execution_time,
            plugin_id=plugin_id,
            action=request.action
        )

@plugins_router.post("/{plugin_id}/disconnect")
async def disconnect_plugin(
    plugin_id: str,
    user=Depends(get_current_user)
):
    """Disconnect a plugin"""
    if not plugin_manager:
        raise HTTPException(status_code=503, detail="Plugin manager not initialized")

    plugin = plugin_manager.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Plugin '{plugin_id}' not found")

    try:
        success = await plugin.disconnect()
        if success:
            return {"success": True, "message": f"Plugin '{plugin_id}' disconnected successfully"}
        else:
            raise HTTPException(status_code=400, detail=f"Failed to disconnect plugin '{plugin_id}'")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error disconnecting plugin: {str(e)}")

# Agent endpoints (basic implementation)
@agents_router.post("/", response_model=AgentInfo)
async def create_agent(
    request: AgentCreateRequest,
    user=Depends(get_current_user)
):
    """Create a new agent"""
    # TODO: Implement agent creation
    agent_id = f"agent_{int(time.time())}"
    return AgentInfo(
        id=agent_id,
        name=request.name,
        plugins=request.plugins,
        status="created",
        created_at=datetime.utcnow().isoformat()
    )

@agents_router.get("/", response_model=List[AgentInfo])
async def list_agents(user=Depends(get_current_user)):
    """List all agents"""
    # TODO: Implement agent listing
    return []

@agents_router.get("/{agent_id}", response_model=AgentInfo)
async def get_agent(
    agent_id: str,
    user=Depends(get_current_user)
):
    """Get agent information"""
    # TODO: Implement agent retrieval
    raise HTTPException(status_code=404, detail="Agent not found")

@agents_router.post("/{agent_id}/execute", response_model=AgentExecuteResponse)
async def execute_agent(
    agent_id: str,
    request: AgentExecuteRequest,
    user=Depends(get_current_user)
):
    """Execute an agent task"""
    # TODO: Implement agent execution
    start_time = time.time()
    execution_time = time.time() - start_time

    return AgentExecuteResponse(
        success=True,
        result={"message": "Agent execution not yet implemented"},
        error=None,
        execution_time=execution_time,
        agent_id=agent_id,
        task=request.task
    )

@agents_router.delete("/{agent_id}")
async def delete_agent(
    agent_id: str,
    user=Depends(get_current_user)
):
    """Delete an agent"""
    # TODO: Implement agent deletion
    return {"success": True, "message": f"Agent '{agent_id}' deleted"}

# System endpoints
@system_router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    if not plugin_manager:
        raise HTTPException(status_code=503, detail="Plugin manager not initialized")

    all_plugins = plugin_manager.get_all_plugins()
    return HealthResponse(
        status="healthy",
        version="2.0.0-alpha",
        uptime=time.time() - plugin_manager.start_time,
        plugins_loaded=len(all_plugins),
        plugins_active=len(all_plugins)
    )

@system_router.get("/info")
async def system_info():
    """Get system information"""
    if not plugin_manager:
        raise HTTPException(status_code=503, detail="Plugin manager not initialized")

    all_plugins = plugin_manager.get_all_plugins()

    # Calculate statistics
    categories = {}
    plugin_types = {}
    for p in all_plugins:
        for tag in p.get('tags', []):
            categories[tag] = categories.get(tag, 0) + 1
        pt = p.get('plugin_type', 'integration')
        plugin_types[pt] = plugin_types.get(pt, 0) + 1

    return {
        "name": "Windows AI",
        "version": "2.0.0-alpha",
        "status": "active_development",
        "uptime": time.time() - plugin_manager.start_time,
        "plugins": {
            "total": len(all_plugins),
            "categories": categories,
            "types": plugin_types
        },
        "api_version": "1.0",
        "documentation": "/docs"
    }

@system_router.get("/stats")
async def system_stats():
    """Get system statistics"""
    if not plugin_manager:
        raise HTTPException(status_code=503, detail="Plugin manager not initialized")

    return {
        "uptime": time.time() - plugin_manager.start_time,
        "requests_served": 0,  # TODO: Track requests
        "errors": 0,  # TODO: Track errors
        "avg_response_time": 0.0  # TODO: Track response times
    }

# Include all routers in main router
router.include_router(plugins_router)
router.include_router(agents_router)
router.include_router(system_router)
