"""Unified tool/action subsystem."""
from .adapters import MCPToolBridge, StaticToolProvider, ToolProvider, register_provider
from .builtins import builtin_tools
from .discovery import discover_tools
from .models import ToolCall, ToolDefinition, ToolPermission, ToolResult
from .registry import ToolRegistry
from .router import ToolPermissionError, ToolRouter
from .runtime import create_default_registry, create_default_router

__all__ = [
    "ToolCall", "ToolDefinition", "ToolPermission", "ToolResult",
    "ToolRegistry", "ToolRouter", "ToolPermissionError",
    "builtin_tools", "create_default_registry", "create_default_router",
    "ToolProvider", "StaticToolProvider", "register_provider", "MCPToolBridge",
    "discover_tools",
]
