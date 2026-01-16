"""Monitoring dashboard with Prometheus integration.

Real-time system monitoring, alerting, and visualization support.
"""

import json
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    RESOLVED = "resolved"


class MetricCategory(str, Enum):
    """Dashboard metric categories."""
    API_REQUESTS = "api_requests"
    DATABASE = "database"
    CACHE = "cache"
    SYSTEM = "system"
    CUSTOM = "custom"


@dataclass
class DashboardWidget:
    """Dashboard widget configuration."""
    widget_id: str
    title: str
    category: MetricCategory
    metric_name: str
    chart_type: str  # "line", "bar", "gauge", "table"
    refresh_interval_seconds: int = 30
    y_axis_label: str = ""
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None
    tags: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "widget_id": self.widget_id,
            "title": self.title,
            "category": self.category.value,
            "metric_name": self.metric_name,
            "chart_type": self.chart_type,
            "refresh_interval_seconds": self.refresh_interval_seconds,
            "y_axis_label": self.y_axis_label,
            "threshold_warning": self.threshold_warning,
            "threshold_critical": self.threshold_critical,
            "tags": self.tags,
        }


@dataclass
class Alert:
    """Alert configuration and instance."""
    alert_id: str
    title: str
    metric_name: str
    condition: str  # e.g., "> 1000"
    severity: AlertSeverity
    enabled: bool = True
    notification_channels: List[str] = field(default_factory=list)  # "email", "slack", "pagerduty"
    created_at: datetime = field(default_factory=datetime.now)
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "alert_id": self.alert_id,
            "title": self.title,
            "metric_name": self.metric_name,
            "condition": self.condition,
            "severity": self.severity.value,
            "enabled": self.enabled,
            "notification_channels": self.notification_channels,
            "created_at": self.created_at.isoformat(),
            "last_triggered": self.last_triggered.isoformat() if self.last_triggered else None,
            "trigger_count": self.trigger_count,
        }


@dataclass
class AlertEvent:
    """Alert event instance."""
    alert_id: str
    triggered_at: datetime
    severity: AlertSeverity
    metric_value: float
    metric_name: str
    condition: str
    message: str
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "alert_id": self.alert_id,
            "triggered_at": self.triggered_at.isoformat(),
            "severity": self.severity.value,
            "metric_value": self.metric_value,
            "metric_name": self.metric_name,
            "condition": self.condition,
            "message": self.message,
            "acknowledged": self.acknowledged,
            "acknowledged_by": self.acknowledged_by,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
        }


@dataclass
class PrometheusMetric:
    """Prometheus metric in OpenMetrics format."""
    name: str
    metric_type: str  # "counter", "gauge", "histogram", "summary"
    help_text: str
    unit: str = ""
    value: float = 0.0
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp_ms: Optional[int] = None

    def to_prometheus_format(self) -> str:
        """Convert to Prometheus format."""
        full_name = self.name
        if self.unit:
            full_name = f"{self.name}_{self.unit}"

        label_str = ""
        if self.labels:
            label_pairs = [f'{k}="{v}"' for k, v in self.labels.items()]
            label_str = "{" + ",".join(label_pairs) + "}"

        timestamp_str = ""
        if self.timestamp_ms:
            timestamp_str = f" {self.timestamp_ms}"

        return f"{full_name}{label_str} {self.value}{timestamp_str}"


class MonitoringDashboard:
    """Manages dashboard configuration and display."""

    def __init__(self):
        """Initialize dashboard."""
        self.widgets: Dict[str, DashboardWidget] = {}
        self.alerts: Dict[str, Alert] = {}
        self.alert_events: List[AlertEvent] = []
        self.active_incidents: Dict[str, AlertEvent] = {}
        self.metrics_registry: Dict[str, PrometheusMetric] = {}

    async def add_widget(self, widget: DashboardWidget):
        """Add dashboard widget.

        Args:
            widget: Widget configuration
        """
        self.widgets[widget.widget_id] = widget
        logger.info(f"Added widget: {widget.title}")

    async def remove_widget(self, widget_id: str):
        """Remove dashboard widget.

        Args:
            widget_id: Widget ID
        """
        if widget_id in self.widgets:
            del self.widgets[widget_id]
            logger.info(f"Removed widget: {widget_id}")

    async def create_alert(self, alert: Alert):
        """Create alert.

        Args:
            alert: Alert configuration
        """
        self.alerts[alert.alert_id] = alert
        logger.info(f"Created alert: {alert.title}")

    async def trigger_alert(
        self,
        alert_id: str,
        metric_value: float,
        metric_name: str,
    ):
        """Trigger an alert.

        Args:
            alert_id: Alert ID
            metric_value: Current metric value
            metric_name: Metric name
        """
        if alert_id not in self.alerts:
            return

        alert = self.alerts[alert_id]
        if not alert.enabled:
            return

        event = AlertEvent(
            alert_id=alert_id,
            triggered_at=datetime.now(),
            severity=alert.severity,
            metric_value=metric_value,
            metric_name=metric_name,
            condition=alert.condition,
            message=f"{alert.title}: {metric_name}={metric_value} {alert.condition}",
        )

        self.alert_events.append(event)
        self.active_incidents[alert_id] = event
        alert.last_triggered = datetime.now()
        alert.trigger_count += 1

        logger.warning(f"Alert triggered: {event.message}")

    async def acknowledge_alert(
        self,
        alert_id: str,
        acknowledged_by: str,
    ):
        """Acknowledge an alert.

        Args:
            alert_id: Alert ID
            acknowledged_by: User acknowledging
        """
        if alert_id in self.active_incidents:
            event = self.active_incidents[alert_id]
            event.acknowledged = True
            event.acknowledged_by = acknowledged_by
            event.acknowledged_at = datetime.now()
            logger.info(f"Alert acknowledged by {acknowledged_by}: {alert_id}")

    async def resolve_alert(self, alert_id: str):
        """Resolve an alert.

        Args:
            alert_id: Alert ID
        """
        if alert_id in self.active_incidents:
            del self.active_incidents[alert_id]
            logger.info(f"Alert resolved: {alert_id}")

    async def register_metric(
        self,
        name: str,
        metric_type: str,
        help_text: str,
        unit: str = "",
    ):
        """Register Prometheus metric.

        Args:
            name: Metric name
            metric_type: Type (counter, gauge, histogram, summary)
            help_text: Help text
            unit: Unit of measurement
        """
        self.metrics_registry[name] = PrometheusMetric(
            name=name,
            metric_type=metric_type,
            help_text=help_text,
            unit=unit,
        )

    async def record_metric(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
    ):
        """Record metric value.

        Args:
            name: Metric name
            value: Metric value
            labels: Optional labels
        """
        if name in self.metrics_registry:
            self.metrics_registry[name].value = value
            self.metrics_registry[name].labels = labels or {}
            self.metrics_registry[name].timestamp_ms = int(datetime.now().timestamp() * 1000)

    async def get_dashboard_config(self) -> Dict[str, Any]:
        """Get complete dashboard configuration.

        Returns:
            Dashboard configuration
        """
        return {
            "widgets": [w.to_dict() for w in self.widgets.values()],
            "alerts": [a.to_dict() for a in self.alerts.values()],
            "active_incidents": len(self.active_incidents),
            "recent_events": [e.to_dict() for e in self.alert_events[-50:]],
        }

    async def get_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus format.

        Returns:
            Prometheus formatted metrics
        """
        output = []
        for metric in self.metrics_registry.values():
            # Add TYPE line
            output.append(f"# TYPE {metric.name} {metric.metric_type}")
            # Add HELP line
            output.append(f"# HELP {metric.name} {metric.help_text}")
            # Add metric line
            output.append(metric.to_prometheus_format())

        return "\n".join(output)

    async def get_incident_report(self) -> Dict[str, Any]:
        """Get incident report.

        Returns:
            Incident statistics and recent events
        """
        if not self.alert_events:
            return {
                "total_incidents": 0,
                "active_incidents": 0,
                "recent_events": [],
            }

        critical_count = sum(1 for e in self.alert_events if e.severity == AlertSeverity.CRITICAL)
        warning_count = sum(1 for e in self.alert_events if e.severity == AlertSeverity.WARNING)

        return {
            "total_incidents": len(self.alert_events),
            "active_incidents": len(self.active_incidents),
            "critical_count": critical_count,
            "warning_count": warning_count,
            "acknowledged_count": sum(1 for e in self.alert_events if e.acknowledged),
            "recent_events": [e.to_dict() for e in self.alert_events[-20:]],
        }

    async def get_health_status(self) -> Dict[str, Any]:
        """Get overall system health.

        Returns:
            Health status
        """
        if not self.active_incidents:
            return {
                "status": "healthy",
                "active_incidents": 0,
            }

        critical_incidents = [
            e for e in self.active_incidents.values()
            if e.severity == AlertSeverity.CRITICAL
        ]

        status = "critical" if critical_incidents else "degraded"

        return {
            "status": status,
            "active_incidents": len(self.active_incidents),
            "critical_incidents": len(critical_incidents),
            "incidents": [e.to_dict() for e in self.active_incidents.values()],
        }


class DashboardFactory:
    """Factory for creating pre-configured dashboards."""

    @staticmethod
    async def create_api_dashboard() -> MonitoringDashboard:
        """Create API monitoring dashboard.

        Returns:
            Configured dashboard
        """
        dashboard = MonitoringDashboard()

        # Add API widgets
        widgets = [
            DashboardWidget(
                widget_id="api_requests_per_second",
                title="API Requests/sec",
                category=MetricCategory.API_REQUESTS,
                metric_name="http_requests_total",
                chart_type="line",
                y_axis_label="Requests/sec",
                threshold_warning=1000,
                threshold_critical=5000,
            ),
            DashboardWidget(
                widget_id="api_response_time_p95",
                title="API Response Time (p95)",
                category=MetricCategory.API_REQUESTS,
                metric_name="http_request_duration_ms",
                chart_type="line",
                y_axis_label="Milliseconds",
                threshold_warning=500,
                threshold_critical=2000,
            ),
            DashboardWidget(
                widget_id="api_error_rate",
                title="API Error Rate",
                category=MetricCategory.API_REQUESTS,
                metric_name="http_errors_total",
                chart_type="gauge",
                y_axis_label="Percentage",
                threshold_warning=1.0,
                threshold_critical=5.0,
            ),
        ]

        for widget in widgets:
            await dashboard.add_widget(widget)

        return dashboard

    @staticmethod
    async def create_database_dashboard() -> MonitoringDashboard:
        """Create database monitoring dashboard.

        Returns:
            Configured dashboard
        """
        dashboard = MonitoringDashboard()

        widgets = [
            DashboardWidget(
                widget_id="db_query_time_p95",
                title="DB Query Time (p95)",
                category=MetricCategory.DATABASE,
                metric_name="db_query_duration_ms",
                chart_type="line",
                y_axis_label="Milliseconds",
                threshold_warning=100,
                threshold_critical=500,
            ),
            DashboardWidget(
                widget_id="db_connection_pool_usage",
                title="Connection Pool Usage",
                category=MetricCategory.DATABASE,
                metric_name="db_pool_connections_active",
                chart_type="gauge",
                threshold_warning=15,
                threshold_critical=19,
            ),
        ]

        for widget in widgets:
            await dashboard.add_widget(widget)

        return dashboard
