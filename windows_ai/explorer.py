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

    def suggest_cleanup(self, files: List[str]) -> List[Dict[str, Any]]:
        """Return model suggestions for cleaning up *files*.

        The method collects basic metadata for each file and sends it to the
        underlying ``model`` as a JSON encoded prompt. The expected model
        response is a JSON string describing recommended actions for each file.
        The parsed response is returned to callers as native Python objects.
        """

        file_info: List[Dict[str, Any]] = []
        for path in files:
            size = os.path.getsize(path)
            ext = os.path.splitext(path)[1]
            file_info.append({"name": path, "size": size, "extension": ext})

        prompt = json.dumps({"files": file_info})
        self._logs.append(prompt)

        response = self.model.generate(prompt)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return []

    def get_logs(self) -> List[str]:
        """Return recorded prompts."""

        return list(self._logs)
