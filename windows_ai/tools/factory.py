"""Construct the canonical application tool runtime."""
from __future__ import annotations

from .builtins import definitions as builtin_definitions
from .registry import ToolRegistry
from .router import ToolRouter
from .windows import definitions as windows_definitions


def create_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register_many(builtin_definitions())
    registry.register_many(windows_definitions())
    return registry


def create_router(*, approval_callback=None, audit_callback=None) -> ToolRouter:
    return ToolRouter(create_registry(), approval_callback=approval_callback, audit_callback=audit_callback)


__all__ = ["create_registry", "create_router"]
