"""
Anomaly Detection and Alerting System
Monitors system behavior and detects anomalies using ML techniques
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, asdict
from pathlib import Path
import json
from collections import deque
import threading
import time
import math
import psutil

logger = logging.getLogger(__name__)


@dataclass
class Anomaly:
    """Detected anomaly."""
    anomaly_id: str
    anomaly_type: str
    severity: str
    timestamp: str
    description: str
    metrics: Dict[str, Any]
    baseline: Dict[str, Any]
    deviation: float
    suggested_action: str
    auto_resolved: bool = False


@dataclass
class SystemBaseline:
    """Baseline metrics for normal system behavior."""
    metric_name: str
    mean: float
    std_dev: float
    min_val: float
    max_val: float
    samples: int
    last_updated: str


class AnomalyDetector:
    """Real-time system anomaly detection with durable baselines and history."""

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir).expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.anomalies_file = self.data_dir / "anomalies.json"
        self.baselines_file = self.data_dir / "baselines.json"
        self.anomalies: deque = deque(maxlen=1000)
        self.baselines: Dict[str, SystemBaseline] = {}
        self.metric_history: Dict[str, deque] = {
            'cpu_percent': deque(maxlen=500),
            'memory_percent': deque(maxlen=500),
            'disk_io_read': deque(maxlen=500),
            'disk_io_write': deque(maxlen=500),
            'network_sent': deque(maxlen=500),
            'network_recv': deque(maxlen=500),
            'process_count': deque(maxlen=500),
            'thread_count': deque(maxlen=500),
        }
        self.z_score_threshold = 3.0
        self.severity_thresholds = {
            'low': 2.0,
            'medium': 3.0,
            'high': 4.0,
            'critical': 5.0,
        }
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._state_lock = threading.RLock()
        self.alert_callbacks: List = []

        self._load_baselines()
        self._load_anomalies()

    def start_monitoring(self, interval: int = 30):
        """Start anomaly detection monitoring."""
        if not isinstance(interval, (int, float)) or not math.isfinite(interval) or interval <= 0:
            raise ValueError("interval must be a positive finite number")
        with self._state_lock:
            if self._monitoring:
                return
            self._monitoring = True
            self._monitor_thread = threading.Thread(
                target=self._monitor_loop,
                args=(float(interval),),
                daemon=True,
                name="windows-ai-anomaly-detector",
            )
            self._monitor_thread.start()
        logger.info("Started anomaly detection (interval: %ss)", interval)

    def stop_monitoring(self):
        """Stop anomaly detection."""
        with self._state_lock:
            self._monitoring = False
            monitor_thread = self._monitor_thread
            self._monitor_thread = None
        if monitor_thread and monitor_thread is not threading.current_thread():
            monitor_thread.join(timeout=2)
        logger.info("Stopped anomaly detection")

    def _monitor_loop(self, interval: float):
        """Background monitoring loop."""
        while self._monitoring:
            try:
                metrics = self._collect_metrics()
                if metrics:
                    self._update_baselines(metrics)
                    anomalies = self._detect_anomalies(metrics)
                    for anomaly in anomalies:
                        self._trigger_alert(anomaly)
                    self._save_baselines()
                    self._save_anomalies()
                if self._monitoring:
                    time.sleep(interval)
            except Exception:
                logger.exception("Error in anomaly detection loop")
                if self._monitoring:
                    time.sleep(interval)

    def _collect_metrics(self) -> Dict[str, Any]:
        """Collect current system metrics."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_per_core = psutil.cpu_percent(interval=1, percpu=True)
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            disk_io = psutil.disk_io_counters()
            network_io = psutil.net_io_counters()
            process_count = len(psutil.pids())
            thread_count = 0
            for process in psutil.process_iter(['num_threads']):
                try:
                    thread_count += process.info.get('num_threads') or 0
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cpu_percent': cpu_percent,
                'cpu_per_core': cpu_per_core,
                'memory_percent': memory.percent,
                'memory_available': memory.available,
                'swap_percent': swap.percent,
                'disk_io_read': disk_io.read_bytes if disk_io else 0,
                'disk_io_write': disk_io.write_bytes if disk_io else 0,
                'network_sent': network_io.bytes_sent,
                'network_recv': network_io.bytes_recv,
                'process_count': process_count,
                'thread_count': thread_count,
            }
        except Exception:
            logger.exception("Error collecting metrics")
            return {}

    def _update_baselines(self, metrics: Dict[str, Any]):
        """Update baseline metrics with new data."""
        for metric_name in ['cpu_percent', 'memory_percent', 'process_count', 'thread_count']:
            if metric_name not in metrics:
                continue
            value = metrics[metric_name]
            if not isinstance(value, (int, float)) or not math.isfinite(value):
                continue
            with self._state_lock:
                self.metric_history[metric_name].append(value)
                values = list(self.metric_history[metric_name])
            if len(values) >= 30:
                mean = sum(values) / len(values)
                variance = sum((x - mean) ** 2 for x in values) / len(values)
                self.baselines[metric_name] = SystemBaseline(
                    metric_name=metric_name,
                    mean=mean,
                    std_dev=variance ** 0.5,
                    min_val=min(values),
                    max_val=max(values),
                    samples=len(values),
                    last_updated=datetime.now(timezone.utc).isoformat(),
                )

    def _detect_anomalies(self, metrics: Dict[str, Any]) -> List[Anomaly]:
        """Detect anomalies in current metrics."""
        anomalies = []
        import uuid

        for metric_name, baseline in self.baselines.items():
            if metric_name not in metrics:
                continue
            current_value = metrics[metric_name]
            if not isinstance(current_value, (int, float)) or not math.isfinite(current_value):
                continue
            if baseline.std_dev <= 0:
                continue
            z_score = abs((current_value - baseline.mean) / baseline.std_dev)
            if z_score < self.z_score_threshold:
                continue
            severity = 'low'
            for sev_level in ['critical', 'high', 'medium', 'low']:
                if z_score >= self.severity_thresholds[sev_level]:
                    severity = sev_level
                    break
            anomaly = Anomaly(
                anomaly_id=str(uuid.uuid4()),
                anomaly_type=self._classify_anomaly_type(metric_name),
                severity=severity,
                timestamp=datetime.now(timezone.utc).isoformat(),
                description=f"{metric_name} is {z_score:.2f} standard deviations from normal",
                metrics={metric_name: current_value},
                baseline={
                    'mean': baseline.mean,
                    'std_dev': baseline.std_dev,
                    'expected_range': f"{baseline.mean - 2 * baseline.std_dev:.2f} - {baseline.mean + 2 * baseline.std_dev:.2f}",
                },
                deviation=z_score,
                suggested_action=self._suggest_remediation(metric_name, current_value, baseline),
            )
            anomalies.append(anomaly)
            self.anomalies.append(asdict(anomaly))

        anomalies.extend(self._detect_behavioral_anomalies(metrics))
        return anomalies

    def _classify_anomaly_type(self, metric_name: str) -> str:
        if metric_name in ['cpu_percent', 'memory_percent']:
            return 'resource'
        if metric_name in ['process_count', 'thread_count']:
            return 'behavior'
        if metric_name in ['network_sent', 'network_recv']:
            return 'security'
        return 'performance'

    def _suggest_remediation(self, metric_name: str, current_value: float, baseline: SystemBaseline) -> str:
        suggestions = {
            'cpu_percent': "Check for runaway processes using Task Manager. Consider closing resource-intensive applications.",
            'memory_percent': "Close unnecessary applications. Check for memory leaks. Consider increasing available RAM.",
            'process_count': "Unusual number of processes detected. Check Task Manager for suspicious processes.",
            'thread_count': "High thread count detected. Some application may be misbehaving.",
        }
        return suggestions.get(metric_name, "Monitor the situation and investigate if it persists.")

    def _detect_behavioral_anomalies(self, metrics: Dict[str, Any]) -> List[Anomaly]:
        """Detect behavioral anomalies."""
        anomalies = []
        import uuid
        now = datetime.now(timezone.utc)
        current_hour = now.hour
        if 2 <= current_hour <= 5 and metrics.get('cpu_percent', 0) > 50:
            anomaly = Anomaly(
                anomaly_id=str(uuid.uuid4()), anomaly_type='behavior', severity='medium',
                timestamp=now.isoformat(),
                description=f"Unusual high CPU activity at {current_hour}:00",
                metrics={'cpu_percent': metrics['cpu_percent'], 'hour': current_hour},
                baseline={'expected': 'low activity during night'}, deviation=3.0,
                suggested_action="Check for scheduled tasks or background processes running unexpectedly.",
            )
            anomalies.append(anomaly)
            self.anomalies.append(asdict(anomaly))

        if 'process_count' in metrics and len(self.metric_history['process_count']) >= 2:
            recent_change = abs(self.metric_history['process_count'][-1] - self.metric_history['process_count'][-2])
            if recent_change > 20:
                anomaly = Anomaly(
                    anomaly_id=str(uuid.uuid4()), anomaly_type='security', severity='high',
                    timestamp=now.isoformat(),
                    description=f"Rapid process creation/termination detected ({recent_change} processes)",
                    metrics={'process_change': recent_change},
                    baseline={'expected': 'gradual process changes'}, deviation=4.0,
                    suggested_action="Potential malware activity. Run security scan immediately.",
                )
                anomalies.append(anomaly)
                self.anomalies.append(asdict(anomaly))
        return anomalies

    def _trigger_alert(self, anomaly: Anomaly):
        logger.warning("ANOMALY DETECTED [%s]: %s", anomaly.severity.upper(), anomaly.description)
        for callback in tuple(self.alert_callbacks):
            try:
                callback(anomaly)
            except Exception:
                logger.exception("Error in alert callback")

    def register_alert_callback(self, callback):
        """Register a callable invoked for each detected anomaly."""
        if not callable(callback):
            raise TypeError("callback must be callable")
        if callback not in self.alert_callbacks:
            self.alert_callbacks.append(callback)
        logger.info("Registered alert callback")

    def get_recent_anomalies(self, limit: int = 50, severity: Optional[str] = None) -> List[Dict]:
        """Get recent anomalies."""
        if not isinstance(limit, int) or limit < 0:
            raise ValueError("limit must be a non-negative integer")
        if severity is not None and severity not in self.severity_thresholds:
            raise ValueError(f"Unknown severity: {severity}")
        anomalies = list(self.anomalies)
        if severity:
            anomalies = [a for a in anomalies if a.get('severity') == severity]
        return list(reversed(anomalies))[:limit]

    def get_baselines(self) -> List[Dict]:
        """Get current baselines."""
        return [asdict(b) for b in self.baselines.values()]

    def get_health_status(self) -> Dict[str, Any]:
        """Get overall system health status."""
        try:
            current_metrics = self._collect_metrics()
            recent_time = datetime.now(timezone.utc) - timedelta(hours=1)
            recent_anomalies = []
            for anomaly in self.anomalies:
                try:
                    timestamp = datetime.fromisoformat(anomaly['timestamp'])
                    if timestamp.tzinfo is None:
                        timestamp = timestamp.replace(tzinfo=timezone.utc)
                    if timestamp > recent_time:
                        recent_anomalies.append(anomaly)
                except (KeyError, TypeError, ValueError):
                    continue

            severity_counts = {
                'critical': sum(1 for a in recent_anomalies if a.get('severity') == 'critical'),
                'high': sum(1 for a in recent_anomalies if a.get('severity') == 'high'),
                'medium': sum(1 for a in recent_anomalies if a.get('severity') == 'medium'),
                'low': sum(1 for a in recent_anomalies if a.get('severity') == 'low'),
            }
            if severity_counts['critical'] > 0:
                health = 'critical'
            elif severity_counts['high'] > 2:
                health = 'poor'
            elif severity_counts['high'] > 0 or severity_counts['medium'] > 5:
                health = 'fair'
            elif severity_counts['medium'] > 0:
                health = 'good'
            else:
                health = 'excellent'
            return {
                'health': health,
                'current_metrics': current_metrics,
                'anomalies_last_hour': len(recent_anomalies),
                'severity_breakdown': severity_counts,
                'baselines_established': len(self.baselines),
                'timestamp': datetime.now(timezone.utc).isoformat(),
            }
        except Exception:
            logger.exception("Error getting health status")
            return {'health': 'unknown'}

    def _save_baselines(self):
        """Persist baselines atomically."""
        baselines_data = {name: asdict(baseline) for name, baseline in self.baselines.items()}
        self._atomic_json_write(self.baselines_file, baselines_data)

    def _save_anomalies(self):
        """Persist anomaly history atomically."""
        self._atomic_json_write(self.anomalies_file, list(self.anomalies))

    @staticmethod
    def _atomic_json_write(path: Path, payload: Any) -> None:
        """Write JSON without leaving a partially written state file."""
        temp_path = path.with_suffix(path.suffix + ".tmp")
        with temp_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
            handle.write("\n")
        temp_path.replace(path)

    def _load_baselines(self):
        """Load baselines from file."""
        try:
            if self.baselines_file.exists():
                with self.baselines_file.open("r", encoding="utf-8") as f:
                    baselines_data = json.load(f)
                if not isinstance(baselines_data, dict):
                    raise ValueError("baseline state must be an object")
                self.baselines = {
                    name: SystemBaseline(**data)
                    for name, data in baselines_data.items()
                    if isinstance(data, dict)
                }
                logger.info("Loaded %s baselines", len(self.baselines))
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as e:
            logger.warning("Unable to load anomaly baselines: %s", e)

    def _load_anomalies(self):
        """Load anomaly history from file."""
        try:
            if self.anomalies_file.exists():
                with self.anomalies_file.open("r", encoding="utf-8") as f:
                    anomalies_data = json.load(f)
                if not isinstance(anomalies_data, list):
                    raise ValueError("anomaly state must be a list")
                self.anomalies = deque(
                    (item for item in anomalies_data if isinstance(item, dict)),
                    maxlen=1000,
                )
                logger.info("Loaded %s anomalies", len(self.anomalies))
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as e:
            logger.warning("Unable to load anomaly history: %s", e)


_anomaly_detector: Optional[AnomalyDetector] = None


def get_anomaly_detector(data_dir: Path = None) -> AnomalyDetector:
    """Get or create the global anomaly detector."""
    global _anomaly_detector
    if _anomaly_detector is None:
        if data_dir is None:
            data_dir = Path.home() / ".windows-ai" / "anomaly"
        _anomaly_detector = AnomalyDetector(data_dir)
    elif data_dir is not None and Path(data_dir).expanduser() != _anomaly_detector.data_dir:
        raise RuntimeError("global anomaly detector is already initialized with a different data_dir")
    return _anomaly_detector


def initialize_anomaly_detector(data_dir: Path = None, start_monitoring: bool = True):
    """Initialize the anomaly detector."""
    detector = get_anomaly_detector(data_dir)
    if start_monitoring:
        detector.start_monitoring(interval=30)
    logger.info("Anomaly detector initialized")
    return detector
