"""
Brain-Computer Interface Readiness Layer

Foundation for future brain-computer interface integration.
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
class BciInterfaceResult:
    """Result from BciInterface"""
    result_id: str
    status: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


class BciInterface:
    """
    BciInterface

    Brain-Computer Interface Readiness Layer
    """

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[BciInterfaceResult] = []
        self._load_state()
        logger.info("BciInterface initialized")

    def process(self, input_data: Dict[str, Any]) -> BciInterfaceResult:
        """Main processing function"""
        result = BciInterfaceResult(
            result_id=str(uuid.uuid4()),
            status="success",
            data={"processed": True, "input": input_data}
        )
        self.results.append(result)
        self._save_state()
        logger.info(f"Processed request in BciInterface")
        return result

    def get_results(self) -> List[BciInterfaceResult]:
        """Get all results"""
        return self.results

    def _save_state(self):
        try:
            data = {"results_count": len(self.results)}
            with open(self.data_dir / "bci_interface_state.json", "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def _load_state(self):
        try:
            state_file = self.data_dir / "bci_interface_state.json"
            if state_file.exists():
                with open(state_file, "r") as f:
                    data = json.load(f)
                logger.info(f"Loaded {data.get('results_count', 0)} results")
        except Exception as e:
            logger.error(f"Failed to load state: {e}")


# Global instance
_bci_interface: Optional[BciInterface] = None


def get_bci_interface() -> Optional[BciInterface]:
    """Get global instance"""
    return _bci_interface


def initialize_bci_interface(data_dir: Path) -> BciInterface:
    """Initialize system"""
    global _bci_interface
    _bci_interface = BciInterface(data_dir)
    return _bci_interface
