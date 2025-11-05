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
        """Return model analysis for the provided process names.

        For each requested ``process`` a tuple of ``(cpu, memory)`` usage is
        collected via :mod:`psutil`.  CPU usage is reported as a percentage and
        memory usage is reported in megabytes.  The metrics are embedded into
        the prompt that is passed to the model.
        """

        metrics: Dict[str, Tuple[float, float]] = {}
        try:
            # Gather CPU and memory information in a single iteration to reduce
            # psutil overhead.
            for proc in psutil.process_iter(["name", "cpu_percent", "memory_info"]):
                name = proc.info.get("name")
                if name in processes and name not in metrics:
                    info = proc.info
                    try:
                        cpu = float(info.get("cpu_percent") or 0.0)
                    except Exception:  # pragma: no cover - defensive
                        cpu = 0.0
                    try:
                        mem_info = info.get("memory_info")
                        mem = float(mem_info.rss) / (1024 * 1024) if mem_info else 0.0
                    except Exception:  # pragma: no cover - defensive
                        mem = 0.0
                    metrics[name] = (cpu, mem)
                    if len(metrics) == len(processes):
                        break
        except Exception:  # pragma: no cover - psutil may raise AccessDenied
            pass

        details: List[str] = []
        for name in processes:
            cpu, mem = metrics.get(name, (0.0, 0.0))
            details.append(f"{name} (cpu={cpu:.1f}%, mem={mem:.1f}MB)")

        prompt = "analyze: " + ", ".join(details)
        self._queries.append(prompt)
        return self.model.generate(prompt)

    def get_queries(self) -> List[str]:
        """Return recorded queries."""

        return list(self._queries)
