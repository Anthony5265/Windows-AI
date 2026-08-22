"""Real-time API monitoring and analytics."""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

logger = logging.getLogger(__name__)


@dataclass
class ApiMonitorResult:
    result_id: str
    status: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ApiMonitor:
    """Collect and persist API-monitoring results."""

    STATE_VERSION = 1

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[ApiMonitorResult] = []
        self._load_state()

    def process(self, input_data: Dict[str, Any]) -> ApiMonitorResult:
        if not isinstance(input_data, dict):
            raise TypeError("input_data must be a dictionary")
        result = ApiMonitorResult(str(uuid.uuid4()), "success", {"processed": True, "input": dict(input_data)})
        self.results.append(result)
        self._save_state()
        return result

    def get_results(self) -> List[ApiMonitorResult]:
        return list(self.results)

    def _save_state(self) -> None:
        state = {"version": self.STATE_VERSION, "results": [self._serialize(r) for r in self.results]}
        target = self.data_dir / "api_monitor_state.json"
        temp = target.with_suffix(".tmp")
        temp.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
        temp.replace(target)

    @staticmethod
    def _serialize(result: ApiMonitorResult) -> Dict[str, Any]:
        item = asdict(result)
        item["timestamp"] = result.timestamp.astimezone(timezone.utc).isoformat()
        return item

    def _load_state(self) -> None:
        target = self.data_dir / "api_monitor_state.json"
        if not target.exists():
            return
        try:
            state = json.loads(target.read_text(encoding="utf-8"))
            if state.get("version") != self.STATE_VERSION:
                return
            restored = []
            for item in state.get("results", []):
                restored.append(ApiMonitorResult(item["result_id"], item["status"], dict(item["data"]), datetime.fromisoformat(item["timestamp"])))
            self.results = restored
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
            logger.warning("Ignoring invalid API monitor state: %s", target)


_api_monitor: Optional[ApiMonitor] = None


def get_api_monitor() -> Optional[ApiMonitor]:
    return _api_monitor


def initialize_api_monitor(data_dir: Path) -> ApiMonitor:
    global _api_monitor
    _api_monitor = ApiMonitor(data_dir)
    return _api_monitor
