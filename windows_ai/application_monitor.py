"""Active application monitoring with durable result history."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import threading
import uuid
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)
_STATE_VERSION = 1


@dataclass
class ApplicationMonitorResult:
    """A single application-monitoring result."""

    result_id: str
    status: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ApplicationMonitor:
    """Collect and durably retain application-monitoring results."""

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._state_file = self.data_dir / "application_monitor_state.json"
        self._lock = threading.RLock()
        self.results: List[ApplicationMonitorResult] = []
        self._load_state()
        logger.info("ApplicationMonitor initialized")

    def process(self, input_data: Dict[str, Any]) -> ApplicationMonitorResult:
        """Record a validated monitoring result."""
        if not isinstance(input_data, dict):
            raise TypeError("input_data must be a dictionary")

        result = ApplicationMonitorResult(
            result_id=str(uuid.uuid4()),
            status="success",
            data={"processed": True, "input": dict(input_data)},
        )
        with self._lock:
            self.results.append(result)
            self._save_state()
        return result

    def get_results(self) -> List[ApplicationMonitorResult]:
        """Return a snapshot of retained results."""
        with self._lock:
            return list(self.results)

    def _save_state(self) -> None:
        with self._lock:
            payload = {
                "version": _STATE_VERSION,
                "results": [
                    {
                        **asdict(result),
                        "timestamp": result.timestamp.astimezone(timezone.utc).isoformat(),
                    }
                    for result in self.results
                ],
            }
            temporary = self._state_file.with_suffix(".json.tmp")
            temporary.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
            temporary.replace(self._state_file)

    def _load_state(self) -> None:
        if not self._state_file.exists():
            return
        try:
            payload = json.loads(self._state_file.read_text(encoding="utf-8"))
            if payload.get("version") != _STATE_VERSION:
                logger.warning("Ignoring unsupported application-monitor state version")
                return
            loaded: List[ApplicationMonitorResult] = []
            for item in payload.get("results", []):
                if not isinstance(item, dict):
                    continue
                try:
                    loaded.append(
                        ApplicationMonitorResult(
                            result_id=str(item["result_id"]),
                            status=str(item["status"]),
                            data=dict(item.get("data", {})),
                            timestamp=datetime.fromisoformat(str(item["timestamp"])).astimezone(timezone.utc),
                        )
                    )
                except (KeyError, TypeError, ValueError):
                    logger.warning("Skipping malformed application-monitor result")
            self.results = loaded
        except (OSError, json.JSONDecodeError, TypeError) as exc:
            logger.warning("Unable to load application-monitor state: %s", exc)


_application_monitor: Optional[ApplicationMonitor] = None


def get_application_monitor() -> Optional[ApplicationMonitor]:
    """Return the initialized global monitor, if any."""
    return _application_monitor


def initialize_application_monitor(data_dir: Path) -> ApplicationMonitor:
    """Initialize and return the global application monitor."""
    global _application_monitor
    _application_monitor = ApplicationMonitor(data_dir)
    return _application_monitor
