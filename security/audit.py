"""Simple audit logging utilities."""

from __future__ import annotations

from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import List
import csv
import json


@dataclass
class AuditLogger:
    """Record security related events to a log file."""

    path: Path | str | None = None
    compliance_events: List["ComplianceEvent"] = field(default_factory=list)

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

    # ---------------------------------------------------------- compliance API
    def log_compliance(self, user: str, action: str, resource: str) -> None:
        """Record a structured compliance event in memory."""

        event = ComplianceEvent(datetime.utcnow(), user, action, resource)
        self.compliance_events.append(event)

    def export(self, dest: Path | str, fmt: str = "json") -> None:
        """Export collected compliance events to *dest* in JSON or CSV format."""

        dest_path = Path(dest)
        if fmt == "json":
            data = [
                {**asdict(e), "timestamp": e.timestamp.isoformat()}
                for e in self.compliance_events
            ]
            dest_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        elif fmt == "csv":
            with dest_path.open("w", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(
                    fh, fieldnames=["timestamp", "user", "action", "resource"]
                )
                writer.writeheader()
                for e in self.compliance_events:
                    writer.writerow(
                        {
                            "timestamp": e.timestamp.isoformat(),
                            "user": e.user,
                            "action": e.action,
                            "resource": e.resource,
                        }
                    )
        else:  # pragma: no cover - defensive
            raise ValueError(f"unknown format: {fmt}")


@dataclass
class ComplianceEvent:
    """Single compliance log entry."""

    timestamp: datetime
    user: str
    action: str
    resource: str
