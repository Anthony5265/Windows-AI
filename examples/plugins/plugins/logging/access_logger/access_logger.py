"""
Access logger focused on authorization decisions.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Deque, DefaultDict, Dict, List, Optional

from plugins.logging.base import JsonLogStore


class AccessLogger:
    """
    Records user/resource access attempts and highlights anomalies.
    """

    def __init__(
        self,
        log_dir: str = "logs/access",
        window_seconds: int = 300,
        deny_threshold: int = 5,
    ):
        self.log_dir = Path(log_dir)
        self.store = JsonLogStore(self.log_dir / "access_events.jsonl")
        self.window_seconds = window_seconds
        self.deny_threshold = deny_threshold
        self._denied_windows: DefaultDict[str, Deque[float]] = defaultdict(deque)

    def log_access(
        self,
        user: str,
        resource: str,
        action: str,
        decision: str,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Write an access decision and perform anomaly detection."""
        timestamp = time.time()
        event = {
            "timestamp": timestamp,
            "user": user,
            "resource": resource,
            "action": action,
            "decision": decision.lower(),
            "reason": reason,
            "ip": ip_address,
            "metadata": metadata or {},
        }

        if event["decision"] == "denied":
            event["alert"] = self._register_denial(user, timestamp)
        else:
            self._denied_windows.pop(user, None)

        self.store.append(event)
        return event

    def _register_denial(self, user: str, timestamp: float) -> Optional[str]:
        bucket = self._denied_windows[user]
        bucket.append(timestamp)
        while bucket and timestamp - bucket[0] > self.window_seconds:
            bucket.popleft()

        if len(bucket) >= self.deny_threshold:
            return "possible_bruteforce"
        return None

    def recent_events(self, user: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return recent access events, optionally filtered by user."""
        events = self.store.read_all()
        if user:
            events = [event for event in events if event.get("user") == user]
        return events[-100:]

    def report(self) -> Dict[str, Any]:
        """Generate a summary of allow/deny ratios."""
        data = {"allow": 0, "deny": 0}
        for entry in self.store.iter_records():
            if entry.get("decision") == "allowed":
                data["allow"] += 1
            elif entry.get("decision") == "denied":
                data["deny"] += 1
        total = data["allow"] + data["deny"]
        data["total"] = total
        if total:
            data["deny_rate"] = round(data["deny"] / total, 3)
        return data
