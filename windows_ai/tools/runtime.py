"""Default tool runtime shared by Windows-AI integrations."""

from __future__ import annotations

from .builtins import builtin_tools
from .registry import ToolRegistry
from .router import ToolRouter


def create_default_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register_many(builtin_tools())
    return registry


_registry = create_default_registry()
_router = ToolRouter(_registry)


def get_tool_registry() -> ToolRegistry:
    return _registry


def get_tool_router() -> ToolRouter:
    return _router


__all__ = ["create_default_registry", "get_tool_registry", "get_tool_router"]
