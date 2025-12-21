"""Minimal audit logger stub.

Writes audit events to a simple log file under the user's `.windows-ai` data
folder. Extend with structured logging or remote sinks as needed.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


class AuditLogger:
    def __init__(self, data_dir: str | Path | None = None) -> None:
        base = Path(data_dir) if data_dir else Path.home() / ".windows-ai"
        base.mkdir(parents=True, exist_ok=True)
        self.log_path = base / "audit.log"

    def log_event(self, event: str, details: Dict[str, Any] | None = None) -> None:
        record = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "event": event,
            "details": details or {},
        }
        line = json.dumps(record, ensure_ascii=True)
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")


__all__ = ["AuditLogger"]
