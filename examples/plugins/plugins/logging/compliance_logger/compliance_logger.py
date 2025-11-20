"""
Compliance logging utilities for Windows-AI.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from plugins.logging.base import JsonLogStore

ISO_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _to_iso(ts: datetime) -> str:
    return ts.strftime(ISO_FORMAT)


def _from_iso(value: str) -> datetime:
    return datetime.strptime(value, ISO_FORMAT).replace(tzinfo=timezone.utc)


@dataclass
class ControlResult:
    control_id: str
    status: str
    owner: str
    evidence_path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ComplianceLogger:
    """
    Tracks compliance control checks, exceptions, and remediation work.
    """

    def __init__(
        self,
        log_dir: str = "logs/compliance",
        retention_days: int = 365,
    ) -> None:
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.store = JsonLogStore(self.log_dir / "compliance_events.jsonl")
        self.retention_days = retention_days

    def record_control(self, result: ControlResult) -> Dict[str, Any]:
        """Persist the outcome of a control validation with metadata."""
        record = {
            "type": "control_check",
            "timestamp": _to_iso(_utc_now()),
            "control_id": result.control_id,
            "status": result.status.lower(),
            "owner": result.owner,
            "evidence_path": result.evidence_path,
            "metadata": result.metadata,
        }
        self.store.append(record)
        return record

    def record_exception(
        self,
        control_id: str,
        description: str,
        severity: str,
        remediation_owner: str,
        remediation_due: datetime,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Log an exception when a control fails."""
        record = {
            "type": "exception",
            "timestamp": _to_iso(_utc_now()),
            "control_id": control_id,
            "description": description,
            "severity": severity,
            "remediation_owner": remediation_owner,
            "remediation_due": _to_iso(remediation_due.astimezone(timezone.utc)),
            "tags": tags or [],
            "status": "open",
        }
        self.store.append(record)
        return record

    def close_exception(self, control_id: str, note: str) -> bool:
        """Mark the latest exception for a control as resolved."""
        records = self.store.read_all()
        updated = False
        for record in reversed(records):
            if (
                record.get("type") == "exception"
                and record.get("control_id") == control_id
                and record.get("status") == "open"
            ):
                record["status"] = "closed"
                record["closed_at"] = _to_iso(_utc_now())
                record["closure_note"] = note
                updated = True
                break

        if updated:
            self._rewrite(records)
        return updated

    def overdue_exceptions(self) -> List[Dict[str, Any]]:
        """Return all open exceptions whose remediation date is in the past."""
        now = _utc_now()
        overdue: List[Dict[str, Any]] = []
        for record in self.store.iter_records():
            if record.get("type") != "exception":
                continue
            if record.get("status") != "open":
                continue
            due = record.get("remediation_due")
            if not due:
                continue
            if _from_iso(due) < now:
                overdue.append(record)
        return overdue

    def purge_old_events(self) -> None:
        """Drop control records older than the retention window."""
        cutoff = _utc_now() - timedelta(days=self.retention_days)
        filtered = [
            record
            for record in self.store.read_all()
            if _from_iso(record["timestamp"]) >= cutoff
        ]
        self._rewrite(filtered)

    def generate_audit_report(self, period_days: int = 30) -> Dict[str, Any]:
        """Summarise control activity for the requested time range."""
        since = _utc_now() - timedelta(days=period_days)
        report = {
            "generated_at": _to_iso(_utc_now()),
            "period_days": period_days,
            "controls_checked": 0,
            "controls_passing": 0,
            "controls_failing": 0,
            "open_exceptions": len(self.overdue_exceptions()),
        }

        seen: Dict[str, Dict[str, Any]] = {}
        for record in self.store.iter_records():
            ts = _from_iso(record["timestamp"])
            if ts < since:
                continue
            if record.get("type") == "control_check":
                report["controls_checked"] += 1
                seen[record["control_id"]] = record
                if record["status"] == "pass":
                    report["controls_passing"] += 1
                else:
                    report["controls_failing"] += 1

        report["latest_controls"] = list(seen.values())[-10:]
        return report

    def _rewrite(self, records: Iterable[Dict[str, Any]]) -> None:
        """Rewrite the JSONL file with the provided records."""
        with self.store.log_path.open("w", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(record, default=str) + "\n")
