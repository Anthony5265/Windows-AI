"""
Windows AI - Unified AI Platform.

The package exposes the existing application APIs plus the canonical agent/tool runtime.
"""

__version__ = "2.0.0a1"

from windows_ai.core import WindowsAI, get_windows_ai, quick_start
from windows_ai.agent_runtime import AgentDefinition, AgentRuntime, AgentSession
from windows_ai.bootstrap import create_runtime
from windows_ai.canonical_runtime import CanonicalRuntime
from windows_ai.tools import (
    ToolCall, ToolDefinition, ToolPermission, ToolRegistry, ToolResult, ToolRouter,
    create_default_registry, create_default_router,
)

__all__ = [
    "WindowsAI", "get_windows_ai", "quick_start", "__version__",
    "CanonicalRuntime", "create_runtime",
    "AgentDefinition", "AgentRuntime", "AgentSession",
    "ToolCall", "ToolDefinition", "ToolPermission", "ToolRegistry", "ToolResult", "ToolRouter",
    "create_default_registry", "create_default_router",
]
