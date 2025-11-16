"""
Security auditing logger with tamper-evident hashing.
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from plugins.logging.base import JsonLogStore


class SecurityLogger:
    """
    Records authentication/authorization/security events with a hash chain.
    """

    def __init__(self, log_dir: str = "logs/security"):
        self.log_dir = Path(log_dir)
        self.store = JsonLogStore(self.log_dir / "security_events.jsonl")
        last = self.store.last_record()
        self._previous_hash = last.get("chain_hash") if last else "0" * 64

    def log_event(
        self,
        event_type: str,
        severity: str = "info",
        actor: Optional[str] = None,
        target: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Persist a security event and update the hash chain."""
        base_event = {
            "id": str(uuid.uuid4()),
            "timestamp": time.time(),
            "event_type": event_type,
            "severity": severity.lower(),
            "actor": actor,
            "target": target,
            "details": details or {},
            "tags": tags or [],
        }
        chain_hash = self._compute_chain_hash(base_event)
        event = {**base_event, "chain_hash": chain_hash}
        self.store.append(event)
        return event

    def _compute_chain_hash(self, event: Dict[str, Any]) -> str:
        payload = json.dumps(event, sort_keys=True, default=str).encode("utf-8")
        digest = hashlib.sha256(self._previous_hash.encode("utf-8") + payload).hexdigest()
        self._previous_hash = digest
        return digest

    def verify_chain(self) -> bool:
        """Recompute hashes to ensure the log has not been tampered with."""
        previous = "0" * 64
        for entry in self.store.iter_records():
            expected = hashlib.sha256(
                previous.encode("utf-8")
                + json.dumps(
                    {k: v for k, v in entry.items() if k != "chain_hash"},
                    sort_keys=True,
                    default=str,
                ).encode("utf-8")
            ).hexdigest()
            if expected != entry.get("chain_hash"):
                return False
            previous = expected
        return True

    def flag_alert(
        self,
        event_type: str,
        severity: str,
        actor: str,
        target: str,
        description: str,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Convenience helper for critical alerts."""
        return self.log_event(
            event_type=event_type,
            severity=severity,
            actor=actor,
            target=target,
            details={"message": description, "alert": True},
            tags=(tags or []) + ["alert"],
        )

    def recent_events(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Return the most recent entries."""
        events = self.store.read_all()
        return events[-limit:]
