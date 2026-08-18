"""Construct the canonical application tool runtime."""
from __future__ import annotations

from .builtins import builtin_tools
from .registry import ToolRegistry
from .router import ToolRouter
from .windows import windows_tools


def create_registry() -> ToolRegistry:
    """Create the canonical registry with all first-party tools."""
    registry = ToolRegistry()
    registry.register_many(builtin_tools())
    registry.register_many(windows_tools())
    return registry


def create_router(*, approval_callback=None, audit_callback=None) -> ToolRouter:
    """Create the canonical tool router with the first-party registry."""
    return ToolRouter(
        create_registry(),
        approval_callback=approval_callback,
        audit_callback=audit_callback,
    )


__all__ = ["create_registry", "create_router"]
