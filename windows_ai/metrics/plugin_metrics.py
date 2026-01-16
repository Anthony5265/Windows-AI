"""Plugin performance monitoring and optimization.

Tracks performance metrics for all plugins including execution time,
resource usage, error rates, and provides optimization recommendations.
"""

import time
import asyncio
from typing import Any, Dict, List, Optional, Callable, Coroutine
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PerformanceLevel(str, Enum):
    """Performance health levels."""
    EXCELLENT = "excellent"  # < 100ms
    GOOD = "good"  # 100-500ms
    ACCEPTABLE = "acceptable"  # 500-1000ms
    SLOW = "slow"  # 1000-5000ms
    CRITICAL = "critical"  # > 5000ms


@dataclass
class PluginMetric:
    """Individual plugin execution metric."""
    plugin_name: str
    execution_time_ms: float
    memory_delta_mb: float = 0.0
    cpu_percent: float = 0.0
    success: bool = True
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    input_size_bytes: int = 0
    output_size_bytes: int = 0

    @property
    def data_throughput_mbps(self) -> float:
        """Calculate data throughput in MB/s."""
        if self.execution_time_ms == 0:
            return 0.0
        total_mb = (self.input_size_bytes + self.output_size_bytes) / (1024 * 1024)
        duration_s = self.execution_time_ms / 1000
        return total_mb / duration_s if duration_s > 0 else 0.0

    def get_performance_level(self) -> PerformanceLevel:
        """Determine performance level based on execution time."""
        if self.execution_time_ms < 100:
            return PerformanceLevel.EXCELLENT
        elif self.execution_time_ms < 500:
            return PerformanceLevel.GOOD
        elif self.execution_time_ms < 1000:
            return PerformanceLevel.ACCEPTABLE
        elif self.execution_time_ms < 5000:
            return PerformanceLevel.SLOW
        else:
            return PerformanceLevel.CRITICAL

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "plugin_name": self.plugin_name,
            "execution_time_ms": self.execution_time_ms,
            "memory_delta_mb": self.memory_delta_mb,
            "cpu_percent": self.cpu_percent,
            "success": self.success,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
            "performance_level": self.get_performance_level().value,
            "data_throughput_mbps": self.data_throughput_mbps,
        }


@dataclass
class PluginMetrics:
    """Aggregated metrics for a plugin."""
    plugin_name: str
    execution_count: int = 0
    success_count: int = 0
    error_count: int = 0
    total_time_ms: float = 0.0
    avg_time_ms: float = 0.0
    min_time_ms: float = float('inf')
    max_time_ms: float = 0.0
    p50_time_ms: float = 0.0
    p95_time_ms: float = 0.0
    p99_time_ms: float = 0.0
    avg_memory_mb: float = 0.0
    peak_memory_mb: float = 0.0
    total_data_processed_mb: float = 0.0
    last_execution: Optional[datetime] = None
    last_error: Optional[str] = None
    execution_times: deque = field(default_factory=lambda: deque(maxlen=1000))

    @property
    def error_rate(self) -> float:
        """Calculate error rate as percentage."""
        if self.execution_count == 0:
            return 0.0
        return (self.error_count / self.execution_count) * 100

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        return 100.0 - self.error_rate

    @property
    def performance_level(self) -> PerformanceLevel:
        """Determine overall performance level."""
        return PerformanceLevel.EXCELLENT if self.avg_time_ms < 100 \
            else PerformanceLevel.GOOD if self.avg_time_ms < 500 \
            else PerformanceLevel.ACCEPTABLE if self.avg_time_ms < 1000 \
            else PerformanceLevel.SLOW if self.avg_time_ms < 5000 \
            else PerformanceLevel.CRITICAL

    def update(self, metric: PluginMetric):
        """Update aggregated metrics with new execution metric."""
        self.execution_count += 1
        self.last_execution = metric.timestamp

        if metric.success:
            self.success_count += 1
            self.total_time_ms += metric.execution_time_ms
            self.avg_time_ms = self.total_time_ms / self.success_count
            self.min_time_ms = min(self.min_time_ms, metric.execution_time_ms)
            self.max_time_ms = max(self.max_time_ms, metric.execution_time_ms)
            self.execution_times.append(metric.execution_time_ms)

            # Update percentiles
            if len(self.execution_times) >= 10:
                sorted_times = sorted(self.execution_times)
                self.p50_time_ms = sorted_times[len(sorted_times) // 2]
                self.p95_time_ms = sorted_times[int(len(sorted_times) * 0.95)]
                self.p99_time_ms = sorted_times[int(len(sorted_times) * 0.99)]

            self.avg_memory_mb = (self.avg_memory_mb + metric.memory_delta_mb) / 2
            self.peak_memory_mb = max(self.peak_memory_mb, metric.memory_delta_mb)
            self.total_data_processed_mb += (metric.input_size_bytes + metric.output_size_bytes) / (1024 * 1024)
        else:
            self.error_count += 1
            self.last_error = metric.error

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "plugin_name": self.plugin_name,
            "execution_count": self.execution_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": self.success_rate,
            "error_rate": self.error_rate,
            "total_time_ms": self.total_time_ms,
            "avg_time_ms": self.avg_time_ms,
            "min_time_ms": self.min_time_ms if self.min_time_ms != float('inf') else None,
            "max_time_ms": self.max_time_ms,
            "p50_time_ms": self.p50_time_ms,
            "p95_time_ms": self.p95_time_ms,
            "p99_time_ms": self.p99_time_ms,
            "avg_memory_mb": self.avg_memory_mb,
            "peak_memory_mb": self.peak_memory_mb,
            "total_data_processed_mb": self.total_data_processed_mb,
            "performance_level": self.performance_level.value,
            "last_execution": self.last_execution.isoformat() if self.last_execution else None,
            "last_error": self.last_error,
        }


class PluginPerformanceMonitor:
    """Monitors and analyzes plugin performance metrics."""

    def __init__(self):
        """Initialize performance monitor."""
        self.metrics: Dict[str, PluginMetrics] = {}
        self.timeout_seconds = 30  # Default plugin timeout

    def record_execution(self, metric: PluginMetric):
        """Record a plugin execution metric.

        Args:
            metric: The execution metric to record
        """
        if metric.plugin_name not in self.metrics:
            self.metrics[metric.plugin_name] = PluginMetrics(plugin_name=metric.plugin_name)

        self.metrics[metric.plugin_name].update(metric)

    async def run_plugin_with_timeout(
        self,
        plugin_name: str,
        plugin_func: Callable[..., Coroutine],
        *args,
        timeout_seconds: Optional[float] = None,
        **kwargs,
    ) -> Any:
        """Run a plugin function with timeout and performance tracking.

        Args:
            plugin_name: Name of the plugin
            plugin_func: Async function to execute
            *args: Function arguments
            timeout_seconds: Timeout in seconds (uses default if not provided)
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            asyncio.TimeoutError: If execution exceeds timeout
        """
        timeout = timeout_seconds or self.timeout_seconds
        start_time = time.time()
        success = False
        error_msg = None
        result = None

        try:
            result = await asyncio.wait_for(
                plugin_func(*args, **kwargs),
                timeout=timeout,
            )
            success = True
        except asyncio.TimeoutError:
            error_msg = f"Plugin execution exceeded {timeout}s timeout"
            logger.warning(f"{plugin_name}: {error_msg}")
            raise
        except Exception as e:
            error_msg = str(e)
            logger.error(f"{plugin_name}: Execution failed - {error_msg}")
            raise
        finally:
            execution_time_ms = (time.time() - start_time) * 1000
            metric = PluginMetric(
                plugin_name=plugin_name,
                execution_time_ms=execution_time_ms,
                success=success,
                error=error_msg,
            )
            self.record_execution(metric)

        return result

    def get_slowest_plugins(self, limit: int = 10) -> List[PluginMetrics]:
        """Get plugins with slowest average execution time.

        Args:
            limit: Maximum number of plugins to return

        Returns:
            List of slowest plugins, sorted by avg_time_ms descending
        """
        return sorted(
            self.metrics.values(),
            key=lambda m: m.avg_time_ms,
            reverse=True,
        )[:limit]

    def get_problematic_plugins(self) -> List[PluginMetrics]:
        """Get plugins with high error rates or critical performance.

        Returns:
            List of problematic plugins
        """
        problematic = [
            m for m in self.metrics.values()
            if m.error_rate > 10 or m.performance_level == PerformanceLevel.CRITICAL
        ]
        return sorted(
            problematic,
            key=lambda m: (m.error_rate, m.avg_time_ms),
            reverse=True,
        )

    def get_optimization_recommendations(self, plugin_name: str) -> List[str]:
        """Get optimization recommendations for a plugin.

        Args:
            plugin_name: Name of the plugin

        Returns:
            List of optimization recommendations
        """
        if plugin_name not in self.metrics:
            return []

        metrics = self.metrics[plugin_name]
        recommendations = []

        # Performance recommendations
        if metrics.performance_level == PerformanceLevel.CRITICAL:
            recommendations.append(
                f"CRITICAL: Plugin takes {metrics.avg_time_ms:.0f}ms on average. "
                "Consider caching results or optimizing algorithm."
            )
        elif metrics.performance_level == PerformanceLevel.SLOW:
            recommendations.append(
                f"Plugin is slow ({metrics.avg_time_ms:.0f}ms avg). "
                "Profile to identify bottlenecks."
            )

        # Error rate recommendations
        if metrics.error_rate > 10:
            recommendations.append(
                f"High error rate ({metrics.error_rate:.1f}%). "
                "Review error logs and add error handling."
            )

        # Memory recommendations
        if metrics.peak_memory_mb > 1000:
            recommendations.append(
                f"High memory usage ({metrics.peak_memory_mb:.0f}MB peak). "
                "Consider streaming or chunking processing."
            )

        # Data throughput recommendations
        throughput_avg = (
            metrics.total_data_processed_mb / metrics.execution_count
            if metrics.execution_count > 0 else 0
        )
        if throughput_avg > 100:
            recommendations.append(
                f"Processing large amounts of data ({throughput_avg:.0f}MB per execution). "
                "Consider batching or parallel processing."
            )

        # Timeout recommendations
        if metrics.p99_time_ms > 20000:
            recommendations.append(
                f"P99 latency is {metrics.p99_time_ms:.0f}ms. Consider increasing timeout "
                "or implementing cancellation."
            )

        return recommendations

    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report.

        Returns:
            Detailed performance report for all plugins
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "total_plugins": len(self.metrics),
            "total_executions": sum(m.execution_count for m in self.metrics.values()),
            "total_errors": sum(m.error_count for m in self.metrics.values()),
            "overall_success_rate": (
                sum(m.success_count for m in self.metrics.values())
                / sum(m.execution_count for m in self.metrics.values()) * 100
                if sum(m.execution_count for m in self.metrics.values()) > 0 else 0
            ),
            "avg_execution_time_ms": (
                sum(m.total_time_ms for m in self.metrics.values())
                / sum(m.success_count for m in self.metrics.values())
                if sum(m.success_count for m in self.metrics.values()) > 0 else 0
            ),
            "slowest_plugins": [
                m.to_dict() for m in self.get_slowest_plugins(5)
            ],
            "problematic_plugins": [
                m.to_dict() for m in self.get_problematic_plugins()
            ],
            "performance_distribution": self._get_performance_distribution(),
            "plugins": {
                name: metrics.to_dict()
                for name, metrics in sorted(self.metrics.items())
            },
        }

    def _get_performance_distribution(self) -> Dict[str, int]:
        """Get distribution of plugins by performance level."""
        distribution = {level.value: 0 for level in PerformanceLevel}
        for metrics in self.metrics.values():
            if metrics.execution_count > 0:  # Only count plugins with executions
                distribution[metrics.performance_level.value] += 1
        return distribution

    async def generate_optimization_report(self) -> str:
        """Generate a text report with optimization recommendations.

        Returns:
            Formatted report text
        """
        report_lines = [
            "=" * 80,
            "PLUGIN PERFORMANCE OPTIMIZATION REPORT",
            f"Generated: {datetime.now().isoformat()}",
            "=" * 80,
            "",
        ]

        # Summary
        perf_report = self.get_performance_report()
        report_lines.extend([
            "SUMMARY",
            "-" * 80,
            f"Total Plugins: {perf_report['total_plugins']}",
            f"Total Executions: {perf_report['total_executions']}",
            f"Overall Success Rate: {perf_report['overall_success_rate']:.1f}%",
            f"Average Execution Time: {perf_report['avg_execution_time_ms']:.2f}ms",
            "",
        ])

        # Problematic plugins with recommendations
        problematic = self.get_problematic_plugins()
        if problematic:
            report_lines.extend([
                "PROBLEMATIC PLUGINS",
                "-" * 80,
            ])
            for metrics in problematic:
                report_lines.extend([
                    f"\n{metrics.plugin_name}",
                    f"  Performance Level: {metrics.performance_level.value.upper()}",
                    f"  Avg Execution Time: {metrics.avg_time_ms:.2f}ms",
                    f"  Error Rate: {metrics.error_rate:.1f}%",
                    f"  Peak Memory: {metrics.peak_memory_mb:.1f}MB",
                ])
                for rec in self.get_optimization_recommendations(metrics.plugin_name):
                    report_lines.append(f"  ⚠️  {rec}")

        report_lines.extend(["", "=" * 80])
        return "\n".join(report_lines)
