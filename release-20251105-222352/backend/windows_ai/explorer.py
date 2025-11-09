"""AI helpers for Windows Explorer integration."""

from __future__ import annotations

import collections
import json
import os
from typing import Any, Dict, List


class CleanupResult(dict):
    """Mapping wrapper that is also comparable to a list of recommendations."""

    def __init__(self, recommendations: List[Dict[str, Any]], summary: Dict[str, int]) -> None:
        rec_copy = [dict(item) for item in recommendations]
        summary_copy = dict(summary)
        super().__init__(recommendations=rec_copy, summary=summary_copy)
        self._recommendations = rec_copy
        self._summary = summary_copy

    def __getitem__(self, key):  # type: ignore[override]
        if key == "recommendations":
            return list(self._recommendations)
        if key == "summary":
            return dict(self._summary)
        return super().__getitem__(key)

    def get(self, key, default=None):  # type: ignore[override]
        if key == "recommendations":
            return list(self._recommendations)
        if key == "summary":
            return dict(self._summary)
        return super().get(key, default)

    def __eq__(self, other):  # type: ignore[override]
        if isinstance(other, list):
            return self._recommendations == other
        return dict.__eq__(self, other)

    def __repr__(self) -> str:
        return (
            f"CleanupResult(recommendations={self._recommendations!r}, "
            f'summary={self._summary!r})'
        )


class ExplorerAI:
    """Simple AI utility for working with file explorer data.

    The class is intentionally small and framework agnostic.  It records
    prompts sent to the supplied ``model`` allowing tests to assert that
    interactions occurred without needing a real language model.
    """

    def __init__(self, model: Any):
        self.model = model
        self._logs: List[str] = []

    def suggest_cleanup(self, files: List[str]) -> CleanupResult:
        """Return model suggestions for cleaning up *files*.

        The method inspects each file's size and extension before constructing
        the prompt sent to the underlying ``model``. The model should return a
        JSON string describing recommended actions for each file. Along with the
        per-file recommendations, a summary of the recommended actions is
        provided in the returned value.
        """

        file_info: List[Dict[str, Any]] = []
        for path in files:
            # Collect metadata up front so it's available for prompting and
            # for the structured summary returned to callers.
            size = os.path.getsize(path)
            ext = os.path.splitext(path)[1]
            file_info.append({"name": path, "size": size, "extension": ext})

        prompt = json.dumps({"files": file_info})
        self._logs.append(prompt)

        response = self.model.generate(prompt)
        try:
            model_data = json.loads(response)
        except json.JSONDecodeError:
            model_data = []

        # Map the model's recommended action by file name for quick lookup.
        actions = {item.get("name"): item.get("action") for item in model_data if isinstance(item, dict)}

        recommendations: List[Dict[str, Any]] = []
        for info in file_info:
            recommendations.append(
                {
                    "name": info["name"],
                    "size": info["size"],
                    "extension": info["extension"],
                    "action": actions.get(info["name"], "none"),
                }
            )

        summary = collections.Counter(r['action'] for r in recommendations)
        return CleanupResult(recommendations, summary)

    def get_logs(self) -> List[str]:
        """Return recorded prompts."""

        return list(self._logs)