"""Default construction helpers for the unified tool runtime."""
from __future__ import annotations

from .builtins import builtin_tools
from .registry import ToolRegistry
from .router import ToolRouter


def create_default_registry() -> ToolRegistry:
    """Create a registry containing the built-in offline-safe tools."""
    registry = ToolRegistry()
    for tool in builtin_tools():
        registry.register(tool)
    return registry


def create_default_router() -> ToolRouter:
    """Create the standard router backed by the default registry."""
    return ToolRouter(create_default_registry())


__all__ = ["create_default_registry", "create_default_router"]
