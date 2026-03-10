"""Comprehensive monitoring and metrics collection"""

import asyncio
import logging
import time
import psutil
import platform
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import deque
from dataclasses import dataclass, field
import json

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """Single metric data point"""
    timestamp: datetime
    value: float
    tags: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            'timestamp': self.timestamp.isoformat(),
            'value': self.value,
            'tags': self.tags
        }


class MetricsCollector:
    """
    Collects and stores application metrics

    Features:
    - Time-series metrics storage
    - Metric aggregation (avg, min, max, sum)
    - Automatic cleanup of old metrics
    - Tag-based filtering
    """

    def __init__(self, retention_hours: int = 24):
        self.retention_hours = retention_hours
        self.metrics: Dict[str, deque] = {}
        self._lock = asyncio.Lock()

        # Statistics
        self.total_metrics_recorded = 0

    async def record(
        self,
        metric_name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None
    ):
        """Record a metric value"""
        async with self._lock:
            if metric_name not in self.metrics:
                self.metrics[metric_name] = deque()

            point = MetricPoint(
                timestamp=datetime.utcnow(),
                value=value,
                tags=tags or {}
            )

            self.metrics[metric_name].append(point)
            self.total_metrics_recorded += 1

            # Cleanup old metrics
            await self._cleanup_old_metrics(metric_name)

    async def _cleanup_old_metrics(self, metric_name: str):
        """Remove metrics older than retention period"""
        cutoff = datetime.utcnow() - timedelta(hours=self.retention_hours)
        queue = self.metrics[metric_name]

        while queue and queue[0].timestamp < cutoff:
            queue.popleft()

    async def get_metrics(
        self,
        metric_name: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> List[MetricPoint]:
        """Get metrics with optional time range and tag filtering"""
        async with self._lock:
            if metric_name not in self.metrics:
                return []

            points = list(self.metrics[metric_name])

            # Filter by time range
            if start_time:
                points = [p for p in points if p.timestamp >= start_time]
            if end_time:
                points = [p for p in points if p.timestamp <= end_time]

            # Filter by tags
            if tags:
                points = [
                    p for p in points
                    if all(p.tags.get(k) == v for k, v in tags.items())
                ]

            return points

    async def get_aggregated(
        self,
        metric_name: str,
        aggregation: str = 'avg',
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Optional[float]:
        """
        Get aggregated metric value

        Args:
            metric_name: Metric name
            aggregation: One of 'avg', 'min', 'max', 'sum', 'count'
            start_time: Start of time range
            end_time: End of time range

        Returns:
            Aggregated value or None if no data
        """
        points = await self.get_metrics(metric_name, start_time, end_time)

        if not points:
            return None

        values = [p.value for p in points]

        if aggregation == 'avg':
            return sum(values) / len(values)
        elif aggregation == 'min':
            return min(values)
        elif aggregation == 'max':
            return max(values)
        elif aggregation == 'sum':
            return sum(values)
        elif aggregation == 'count':
            return len(values)
        else:
            raise ValueError(f"Unknown aggregation: {aggregation}")

    async def get_all_metric_names(self) -> List[str]:
        """Get list of all metric names"""
        async with self._lock:
            return list(self.metrics.keys())


class SystemMonitor:
    """
    Monitors system resources and performance

    Tracks:
    - CPU usage
    - Memory usage
    - Disk I/O
    - Network I/O
    - Process statistics
    """

    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.process = psutil.Process()
        self.monitoring = False
        self.monitor_task: Optional[asyncio.Task] = None

        # Baseline measurements
        self.start_time = time.time()
        self.initial_cpu_times = psutil.cpu_times()
        self.initial_net_io = psutil.net_io_counters()

    async def start(self, interval_seconds: int = 60):
        """Start monitoring"""
        if self.monitoring:
            logger.warning("System monitor already running")
            return

        self.monitoring = True
        self.monitor_task = asyncio.create_task(self._monitor_loop(interval_seconds))
        logger.info(f"System monitor started (interval: {interval_seconds}s)")

    async def stop(self):
        """Stop monitoring"""
        if not self.monitoring:
            return

        self.monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass

        logger.info("System monitor stopped")

    async def _monitor_loop(self, interval: int):
        """Monitoring loop"""
        while self.monitoring:
            try:
                await self._collect_metrics()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}", exc_info=True)

    async def _collect_metrics(self):
        """Collect system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            await self.metrics.record('system.cpu.percent', cpu_percent)

            # Memory metrics
            memory = psutil.virtual_memory()
            await self.metrics.record('system.memory.percent', memory.percent)
            await self.metrics.record('system.memory.used_mb', memory.used / 1024 / 1024)
            await self.metrics.record('system.memory.available_mb', memory.available / 1024 / 1024)

            # Disk metrics
            disk = psutil.disk_usage('/')
            await self.metrics.record('system.disk.percent', disk.percent)
            await self.metrics.record('system.disk.used_gb', disk.used / 1024 / 1024 / 1024)

            # Process metrics
            process_cpu = self.process.cpu_percent()
            process_memory = self.process.memory_info()
            await self.metrics.record('process.cpu.percent', process_cpu)
            await self.metrics.record('process.memory.rss_mb', process_memory.rss / 1024 / 1024)
            await self.metrics.record('process.memory.vms_mb', process_memory.vms / 1024 / 1024)

            # Thread count
            await self.metrics.record('process.threads', self.process.num_threads())

        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")

    async def get_current_stats(self) -> Dict[str, Any]:
        """Get current system statistics"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count()

            # Memory
            memory = psutil.virtual_memory()

            # Disk
            disk = psutil.disk_usage('/')

            # Network
            net_io = psutil.net_io_counters()

            # Process
            process_info = {
                'cpu_percent': self.process.cpu_percent(),
                'memory_mb': self.process.memory_info().rss / 1024 / 1024,
                'threads': self.process.num_threads(),
                'open_files': len(self.process.open_files()) if hasattr(self.process, 'open_files') else 0,
                'connections': len(self.process.connections()) if hasattr(self.process, 'connections') else 0,
            }

            # Uptime
            uptime_seconds = time.time() - self.start_time

            return {
                'timestamp': datetime.utcnow().isoformat(),
                'uptime_seconds': int(uptime_seconds),
                'system': {
                    'platform': platform.system(),
                    'platform_version': platform.version(),
                    'python_version': platform.python_version(),
                },
                'cpu': {
                    'percent': cpu_percent,
                    'count': cpu_count,
                    'count_logical': psutil.cpu_count(logical=True),
                },
                'memory': {
                    'total_mb': memory.total / 1024 / 1024,
                    'available_mb': memory.available / 1024 / 1024,
                    'used_mb': memory.used / 1024 / 1024,
                    'percent': memory.percent,
                },
                'disk': {
                    'total_gb': disk.total / 1024 / 1024 / 1024,
                    'used_gb': disk.used / 1024 / 1024 / 1024,
                    'free_gb': disk.free / 1024 / 1024 / 1024,
                    'percent': disk.percent,
                },
                'network': {
                    'bytes_sent': net_io.bytes_sent,
                    'bytes_recv': net_io.bytes_recv,
                    'packets_sent': net_io.packets_sent,
                    'packets_recv': net_io.packets_recv,
                },
                'process': process_info
            }

        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            return {'error': str(e)}


class PerformanceTracker:
    """
    Tracks application performance metrics

    Features:
    - Request latency tracking
    - Throughput measurement
    - Error rate tracking
    - Custom event tracking
    """

    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.request_count = 0
        self.error_count = 0
        self.start_time = time.time()

    async def track_request(
        self,
        endpoint: str,
        duration_ms: float,
        status_code: int,
        error: bool = False
    ):
        """Track API request"""
        self.request_count += 1
        if error:
            self.error_count += 1

        tags = {
            'endpoint': endpoint,
            'status': str(status_code),
            'error': str(error)
        }

        await self.metrics.record('api.request.duration_ms', duration_ms, tags)
        await self.metrics.record('api.request.count', 1, tags)

        if error:
            await self.metrics.record('api.request.errors', 1, tags)

    async def track_agent_task(
        self,
        agent_id: str,
        task_type: str,
        duration_ms: float,
        success: bool
    ):
        """Track agent task execution"""
        tags = {
            'agent_id': agent_id,
            'task_type': task_type,
            'success': str(success)
        }

        await self.metrics.record('agent.task.duration_ms', duration_ms, tags)
        await self.metrics.record('agent.task.count', 1, tags)

        if not success:
            await self.metrics.record('agent.task.failures', 1, tags)

    async def track_plugin_execution(
        self,
        plugin_id: str,
        action: str,
        duration_ms: float,
        success: bool
    ):
        """Track plugin execution"""
        tags = {
            'plugin_id': plugin_id,
            'action': action,
            'success': str(success)
        }

        await self.metrics.record('plugin.execution.duration_ms', duration_ms, tags)
        await self.metrics.record('plugin.execution.count', 1, tags)

        if not success:
            await self.metrics.record('plugin.execution.failures', 1, tags)

    async def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        uptime = time.time() - self.start_time
        error_rate = (self.error_count / self.request_count * 100) if self.request_count > 0 else 0

        return {
            'uptime_seconds': int(uptime),
            'total_requests': self.request_count,
            'total_errors': self.error_count,
            'error_rate_percent': round(error_rate, 2),
            'requests_per_second': round(self.request_count / uptime, 2) if uptime > 0 else 0
        }


# Global instances
_metrics_collector: Optional[MetricsCollector] = None
_system_monitor: Optional[SystemMonitor] = None
_performance_tracker: Optional[PerformanceTracker] = None


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def get_system_monitor() -> SystemMonitor:
    """Get global system monitor"""
    global _system_monitor
    if _system_monitor is None:
        _system_monitor = SystemMonitor(get_metrics_collector())
    return _system_monitor


def get_performance_tracker() -> PerformanceTracker:
    """Get global performance tracker"""
    global _performance_tracker
    if _performance_tracker is None:
        _performance_tracker = PerformanceTracker(get_metrics_collector())
    return _performance_tracker


async def start_monitoring():
    """Start all monitoring services"""
    monitor = get_system_monitor()
    await monitor.start()


async def stop_monitoring():
    """Stop all monitoring services"""
    monitor = get_system_monitor()
    await monitor.stop()
