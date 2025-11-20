"""
Archive and compress historical log files.
"""

from __future__ import annotations

import gzip
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional


class LogArchiver:
    """
    Moves old logs into an archive directory and optionally compresses them.
    """

    def __init__(
        self,
        source_dir: str = "logs",
        archive_dir: str = "logs/archive",
        default_max_age_days: int = 7,
    ) -> None:
        self.source_dir = Path(source_dir)
        self.archive_dir = Path(archive_dir)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        self.default_max_age_days = default_max_age_days

    def archive(self, max_age_days: Optional[int] = None, compress: bool = True) -> List[Path]:
        """
        Move files older than ``max_age_days`` into the archive directory.
        Returns a list of archived paths (post-move).
        """
        threshold = datetime.now() - timedelta(days=max_age_days or self.default_max_age_days)
        archived: List[Path] = []

        for path in self.source_dir.rglob("*"):
            if not path.is_file():
                continue
            if self._is_active_log(path):
                continue
            if datetime.fromtimestamp(path.stat().st_mtime) > threshold:
                continue

            destination = self.archive_dir / path.relative_to(self.source_dir)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(path), str(destination))
            if compress and destination.suffix not in {".gz", ".zip"}:
                destination = self._compress(destination)
            archived.append(destination)

        return archived

    def list_archives(self) -> List[Path]:
        """Return archived log files sorted by modification time."""
        archives = [p for p in self.archive_dir.rglob("*") if p.is_file()]
        return sorted(archives, key=lambda p: p.stat().st_mtime, reverse=True)

    def cleanup_archives(self, max_total_gb: float = 5.0) -> None:
        """
        Keep archive storage usage under ``max_total_gb`` by deleting oldest files.
        """
        limit_bytes = max_total_gb * (1024**3)
        archives = self.list_archives()
        total = sum(p.stat().st_size for p in archives)
        for archive in reversed(archives):
            if total <= limit_bytes:
                break
            size = archive.stat().st_size
            archive.unlink(missing_ok=True)
            total -= size

    def _is_active_log(self, path: Path) -> bool:
        """Skip active log files (current compliance JSONL files, etc.)."""
        return path.suffix.lower() in {".lock", ".tmp"}

    def _compress(self, path: Path) -> Path:
        """Compress the log using gzip and remove the original."""
        compressed_path = path.with_suffix(path.suffix + ".gz")
        with path.open("rb") as source, gzip.open(compressed_path, "wb") as target:
            shutil.copyfileobj(source, target)
        path.unlink(missing_ok=True)
        return compressed_path
