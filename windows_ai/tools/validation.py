"""Lightweight production-time validation for tool contracts.

This is not a test framework. It validates a tool definition before registration
so malformed extensions cannot enter the execution layer.
"""
from __future__ import annotations

from collections.abc import Mapping

from .models import ToolDefinition


class ToolContractError(ValueError):
    pass


def validate_tool_definition(tool: ToolDefinition) -> None:
    if not tool.name.strip():
        raise ToolContractError("Tool name is required")
    if not tool.description.strip():
        raise ToolContractError(f"Description is required: {tool.name}")
    if not callable(tool.handler):
        raise ToolContractError(f"Handler is not callable: {tool.name}")
    if not isinstance(tool.input_schema, Mapping):
        raise ToolContractError(f"Input schema must be a mapping: {tool.name}")
    if tool.risk_level not in {"low", "medium", "high", "critical"}:
        raise ToolContractError(f"Invalid risk level: {tool.risk_level}")
