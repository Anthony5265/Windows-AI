"""AI helpers for Windows Task Manager integration."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import psutil


class TaskManagerAI:
    """Small helper that analyzes process lists via a model."""

    def __init__(self, model: Any):
        self.model = model
        self._queries: List[str] = []

    def analyze_processes(self, processes: List[str]) -> str:
        """Return model analysis for the provided process names."""

        metrics: Dict[str, Tuple[float, float]] = {}
        try:
            for proc in psutil.process_iter(["name"]):
                name = proc.info.get("name")
                if name in processes and name not in metrics:
                    try:
                        cpu = proc.cpu_percent(interval=None)
                        mem = proc.memory_info().rss / (1024 * 1024)
                    except Exception:
                        cpu = 0.0
                        mem = 0.0
                    metrics[name] = (cpu, mem)
                    if len(metrics) == len(processes):
                        break
        except Exception:
            pass

        details = []
        for name in processes:
            cpu, mem = metrics.get(name, (0.0, 0.0))
            details.append(f"{name} (cpu={cpu:.1f}%, mem={mem:.1f}MB)")

        prompt = "analyze: " + ", ".join(details)
        self._queries.append(prompt)
        return self.model.generate(prompt)

    def get_queries(self) -> List[str]:
        """Return recorded queries."""

        return list(self._queries)
