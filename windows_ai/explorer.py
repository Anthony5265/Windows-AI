"""AI helpers for Windows Explorer integration."""

from __future__ import annotations

import json
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

        The method inspects each file's size and extension before constructing
        the prompt sent to the underlying ``model``. The model should return a
        JSON string describing recommended actions for each file. Along with the
        per-file recommendations, a summary of the recommended actions is
        provided in the returned value.
        """

        file_info: List[Dict[str, Any]] = []
        for path in files:
            try:
                size = os.path.getsize(path)
                ext = os.path.splitext(path)[1]
            except OSError:
                # Skip files that cannot be accessed
                continue
            file_info.append({"name": path, "size": size, "extension": ext})

        prompt = json.dumps({"files": file_info})
        self._logs.append(prompt)

        response = self.model.generate(prompt)
        try:
            recommendations = json.loads(response)
        except json.JSONDecodeError:
            recommendations = []

        summary: Dict[str, int] = {}
        for item in recommendations:
            action = item.get("action")
            if action:
                summary[action] = summary.get(action, 0) + 1

        return {"recommendations": recommendations, "summary": summary}

    def get_logs(self) -> List[str]:
        """Return recorded prompts."""

        return list(self._logs)
