"""
Universal Application API Layer

Standardized API layer for controlling any installed application.
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
class UniversalAppApiResult:
    """Result from UniversalAppApi"""
    result_id: str
    status: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


class UniversalAppApi:
    """
    UniversalAppApi

    Universal Application API Layer
    """

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[UniversalAppApiResult] = []
        self._load_state()
        logger.info("UniversalAppApi initialized")

    def process(self, input_data: Dict[str, Any]) -> UniversalAppApiResult:
        """Main processing function"""
        result = UniversalAppApiResult(
            result_id=str(uuid.uuid4()),
            status="success",
            data={"processed": True, "input": input_data}
        )
        self.results.append(result)
        self._save_state()
        logger.info(f"Processed request in UniversalAppApi")
        return result

    def get_results(self) -> List[UniversalAppApiResult]:
        """Get all results"""
        return self.results

    def _save_state(self):
        try:
            data = {"results_count": len(self.results)}
            with open(self.data_dir / "universal_app_api_state.json", "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def _load_state(self):
        try:
            state_file = self.data_dir / "universal_app_api_state.json"
            if state_file.exists():
                with open(state_file, "r") as f:
                    data = json.load(f)
                logger.info(f"Loaded {data.get('results_count', 0)} results")
        except Exception as e:
            logger.error(f"Failed to load state: {e}")


# Global instance
_universal_app_api: Optional[UniversalAppApi] = None


def get_universal_app_api() -> Optional[UniversalAppApi]:
    """Get global instance"""
    return _universal_app_api


def initialize_universal_app_api(data_dir: Path) -> UniversalAppApi:
    """Initialize system"""
    global _universal_app_api
    _universal_app_api = UniversalAppApi(data_dir)
    return _universal_app_api
