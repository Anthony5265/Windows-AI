"""Permission management for plugins."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json
from typing import Dict, Set, Callable

from .audit import AuditLogger


@dataclass
class PermissionManager:
    """Keep track of plugin permissions and enforce them."""

    permissions: Dict[str, Set[str]] = field(default_factory=dict)
    audit_logger: AuditLogger | None = None
    path: str | Path | None = None

    def __post_init__(self) -> None:  # pragma: no cover - trivial
        if self.path:
            self.path = Path(self.path)
            self.load(self.path)

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

    def prompt(
        self,
        plugin: str,
        permission: str,
        ask: Callable[[str, str], bool],
    ) -> bool:
        """Prompt the user via *ask* callback to grant *permission* for *plugin*.

        The callback should return ``True`` to grant the permission. ``False``
        results in a denial. The decision is audited and stored.
        """

        if self.has(plugin, permission):
            if self.audit_logger:
                self.audit_logger.log(plugin, "ALLOW", permission)
            return True
        allowed = ask(plugin, permission)
        if allowed:
            self.grant(plugin, permission)
        else:
            if self.audit_logger:
                self.audit_logger.log(plugin, "DENIED", permission)
        return allowed

    # ------------------------------------------------------------ persistence
    def save(self, path: str | Path | None = None) -> None:
        """Persist permissions to ``path`` or ``self.path`` as JSON."""

        target_input = path or self.path
        if not target_input:
            raise ValueError("No path provided for saving permissions")
        target = Path(target_input)
        target.parent.mkdir(parents=True, exist_ok=True)
        data = {plugin: sorted(perms) for plugin, perms in self.permissions.items()}
        target.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def load(self, path: str | Path | None = None) -> None:
        """Load permissions from ``path`` or ``self.path`` if available."""

        target_input = path or self.path
        if not target_input:
            return
        target = Path(target_input)
        if not target.exists():
            return
        data = json.loads(target.read_text(encoding="utf-8"))
        self.permissions = {plugin: set(perms) for plugin, perms in data.items()}
