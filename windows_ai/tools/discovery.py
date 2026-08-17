"""Capability discovery helpers for agents and UI clients."""
from __future__ import annotations

from typing import Any

from .registry import ToolRegistry


def discover_tools(registry: ToolRegistry, *, source: str | None = None, category: str | None = None) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for tool in registry.list(source=source):
        if category and tool.metadata.get("category") != category:
            continue
        result.append({
            "name": tool.name,
            "description": tool.description,
            "input_schema": dict(tool.input_schema),
            "permissions": sorted(permission.value for permission in tool.permissions),
            "risk_level": tool.risk_level,
            "source": tool.source,
            "metadata": dict(tool.metadata),
        })
    return result


__all__ = ["discover_tools"]
