"""Contracts shared by built-in tools, plugins, and MCP adapters."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Awaitable, Callable, Mapping


class ToolPermission(str, Enum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    NETWORK = "network"
    SYSTEM = "system"
    ADMIN = "admin"
    CREDENTIALS = "credentials"
    DEVICE = "device"
    AUTOMATION = "automation"


ToolHandler = Callable[[Mapping[str, Any]], Any | Awaitable[Any]]


@dataclass(frozen=True)
class ToolDefinition:
    """A discoverable capability exposed to an agent."""

    name: str
    description: str
    handler: ToolHandler
    input_schema: Mapping[str, Any] = field(default_factory=lambda: {"type": "object"})
    permissions: frozenset[ToolPermission] = frozenset()
    risk_level: str = "low"
    source: str = "builtin"
    enabled: bool = True
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ToolCall:
    tool_name: str
    arguments: Mapping[str, Any] = field(default_factory=dict)
    actor: str = "default"
    approved_permissions: frozenset[ToolPermission] = frozenset()
    request_id: str | None = None


@dataclass(frozen=True)
class ToolResult:
    success: bool
    tool_name: str
    output: Any = None
    error: str | None = None
    request_id: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def ok(cls, call: ToolCall, output: Any, **metadata: Any) -> "ToolResult":
        return cls(True, call.tool_name, output=output, request_id=call.request_id, metadata=metadata)

    @classmethod
    def fail(cls, call: ToolCall, error: str, **metadata: Any) -> "ToolResult":
        return cls(False, call.tool_name, error=error, request_id=call.request_id, metadata=metadata)
