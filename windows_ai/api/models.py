"""Pydantic models for API requests and responses"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from enum import Enum

class PluginType(str, Enum):
    """Plugin type enumeration"""
    ACTION = "action"
    TOOL = "tool"
    INTEGRATION = "integration"
    UI = "ui"
    AUTOMATION = "automation"

class PluginStatus(str, Enum):
    """Plugin status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    LOADING = "loading"

# Request models
class PluginExecuteRequest(BaseModel):
    """Request to execute a plugin action"""
    action: str = Field(..., description="Action to execute")
    params: Dict[str, Any] = Field(default_factory=dict, description="Action parameters")
    timeout: Optional[int] = Field(default=30, description="Execution timeout in seconds")

class PluginConnectRequest(BaseModel):
    """Request to connect a plugin with credentials"""
    credentials: Dict[str, Any] = Field(..., description="Plugin credentials")

class AgentCreateRequest(BaseModel):
    """Request to create an agent"""
    name: str = Field(..., description="Agent name")
    plugins: List[str] = Field(..., description="List of plugin IDs")
    config: Dict[str, Any] = Field(default_factory=dict, description="Agent configuration")

class AgentExecuteRequest(BaseModel):
    """Request to execute an agent task"""
    task: str = Field(..., description="Task description")
    params: Dict[str, Any] = Field(default_factory=dict, description="Task parameters")

# Response models
class PluginInfo(BaseModel):
    """Plugin information"""
    id: str
    name: str
    description: str
    version: str
    author: str
    plugin_type: PluginType
    tags: List[str]
    status: PluginStatus
    enabled: bool

class PluginListResponse(BaseModel):
    """Response containing list of plugins"""
    plugins: List[PluginInfo]
    total: int
    categories: Dict[str, int]

class PluginExecuteResponse(BaseModel):
    """Response from plugin execution"""
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time: float
    plugin_id: str
    action: str

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    uptime: float
    plugins_loaded: int
    plugins_active: int

class AgentInfo(BaseModel):
    """Agent information"""
    id: str
    name: str
    plugins: List[str]
    status: str
    created_at: str

class AgentExecuteResponse(BaseModel):
    """Response from agent execution"""
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time: float
    agent_id: str
    task: str

class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None
