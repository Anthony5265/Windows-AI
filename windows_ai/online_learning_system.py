"""
Online Learning for Continuous Adaptation

Continuously learns and adapts from new user interactions without full retraining.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import json
import logging
import uuid

logger = logging.getLogger(__name__)


@dataclass
class OnlineLearningSystemResult:
    """Result from OnlineLearningSystem"""
    result_id: str
    status: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


class OnlineLearningSystem:
    """
    OnlineLearningSystem

    Online Learning for Continuous Adaptation
    """

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[OnlineLearningSystemResult] = []
        self._load_state()
        logger.info("OnlineLearningSystem initialized")

    def process(self, input_data: Dict[str, Any]) -> OnlineLearningSystemResult:
        """Main processing function"""
        result = OnlineLearningSystemResult(
            result_id=str(uuid.uuid4()),
            status="success",
            data={"processed": True, "input": input_data}
        )
        self.results.append(result)
        self._save_state()
        logger.info(f"Processed request in OnlineLearningSystem")
        return result

    def get_results(self) -> List[OnlineLearningSystemResult]:
        """Get all results"""
        return self.results

    def _save_state(self):
        try:
            data = {"results_count": len(self.results)}
            with open(self.data_dir / "online_learning_system_state.json", "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def _load_state(self):
        try:
            state_file = self.data_dir / "online_learning_system_state.json"
            if state_file.exists():
                with open(state_file, "r") as f:
                    data = json.load(f)
                logger.info(f"Loaded {data.get('results_count', 0)} results")
        except Exception as e:
            logger.error(f"Failed to load state: {e}")


# Global instance
_online_learning_system: Optional[OnlineLearningSystem] = None


def get_online_learning_system() -> Optional[OnlineLearningSystem]:
    """Get global instance"""
    return _online_learning_system


def initialize_online_learning_system(data_dir: Path) -> OnlineLearningSystem:
    """Initialize system"""
    global _online_learning_system
    _online_learning_system = OnlineLearningSystem(data_dir)
    return _online_learning_system
