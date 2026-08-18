"""AI-guided learning paths for developers."""
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import logging
import uuid

logger = logging.getLogger(__name__)


@dataclass
class AiGuidedLearningResult:
    result_id: str
    status: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class AiGuidedLearning:
    """Store and retrieve deterministic learning-plan processing results."""

    STATE_VERSION = 1

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._state_file = self.data_dir / "ai_guided_learning_state.json"
        self.results: List[AiGuidedLearningResult] = []
        self._load_state()

    def process(self, input_data: Dict[str, Any]) -> AiGuidedLearningResult:
        if not isinstance(input_data, dict):
            raise TypeError("input_data must be a dictionary")
        result = AiGuidedLearningResult(
            result_id=str(uuid.uuid4()),
            status="success",
            data={"processed": True, "input": dict(input_data)},
        )
        self.results.append(result)
        self._save_state()
        return result

    def get_results(self) -> List[AiGuidedLearningResult]:
        """Return a snapshot so callers cannot mutate internal state."""
        return list(self.results)

    def _save_state(self) -> None:
        payload = {
            "version": self.STATE_VERSION,
            "results": [
                {**asdict(result), "timestamp": result.timestamp.isoformat()}
                for result in self.results
            ],
        }
        temporary = self._state_file.with_suffix(".tmp")
        temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        temporary.replace(self._state_file)

    def _load_state(self) -> None:
        if not self._state_file.exists():
            return
        try:
            payload = json.loads(self._state_file.read_text(encoding="utf-8"))
            if payload.get("version") != self.STATE_VERSION:
                logger.warning("Ignoring unsupported AI-guided-learning state version")
                return
            loaded: List[AiGuidedLearningResult] = []
            for item in payload.get("results", []):
                loaded.append(
                    AiGuidedLearningResult(
                        result_id=str(item["result_id"]),
                        status=str(item["status"]),
                        data=dict(item.get("data", {})),
                        timestamp=datetime.fromisoformat(item["timestamp"]),
                    )
                )
            self.results = loaded
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            logger.warning("Ignoring unreadable AI-guided-learning state: %s", exc)


_ai_guided_learning: Optional[AiGuidedLearning] = None


def get_ai_guided_learning() -> Optional[AiGuidedLearning]:
    return _ai_guided_learning


def initialize_ai_guided_learning(data_dir: Path) -> AiGuidedLearning:
    global _ai_guided_learning
    _ai_guided_learning = AiGuidedLearning(data_dir)
    return _ai_guided_learning
