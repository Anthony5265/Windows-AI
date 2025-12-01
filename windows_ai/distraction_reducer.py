"""
AI-Driven Distraction Reduction

AI-driven focus modes that filter distractions.
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
class DistractionReducerResult:
    """Result from DistractionReducer"""
    result_id: str
    status: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


class DistractionReducer:
    """
    DistractionReducer

    AI-Driven Distraction Reduction
    """

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[DistractionReducerResult] = []
        self._load_state()
        logger.info("DistractionReducer initialized")

    def process(self, input_data: Dict[str, Any]) -> DistractionReducerResult:
        """Main processing function"""
        result = DistractionReducerResult(
            result_id=str(uuid.uuid4()),
            status="success",
            data={"processed": True, "input": input_data}
        )
        self.results.append(result)
        self._save_state()
        logger.info(f"Processed request in DistractionReducer")
        return result

    def get_results(self) -> List[DistractionReducerResult]:
        """Get all results"""
        return self.results

    def _save_state(self):
        try:
            data = {"results_count": len(self.results)}
            with open(self.data_dir / "distraction_reducer_state.json", "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def _load_state(self):
        try:
            state_file = self.data_dir / "distraction_reducer_state.json"
            if state_file.exists():
                with open(state_file, "r") as f:
                    data = json.load(f)
                logger.info(f"Loaded {data.get('results_count', 0)} results")
        except Exception as e:
            logger.error(f"Failed to load state: {e}")


# Global instance
_distraction_reducer: Optional[DistractionReducer] = None


def get_distraction_reducer() -> Optional[DistractionReducer]:
    """Get global instance"""
    return _distraction_reducer


def initialize_distraction_reducer(data_dir: Path) -> DistractionReducer:
    """Initialize system"""
    global _distraction_reducer
    _distraction_reducer = DistractionReducer(data_dir)
    return _distraction_reducer
