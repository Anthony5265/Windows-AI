"""Persistent active-learning feedback collection."""
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pathlib import Path
import json
import logging
import uuid

logger = logging.getLogger(__name__)


@dataclass
class ActiveLearningCollectorResult:
    result_id: str
    status: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ActiveLearningCollector:
    """Collect and persist user-feedback records for later learning workflows."""

    STATE_FILENAME = "active_learning_collector_state.json"

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[ActiveLearningCollectorResult] = []
        self._load_state()
        logger.info("ActiveLearningCollector initialized")

    def process(self, input_data: Dict[str, Any]) -> ActiveLearningCollectorResult:
        if not isinstance(input_data, dict):
            raise TypeError("input_data must be a dictionary")
        result = ActiveLearningCollectorResult(
            result_id=str(uuid.uuid4()),
            status="success",
            data={"processed": True, "input": dict(input_data)},
        )
        self.results.append(result)
        self._save_state()
        logger.info("Processed request in ActiveLearningCollector")
        return result

    def get_results(self) -> List[ActiveLearningCollectorResult]:
        return list(self.results)

    @property
    def state_path(self) -> Path:
        return self.data_dir / self.STATE_FILENAME

    def _save_state(self) -> None:
        payload = {
            "version": 1,
            "results": [
                {
                    **asdict(result),
                    "timestamp": result.timestamp.isoformat(),
                }
                for result in self.results
            ],
        }
        temporary = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        try:
            temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
            temporary.replace(self.state_path)
        except OSError:
            logger.exception("Failed to save active learning collector state")
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass

    def _load_state(self) -> None:
        try:
            if not self.state_path.exists():
                return
            payload = json.loads(self.state_path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict) or not isinstance(payload.get("results", []), list):
                raise ValueError("invalid collector state format")
            loaded: List[ActiveLearningCollectorResult] = []
            for item in payload["results"]:
                if not isinstance(item, dict):
                    continue
                timestamp = datetime.fromisoformat(item["timestamp"]) if item.get("timestamp") else datetime.now(timezone.utc)
                if timestamp.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=timezone.utc)
                loaded.append(ActiveLearningCollectorResult(
                    result_id=str(item["result_id"]),
                    status=str(item["status"]),
                    data=dict(item.get("data", {})),
                    timestamp=timestamp,
                ))
            self.results = loaded
            logger.info("Loaded %d active-learning results", len(self.results))
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
            logger.exception("Failed to load active learning collector state")
            self.results = []


_active_learning_collector: Optional[ActiveLearningCollector] = None


def get_active_learning_collector() -> Optional[ActiveLearningCollector]:
    return _active_learning_collector


def initialize_active_learning_collector(data_dir: Path) -> ActiveLearningCollector:
    global _active_learning_collector
    _active_learning_collector = ActiveLearningCollector(data_dir)
    return _active_learning_collector
