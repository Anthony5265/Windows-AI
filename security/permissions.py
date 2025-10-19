"""Permission management for plugins."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json
from typing import Dict, Set

from .audit import AuditLogger


@dataclass
class PermissionManager:
    """Keep track of plugin permissions and enforce them."""

    permissions: Dict[str, Set[str]] = field(default_factory=dict)
    audit_logger: AuditLogger | None = None
    path: str | Path | None = None

    def __post_init__(self) -> None:  # pragma: no cover - trivial
        if self.path:
            # Normalize to Path and eagerly load any existing permissions
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

    # ------------------------------------------------------------ persistence
    def save(self, path: str | Path | None = None) -> None:
        """Persist current permissions to a JSON file."""

        target_input = path or self.path
        if not target_input:
            raise ValueError("No path provided for saving permissions")

        target = Path(target_input)
        # Remember the location so subsequent calls can omit a path
        self.path = target
        target.parent.mkdir(parents=True, exist_ok=True)

        data = {
            plugin: sorted(list(perms))
            for plugin, perms in self.permissions.items()
        }
        target.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def load(self, path: str | Path | None = None) -> None:
        """Load permissions from a JSON file if it exists."""

        target_input = path or self.path
        if not target_input:
            return

        target = Path(target_input)
        # Store the path so future saves default to the same location
        self.path = target
        if not target.exists():
            return

        data = json.loads(target.read_text(encoding="utf-8"))
        self.permissions = {plugin: set(perms) for plugin, perms in data.items()}
