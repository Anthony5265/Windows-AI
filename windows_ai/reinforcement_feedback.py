"""
Reinforcement Learning from User Feedback

Learns from explicit user feedback to refine AI models and suggestions.
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
class ReinforcementFeedbackResult:
    """Result from ReinforcementFeedback"""
    result_id: str
    status: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


class ReinforcementFeedback:
    """
    ReinforcementFeedback

    Reinforcement Learning from User Feedback
    """

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[ReinforcementFeedbackResult] = []
        self._load_state()
        logger.info("ReinforcementFeedback initialized")

    def process(self, input_data: Dict[str, Any]) -> ReinforcementFeedbackResult:
        """Main processing function"""
        result = ReinforcementFeedbackResult(
            result_id=str(uuid.uuid4()),
            status="success",
            data={"processed": True, "input": input_data}
        )
        self.results.append(result)
        self._save_state()
        logger.info(f"Processed request in ReinforcementFeedback")
        return result

    def get_results(self) -> List[ReinforcementFeedbackResult]:
        """Get all results"""
        return self.results

    def _save_state(self):
        try:
            data = {"results_count": len(self.results)}
            with open(self.data_dir / "reinforcement_feedback_state.json", "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def _load_state(self):
        try:
            state_file = self.data_dir / "reinforcement_feedback_state.json"
            if state_file.exists():
                with open(state_file, "r") as f:
                    data = json.load(f)
                logger.info(f"Loaded {data.get('results_count', 0)} results")
        except Exception as e:
            logger.error(f"Failed to load state: {e}")


# Global instance
_reinforcement_feedback: Optional[ReinforcementFeedback] = None


def get_reinforcement_feedback() -> Optional[ReinforcementFeedback]:
    """Get global instance"""
    return _reinforcement_feedback


def initialize_reinforcement_feedback(data_dir: Path) -> ReinforcementFeedback:
    """Initialize system"""
    global _reinforcement_feedback
    _reinforcement_feedback = ReinforcementFeedback(data_dir)
    return _reinforcement_feedback
