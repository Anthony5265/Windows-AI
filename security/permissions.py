"""Permission management for plugins."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Set

from .audit import AuditLogger


@dataclass
class PermissionManager:
    """Keep track of plugin permissions and enforce them."""

    permissions: Dict[str, Set[str]] = field(default_factory=dict)
    audit_logger: AuditLogger | None = None

    # --------------------------------------------------------------- management
    def grant(self, plugin: str, permission: str) -> None:
        self.permissions.setdefault(plugin, set()).add(permission)
        if self.audit_logger:
            self.audit_logger.log(plugin, "GRANT", permission)

    def revoke(self, plugin: str, permission: str) -> None:
        if plugin in self.permissions:
            self.permissions[plugin].discard(permission)
        if self.audit_logger:
            self.audit_logger.log(plugin, "REVOKE", permission)

    # ----------------------------------------------------------------- checking
    def has(self, plugin: str, permission: str) -> bool:
        return permission in self.permissions.get(plugin, set())

    def require(self, plugin: str, permission: str) -> None:
        """Ensure a plugin possesses a given permission."""

        if not self.has(plugin, permission):
            if self.audit_logger:
                self.audit_logger.log(plugin, "DENIED", permission)
            raise PermissionError(f"{plugin} lacks {permission} permission")
        if self.audit_logger:
            self.audit_logger.log(plugin, "ALLOW", permission)
