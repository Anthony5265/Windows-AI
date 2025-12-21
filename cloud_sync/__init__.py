"""Minimal cloud sync provider placeholder.

This stub ensures the PhaseTracker detects the cloud_sync integration while
providing a simple file-copy style sync hook that can be extended later.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable


class CloudSyncProvider:
    """Simple placeholder sync provider.

    This class can be extended to back cloud storage SDKs. For now it
    mirrors files between a source folder and a destination folder.
    """

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def sync(self, sources: Iterable[Path], destination: str | Path) -> None:
        dest = Path(destination)
        dest.mkdir(parents=True, exist_ok=True)
        for source in sources:
            if not source.exists() or not source.is_file():
                continue
            target = dest / source.name
            target.write_bytes(source.read_bytes())

    def pull(self, manifest: Iterable[str], destination: str | Path) -> None:
        dest = Path(destination)
        dest.mkdir(parents=True, exist_ok=True)
        for name in manifest:
            candidate = self.root / name
            if candidate.exists():
                (dest / name).write_bytes(candidate.read_bytes())


__all__ = ["CloudSyncProvider"]
