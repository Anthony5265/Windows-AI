"""Augmented-reality overlay state and processing facade."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import os
import tempfile
from typing import Any, Dict, List, Optional
import uuid

logger = logging.getLogger(__name__)
_STATE_VERSION = 1


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class ArOverlaySystemResult:
    """Result from an AR overlay operation."""

    result_id: str
    status: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=_utc_now)

    def to_dict(self) -> Dict[str, Any]:
        value = asdict(self)
        value["timestamp"] = self.timestamp.isoformat()
        return value


class ArOverlaySystem:
    """Record deterministic overlay requests and retain their complete results."""

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir).expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if not self.data_dir.is_dir():
            raise ValueError(f"data_dir must be a directory: {self.data_dir}")
        self._state_file = self.data_dir / "ar_overlay_system_state.json"
        self.results: List[ArOverlaySystemResult] = []
        self._load_state()
        logger.info("ArOverlaySystem initialized")

    def process(self, input_data: Dict[str, Any]) -> ArOverlaySystemResult:
        """Process and record an overlay request without mutating caller data."""
        if not isinstance(input_data, dict):
            raise TypeError("input_data must be a dictionary")

        result = ArOverlaySystemResult(
            result_id=str(uuid.uuid4()),
            status="success",
            data={"processed": True, "input": dict(input_data)},
        )
        self.results.append(result)
        self._save_state()
        return result

    def get_results(self) -> List[ArOverlaySystemResult]:
        """Return a snapshot of recorded results."""
        return list(self.results)

    def _save_state(self) -> None:
        payload = {
            "version": _STATE_VERSION,
            "results": [result.to_dict() for result in self.results],
        }
        self.data_dir.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=".ar_overlay.", dir=self.data_dir, text=True)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2, ensure_ascii=False)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self._state_file)
        except Exception:
            try:
                os.unlink(temporary)
            except OSError:
                pass
            raise

    def _load_state(self) -> None:
        if not self._state_file.exists():
            return
        try:
            with self._state_file.open("r", encoding="utf-8") as handle:
                state = json.load(handle)
            if state.get("version") != _STATE_VERSION:
                logger.warning("Ignoring unsupported AR overlay state version")
                return
            loaded: List[ArOverlaySystemResult] = []
            for item in state.get("results", []):
                timestamp = datetime.fromisoformat(item["timestamp"])
                loaded.append(ArOverlaySystemResult(
                    result_id=str(item["result_id"]),
                    status=str(item["status"]),
                    data=dict(item.get("data", {})),
                    timestamp=timestamp,
                ))
            self.results = loaded
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            logger.warning("Ignoring invalid AR overlay state: %s", exc)


_ar_overlay_system: Optional[ArOverlaySystem] = None


def get_ar_overlay_system() -> Optional[ArOverlaySystem]:
    """Get the initialized global instance, if one exists."""
    return _ar_overlay_system


def initialize_ar_overlay_system(data_dir: Path) -> ArOverlaySystem:
    """Initialize and replace the process-local global instance."""
    global _ar_overlay_system
    _ar_overlay_system = ArOverlaySystem(data_dir)
    return _ar_overlay_system
