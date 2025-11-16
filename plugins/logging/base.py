"""
Shared helpers for advanced logging plugins.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional


class JsonLogStore:
    """
    Thread-safe JSON lines writer/reader used by logging plugins.
    """

    def __init__(self, log_path: Path):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def append(self, record: Dict[str, Any]) -> None:
        """Append a record to the log file."""
        serialized = json.dumps(record, default=str, ensure_ascii=False)
        with self._lock:
            with self.log_path.open("a", encoding="utf-8") as handle:
                handle.write(serialized + "\n")

    def iter_records(self) -> Iterator[Dict[str, Any]]:
        """Iterate over log records."""
        if not self.log_path.exists():
            return iter(())

        def _iterator() -> Iterator[Dict[str, Any]]:
            with self.log_path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        continue

        return _iterator()

    def read_all(self) -> List[Dict[str, Any]]:
        """Return all log records."""
        return list(self.iter_records())

    def last_record(self) -> Optional[Dict[str, Any]]:
        """Return the most recent log entry, if any."""
        last: Optional[Dict[str, Any]] = None
        for record in self.iter_records():
            last = record
        return last
