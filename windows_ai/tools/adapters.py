"""Adapters that normalize external capabilities into the unified tool registry."""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any, Protocol

from .models import ToolDefinition, ToolPermission
from .registry import ToolRegistry


class ToolProvider(Protocol):
    source: str

    def tools(self) -> Iterable[ToolDefinition]: ...


class StaticToolProvider:
    """Small provider used by plugins, integrations, and MCP bridges."""
    def __init__(self, source: str, tools: Iterable[ToolDefinition]) -> None:
        self.source = source
        self._tools = tuple(tools)

    def tools(self) -> tuple[ToolDefinition, ...]:
        return self._tools


def register_provider(registry: ToolRegistry, provider: ToolProvider, *, replace: bool = False) -> int:
    tools = list(provider.tools())
    normalized = [
        ToolDefinition(
            name=tool.name,
            description=tool.description,
            handler=tool.handler,
            input_schema=tool.input_schema,
            permissions=tool.permissions,
            risk_level=tool.risk_level,
            source=provider.source,
            enabled=tool.enabled,
            metadata=tool.metadata,
        )
        for tool in tools
    ]
    registry.register_many(normalized, replace=replace)
    return len(normalized)


class MCPToolBridge:
    """Transport-neutral MCP tool bridge.

    A concrete MCP transport can call ``register_tools`` after performing
    MCP discovery. Keeping transport out of the core runtime prevents the
    rest of Windows-AI from depending on a particular MCP implementation.
    """
    source = "mcp"

    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry

    def register_tools(self, tools: Iterable[Mapping[str, Any]], handler_factory, *, replace: bool = False) -> int:
        definitions: list[ToolDefinition] = []
        for remote in tools:
            name = str(remote["name"])
            definitions.append(
                ToolDefinition(
                    name=name,
                    description=str(remote.get("description", f"MCP tool: {name}")),
                    handler=handler_factory(name),
                    input_schema=remote.get("inputSchema", {"type": "object"}),
                    permissions=frozenset(
                        ToolPermission(str(value))
                        for value in remote.get("permissions", [])
                        if str(value) in {permission.value for permission in ToolPermission}
                    ),
                    risk_level=str(remote.get("riskLevel", "medium")),
                    source=self.source,
                    metadata={"protocol": "mcp", "remote": True},
                )
            )
        self.registry.register_many(definitions, replace=replace)
        return len(definitions)


__all__ = ["ToolProvider", "StaticToolProvider", "register_provider", "MCPToolBridge"]
