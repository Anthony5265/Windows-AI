"""Real-time metrics collection and aggregation.

Implements high-performance metrics collection for API requests,
database operations, and system resource usage.
"""

import time
import asyncio
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Types of metrics collected."""
    REQUEST_LATENCY = "request_latency"
    DATABASE_QUERY = "database_query"
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"
    ERROR = "error"
    CUSTOM = "custom"


class MetricLevel(str, Enum):
    """Aggregation levels."""
    SECOND = "second"
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"


@dataclass
class MetricPoint:
    """Single metric data point."""
    timestamp: datetime
    metric_type: MetricType
    value: float
    tags: Dict[str, str] = field(default_factory=dict)
    endpoint: Optional[str] = None
    status_code: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "type": self.metric_type.value,
            "value": self.value,
            "tags": self.tags,
            "endpoint": self.endpoint,
            "status_code": self.status_code,
        }


@dataclass
class MetricAggregate:
    """Aggregated metrics over time period."""
    metric_type: MetricType
    level: MetricLevel
    start_time: datetime
    end_time: datetime
    count: int
    min_value: float
    max_value: float
    avg_value: float
    p50_value: float
    p95_value: float
    p99_value: float
    sum_value: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.metric_type.value,
            "level": self.level.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "count": self.count,
            "min": self.min_value,
            "max": self.max_value,
            "avg": self.avg_value,
            "p50": self.p50_value,
            "p95": self.p95_value,
            "p99": self.p99_value,
            "sum": self.sum_value,
        }


class MetricsCollector:
    """Collects and aggregates metrics in real-time."""

    def __init__(self, window_size_seconds: int = 60):
        """Initialize metrics collector.

        Args:
            window_size_seconds: Time window for in-memory metrics
        """
        self.window_size_seconds = window_size_seconds
        self.metrics: List[MetricPoint] = []
        self.aggregates: Dict[Tuple, MetricAggregate] = {}
        self.lock = asyncio.Lock()

    async def record(
        self,
        metric_type: MetricType,
        value: float,
        endpoint: Optional[str] = None,
        status_code: Optional[int] = None,
        tags: Optional[Dict[str, str]] = None,
    ):
        """Record a single metric.

        Args:
            metric_type: Type of metric
            value: Metric value
            endpoint: API endpoint (for request metrics)
            status_code: HTTP status code (for request metrics)
            tags: Additional metric tags
        """
        async with self.lock:
            metric = MetricPoint(
                timestamp=datetime.now(),
                metric_type=metric_type,
                value=value,
                endpoint=endpoint,
                status_code=status_code,
                tags=tags or {},
            )
            self.metrics.append(metric)

            # Remove old metrics outside window
            cutoff_time = datetime.now() - timedelta(seconds=self.window_size_seconds)
            self.metrics = [m for m in self.metrics if m.timestamp > cutoff_time]

    async def get_metrics_by_type(
        self,
        metric_type: MetricType,
        endpoint: Optional[str] = None,
    ) -> List[float]:
        """Get all metric values of specific type.

        Args:
            metric_type: Type of metric
            endpoint: Filter by endpoint (optional)

        Returns:
            List of metric values
        """
        async with self.lock:
            metrics = [
                m.value for m in self.metrics
                if m.metric_type == metric_type
                and (endpoint is None or m.endpoint == endpoint)
            ]
            return metrics

    async def aggregate(self,
                       metric_type: MetricType,
                       level: MetricLevel,
                       endpoint: Optional[str] = None,
                       ) -> Optional[MetricAggregate]:
        """Aggregate metrics over time period.

        Args:
            metric_type: Type of metric
            level: Aggregation level
            endpoint: Filter by endpoint (optional)

        Returns:
            Aggregated metric or None if no data
        """
        async with self.lock:
            # Filter metrics
            filtered = [
                m.value for m in self.metrics
                if m.metric_type == metric_type
                and (endpoint is None or m.endpoint == endpoint)
            ]

            if not filtered:
                return None

            # Calculate aggregates
            sorted_values = sorted(filtered)
            count = len(filtered)
            min_val = min(filtered)
            max_val = max(filtered)
            avg_val = sum(filtered) / count
            sum_val = sum(filtered)
            p50_val = sorted_values[int(count * 0.50)]
            p95_val = sorted_values[int(count * 0.95)]
            p99_val = sorted_values[int(count * 0.99)]

            # Determine time range
            now = datetime.now()
            if level == MetricLevel.SECOND:
                start_time = now.replace(microsecond=0)
                end_time = start_time + timedelta(seconds=1)
            elif level == MetricLevel.MINUTE:
                start_time = now.replace(second=0, microsecond=0)
                end_time = start_time + timedelta(minutes=1)
            elif level == MetricLevel.HOUR:
                start_time = now.replace(minute=0, second=0, microsecond=0)
                end_time = start_time + timedelta(hours=1)
            else:  # DAY
                start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
                end_time = start_time + timedelta(days=1)

            aggregate = MetricAggregate(
                metric_type=metric_type,
                level=level,
                start_time=start_time,
                end_time=end_time,
                count=count,
                min_value=min_val,
                max_value=max_val,
                avg_value=avg_val,
                p50_value=p50_val,
                p95_value=p95_val,
                p99_value=p99_val,
                sum_value=sum_val,
            )

            return aggregate

    async def get_endpoint_summary(
        self,
        time_window_seconds: int = 60,
    ) -> Dict[str, Dict[str, Any]]:
        """Get metrics summary by endpoint.

        Args:
            time_window_seconds: Time window for metrics

        Returns:
            Summary by endpoint
        """
        async with self.lock:
            cutoff = datetime.now() - timedelta(seconds=time_window_seconds)
            recent = [m for m in self.metrics if m.timestamp > cutoff]

            endpoints = defaultdict(lambda: {
                "request_count": 0,
                "latencies": [],
                "errors": 0,
                "status_codes": defaultdict(int),
            })

            for metric in recent:
                if metric.endpoint:
                    ep = endpoints[metric.endpoint]
                    if metric.metric_type == MetricType.REQUEST_LATENCY:
                        ep["latencies"].append(metric.value)
                        ep["request_count"] += 1
                    elif metric.metric_type == MetricType.ERROR:
                        ep["errors"] += 1
                    if metric.status_code:
                        ep["status_codes"][metric.status_code] += 1

            # Calculate percentiles
            summary = {}
            for endpoint, data in endpoints.items():
                if data["latencies"]:
                    sorted_lat = sorted(data["latencies"])
                    count = len(sorted_lat)
                    summary[endpoint] = {
                        "request_count": data["request_count"],
                        "avg_latency_ms": sum(sorted_lat) / count,
                        "p95_latency_ms": sorted_lat[int(count * 0.95)],
                        "p99_latency_ms": sorted_lat[int(count * 0.99)],
                        "error_count": data["errors"],
                        "error_rate": f"{data['errors'] / data['request_count'] * 100:.2f}%",
                        "status_codes": dict(data["status_codes"]),
                    }

            return summary

    async def get_health_metrics(self) -> Dict[str, Any]:
        """Get overall health metrics.

        Returns:
            System health metrics
        """
        async with self.lock:
            if not self.metrics:
                return {
                    "healthy": True,
                    "total_requests": 0,
                    "error_rate": 0.0,
                }

            # Count requests and errors
            requests = [m for m in self.metrics if m.metric_type == MetricType.REQUEST_LATENCY]
            errors = [m for m in self.metrics if m.metric_type == MetricType.ERROR]

            if not requests:
                return {
                    "healthy": True,
                    "total_requests": 0,
                    "error_rate": 0.0,
                }

            error_rate = len(errors) / len(requests) if requests else 0
            
            # Get latency stats
            latencies = [m.value for m in requests]
            avg_latency = sum(latencies) / len(latencies)
            p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]

            is_healthy = error_rate < 0.05 and avg_latency < 1000  # <5% errors and <1s avg

            return {
                "healthy": is_healthy,
                "total_requests": len(requests),
                "total_errors": len(errors),
                "error_rate": f"{error_rate * 100:.2f}%",
                "avg_latency_ms": avg_latency,
                "p95_latency_ms": p95_latency,
                "warning_flags": [
                    "high_error_rate" if error_rate > 0.05 else None,
                    "high_latency" if avg_latency > 1000 else None,
                    "high_p95_latency" if p95_latency > 2000 else None,
                ],
            }

    async def clear_old_metrics(self, max_age_seconds: int = 3600):
        """Clear metrics older than max age.

        Args:
            max_age_seconds: Maximum age in seconds
        """
        async with self.lock:
            cutoff = datetime.now() - timedelta(seconds=max_age_seconds)
            self.metrics = [m for m in self.metrics if m.timestamp > cutoff]

    async def get_all_metrics(self) -> List[Dict[str, Any]]:
        """Get all current metrics.

        Returns:
            List of metric dictionaries
        """
        async with self.lock:
            return [m.to_dict() for m in self.metrics]


class PerformanceAnalyzer:
    """Analyzes performance metrics for bottlenecks."""

    def __init__(self, collector: MetricsCollector):
        """Initialize analyzer.

        Args:
            collector: Metrics collector instance
        """
        self.collector = collector
        self.performance_history: List[Dict[str, Any]] = []

    async def detect_performance_degradation(
        self,
        threshold_ratio: float = 1.5,
        window_seconds: int = 300,
    ) -> Optional[Dict[str, Any]]:
        """Detect if performance is degrading.

        Args:
            threshold_ratio: Ratio for degradation detection (current/baseline)
            window_seconds: Time window for comparison

        Returns:
            Degradation report or None
        """
        if len(self.performance_history) < 2:
            return None

        # Compare recent vs historical
        baseline = self.performance_history[-60] if len(self.performance_history) >= 60 else self.performance_history[0]
        current = self.performance_history[-1]

        if "avg_latency_ms" not in baseline or "avg_latency_ms" not in current:
            return None

        ratio = current["avg_latency_ms"] / baseline["avg_latency_ms"]

        if ratio > threshold_ratio:
            return {
                "degradation_detected": True,
                "baseline_latency_ms": baseline["avg_latency_ms"],
                "current_latency_ms": current["avg_latency_ms"],
                "degradation_ratio": ratio,
                "recommendation": "Investigate slow queries or resource exhaustion",
            }

        return None

    async def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report.

        Returns:
            Performance analysis report
        """
        endpoints = await self.collector.get_endpoint_summary()
        health = await self.collector.get_health_metrics()

        # Find problematic endpoints
        problematic = [
            ep for ep, metrics in endpoints.items()
            if float(metrics["error_rate"].rstrip("%")) > 5 or
            metrics["avg_latency_ms"] > 1000
        ]

        return {
            "overall_health": health,
            "endpoints": endpoints,
            "problematic_endpoints": problematic,
            "recommendations": [
                "Focus on endpoints with >5% error rate" if any(
                    float(m["error_rate"].rstrip("%")) > 5 for m in endpoints.values()
                ) else None,
                "Investigate slow endpoints (>1s average)" if any(
                    m["avg_latency_ms"] > 1000 for m in endpoints.values()
                ) else None,
            ],
        }
