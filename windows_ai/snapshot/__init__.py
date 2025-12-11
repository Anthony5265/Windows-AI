from __future__ import annotations

"""Configuration snapshot utilities for per-feature rollback.

This lightweight module stores copies of configuration files or directories
before they are modified. Each snapshot is keyed by a feature name allowing
individual rollback without affecting unrelated components.
"""

from pathlib import Path
import json
import shutil


SNAPSHOT_DIR = Path.home() / ".windows_ai" / "snapshots"
INDEX_FILE = SNAPSHOT_DIR / "index.json"


def _load_index() -> dict[str, str]:
    if INDEX_FILE.exists():
        try:
            return json.loads(INDEX_FILE.read_text())
        except Exception:
            return {}
    return {}


def _save_index(index: dict[str, str]) -> None:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(json.dumps(index, indent=2))


def capture(feature: str, path: Path | str) -> Path:
    """Capture the current state of ``path`` for ``feature``.

    Any existing snapshot for the feature is replaced. A copy of ``path`` is
    stored inside :data:`SNAPSHOT_DIR` and the original location is recorded in
    an index file so that :func:`rollback` knows where to restore it.
    """

    path = Path(path)
    dest = SNAPSHOT_DIR / feature
    if dest.exists():
        if dest.is_dir():
            shutil.rmtree(dest)
        else:
            dest.unlink()
    if path.exists():
        if path.is_dir():
            shutil.copytree(path, dest)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)
    else:
        dest.mkdir(parents=True, exist_ok=True)
    index = _load_index()
    index[feature] = str(path)
    _save_index(index)
    return dest


def rollback(feature: str) -> None:
    """Restore the configuration snapshot for ``feature`` if it exists."""

    index = _load_index()
    target = Path(index.get(feature, ""))
    backup = SNAPSHOT_DIR / feature
    if not backup.exists() or not target:
        return
    if target.exists():
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
    if backup.is_dir():
        shutil.copytree(backup, target, dirs_exist_ok=True)
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(backup, target)


def remove(feature: str) -> None:
    """Remove snapshot data for ``feature`` without restoring it."""

    backup = SNAPSHOT_DIR / feature
    if backup.exists():
        if backup.is_dir():
            shutil.rmtree(backup)
        else:
            backup.unlink()
    index = _load_index()
    if feature in index:
        del index[feature]
        _save_index(index)


__all__ = ["capture", "rollback", "remove", "SNAPSHOT_DIR"]
