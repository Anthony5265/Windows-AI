"""System performance analysis and optimization helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List
import platform

try:  # pragma: no cover - optional dependency
    import psutil  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    psutil = None  # type: ignore[assignment]

__all__ = ["SystemMetrics", "SystemOptimizer"]


@dataclass
class SystemMetrics:
    """Basic hardware and OS statistics."""

    cpu_percent: float | None
    memory_percent: float | None
    disk_percent: float | None
    os: str


class SystemOptimizer:
    """Collect system metrics and recommend performance tweaks."""

    def collect_metrics(self) -> SystemMetrics:
        """Return current system metrics.

        Values may be ``None`` when the required APIs are not available.
        """

        cpu = mem = disk = None
        if psutil:
            try:
                cpu = psutil.cpu_percent(interval=0.1)
                mem = psutil.virtual_memory().percent
                disk = psutil.disk_usage("/").percent
            except Exception:
                pass
        os_name = platform.platform()
        return SystemMetrics(cpu, mem, disk, os_name)

    def recommend_tweaks(self, metrics: SystemMetrics) -> List[str]:
        """Return a list of suggested performance optimizations."""

        recs: List[str] = []
        if metrics.cpu_percent is not None and metrics.cpu_percent > 85:
            recs.append("High CPU usage detected; close background applications.")
        if metrics.memory_percent is not None and metrics.memory_percent > 90:
            recs.append("Memory usage is high; consider closing apps or upgrading RAM.")
        if metrics.disk_percent is not None and metrics.disk_percent > 90:
            recs.append("Disk nearly full; clean temporary files or expand storage.")
        if not recs:
            recs.append("System performance within normal ranges.")
        return recs
