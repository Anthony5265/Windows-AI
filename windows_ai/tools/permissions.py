"""Reusable permission policies for the unified tool layer."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .models import ToolCall, ToolPermission


@dataclass(frozen=True)
class PermissionPolicy:
    """Allow-list policy evaluated before a tool is executed."""

    grants: dict[str, frozenset[ToolPermission]] = field(default_factory=dict)
    default_grants: frozenset[ToolPermission] = frozenset()

    def granted(self, actor: str) -> frozenset[ToolPermission]:
        return self.grants.get(actor, self.default_grants)

    def missing(self, call: ToolCall, required: Iterable[ToolPermission]) -> frozenset[ToolPermission]:
        effective = self.granted(call.actor) | call.approved_permissions
        return frozenset(permission for permission in required if permission not in effective)

    def allows(self, call: ToolCall, required: Iterable[ToolPermission]) -> bool:
        return not self.missing(call, required)


__all__ = ["PermissionPolicy"]
