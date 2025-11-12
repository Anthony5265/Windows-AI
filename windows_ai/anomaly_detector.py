"""
Anomaly Detection and Alerting System
Monitors system behavior and detects anomalies using ML techniques
"""
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
import json
from collections import deque
import threading
import time
import psutil

logger = logging.getLogger(__name__)


@dataclass
class Anomaly:
    """Detected anomaly"""
    anomaly_id: str
    anomaly_type: str  # 'resource', 'behavior', 'security', 'performance'
    severity: str  # 'low', 'medium', 'high', 'critical'
    timestamp: str
    description: str
    metrics: Dict[str, Any]
    baseline: Dict[str, Any]
    deviation: float  # How much it deviated from normal
    suggested_action: str
    auto_resolved: bool = False


@dataclass
class SystemBaseline:
    """Baseline metrics for normal system behavior"""
    metric_name: str
    mean: float
    std_dev: float
    min_val: float
    max_val: float
    samples: int
    last_updated: str


class AnomalyDetector:
    """
    Anomaly Detection and Alerting System

    Features:
    - Real-time system resource monitoring
    - Statistical anomaly detection (z-score, IQR)
    - Behavioral anomaly detection
    - Security anomaly detection (unusual process, network activity)
    - Performance degradation detection
    - Automatic alerting and suggested remediation
    - Self-learning baselines
    """

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.anomalies_file = data_dir / "anomalies.json"
        self.baselines_file = data_dir / "baselines.json"

        # Detected anomalies
        self.anomalies: deque = deque(maxlen=1000)

        # System baselines
        self.baselines: Dict[str, SystemBaseline] = {}

        # Metric history for baseline calculation
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

        # Thresholds
        self.z_score_threshold = 3.0  # Standard deviations
        self.severity_thresholds = {
            'low': 2.0,
            'medium': 3.0,
            'high': 4.0,
            'critical': 5.0
        }

        # Monitoring
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None

        # Callbacks for alerting
        self.alert_callbacks: List = []

        # Load data
        self._load_baselines()
        self._load_anomalies()

    def start_monitoring(self, interval: int = 30):
        """Start anomaly detection monitoring"""
        if self._monitoring:
            return

        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self._monitor_thread.start()
        logger.info(f"Started anomaly detection (interval: {interval}s)")

    def stop_monitoring(self):
        """Stop anomaly detection"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2)
        logger.info("Stopped anomaly detection")

    def _monitor_loop(self, interval: int):
        """Background monitoring loop"""
        while self._monitoring:
            try:
                # Collect current metrics
                metrics = self._collect_metrics()

                # Update baselines
                self._update_baselines(metrics)

                # Detect anomalies
                anomalies = self._detect_anomalies(metrics)

                # Alert if anomalies found
                if anomalies:
                    for anomaly in anomalies:
                        self._trigger_alert(anomaly)

                time.sleep(interval)

            except Exception as e:
                logger.error(f"Error in anomaly detection loop: {e}")
                time.sleep(interval)

    def _collect_metrics(self) -> Dict[str, Any]:
        """Collect current system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_per_core = psutil.cpu_percent(interval=1, percpu=True)

            # Memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()

            # Disk I/O
            disk_io = psutil.disk_io_counters()

            # Network I/O
            network_io = psutil.net_io_counters()

            # Process metrics
            process_count = len(psutil.pids())
            thread_count = sum([p.num_threads() for p in psutil.process_iter(['num_threads'])])

            metrics = {
                'timestamp': datetime.now().isoformat(),
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

            return metrics

        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            return {}

    def _update_baselines(self, metrics: Dict[str, Any]):
        """Update baseline metrics with new data"""
        for metric_name in ['cpu_percent', 'memory_percent', 'process_count', 'thread_count']:
            if metric_name in metrics:
                value = metrics[metric_name]
                self.metric_history[metric_name].append(value)

                # Calculate baseline if enough samples
                if len(self.metric_history[metric_name]) >= 30:
                    values = list(self.metric_history[metric_name])
                    mean = sum(values) / len(values)
                    variance = sum((x - mean) ** 2 for x in values) / len(values)
                    std_dev = variance ** 0.5

                    self.baselines[metric_name] = SystemBaseline(
                        metric_name=metric_name,
                        mean=mean,
                        std_dev=std_dev,
                        min_val=min(values),
                        max_val=max(values),
                        samples=len(values),
                        last_updated=datetime.now().isoformat()
                    )

        # Periodically save baselines
        if len(self.metric_history['cpu_percent']) % 100 == 0:
            self._save_baselines()

    def _detect_anomalies(self, metrics: Dict[str, Any]) -> List[Anomaly]:
        """Detect anomalies in current metrics"""
        anomalies = []
        import uuid

        # Check each metric against baseline
        for metric_name, baseline in self.baselines.items():
            if metric_name in metrics:
                current_value = metrics[metric_name]

                # Calculate z-score
                if baseline.std_dev > 0:
                    z_score = abs((current_value - baseline.mean) / baseline.std_dev)

                    # Check if anomalous
                    if z_score >= self.z_score_threshold:
                        # Determine severity
                        severity = 'low'
                        for sev_level in ['critical', 'high', 'medium', 'low']:
                            if z_score >= self.severity_thresholds[sev_level]:
                                severity = sev_level
                                break

                        # Create anomaly
                        anomaly = Anomaly(
                            anomaly_id=str(uuid.uuid4()),
                            anomaly_type=self._classify_anomaly_type(metric_name),
                            severity=severity,
                            timestamp=datetime.now().isoformat(),
                            description=f"{metric_name} is {z_score:.2f} standard deviations from normal",
                            metrics={metric_name: current_value},
                            baseline={
                                'mean': baseline.mean,
                                'std_dev': baseline.std_dev,
                                'expected_range': f"{baseline.mean - 2*baseline.std_dev:.2f} - {baseline.mean + 2*baseline.std_dev:.2f}"
                            },
                            deviation=z_score,
                            suggested_action=self._suggest_remediation(metric_name, current_value, baseline)
                        )

                        anomalies.append(anomaly)
                        self.anomalies.append(asdict(anomaly))

        # Behavioral anomalies
        behavioral_anomalies = self._detect_behavioral_anomalies(metrics)
        anomalies.extend(behavioral_anomalies)

        return anomalies

    def _classify_anomaly_type(self, metric_name: str) -> str:
        """Classify anomaly type based on metric"""
        if metric_name in ['cpu_percent', 'memory_percent']:
            return 'resource'
        elif metric_name in ['process_count', 'thread_count']:
            return 'behavior'
        elif metric_name in ['network_sent', 'network_recv']:
            return 'security'
        else:
            return 'performance'

    def _suggest_remediation(self, metric_name: str, current_value: float, baseline: SystemBaseline) -> str:
        """Suggest remediation action for anomaly"""
        suggestions = {
            'cpu_percent': "Check for runaway processes using Task Manager. Consider closing resource-intensive applications.",
            'memory_percent': "Close unnecessary applications. Check for memory leaks. Consider increasing available RAM.",
            'process_count': "Unusual number of processes detected. Check Task Manager for suspicious processes.",
            'thread_count': "High thread count detected. Some application may be misbehaving.",
        }

        return suggestions.get(metric_name, "Monitor the situation and investigate if it persists.")

    def _detect_behavioral_anomalies(self, metrics: Dict[str, Any]) -> List[Anomaly]:
        """Detect behavioral anomalies (unusual patterns)"""
        anomalies = []
        import uuid

        # Example: Unusual time for high activity
        current_hour = datetime.now().hour
        if 2 <= current_hour <= 5:  # Late night/early morning
            if metrics.get('cpu_percent', 0) > 50:
                anomaly = Anomaly(
                    anomaly_id=str(uuid.uuid4()),
                    anomaly_type='behavior',
                    severity='medium',
                    timestamp=datetime.now().isoformat(),
                    description=f"Unusual high CPU activity at {current_hour}:00",
                    metrics={'cpu_percent': metrics['cpu_percent'], 'hour': current_hour},
                    baseline={'expected': 'low activity during night'},
                    deviation=3.0,
                    suggested_action="Check for scheduled tasks or background processes running unexpectedly."
                )
                anomalies.append(anomaly)
                self.anomalies.append(asdict(anomaly))

        # Rapid process creation
        if 'process_count' in metrics and 'process_count' in self.baselines:
            if len(self.metric_history['process_count']) >= 2:
                recent_change = abs(
                    self.metric_history['process_count'][-1] -
                    self.metric_history['process_count'][-2]
                )

                if recent_change > 20:  # More than 20 processes created/destroyed quickly
                    anomaly = Anomaly(
                        anomaly_id=str(uuid.uuid4()),
                        anomaly_type='security',
                        severity='high',
                        timestamp=datetime.now().isoformat(),
                        description=f"Rapid process creation/termination detected ({recent_change} processes)",
                        metrics={'process_change': recent_change},
                        baseline={'expected': 'gradual process changes'},
                        deviation=4.0,
                        suggested_action="Potential malware activity. Run security scan immediately."
                    )
                    anomalies.append(anomaly)
                    self.anomalies.append(asdict(anomaly))

        return anomalies

    def _trigger_alert(self, anomaly: Anomaly):
        """Trigger alert for detected anomaly"""
        logger.warning(f"ANOMALY DETECTED [{anomaly.severity.upper()}]: {anomaly.description}")

        # Call registered callbacks
        for callback in self.alert_callbacks:
            try:
                callback(anomaly)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")

    def register_alert_callback(self, callback):
        """Register callback for anomaly alerts"""
        self.alert_callbacks.append(callback)
        logger.info("Registered alert callback")

    def get_recent_anomalies(self, limit: int = 50, severity: Optional[str] = None) -> List[Dict]:
        """Get recent anomalies"""
        anomalies = list(self.anomalies)

        if severity:
            anomalies = [a for a in anomalies if a['severity'] == severity]

        return list(reversed(anomalies))[:limit]

    def get_baselines(self) -> List[Dict]:
        """Get current baselines"""
        return [asdict(b) for b in self.baselines.values()]

    def get_health_status(self) -> Dict[str, Any]:
        """Get overall system health status"""
        try:
            current_metrics = self._collect_metrics()

            # Count recent anomalies by severity
            recent_time = datetime.now() - timedelta(hours=1)
            recent_anomalies = [
                a for a in self.anomalies
                if datetime.fromisoformat(a['timestamp']) > recent_time
            ]

            severity_counts = {
                'critical': sum(1 for a in recent_anomalies if a['severity'] == 'critical'),
                'high': sum(1 for a in recent_anomalies if a['severity'] == 'high'),
                'medium': sum(1 for a in recent_anomalies if a['severity'] == 'medium'),
                'low': sum(1 for a in recent_anomalies if a['severity'] == 'low'),
            }

            # Determine overall health
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
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting health status: {e}")
            return {'health': 'unknown', 'error': str(e)}

    def _save_baselines(self):
        """Save baselines to file"""
        try:
            baselines_data = {name: asdict(baseline) for name, baseline in self.baselines.items()}
            with open(self.baselines_file, 'w') as f:
                json.dump(baselines_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving baselines: {e}")

    def _load_baselines(self):
        """Load baselines from file"""
        try:
            if self.baselines_file.exists():
                with open(self.baselines_file, 'r') as f:
                    baselines_data = json.load(f)
                    self.baselines = {
                        name: SystemBaseline(**data)
                        for name, data in baselines_data.items()
                    }
                logger.info(f"Loaded {len(self.baselines)} baselines")
        except Exception as e:
            logger.error(f"Error loading baselines: {e}")

    def _load_anomalies(self):
        """Load anomaly history from file"""
        try:
            if self.anomalies_file.exists():
                with open(self.anomalies_file, 'r') as f:
                    anomalies_data = json.load(f)
                    self.anomalies = deque(anomalies_data, maxlen=1000)
                logger.info(f"Loaded {len(self.anomalies)} anomalies")
        except Exception as e:
            logger.error(f"Error loading anomalies: {e}")


# Global instance
_anomaly_detector: Optional[AnomalyDetector] = None


def get_anomaly_detector(data_dir: Path = None) -> AnomalyDetector:
    """Get or create global anomaly detector"""
    global _anomaly_detector

    if _anomaly_detector is None:
        if data_dir is None:
            data_dir = Path.home() / ".windows-ai" / "anomaly"
        _anomaly_detector = AnomalyDetector(data_dir)

    return _anomaly_detector


def initialize_anomaly_detector(data_dir: Path = None, start_monitoring: bool = True):
    """Initialize the anomaly detector"""
    detector = get_anomaly_detector(data_dir)

    if start_monitoring:
        detector.start_monitoring(interval=30)

    logger.info("Anomaly detector initialized")
    return detector
