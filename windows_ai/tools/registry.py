"""Thread-safe-ish in-process registry for every Windows-AI tool source."""

from __future__ import annotations

from collections.abc import Iterable
from threading import RLock
from typing import Any

from .models import ToolDefinition


class ToolRegistry:
    """Central registry used by built-ins, plugins, and MCP integrations."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}
        self._lock = RLock()

    def register(self, tool: ToolDefinition, *, replace: bool = False) -> ToolDefinition:
        if not tool.name or not tool.name.strip():
            raise ValueError("Tool name cannot be empty")
        with self._lock:
            if tool.name in self._tools and not replace:
                raise ValueError(f"Tool already registered: {tool.name}")
            self._tools[tool.name] = tool
        return tool

    def register_many(self, tools: Iterable[ToolDefinition], *, replace: bool = False) -> None:
        for tool in tools:
            self.register(tool, replace=replace)

    def unregister(self, name: str) -> bool:
        with self._lock:
            return self._tools.pop(name, None) is not None

    def get(self, name: str) -> ToolDefinition | None:
        with self._lock:
            return self._tools.get(name)

    def require(self, name: str) -> ToolDefinition:
        tool = self.get(name)
        if tool is None:
            raise KeyError(f"Unknown tool: {name}")
        return tool

    def list(self, *, source: str | None = None, enabled_only: bool = True) -> list[ToolDefinition]:
        with self._lock:
            tools = list(self._tools.values())
        if source is not None:
            tools = [tool for tool in tools if tool.source == source]
        if enabled_only:
            tools = [tool for tool in tools if tool.enabled]
        return sorted(tools, key=lambda tool: tool.name)

    def schemas(self) -> list[dict[str, Any]]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": dict(tool.input_schema),
                "permissions": sorted(permission.value for permission in tool.permissions),
                "risk_level": tool.risk_level,
                "source": tool.source,
            }
            for tool in self.list()
        ]

    def __len__(self) -> int:
        with self._lock:
            return len(self._tools)
