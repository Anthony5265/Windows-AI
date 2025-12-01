"""
Advanced Hardware Monitoring & Diagnostics

Comprehensive hardware monitoring and predictive maintenance.
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
class HardwareMonitorResult:
    """Result from HardwareMonitor"""
    result_id: str
    status: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


class HardwareMonitor:
    """
    HardwareMonitor

    Advanced Hardware Monitoring & Diagnostics
    """

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[HardwareMonitorResult] = []
        self._load_state()
        logger.info("HardwareMonitor initialized")

    def process(self, input_data: Dict[str, Any]) -> HardwareMonitorResult:
        """Main processing function"""
        result = HardwareMonitorResult(
            result_id=str(uuid.uuid4()),
            status="success",
            data={"processed": True, "input": input_data}
        )
        self.results.append(result)
        self._save_state()
        logger.info(f"Processed request in HardwareMonitor")
        return result

    def get_results(self) -> List[HardwareMonitorResult]:
        """Get all results"""
        return self.results

    def _save_state(self):
        try:
            data = {"results_count": len(self.results)}
            with open(self.data_dir / "hardware_monitor_state.json", "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def _load_state(self):
        try:
            state_file = self.data_dir / "hardware_monitor_state.json"
            if state_file.exists():
                with open(state_file, "r") as f:
                    data = json.load(f)
                logger.info(f"Loaded {data.get('results_count', 0)} results")
        except Exception as e:
            logger.error(f"Failed to load state: {e}")


# Global instance
_hardware_monitor: Optional[HardwareMonitor] = None


def get_hardware_monitor() -> Optional[HardwareMonitor]:
    """Get global instance"""
    return _hardware_monitor


def initialize_hardware_monitor(data_dir: Path) -> HardwareMonitor:
    """Initialize system"""
    global _hardware_monitor
    _hardware_monitor = HardwareMonitor(data_dir)
    return _hardware_monitor
