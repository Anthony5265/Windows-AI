"""Pydantic models for API requests and responses."""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PluginType(str, Enum):
    ACTION = "action"
    TOOL = "tool"
    INTEGRATION = "integration"
    UI = "ui"
    AUTOMATION = "automation"


class PluginStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    LOADING = "loading"


class PluginExecuteRequest(BaseModel):
    action: str = Field(..., min_length=1, max_length=200)
    params: Dict[str, Any] = Field(default_factory=dict)
    timeout: Optional[int] = Field(default=30, ge=1, le=3600)


class PluginConnectRequest(BaseModel):
    credentials: Dict[str, Any] = Field(default_factory=dict)


class AgentCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    plugins: List[str] = Field(default_factory=list, max_length=100)
    config: Dict[str, Any] = Field(default_factory=dict)


class AgentExecuteRequest(BaseModel):
    task: str = Field(..., min_length=1, max_length=10000)
    params: Dict[str, Any] = Field(default_factory=dict)


class PluginInfo(BaseModel):
    id: str
    name: str
    description: str
    version: str
    author: str
    plugin_type: PluginType
    tags: List[str] = Field(default_factory=list)
    status: PluginStatus
    enabled: bool


class PluginListResponse(BaseModel):
    plugins: List[PluginInfo]
    total: int = Field(ge=0)
    categories: Dict[str, int] = Field(default_factory=dict)


class PluginExecuteResponse(BaseModel):
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time: float = Field(ge=0)
    plugin_id: str
    action: str


class HealthResponse(BaseModel):
    status: str
    version: str
    uptime: float = Field(ge=0)
    plugins_loaded: int = Field(ge=0)
    plugins_active: int = Field(ge=0)


class AgentInfo(BaseModel):
    id: str
    name: str
    plugins: List[str] = Field(default_factory=list)
    status: str
    created_at: str


class AgentExecuteResponse(BaseModel):
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time: float = Field(ge=0)
    agent_id: str
    task: str


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None
