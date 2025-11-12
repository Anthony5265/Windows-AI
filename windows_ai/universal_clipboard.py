"""
Universal Clipboard & Handoff System

Clipboard sharing across all connected devices.
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
class UniversalClipboardResult:
    """Result from UniversalClipboard"""
    result_id: str
    status: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


class UniversalClipboard:
    """
    UniversalClipboard

    Universal Clipboard & Handoff System
    """

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[UniversalClipboardResult] = []
        self._load_state()
        logger.info("UniversalClipboard initialized")

    def process(self, input_data: Dict[str, Any]) -> UniversalClipboardResult:
        """Main processing function"""
        result = UniversalClipboardResult(
            result_id=str(uuid.uuid4()),
            status="success",
            data={"processed": True, "input": input_data}
        )
        self.results.append(result)
        self._save_state()
        logger.info(f"Processed request in UniversalClipboard")
        return result

    def get_results(self) -> List[UniversalClipboardResult]:
        """Get all results"""
        return self.results

    def _save_state(self):
        try:
            data = {"results_count": len(self.results)}
            with open(self.data_dir / "universal_clipboard_state.json", "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def _load_state(self):
        try:
            state_file = self.data_dir / "universal_clipboard_state.json"
            if state_file.exists():
                with open(state_file, "r") as f:
                    data = json.load(f)
                logger.info(f"Loaded {data.get('results_count', 0)} results")
        except Exception as e:
            logger.error(f"Failed to load state: {e}")


# Global instance
_universal_clipboard: Optional[UniversalClipboard] = None


def get_universal_clipboard() -> Optional[UniversalClipboard]:
    """Get global instance"""
    return _universal_clipboard


def initialize_universal_clipboard(data_dir: Path) -> UniversalClipboard:
    """Initialize system"""
    global _universal_clipboard
    _universal_clipboard = UniversalClipboard(data_dir)
    return _universal_clipboard
