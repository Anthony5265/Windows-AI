"""AI helpers for Windows Task Manager integration."""

from __future__ import annotations

from typing import List, Any

import psutil


class TaskManagerAI:
    """Small helper that analyzes process lists via a model."""

    def __init__(self, model: Any):
        self.model = model
        self._queries: List[str] = []

    def analyze_processes(self, processes: List[str]) -> str:
        """Return model analysis for the provided process names."""

        # Gather CPU and memory metrics for each requested process name
        metrics = {}
        for proc in psutil.process_iter(["name"]):
            name = proc.info.get("name")
            if name in processes and name not in metrics:
                try:
                    cpu = proc.cpu_percent(interval=None)
                except Exception:
                    cpu = 0.0
                try:
                    mem = proc.memory_percent()
                except Exception:
                    mem = 0.0
                metrics[name] = (cpu, mem)

        parts = []
        for name in processes:
            cpu, mem = metrics.get(name, (0.0, 0.0))
            parts.append(f"{name} (cpu={cpu:.1f}, mem={mem:.1f})")

        prompt = "analyze: " + ", ".join(parts)
        self._queries.append(prompt)
        return self.model.generate(prompt)

    def get_queries(self) -> List[str]:
        """Return recorded queries."""

        return list(self._queries)
