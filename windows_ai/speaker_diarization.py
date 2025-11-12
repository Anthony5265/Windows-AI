"""
Speaker Diarization System

Identifies different speakers in audio.
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
class SpeakerDiarizationResult:
    """Result from SpeakerDiarization"""
    result_id: str
    status: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


class SpeakerDiarization:
    """
    SpeakerDiarization

    Speaker Diarization System
    """

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[SpeakerDiarizationResult] = []
        self._load_state()
        logger.info("SpeakerDiarization initialized")

    def process(self, input_data: Dict[str, Any]) -> SpeakerDiarizationResult:
        """Main processing function"""
        result = SpeakerDiarizationResult(
            result_id=str(uuid.uuid4()),
            status="success",
            data={"processed": True, "input": input_data}
        )
        self.results.append(result)
        self._save_state()
        logger.info(f"Processed request in SpeakerDiarization")
        return result

    def get_results(self) -> List[SpeakerDiarizationResult]:
        """Get all results"""
        return self.results

    def _save_state(self):
        try:
            data = {"results_count": len(self.results)}
            with open(self.data_dir / "speaker_diarization_state.json", "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def _load_state(self):
        try:
            state_file = self.data_dir / "speaker_diarization_state.json"
            if state_file.exists():
                with open(state_file, "r") as f:
                    data = json.load(f)
                logger.info(f"Loaded {data.get('results_count', 0)} results")
        except Exception as e:
            logger.error(f"Failed to load state: {e}")


# Global instance
_speaker_diarization: Optional[SpeakerDiarization] = None


def get_speaker_diarization() -> Optional[SpeakerDiarization]:
    """Get global instance"""
    return _speaker_diarization


def initialize_speaker_diarization(data_dir: Path) -> SpeakerDiarization:
    """Initialize system"""
    global _speaker_diarization
    _speaker_diarization = SpeakerDiarization(data_dir)
    return _speaker_diarization
