"""System behavior anomaly detection and alerting."""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import tempfile
import uuid
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)
_STATE_VERSION = 1
_STATE_NAME = "anomaly_detector_system_state.json"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class AnomalyDetectorSystemResult:
    """A durable result produced by the anomaly detector system."""
    result_id: str
    status: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=_utc_now)


class AnomalyDetectorSystem:
    """System behavior anomaly detection and alerting with durable state."""

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[AnomalyDetectorSystemResult] = []
        self._load_state()
        logger.info("AnomalyDetectorSystem initialized")

    @property
    def _state_file(self) -> Path:
        return self.data_dir / _STATE_NAME

    def process(self, input_data: Dict[str, Any]) -> AnomalyDetectorSystemResult:
        """Process a mapping and persist the complete result."""
        if not isinstance(input_data, dict):
            raise TypeError("input_data must be a dictionary")

        result = AnomalyDetectorSystemResult(
            result_id=str(uuid.uuid4()),
            status="success",
            data={"processed": True, "input": dict(input_data)},
        )
        self.results.append(result)
        self._save_state()
        logger.info("Processed request in AnomalyDetectorSystem")
        return result

    def get_results(self) -> List[AnomalyDetectorSystemResult]:
        """Return a snapshot so callers cannot mutate internal state."""
        return list(self.results)

    def _save_state(self) -> None:
        payload = {
            "version": _STATE_VERSION,
            "results": [
                {
                    "result_id": result.result_id,
                    "status": result.status,
                    "data": result.data,
                    "timestamp": result.timestamp.isoformat(),
                }
                for result in self.results
            ],
        }
        self.data_dir.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix=f"{_STATE_NAME}.", dir=self.data_dir)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2, ensure_ascii=False)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, self._state_file)
        except Exception:
            try:
                os.unlink(temp_name)
            except OSError:
                pass
            raise

    def _load_state(self) -> None:
        if not self._state_file.exists():
            return
        try:
            with self._state_file.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            if payload.get("version") != _STATE_VERSION:
                logger.warning("Ignoring unsupported anomaly detector state version")
                return
            restored: List[AnomalyDetectorSystemResult] = []
            for item in payload.get("results", []):
                if not isinstance(item, dict):
                    continue
                try:
                    timestamp = datetime.fromisoformat(item["timestamp"])
                    if timestamp.tzinfo is None:
                        timestamp = timestamp.replace(tzinfo=timezone.utc)
                    restored.append(AnomalyDetectorSystemResult(
                        result_id=str(item["result_id"]),
                        status=str(item["status"]),
                        data=dict(item.get("data", {})),
                        timestamp=timestamp,
                    ))
                except (KeyError, TypeError, ValueError):
                    logger.warning("Skipping malformed persisted anomaly result")
            self.results = restored
            logger.info("Loaded %d anomaly detector results", len(restored))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Unable to load anomaly detector state: %s", exc)


_anomaly_detector_system: Optional[AnomalyDetectorSystem] = None


def get_anomaly_detector_system() -> Optional[AnomalyDetectorSystem]:
    """Return the initialized global instance, if any."""
    return _anomaly_detector_system


def initialize_anomaly_detector_system(data_dir: Path) -> AnomalyDetectorSystem:
    """Initialize and return the global system instance."""
    global _anomaly_detector_system
    _anomaly_detector_system = AnomalyDetectorSystem(data_dir)
    return _anomaly_detector_system
