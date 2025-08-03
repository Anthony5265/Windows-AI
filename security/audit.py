"""Simple audit logging utilities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class AuditLogger:
    """Record security related events to a log file."""

    path: Path | str | None = None

    def __post_init__(self) -> None:
        self.path = Path(self.path or Path("audit.log"))

    # -------------------------------------------------------------- utilities
    def log(self, plugin: str, action: str, permission: str) -> None:
        """Append an entry to the audit log."""

        line = f"{datetime.utcnow().isoformat()} {plugin} {action} {permission}\n"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(line)

    def read(self) -> str:
        """Return the full audit log as a string."""

        if not self.path.exists():
            return ""
        return self.path.read_text(encoding="utf-8")
