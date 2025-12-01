"""
Universal IoT Protocol Adapter

Universal adapter for different IoT protocols.
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
class ProtocolAdapterResult:
    """Result from ProtocolAdapter"""
    result_id: str
    status: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


class ProtocolAdapter:
    """
    ProtocolAdapter

    Universal IoT Protocol Adapter
    """

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[ProtocolAdapterResult] = []
        self._load_state()
        logger.info("ProtocolAdapter initialized")

    def process(self, input_data: Dict[str, Any]) -> ProtocolAdapterResult:
        """Main processing function"""
        result = ProtocolAdapterResult(
            result_id=str(uuid.uuid4()),
            status="success",
            data={"processed": True, "input": input_data}
        )
        self.results.append(result)
        self._save_state()
        logger.info(f"Processed request in ProtocolAdapter")
        return result

    def get_results(self) -> List[ProtocolAdapterResult]:
        """Get all results"""
        return self.results

    def _save_state(self):
        try:
            data = {"results_count": len(self.results)}
            with open(self.data_dir / "protocol_adapter_state.json", "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def _load_state(self):
        try:
            state_file = self.data_dir / "protocol_adapter_state.json"
            if state_file.exists():
                with open(state_file, "r") as f:
                    data = json.load(f)
                logger.info(f"Loaded {data.get('results_count', 0)} results")
        except Exception as e:
            logger.error(f"Failed to load state: {e}")


# Global instance
_protocol_adapter: Optional[ProtocolAdapter] = None


def get_protocol_adapter() -> Optional[ProtocolAdapter]:
    """Get global instance"""
    return _protocol_adapter


def initialize_protocol_adapter(data_dir: Path) -> ProtocolAdapter:
    """Initialize system"""
    global _protocol_adapter
    _protocol_adapter = ProtocolAdapter(data_dir)
    return _protocol_adapter
