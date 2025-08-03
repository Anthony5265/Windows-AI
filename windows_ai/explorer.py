"""AI helpers for Windows Explorer integration."""

from __future__ import annotations

from typing import List, Any


class ExplorerAI:
    """Simple AI utility for working with file explorer data.

    The class is intentionally small and framework agnostic.  It records
    prompts sent to the supplied ``model`` allowing tests to assert that
    interactions occurred without needing a real language model.
    """

    def __init__(self, model: Any):
        self.model = model
        self._logs: List[str] = []

    def suggest_cleanup(self, files: List[str]) -> str:
        """Return model suggestions for cleaning up *files*.

        Parameters
        ----------
        files:
            A list of file names that might require clean up.
        """

        prompt = "cleanup: " + ", ".join(files)
        self._logs.append(prompt)
        return self.model.generate(prompt)

    def get_logs(self) -> List[str]:
        """Return recorded prompts."""

        return list(self._logs)
