"""
Log aggregation helpers: discover, merge, and summarise JSONL log sources.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional


class LogAggregator:
    """
    Aggregates JSON line logs scattered throughout the repository.
    """

    def __init__(self, sources: Optional[List[Path]] = None):
        self.sources: List[Path] = [Path(src) for src in sources or []]

    def register_source(self, path: Path) -> None:
        """Add a log file to the aggregation set."""
        normalized = Path(path)
        if normalized not in self.sources:
            self.sources.append(normalized)

    def discover(self, base_dir: Path, pattern: str = "*.jsonl") -> List[Path]:
        """Recursively find log files that match ``pattern``."""
        matches = [p for p in Path(base_dir).rglob(pattern) if p.is_file()]
        for match in matches:
            self.register_source(match)
        return matches

    def iter_records(self) -> Iterator[Dict[str, Any]]:
        """Yield records from all registered sources in chronological order."""
        for path in sorted(self.sources):
            if not path.exists():
                continue
            with path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        continue

    def tail(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Return the most recent ``limit`` records across all sources."""
        buffer: List[Dict[str, Any]] = []
        for record in self.iter_records():
            buffer.append(record)
            if len(buffer) > limit:
                buffer.pop(0)
        return buffer

    def summarize(self, field: str) -> Dict[str, int]:
        """Count occurrences of values across all records for ``field``."""
        counts: Dict[str, int] = {}
        for record in self.iter_records():
            value = record.get(field)
            if value is None:
                continue
            counts[str(value)] = counts.get(str(value), 0) + 1
        return counts

    def filter(self, **criteria: Any) -> List[Dict[str, Any]]:
        """
        Return records that match ``field=value`` criteria.
        Example: ``aggregator.filter(type=\"exception\", severity=\"high\")``.
        """
        matches: List[Dict[str, Any]] = []
        for record in self.iter_records():
            if all(record.get(key) == value for key, value in criteria.items()):
                matches.append(record)
        return matches
