"""
Performance logger that records latency and resource metrics.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List, Optional

try:
    import psutil
except Exception:  # pragma: no cover - psutil should exist but fall back gracefully
    psutil = None

from plugins.logging.base import JsonLogStore


class PerformanceLogger:
    """
    Observability helper that tracks operation duration, CPU, and memory usage.
    """

    def __init__(self, log_dir: str = "logs/performance", process: Optional[Any] = None):
        self.log_dir = Path(log_dir)
        self.store = JsonLogStore(self.log_dir / "performance_metrics.jsonl")
        if process is not None:
            self.process = process
        else:
            if psutil is None:
                raise RuntimeError("psutil is required for PerformanceLogger")
            self.process = psutil.Process()

    def record_metric(
        self,
        name: str,
        value: float,
        unit: str = "ms",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Persist a metric entry."""
        record = {
            "type": "metric",
            "timestamp": time.time(),
            "name": name,
            "value": value,
            "unit": unit,
            "tags": tags or [],
            "metadata": metadata or {},
        }
        self.store.append(record)
        return record

    @contextmanager
    def track_operation(
        self,
        name: str,
        tags: Optional[List[str]] = None,
        threshold_ms: Optional[float] = None,
    ):
        """Context manager for automatically logging performance of a block."""
        start = time.perf_counter()
        start_cpu = self._cpu_time()
        start_memory = self._rss_bytes()
        try:
            yield
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            cpu_delta = self._cpu_time() - start_cpu
            mem_delta = self._rss_bytes() - start_memory
            metadata = {
                "cpu_time": round(cpu_delta, 6),
                "rss_delta": mem_delta,
                "threshold_ms": threshold_ms,
            }
            record = self.record_metric(
                name=name,
                value=round(duration_ms, 3),
                unit="ms",
                tags=tags,
                metadata=metadata,
            )
            if threshold_ms and duration_ms > threshold_ms:
                record["alert"] = "slow_operation"
                self.store.append(
                    {
                        "type": "alert",
                        "name": name,
                        "timestamp": record["timestamp"],
                        "value": record["value"],
                        "message": f"{name} exceeded {threshold_ms} ms",
                    }
                )

    def summary(self, metric_name: Optional[str] = None) -> Dict[str, Any]:
        """Compute summary statistics for recorded metrics."""
        records = [
            entry
            for entry in self.store.iter_records()
            if entry.get("type") == "metric"
            and (metric_name is None or entry.get("name") == metric_name)
        ]
        if not records:
            return {}

        values = [entry["value"] for entry in records]
        return {
            "count": len(values),
            "avg": mean(values),
            "max": max(values),
            "min": min(values),
            "unit": records[0].get("unit", "ms"),
        }

    def _cpu_time(self) -> float:
        cpu = self.process.cpu_times()
        user = getattr(cpu, "user", 0.0)
        system = getattr(cpu, "system", 0.0)
        return float(user) + float(system)

    def _rss_bytes(self) -> int:
        mem = self.process.memory_info()
        return int(getattr(mem, "rss", 0))
