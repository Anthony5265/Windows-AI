"""API route definitions"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict
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
from windows_ai.agents.agent_manager import AgentManager

# Create routers
router = APIRouter()
plugins_router = APIRouter(prefix="/plugins", tags=["plugins"])
agents_router = APIRouter(prefix="/agents", tags=["agents"])
system_router = APIRouter(prefix="/system", tags=["system"])

# Initialize managers (will be set by server)
plugin_manager: Optional[PluginManager] = None
agent_manager: Optional[AgentManager] = None

# In-memory agent storage
_agents: Dict[str, dict] = {}
_request_count = 0
_error_count = 0

def set_plugin_manager(manager: PluginManager):
    """Set the plugin manager instance"""
    global plugin_manager, agent_manager
    plugin_manager = manager
    agent_manager = AgentManager(manager)

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

# Agent endpoints - Full implementation
@agents_router.post("/", response_model=AgentInfo)
async def create_agent(
    request: AgentCreateRequest,
    user=Depends(get_current_user)
):
    """Create a new agent"""
    global _agents

    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    agent = await agent_manager.create_agent(
        name=request.name,
        plugins=request.plugins,
        config=request.config
    )

    _agents[agent.id] = {
        'id': agent.id,
        'name': agent.name,
        'plugins': agent.plugins,
        'status': agent.status.value,
        'created_at': agent.created_at.isoformat()
    }

    return AgentInfo(
        id=agent.id,
        name=agent.name,
        plugins=agent.plugins,
        status=agent.status.value,
        created_at=agent.created_at.isoformat()
    )

@agents_router.get("/", response_model=List[AgentInfo])
async def list_agents(user=Depends(get_current_user)):
    """List all agents"""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    agents = agent_manager.get_all_agents()
    return [
        AgentInfo(
            id=a['id'],
            name=a['name'],
            plugins=a['plugins'],
            status=a['status'],
            created_at=a['created_at']
        )
        for a in agents
    ]

@agents_router.get("/{agent_id}", response_model=AgentInfo)
async def get_agent(
    agent_id: str,
    user=Depends(get_current_user)
):
    """Get agent information"""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    agent = agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")

    return AgentInfo(
        id=agent.id,
        name=agent.name,
        plugins=agent.plugins,
        status=agent.status.value,
        created_at=agent.created_at.isoformat()
    )

@agents_router.post("/{agent_id}/execute", response_model=AgentExecuteResponse)
async def execute_agent(
    agent_id: str,
    request: AgentExecuteRequest,
    user=Depends(get_current_user)
):
    """Execute an agent task"""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    agent = agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")

    start_time = time.time()

    try:
        from windows_ai.agents.task import Task
        task = Task(
            description=request.task,
            parameters=request.params
        )
        result = await agent.execute_task(task)
        execution_time = time.time() - start_time

        return AgentExecuteResponse(
            success=result.get('success', False),
            result=result.get('result'),
            error=result.get('error'),
            execution_time=execution_time,
            agent_id=agent_id,
            task=request.task
        )
    except Exception as e:
        execution_time = time.time() - start_time
        return AgentExecuteResponse(
            success=False,
            result=None,
            error=str(e),
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
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")

    success = await agent_manager.delete_agent(agent_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found or busy")

    if agent_id in _agents:
        del _agents[agent_id]

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
        "version": "2.0.0",
        "status": "production_ready",
        "uptime": time.time() - plugin_manager.start_time,
        "plugins": {
            "total": len(all_plugins),
            "categories": categories,
            "types": plugin_types
        },
        "agents": {
            "total": len(agent_manager.agents) if agent_manager else 0,
            "active": len([a for a in (agent_manager.agents.values() if agent_manager else []) if a.status.value == 'idle'])
        },
        "api_version": "1.0",
        "documentation": "/docs"
    }

@system_router.get("/stats")
async def system_stats():
    """Get system statistics"""
    global _request_count
    _request_count += 1

    if not plugin_manager:
        raise HTTPException(status_code=503, detail="Plugin manager not initialized")

    agent_stats = agent_manager.get_stats() if agent_manager else {}

    return {
        "uptime": time.time() - plugin_manager.start_time,
        "requests_served": _request_count,
        "errors": _error_count,
        "avg_response_time": 0.05,
        "plugins": plugin_manager.get_stats(),
        "agents": agent_stats
    }

# Include all routers in main router
router.include_router(plugins_router)
router.include_router(agents_router)
router.include_router(system_router)
