"""Execution router enforcing the blueprint's permission boundary."""

from __future__ import annotations

import inspect
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from .models import ToolCall, ToolPermission, ToolResult
from .registry import ToolRegistry

logger = logging.getLogger(__name__)


class ToolPermissionError(PermissionError):
    """Raised when a caller has not been granted a tool's required capability."""


ApprovalCallback = Callable[[ToolCall, frozenset[ToolPermission]], bool | Awaitable[bool]]
AuditCallback = Callable[[ToolCall, ToolResult], None | Awaitable[None]]


class ToolRouter:
    """Single execution path for native, plugin, and future MCP tools."""

    def __init__(
        self,
        registry: ToolRegistry,
        *,
        approval_callback: ApprovalCallback | None = None,
        audit_callback: AuditCallback | None = None,
    ) -> None:
        self.registry = registry
        self.approval_callback = approval_callback
        self.audit_callback = audit_callback

    async def execute(self, call: ToolCall) -> ToolResult:
        tool = self.registry.get(call.tool_name)
        if tool is None:
            return ToolResult.fail(call, f"Unknown tool: {call.tool_name}")
        if not tool.enabled:
            return ToolResult.fail(call, f"Tool is disabled: {call.tool_name}")

        missing = frozenset(tool.permissions - call.approved_permissions)
        if missing:
            approved = False
            if self.approval_callback is not None:
                decision = self.approval_callback(call, missing)
                approved = await decision if inspect.isawaitable(decision) else bool(decision)
            if not approved:
                result = ToolResult.fail(
                    call,
                    "Permission denied",
                    missing_permissions=sorted(permission.value for permission in missing),
                )
                await self._audit(call, result)
                return result

        try:
            value = tool.handler(call.arguments)
            if inspect.isawaitable(value):
                value = await value
            result = ToolResult.ok(call, value, source=tool.source)
        except Exception as exc:  # tool boundaries must not crash the orchestrator
            logger.exception("Tool execution failed: %s", call.tool_name)
            result = ToolResult.fail(call, str(exc), source=tool.source)

        await self._audit(call, result)
        return result

    async def _audit(self, call: ToolCall, result: ToolResult) -> None:
        if self.audit_callback is None:
            return
        value = self.audit_callback(call, result)
        if inspect.isawaitable(value):
            await value


__all__ = ["ToolRouter", "ToolPermissionError"]
