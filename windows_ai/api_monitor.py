"""
Real-time API Monitoring & Analytics.

Durable, thread-safe monitoring primitives for API usage patterns.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any, Dict, List, Optional
import json
import os
import tempfile
import uuid


@dataclass
class ApiMonitorResult:
    """A single API monitoring observation."""
    result_id: str
    status: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {"result_id": self.result_id, "status": self.status, "data": self.data,
                "timestamp": self.timestamp.astimezone(timezone.utc).isoformat()}

    @classmethod
    def from_dict(cls, value: Dict[str, Any]) -> "ApiMonitorResult":
        if not isinstance(value, dict):
            raise ValueError("monitor result must be an object")
        result_id, status, data, raw_timestamp = (value.get(k) for k in ("result_id", "status", "data", "timestamp"))
        if not isinstance(result_id, str) or not result_id:
            raise ValueError("result_id must be a non-empty string")
        if not isinstance(status, str) or not status:
            raise ValueError("status must be a non-empty string")
        if not isinstance(data, dict):
            raise ValueError("data must be an object")
        if not isinstance(raw_timestamp, str):
            raise ValueError("timestamp must be an ISO-8601 string")
        timestamp = datetime.fromisoformat(raw_timestamp.replace("Z", "+00:00"))
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        return cls(result_id, status, data, timestamp.astimezone(timezone.utc))


class ApiMonitor:
    """Thread-safe API monitor with durable state."""
    STATE_VERSION = 1
    STATE_FILENAME = "api_monitor_state.json"

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir).expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[ApiMonitorResult] = []
        self._lock = RLock()
        self._load_state()

    @property
    def state_file(self) -> Path:
        return self.data_dir / self.STATE_FILENAME

    def process(self, input_data: Dict[str, Any]) -> ApiMonitorResult:
        """Record one API observation and persist it."""
        if not isinstance(input_data, dict):
            raise TypeError("input_data must be a dictionary")
        result = ApiMonitorResult(str(uuid.uuid4()), "success", {"processed": True, "input": dict(input_data)})
        with self._lock:
            self.results.append(result)
            self._save_state()
        return result

    def get_results(self, limit: Optional[int] = None) -> List[ApiMonitorResult]:
        """Return a defensive snapshot, optionally limited to newest results."""
        if limit is not None and (not isinstance(limit, int) or limit < 0):
            raise ValueError("limit must be a non-negative integer or None")
        with self._lock:
            snapshot = list(self.results)
        return snapshot[-limit:] if limit else (snapshot if limit is None else [])

    def _save_state(self) -> None:
        payload = {"version": self.STATE_VERSION, "results": [r.to_dict() for r in self.results]}
        fd, temp_name = tempfile.mkstemp(prefix=f".{self.STATE_FILENAME}.", suffix=".tmp", dir=str(self.data_dir))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2, ensure_ascii=False)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, self.state_file)
        except Exception:
            try:
                os.unlink(temp_name)
            except OSError:
                pass
            raise

    def _load_state(self) -> None:
        state_file = self.state_file
        if not state_file.exists():
            return
        try:
            with state_file.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            if not isinstance(payload, dict) or payload.get("version") != self.STATE_VERSION:
                return
            raw_results = payload.get("results", [])
            if not isinstance(raw_results, list):
                return
            restored = []
            for item in raw_results:
                try:
                    restored.append(ApiMonitorResult.from_dict(item))
                except (TypeError, ValueError, KeyError):
                    continue
            self.results = restored
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            self.results = []


_api_monitor: Optional[ApiMonitor] = None


def get_api_monitor() -> Optional[ApiMonitor]:
    return _api_monitor


def initialize_api_monitor(data_dir: Path) -> ApiMonitor:
    global _api_monitor
    _api_monitor = ApiMonitor(data_dir)
    return _api_monitor
