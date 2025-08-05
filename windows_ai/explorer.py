"""AI helpers for Windows Explorer integration."""

from __future__ import annotations

import os
from typing import Any, Dict, List


class ExplorerAI:
    """Simple AI utility for working with file explorer data.

    The class is intentionally small and framework agnostic.  It records
    prompts sent to the supplied ``model`` allowing tests to assert that
    interactions occurred without needing a real language model.
    """

    def __init__(self, model: Any):
        self.model = model
        self._logs: List[str] = []

    def suggest_cleanup(self, files: List[str]) -> Dict[str, Any]:
        """Return model suggestions for cleaning up *files*.

        The function inspects file sizes and extensions to build a richer
        prompt and returns a summary of recommended actions for each file.

        Parameters
        ----------
        files:
            A list of file names that might require clean up.

        Returns
        -------
        Dict[str, Any]
            ``{"suggestion": str, "actions": Dict[str, str]}``
        """

        details: List[str] = []
        actions: Dict[str, str] = {}
        for path in files:
            size = os.path.getsize(path) if os.path.exists(path) else 0
            ext = os.path.splitext(path)[1].lower()
            if ext in {".tmp", ".log"}:
                action = "delete"
            elif size > 1_000_000:
                action = "compress"
            else:
                action = "none"
            actions[path] = action
            details.append(f"{path} ({size} bytes, {ext or 'no ext'})")

        prompt = "cleanup: " + ", ".join(details)
        self._logs.append(prompt)
        suggestion = self.model.generate(prompt)
        return {"suggestion": suggestion, "actions": actions}

    def get_logs(self) -> List[str]:
        """Return recorded prompts."""

        return list(self._logs)
