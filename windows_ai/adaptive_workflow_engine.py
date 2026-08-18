"""Adaptive workflow execution with durable, deterministic state."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from threading import RLock
from typing import Any, Dict, List, Mapping, Optional
import uuid

logger = logging.getLogger(__name__)

_STATE_VERSION = 1
_STATE_FILENAME = "adaptive_workflow_engine_state.json"


@dataclass(frozen=True)
class AdaptiveWorkflowEngineResult:
    """Immutable result produced by the adaptive workflow engine."""

    result_id: str
    status: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class AdaptiveWorkflowEngine:
    """Process workflow requests and durably retain their results."""

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir).expanduser()
        if not str(self.data_dir):
            raise ValueError("data_dir must not be empty")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if not self.data_dir.is_dir():
            raise ValueError(f"data_dir is not a directory: {self.data_dir}")
        self._state_file = self.data_dir / _STATE_FILENAME
        self._lock = RLock()
        self.results: List[AdaptiveWorkflowEngineResult] = []
        self._load_state()
        logger.info("AdaptiveWorkflowEngine initialized: %s", self.data_dir)

    def process(self, input_data: Mapping[str, Any]) -> AdaptiveWorkflowEngineResult:
        """Process one workflow request and persist the resulting state."""
        if not isinstance(input_data, Mapping):
            raise TypeError("input_data must be a mapping")

        # Copy the input so callers cannot mutate a result after submission.
        safe_input = dict(input_data)
        result = AdaptiveWorkflowEngineResult(
            result_id=str(uuid.uuid4()),
            status="success",
            data={"processed": True, "input": safe_input},
        )
        with self._lock:
            self.results.append(result)
            self._save_state()
        logger.info("Processed request in AdaptiveWorkflowEngine: %s", result.result_id)
        return result

    def get_results(self) -> List[AdaptiveWorkflowEngineResult]:
        """Return a snapshot of retained results."""
        with self._lock:
            return list(self.results)

    def _save_state(self) -> None:
        """Persist complete state using an atomic replace."""
        payload = {
            "version": _STATE_VERSION,
            "results": [self._serialize_result(result) for result in self.results],
        }
        temporary = self._state_file.with_suffix(".tmp")
        try:
            temporary.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            temporary.replace(self._state_file)
        except (OSError, TypeError, ValueError) as exc:
            logger.error("Failed to save state: %s", exc)
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                logger.debug("Unable to remove temporary state file", exc_info=True)
            raise

    def _load_state(self) -> None:
        """Restore complete state, ignoring only missing or invalid persisted data."""
        if not self._state_file.exists():
            return
        try:
            data = json.loads(self._state_file.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("state must be a JSON object")
            version = data.get("version", 0)
            if version != _STATE_VERSION:
                raise ValueError(f"unsupported state version: {version}")
            raw_results = data.get("results", [])
            if not isinstance(raw_results, list):
                raise ValueError("results must be a list")
            self.results = [self._deserialize_result(item) for item in raw_results]
            logger.info("Loaded %d workflow results", len(self.results))
        except (OSError, json.JSONDecodeError, TypeError, ValueError, KeyError) as exc:
            logger.warning("Ignoring invalid workflow state: %s", exc)
            self.results = []

    @staticmethod
    def _serialize_result(result: AdaptiveWorkflowEngineResult) -> Dict[str, Any]:
        data = asdict(result)
        data["timestamp"] = result.timestamp.astimezone(timezone.utc).isoformat()
        return data

    @staticmethod
    def _deserialize_result(raw: Any) -> AdaptiveWorkflowEngineResult:
        if not isinstance(raw, dict):
            raise ValueError("result must be an object")
        result_id = raw.get("result_id")
        status = raw.get("status")
        data = raw.get("data")
        timestamp = raw.get("timestamp")
        if not isinstance(result_id, str) or not result_id:
            raise ValueError("result_id must be a non-empty string")
        if not isinstance(status, str) or not status:
            raise ValueError("status must be a non-empty string")
        if not isinstance(data, dict):
            raise ValueError("result data must be an object")
        parsed_timestamp = datetime.fromisoformat(timestamp) if isinstance(timestamp, str) else None
        if parsed_timestamp is None:
            raise ValueError("timestamp must be an ISO-8601 string")
        if parsed_timestamp.tzinfo is None:
            parsed_timestamp = parsed_timestamp.replace(tzinfo=timezone.utc)
        return AdaptiveWorkflowEngineResult(
            result_id=result_id,
            status=status,
            data=data,
            timestamp=parsed_timestamp.astimezone(timezone.utc),
        )


# Compatibility singleton for existing callers.
_adaptive_workflow_engine: Optional[AdaptiveWorkflowEngine] = None


def get_adaptive_workflow_engine() -> Optional[AdaptiveWorkflowEngine]:
    """Return the initialized compatibility singleton, if one exists."""
    return _adaptive_workflow_engine


def initialize_adaptive_workflow_engine(data_dir: Path) -> AdaptiveWorkflowEngine:
    """Initialize and return the compatibility singleton."""
    global _adaptive_workflow_engine
    _adaptive_workflow_engine = AdaptiveWorkflowEngine(data_dir)
    return _adaptive_workflow_engine
