"""
Metrics Collection for Windows AI
Application-level counters, histograms, and gauges
"""
from __future__ import annotations

import logging
import threading
import time
import math
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class Counter:
    """Monotonically increasing counter."""

    def __init__(self, name: str, description: str = "", labels: Optional[Dict[str, str]] = None):
        self.name = name
        self.description = description
        self.labels = labels or {}
        self._value: float = 0
        self._lock = threading.Lock()

    def inc(self, amount: float = 1) -> None:
        with self._lock:
            self._value += amount

    @property
    def value(self) -> float:
        return self._value

    def reset(self) -> None:
        with self._lock:
            self._value = 0

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "type": "counter", "value": self._value, "labels": self.labels}


class Gauge:
    """Value that can go up and down."""

    def __init__(self, name: str, description: str = "", labels: Optional[Dict[str, str]] = None):
        self.name = name
        self.description = description
        self.labels = labels or {}
        self._value: float = 0
        self._lock = threading.Lock()

    def set(self, value: float) -> None:
        with self._lock:
            self._value = value

    def inc(self, amount: float = 1) -> None:
        with self._lock:
            self._value += amount

    def dec(self, amount: float = 1) -> None:
        with self._lock:
            self._value -= amount

    @property
    def value(self) -> float:
        return self._value

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "type": "gauge", "value": self._value, "labels": self.labels}


class Histogram:
    """Tracks the distribution of values."""

    DEFAULT_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, float("inf"))

    def __init__(
        self,
        name: str,
        description: str = "",
        buckets: Optional[tuple] = None,
        labels: Optional[Dict[str, str]] = None,
    ):
        self.name = name
        self.description = description
        self.labels = labels or {}
        self._buckets = buckets or self.DEFAULT_BUCKETS
        self._counts = [0] * len(self._buckets)
        self._sum: float = 0
        self._count: int = 0
        self._lock = threading.Lock()

    def observe(self, value: float) -> None:
        with self._lock:
            self._sum += value
            self._count += 1
            for i, bound in enumerate(self._buckets):
                if value <= bound:
                    self._counts[i] += 1

    @property
    def count(self) -> int:
        return self._count

    @property
    def sum(self) -> float:
        return self._sum

    @property
    def mean(self) -> float:
        return self._sum / self._count if self._count else 0

    def percentile(self, p: float) -> float:
        """Estimate the p-th percentile (0-100)."""
        if self._count == 0:
            return 0
        target = self._count * p / 100.0
        for i, bound in enumerate(self._buckets):
            if self._counts[i] >= target:
                return bound
        return self._buckets[-1]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": "histogram",
            "count": self._count,
            "sum": self._sum,
            "mean": round(self.mean, 4),
            "p50": self.percentile(50),
            "p95": self.percentile(95),
            "p99": self.percentile(99),
            "labels": self.labels,
        }


class MetricsCollector:
    """Central registry for application metrics.

    Usage::

        metrics = MetricsCollector()
        req_counter = metrics.counter("http_requests_total", "Total HTTP requests")
        req_counter.inc()

        latency = metrics.histogram("request_duration_seconds", "Request latency")
        latency.observe(0.042)
    """

    def __init__(self) -> None:
        self._counters: Dict[str, Counter] = {}
        self._gauges: Dict[str, Gauge] = {}
        self._histograms: Dict[str, Histogram] = {}
        self._lock = threading.Lock()

    def counter(self, name: str, description: str = "", labels: Optional[Dict[str, str]] = None) -> Counter:
        """Get or create a counter."""
        with self._lock:
            if name not in self._counters:
                self._counters[name] = Counter(name, description, labels)
            return self._counters[name]

    def gauge(self, name: str, description: str = "", labels: Optional[Dict[str, str]] = None) -> Gauge:
        """Get or create a gauge."""
        with self._lock:
            if name not in self._gauges:
                self._gauges[name] = Gauge(name, description, labels)
            return self._gauges[name]

    def histogram(
        self,
        name: str,
        description: str = "",
        buckets: Optional[tuple] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> Histogram:
        """Get or create a histogram."""
        with self._lock:
            if name not in self._histograms:
                self._histograms[name] = Histogram(name, description, buckets, labels)
            return self._histograms[name]

    def get_all(self) -> Dict[str, Any]:
        """Return all metrics as a dictionary."""
        with self._lock:
            return {
                "counters": {n: c.to_dict() for n, c in self._counters.items()},
                "gauges": {n: g.to_dict() for n, g in self._gauges.items()},
                "histograms": {n: h.to_dict() for n, h in self._histograms.items()},
            }

    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()

    def stats(self) -> Dict[str, Any]:
        """Get collector statistics."""
        with self._lock:
            return {
                "counters": len(self._counters),
                "gauges": len(self._gauges),
                "histograms": len(self._histograms),
                "total_metrics": len(self._counters) + len(self._gauges) + len(self._histograms),
            }
