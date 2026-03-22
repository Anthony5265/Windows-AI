"""API Performance Profiler Middleware.

Tracks per-endpoint response times, memory usage, and request throughput
to help meet the <200ms p95 latency target and <500MB idle memory target.
"""

from __future__ import annotations

import logging
import os
import statistics
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

try:
    import psutil
except ImportError:
    psutil = None

logger = logging.getLogger(__name__)


@dataclass
class EndpointStats:
    """Per-endpoint latency and throughput statistics."""
    path: str
    method: str
    request_count: int = 0
    error_count: int = 0
    total_time_ms: float = 0.0
    min_time_ms: float = float("inf")
    max_time_ms: float = 0.0
    _latencies: List[float] = field(default_factory=list, repr=False)

    def record(self, latency_ms: float, is_error: bool = False) -> None:
        self.request_count += 1
        self.total_time_ms += latency_ms
        self.min_time_ms = min(self.min_time_ms, latency_ms)
        self.max_time_ms = max(self.max_time_ms, latency_ms)
        self._latencies.append(latency_ms)
        if is_error:
            self.error_count += 1
        # Keep only last 1000 latencies to bound memory
        if len(self._latencies) > 1000:
            self._latencies = self._latencies[-1000:]

    @property
    def avg_time_ms(self) -> float:
        return round(self.total_time_ms / max(self.request_count, 1), 2)

    @property
    def p50_ms(self) -> float:
        if not self._latencies:
            return 0.0
        sorted_lat = sorted(self._latencies)
        idx = int(len(sorted_lat) * 0.5)
        return round(sorted_lat[idx], 2)

    @property
    def p95_ms(self) -> float:
        if not self._latencies:
            return 0.0
        sorted_lat = sorted(self._latencies)
        idx = min(int(len(sorted_lat) * 0.95), len(sorted_lat) - 1)
        return round(sorted_lat[idx], 2)

    @property
    def p99_ms(self) -> float:
        if not self._latencies:
            return 0.0
        sorted_lat = sorted(self._latencies)
        idx = min(int(len(sorted_lat) * 0.99), len(sorted_lat) - 1)
        return round(sorted_lat[idx], 2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "method": self.method,
            "request_count": self.request_count,
            "error_count": self.error_count,
            "avg_ms": self.avg_time_ms,
            "min_ms": round(self.min_time_ms, 2) if self.min_time_ms != float("inf") else 0,
            "max_ms": round(self.max_time_ms, 2),
            "p50_ms": self.p50_ms,
            "p95_ms": self.p95_ms,
            "p99_ms": self.p99_ms,
        }


class APIProfiler:
    """Collects API performance metrics.

    Usage::

        profiler = APIProfiler()

        # In middleware or route handler:
        profiler.record_request("/api/chat", "POST", latency_ms=42.5)

        # Query stats:
        summary = profiler.get_summary()
        slow = profiler.get_slow_endpoints(threshold_ms=200)
    """

    def __init__(self):
        self._endpoints: Dict[str, EndpointStats] = {}
        self._start_time = time.time()
        self._total_requests = 0

    def record_request(
        self,
        path: str,
        method: str = "GET",
        latency_ms: float = 0.0,
        status_code: int = 200,
    ) -> None:
        """Record a completed request."""
        key = f"{method}:{path}"
        if key not in self._endpoints:
            self._endpoints[key] = EndpointStats(path=path, method=method)
        self._endpoints[key].record(latency_ms, is_error=(status_code >= 400))
        self._total_requests += 1

    def get_endpoint_stats(self, path: str, method: str = "GET") -> Optional[Dict[str, Any]]:
        """Get stats for a specific endpoint."""
        key = f"{method}:{path}"
        ep = self._endpoints.get(key)
        return ep.to_dict() if ep else None

    def get_all_endpoints(self) -> List[Dict[str, Any]]:
        """Get stats for all endpoints."""
        return [ep.to_dict() for ep in self._endpoints.values()]

    def get_slow_endpoints(self, threshold_ms: float = 200.0) -> List[Dict[str, Any]]:
        """Get endpoints whose p95 exceeds *threshold_ms*."""
        return [
            ep.to_dict()
            for ep in self._endpoints.values()
            if ep.p95_ms > threshold_ms
        ]

    def get_summary(self) -> Dict[str, Any]:
        """Get an overall performance summary."""
        all_latencies = []
        for ep in self._endpoints.values():
            all_latencies.extend(ep._latencies)

        uptime = time.time() - self._start_time
        rps = self._total_requests / max(uptime, 1)

        summary = {
            "total_requests": self._total_requests,
            "unique_endpoints": len(self._endpoints),
            "uptime_seconds": round(uptime, 1),
            "requests_per_second": round(rps, 2),
        }

        if all_latencies:
            sorted_lat = sorted(all_latencies)
            summary["global_avg_ms"] = round(statistics.mean(sorted_lat), 2)
            summary["global_p50_ms"] = round(sorted_lat[int(len(sorted_lat) * 0.5)], 2)
            summary["global_p95_ms"] = round(sorted_lat[min(int(len(sorted_lat) * 0.95), len(sorted_lat) - 1)], 2)
            summary["global_p99_ms"] = round(sorted_lat[min(int(len(sorted_lat) * 0.99), len(sorted_lat) - 1)], 2)

        return summary

    def get_memory_usage(self) -> Dict[str, Any]:
        """Get current process memory usage."""
        if psutil is None:
            return {"status": "unavailable", "message": "psutil not installed"}
        try:
            proc = psutil.Process(os.getpid())
            mem = proc.memory_info()
            return {
                "status": "success",
                "rss_mb": round(mem.rss / (1024 * 1024), 2),
                "vms_mb": round(mem.vms / (1024 * 1024), 2),
                "percent": round(proc.memory_percent(), 2),
                "target_idle_mb": 500,
                "within_target": mem.rss / (1024 * 1024) < 500,
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def reset(self) -> None:
        """Reset all collected metrics."""
        self._endpoints.clear()
        self._total_requests = 0
        self._start_time = time.time()
