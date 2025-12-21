"""Rollback automation shim.

This delegates to the core rollback utilities in `windows_ai.security.rollback`
and provides a convenience helper to register filesystem cleanups.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from windows_ai.security.rollback import RollbackManager as CoreRollbackManager


class RollbackManager(CoreRollbackManager):
    def add_file_cleanup(self, path: str | Path) -> None:
        target = Path(path)

        def _cleanup() -> None:
            try:
                if target.is_file():
                    target.unlink(missing_ok=True)
                elif target.is_dir():
                    for child in target.rglob("*"):
                        if child.is_file():
                            child.unlink(missing_ok=True)
                    target.rmdir()
            except Exception:
                # Best-effort cleanup
                pass

        self.add(_cleanup)


__all__ = ["RollbackManager", "CoreRollbackManager"]
