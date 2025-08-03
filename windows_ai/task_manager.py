"""AI helpers for Windows Task Manager integration."""

from __future__ import annotations

from typing import List, Any


class TaskManagerAI:
    """Small helper that analyzes process lists via a model."""

    def __init__(self, model: Any):
        self.model = model
        self._queries: List[str] = []

    def analyze_processes(self, processes: List[str]) -> str:
        """Return model analysis for the provided process names."""

        prompt = "analyze: " + ", ".join(processes)
        self._queries.append(prompt)
        return self.model.generate(prompt)

    def get_queries(self) -> List[str]:
        """Return recorded queries."""

        return list(self._queries)
