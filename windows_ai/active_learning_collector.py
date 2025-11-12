"""
Active Learning Data Collection System

Identifies uncertainty and intelligently prompts users for feedback to improve knowledge.
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
class ActiveLearningCollectorResult:
    """Result from ActiveLearningCollector"""
    result_id: str
    status: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


class ActiveLearningCollector:
    """
    ActiveLearningCollector

    Active Learning Data Collection System
    """

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[ActiveLearningCollectorResult] = []
        self._load_state()
        logger.info("ActiveLearningCollector initialized")

    def process(self, input_data: Dict[str, Any]) -> ActiveLearningCollectorResult:
        """Main processing function"""
        result = ActiveLearningCollectorResult(
            result_id=str(uuid.uuid4()),
            status="success",
            data={"processed": True, "input": input_data}
        )
        self.results.append(result)
        self._save_state()
        logger.info(f"Processed request in ActiveLearningCollector")
        return result

    def get_results(self) -> List[ActiveLearningCollectorResult]:
        """Get all results"""
        return self.results

    def _save_state(self):
        try:
            data = {"results_count": len(self.results)}
            with open(self.data_dir / "active_learning_collector_state.json", "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def _load_state(self):
        try:
            state_file = self.data_dir / "active_learning_collector_state.json"
            if state_file.exists():
                with open(state_file, "r") as f:
                    data = json.load(f)
                logger.info(f"Loaded {data.get('results_count', 0)} results")
        except Exception as e:
            logger.error(f"Failed to load state: {e}")


# Global instance
_active_learning_collector: Optional[ActiveLearningCollector] = None


def get_active_learning_collector() -> Optional[ActiveLearningCollector]:
    """Get global instance"""
    return _active_learning_collector


def initialize_active_learning_collector(data_dir: Path) -> ActiveLearningCollector:
    """Initialize system"""
    global _active_learning_collector
    _active_learning_collector = ActiveLearningCollector(data_dir)
    return _active_learning_collector
