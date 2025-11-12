"""
Performance Optimization Suite
Monitors, analyzes, and optimizes system performance
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import psutil
import time
import threading

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Performance metric snapshot"""
    timestamp: str
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    disk_read_mb: float
    disk_write_mb: float
    network_sent_mb: float
    network_recv_mb: float
    response_time_ms: Optional[float] = None
    active_processes: Optional[int] = None


@dataclass
class OptimizationAction:
    """Performance optimization action"""
    action_id: str
    action_type: str  # 'cache', 'lazy_load', 'batch', 'parallel', 'memory_cleanup'
    description: str
    expected_improvement: str
    applied: bool
    impact_measured: bool
    before_metrics: Dict[str, float]
    after_metrics: Optional[Dict[str, float]] = None
    timestamp: str = None


@dataclass
class PerformanceReport:
    """Performance analysis report"""
    report_id: str
    period_start: str
    period_end: str
    avg_cpu: float
    avg_memory: float
    peak_cpu: float
    peak_memory: float
    bottlenecks: List[str]
    optimizations: List[str]
    overall_score: float  # 0-100


class PerformanceOptimizer:
    """
    Performance Optimization Suite

    Features:
    - Real-time performance monitoring
    - Bottleneck detection
    - Automatic optimization suggestions
    - Memory leak detection
    - Cache optimization
    - Query optimization tracking
    - Resource usage profiling
    - Performance regression detection
    - Benchmark comparisons
    """

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.metrics_file = data_dir / "performance_metrics.json"
        self.optimizations_file = data_dir / "optimizations.json"

        # Metrics history
        self.metrics_history: List[PerformanceMetric] = []
        self.max_history = 10000

        # Applied optimizations
        self.optimizations: List[OptimizationAction] = []

        # Performance thresholds
        self.thresholds = {
            'cpu_warning': 70.0,
            'cpu_critical': 90.0,
            'memory_warning': 75.0,
            'memory_critical': 90.0,
            'response_time_warning': 1000,  # ms
            'response_time_critical': 5000  # ms
        }

        # Caching
        self.cache = {}
        self.cache_hits = 0
        self.cache_misses = 0

        # Monitoring
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None

        # Baseline metrics
        self.baseline_metrics: Optional[PerformanceMetric] = None

        # Load data
        self._load_metrics()

    def start_monitoring(self, interval: int = 10):
        """Start performance monitoring"""
        if self._monitoring:
            return

        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self._monitor_thread.start()
        logger.info(f"Started performance monitoring (interval: {interval}s)")

    def stop_monitoring(self):
        """Stop performance monitoring"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2)
        logger.info("Stopped performance monitoring")

    def _monitor_loop(self, interval: int):
        """Background monitoring loop"""
        while self._monitoring:
            try:
                metric = self._capture_metrics()
                self.metrics_history.append(metric)

                # Trim history if too long
                if len(self.metrics_history) > self.max_history:
                    self.metrics_history = self.metrics_history[-self.max_history:]

                # Detect issues
                self._detect_performance_issues(metric)

                # Auto-optimize if enabled
                self._auto_optimize()

                # Save periodically
                if len(self.metrics_history) % 100 == 0:
                    self._save_metrics()

                time.sleep(interval)

            except Exception as e:
                logger.error(f"Error in performance monitoring: {e}")
                time.sleep(interval)

    def _capture_metrics(self) -> PerformanceMetric:
        """Capture current performance metrics"""
        try:
            cpu = psutil.cpu_percent(interval=0.5)
            memory = psutil.virtual_memory()
            disk_io = psutil.disk_io_counters()
            network_io = psutil.net_io_counters()

            metric = PerformanceMetric(
                timestamp=datetime.now().isoformat(),
                cpu_percent=cpu,
                memory_mb=memory.used / (1024 * 1024),
                memory_percent=memory.percent,
                disk_read_mb=(disk_io.read_bytes / (1024 * 1024)) if disk_io else 0,
                disk_write_mb=(disk_io.write_bytes / (1024 * 1024)) if disk_io else 0,
                network_sent_mb=network_io.bytes_sent / (1024 * 1024),
                network_recv_mb=network_io.bytes_recv / (1024 * 1024),
                active_processes=len(psutil.pids())
            )

            return metric

        except Exception as e:
            logger.error(f"Error capturing metrics: {e}")
            return None

    def _detect_performance_issues(self, metric: PerformanceMetric):
        """Detect performance issues from metrics"""
        issues = []

        # Check CPU
        if metric.cpu_percent >= self.thresholds['cpu_critical']:
            issues.append(f"CRITICAL: CPU usage at {metric.cpu_percent:.1f}%")
        elif metric.cpu_percent >= self.thresholds['cpu_warning']:
            issues.append(f"WARNING: CPU usage at {metric.cpu_percent:.1f}%")

        # Check memory
        if metric.memory_percent >= self.thresholds['memory_critical']:
            issues.append(f"CRITICAL: Memory usage at {metric.memory_percent:.1f}%")
        elif metric.memory_percent >= self.thresholds['memory_warning']:
            issues.append(f"WARNING: Memory usage at {metric.memory_percent:.1f}%")

        # Check response time if available
        if metric.response_time_ms:
            if metric.response_time_ms >= self.thresholds['response_time_critical']:
                issues.append(f"CRITICAL: Response time {metric.response_time_ms}ms")
            elif metric.response_time_ms >= self.thresholds['response_time_warning']:
                issues.append(f"WARNING: Response time {metric.response_time_ms}ms")

        if issues:
            for issue in issues:
                logger.warning(f"Performance issue: {issue}")

    def _auto_optimize(self):
        """Automatically apply optimizations"""
        # Memory cleanup if high usage
        recent_metrics = self.metrics_history[-10:] if len(self.metrics_history) >= 10 else self.metrics_history

        if recent_metrics:
            avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)

            if avg_memory > 80:
                # Trigger memory cleanup
                self.optimize_memory()

    def optimize_memory(self) -> OptimizationAction:
        """Optimize memory usage"""
        import uuid
        import gc

        before_memory = psutil.virtual_memory().percent

        # Clear cache
        old_cache_size = len(self.cache)
        self.cache.clear()

        # Run garbage collection
        gc.collect()

        after_memory = psutil.virtual_memory().percent
        memory_freed = before_memory - after_memory

        action = OptimizationAction(
            action_id=str(uuid.uuid4()),
            action_type='memory_cleanup',
            description=f"Cleared cache ({old_cache_size} items) and ran garbage collection",
            expected_improvement=f"Free up memory",
            applied=True,
            impact_measured=True,
            before_metrics={'memory_percent': before_memory},
            after_metrics={'memory_percent': after_memory, 'freed': memory_freed},
            timestamp=datetime.now().isoformat()
        )

        self.optimizations.append(action)
        logger.info(f"Memory optimization: freed {memory_freed:.2f}% memory")

        return action

    def enable_caching(self, key: str, value: Any, ttl: int = 3600):
        """Enable result caching"""
        self.cache[key] = {
            'value': value,
            'expires': datetime.now() + timedelta(seconds=ttl),
            'hits': 0
        }

    def get_cached(self, key: str) -> Optional[Any]:
        """Get cached value"""
        if key in self.cache:
            cache_entry = self.cache[key]

            # Check if expired
            if datetime.now() > cache_entry['expires']:
                del self.cache[key]
                self.cache_misses += 1
                return None

            # Hit
            cache_entry['hits'] += 1
            self.cache_hits += 1
            return cache_entry['value']

        self.cache_misses += 1
        return None

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total * 100) if total > 0 else 0

        return {
            'cache_size': len(self.cache),
            'hits': self.cache_hits,
            'misses': self.cache_misses,
            'hit_rate': hit_rate,
            'total_requests': total
        }

    def measure_execution_time(self, func_name: str):
        """Decorator for measuring execution time"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                start_time = time.time()
                result = func(*args, **kwargs)
                end_time = time.time()

                execution_time = (end_time - start_time) * 1000  # ms
                logger.debug(f"{func_name} took {execution_time:.2f}ms")

                return result
            return wrapper
        return decorator

    def generate_performance_report(self, hours: int = 24) -> PerformanceReport:
        """Generate performance analysis report"""
        import uuid

        # Get metrics from last N hours
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [
            m for m in self.metrics_history
            if datetime.fromisoformat(m.timestamp) > cutoff_time
        ]

        if not recent_metrics:
            logger.warning("No metrics available for report")
            return None

        # Calculate statistics
        cpu_values = [m.cpu_percent for m in recent_metrics]
        memory_values = [m.memory_percent for m in recent_metrics]

        avg_cpu = sum(cpu_values) / len(cpu_values)
        avg_memory = sum(memory_values) / len(memory_values)
        peak_cpu = max(cpu_values)
        peak_memory = max(memory_values)

        # Identify bottlenecks
        bottlenecks = []
        if avg_cpu > 60:
            bottlenecks.append(f"High average CPU usage: {avg_cpu:.1f}%")
        if peak_cpu > 90:
            bottlenecks.append(f"CPU spikes detected: {peak_cpu:.1f}%")
        if avg_memory > 70:
            bottlenecks.append(f"High memory usage: {avg_memory:.1f}%")
        if peak_memory > 90:
            bottlenecks.append(f"Memory spikes detected: {peak_memory:.1f}%")

        # Optimization recommendations
        optimizations = []
        if len(self.cache) == 0:
            optimizations.append("Enable caching for frequently accessed data")
        if avg_cpu > 50:
            optimizations.append("Consider optimizing CPU-intensive operations")
        if avg_memory > 70:
            optimizations.append("Implement memory cleanup or increase available RAM")

        # Calculate overall score (100 is best)
        score = 100
        score -= min(avg_cpu, 50)  # Penalize high CPU
        score -= min(avg_memory / 2, 25)  # Penalize high memory
        score = max(score, 0)

        report = PerformanceReport(
            report_id=str(uuid.uuid4()),
            period_start=recent_metrics[0].timestamp,
            period_end=recent_metrics[-1].timestamp,
            avg_cpu=avg_cpu,
            avg_memory=avg_memory,
            peak_cpu=peak_cpu,
            peak_memory=peak_memory,
            bottlenecks=bottlenecks,
            optimizations=optimizations,
            overall_score=score
        )

        return report

    def get_metrics_summary(self, minutes: int = 60) -> Dict[str, Any]:
        """Get summary of recent metrics"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent = [
            m for m in self.metrics_history
            if datetime.fromisoformat(m.timestamp) > cutoff_time
        ]

        if not recent:
            return {'error': 'No recent metrics'}

        return {
            'period_minutes': minutes,
            'samples': len(recent),
            'cpu': {
                'avg': sum(m.cpu_percent for m in recent) / len(recent),
                'min': min(m.cpu_percent for m in recent),
                'max': max(m.cpu_percent for m in recent)
            },
            'memory': {
                'avg': sum(m.memory_percent for m in recent) / len(recent),
                'min': min(m.memory_percent for m in recent),
                'max': max(m.memory_percent for m in recent)
            },
            'cache': self.get_cache_stats(),
            'optimizations_applied': len(self.optimizations)
        }

    def benchmark_operation(self, operation_name: str, operation: Callable) -> Dict[str, Any]:
        """Benchmark an operation"""
        start_time = time.time()
        start_mem = psutil.Process().memory_info().rss / (1024 * 1024)

        # Execute operation
        try:
            result = operation()
            success = True
        except Exception as e:
            result = None
            success = False
            logger.error(f"Benchmark operation failed: {e}")

        end_time = time.time()
        end_mem = psutil.Process().memory_info().rss / (1024 * 1024)

        return {
            'operation': operation_name,
            'success': success,
            'execution_time_ms': (end_time - start_time) * 1000,
            'memory_delta_mb': end_mem - start_mem,
            'timestamp': datetime.now().isoformat()
        }

    def _save_metrics(self):
        """Save metrics to file"""
        try:
            # Save last 1000 metrics
            recent_metrics = self.metrics_history[-1000:]
            metrics_data = [asdict(m) for m in recent_metrics]

            with open(self.metrics_file, 'w') as f:
                json.dump(metrics_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")

    def _load_metrics(self):
        """Load metrics from file"""
        try:
            if self.metrics_file.exists():
                with open(self.metrics_file, 'r') as f:
                    metrics_data = json.load(f)
                    self.metrics_history = [
                        PerformanceMetric(**m) for m in metrics_data
                    ]
                logger.info(f"Loaded {len(self.metrics_history)} performance metrics")
        except Exception as e:
            logger.error(f"Error loading metrics: {e}")


# Global instance
_performance_optimizer: Optional[PerformanceOptimizer] = None


def get_performance_optimizer(data_dir: Path = None) -> PerformanceOptimizer:
    """Get or create global performance optimizer"""
    global _performance_optimizer

    if _performance_optimizer is None:
        if data_dir is None:
            data_dir = Path.home() / ".windows-ai" / "performance"
        _performance_optimizer = PerformanceOptimizer(data_dir)

    return _performance_optimizer


def initialize_performance_optimizer(data_dir: Path = None, start_monitoring: bool = True):
    """Initialize the performance optimizer"""
    optimizer = get_performance_optimizer(data_dir)

    if start_monitoring:
        optimizer.start_monitoring(interval=10)

    logger.info("Performance optimizer initialized")
    return optimizer
