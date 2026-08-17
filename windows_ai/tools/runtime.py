"""Default unified tool runtime for Windows-AI."""
from __future__ import annotations

from .builtins import builtin_tools
from .registry import ToolRegistry
from .router import ToolRouter


def create_default_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register_many(builtin_tools())
    return registry


def create_default_router(*, approval_callback=None, audit_callback=None) -> ToolRouter:
    return ToolRouter(
        create_default_registry(),
        approval_callback=approval_callback,
        audit_callback=audit_callback,
    )


__all__ = ["create_default_registry", "create_default_router"]
