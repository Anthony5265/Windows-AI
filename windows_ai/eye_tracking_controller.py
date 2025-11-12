"""
Eye-Tracking Control System

Control system through eye movements and gaze.
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
class EyeTrackingControllerResult:
    """Result from EyeTrackingController"""
    result_id: str
    status: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


class EyeTrackingController:
    """
    EyeTrackingController

    Eye-Tracking Control System
    """

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[EyeTrackingControllerResult] = []
        self._load_state()
        logger.info("EyeTrackingController initialized")

    def process(self, input_data: Dict[str, Any]) -> EyeTrackingControllerResult:
        """Main processing function"""
        result = EyeTrackingControllerResult(
            result_id=str(uuid.uuid4()),
            status="success",
            data={"processed": True, "input": input_data}
        )
        self.results.append(result)
        self._save_state()
        logger.info(f"Processed request in EyeTrackingController")
        return result

    def get_results(self) -> List[EyeTrackingControllerResult]:
        """Get all results"""
        return self.results

    def _save_state(self):
        try:
            data = {"results_count": len(self.results)}
            with open(self.data_dir / "eye_tracking_controller_state.json", "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def _load_state(self):
        try:
            state_file = self.data_dir / "eye_tracking_controller_state.json"
            if state_file.exists():
                with open(state_file, "r") as f:
                    data = json.load(f)
                logger.info(f"Loaded {data.get('results_count', 0)} results")
        except Exception as e:
            logger.error(f"Failed to load state: {e}")


# Global instance
_eye_tracking_controller: Optional[EyeTrackingController] = None


def get_eye_tracking_controller() -> Optional[EyeTrackingController]:
    """Get global instance"""
    return _eye_tracking_controller


def initialize_eye_tracking_controller(data_dir: Path) -> EyeTrackingController:
    """Initialize system"""
    global _eye_tracking_controller
    _eye_tracking_controller = EyeTrackingController(data_dir)
    return _eye_tracking_controller
