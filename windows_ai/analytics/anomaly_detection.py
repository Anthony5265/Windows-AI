"""Advanced analytics and anomaly detection.

Statistical analysis, trend detection, and anomaly identification.
"""

import statistics
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AnomalyType(str, Enum):
    """Types of anomalies detected."""
    STATISTICAL = "statistical"
    TREND = "trend"
    SEASONAL = "seasonal"
    SPIKE = "spike"
    DIP = "dip"


@dataclass
class Anomaly:
    """Detected anomaly."""
    anomaly_type: AnomalyType
    metric_name: str
    detected_at: datetime
    expected_value: float
    actual_value: float
    deviation_percent: float
    severity: str  # "low", "medium", "high"
    explanation: str
    start_time: datetime
    end_time: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.anomaly_type.value,
            "metric": self.metric_name,
            "detected_at": self.detected_at.isoformat(),
            "expected": self.expected_value,
            "actual": self.actual_value,
            "deviation": f"{self.deviation_percent:.1f}%",
            "severity": self.severity,
            "explanation": self.explanation,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
        }


@dataclass
class Trend:
    """Detected trend in metrics."""
    metric_name: str
    direction: str  # "increasing", "decreasing", "stable"
    slope: float
    r_squared: float  # Goodness of fit
    start_time: datetime
    end_time: datetime
    confidence: float
    historical_avg: float
    current_avg: float
    projected_value: float
    time_to_threshold: Optional[timedelta] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metric": self.metric_name,
            "direction": self.direction,
            "slope": self.slope,
            "r_squared": f"{self.r_squared:.3f}",
            "confidence": f"{self.confidence:.1f}%",
            "historical_avg": self.historical_avg,
            "current_avg": self.current_avg,
            "projected_value": self.projected_value,
            "time_to_threshold": str(self.time_to_threshold) if self.time_to_threshold else None,
        }


@dataclass
class CorrelationAnalysis:
    """Correlation between two metrics."""
    metric_a: str
    metric_b: str
    correlation_coefficient: float
    p_value: float
    is_significant: bool
    relationship_type: str  # "positive", "negative", "no_correlation"
    analysis_window_minutes: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metric_a": self.metric_a,
            "metric_b": self.metric_b,
            "correlation": f"{self.correlation_coefficient:.3f}",
            "p_value": f"{self.p_value:.6f}",
            "significant": self.is_significant,
            "relationship": self.relationship_type,
            "window_minutes": self.analysis_window_minutes,
        }


class AdvancedAnalytics:
    """Advanced analytics engine for metrics."""

    def __init__(self):
        """Initialize analytics engine."""
        self.anomalies: List[Anomaly] = []
        self.trends: List[Trend] = []
        self.correlations: List[CorrelationAnalysis] = []
        self.baseline_stats: Dict[str, Dict[str, float]] = {}

    async def detect_anomalies(
        self,
        metric_name: str,
        values: List[float],
        timestamps: List[datetime],
        sensitivity: float = 2.0,  # Standard deviations
    ) -> List[Anomaly]:
        """Detect statistical anomalies using Z-score.

        Args:
            metric_name: Name of metric
            values: Metric values
            timestamps: Corresponding timestamps
            sensitivity: Number of standard deviations for threshold

        Returns:
            Detected anomalies
        """
        if len(values) < 3:
            return []

        try:
            mean = statistics.mean(values)
            stdev = statistics.stdev(values)
        except Exception:
            return []

        anomalies = []
        for i, value in enumerate(values):
            if stdev == 0:
                continue

            z_score = abs((value - mean) / stdev)
            if z_score > sensitivity:
                deviation_percent = abs((value - mean) / mean * 100) if mean != 0 else 0

                anomaly = Anomaly(
                    anomaly_type=AnomalyType.SPIKE if value > mean else AnomalyType.DIP,
                    metric_name=metric_name,
                    detected_at=datetime.now(),
                    expected_value=mean,
                    actual_value=value,
                    deviation_percent=deviation_percent,
                    severity="high" if z_score > 3 else "medium" if z_score > 2 else "low",
                    explanation=f"Value {value:.2f} is {z_score:.1f} standard deviations from mean",
                    start_time=timestamps[i],
                    end_time=timestamps[i],
                )
                anomalies.append(anomaly)

        self.anomalies.extend(anomalies)
        return anomalies

    async def detect_trends(
        self,
        metric_name: str,
        values: List[float],
        timestamps: List[datetime],
        threshold: float = 100,
    ) -> Optional[Trend]:
        """Detect trends in metric values.

        Args:
            metric_name: Name of metric
            values: Metric values
            timestamps: Corresponding timestamps
            threshold: Threshold for trend detection

        Returns:
            Detected trend or None
        """
        if len(values) < 4:
            return None

        # Simple linear regression
        n = len(values)
        x_vals = list(range(n))
        mean_x = sum(x_vals) / n
        mean_y = sum(values) / n

        slope_numerator = sum(
            (x_vals[i] - mean_x) * (values[i] - mean_y)
            for i in range(n)
        )
        slope_denominator = sum((x - mean_x) ** 2 for x in x_vals)

        if slope_denominator == 0:
            return None

        slope = slope_numerator / slope_denominator

        # Calculate R-squared
        residuals = sum((values[i] - (mean_y + slope * (x_vals[i] - mean_x))) ** 2 for i in range(n))
        total_ss = sum((v - mean_y) ** 2 for v in values)
        r_squared = 1 - (residuals / total_ss) if total_ss != 0 else 0

        # Determine direction
        if abs(slope) < 0.1:
            direction = "stable"
            confidence = 60.0
        elif slope > 0:
            direction = "increasing"
            confidence = min(90.0, r_squared * 100)
        else:
            direction = "decreasing"
            confidence = min(90.0, r_squared * 100)

        # Calculate historical and current averages
        historical_avg = statistics.mean(values[:len(values)//2])
        current_avg = statistics.mean(values[len(values)//2:])

        # Project future value
        projected_value = current_avg + (slope * 10)

        # Calculate time to threshold if increasing/decreasing
        time_to_threshold = None
        if direction == "increasing" and slope > 0:
            steps_needed = (threshold - current_avg) / slope if slope != 0 else 0
            time_to_threshold = timedelta(
                minutes=int(steps_needed * (timestamps[-1] - timestamps[0]).total_seconds() / 60 / n)
            )
        elif direction == "decreasing" and slope < 0:
            steps_needed = (current_avg - threshold) / abs(slope) if slope != 0 else 0
            time_to_threshold = timedelta(
                minutes=int(steps_needed * (timestamps[-1] - timestamps[0]).total_seconds() / 60 / n)
            )

        trend = Trend(
            metric_name=metric_name,
            direction=direction,
            slope=slope,
            r_squared=r_squared,
            start_time=timestamps[0],
            end_time=timestamps[-1],
            confidence=confidence,
            historical_avg=historical_avg,
            current_avg=current_avg,
            projected_value=projected_value,
            time_to_threshold=time_to_threshold,
        )

        self.trends.append(trend)
        return trend

    async def analyze_correlations(
        self,
        metric_a_values: List[float],
        metric_b_values: List[float],
        metric_a_name: str,
        metric_b_name: str,
        window_minutes: int = 60,
    ) -> Optional[CorrelationAnalysis]:
        """Analyze correlation between two metrics.

        Args:
            metric_a_values: First metric values
            metric_b_values: Second metric values
            metric_a_name: First metric name
            metric_b_name: Second metric name
            window_minutes: Analysis window

        Returns:
            Correlation analysis or None
        """
        if len(metric_a_values) < 2 or len(metric_b_values) < 2:
            return None

        if len(metric_a_values) != len(metric_b_values):
            return None

        # Calculate Pearson correlation coefficient
        n = len(metric_a_values)
        mean_a = statistics.mean(metric_a_values)
        mean_b = statistics.mean(metric_b_values)

        covariance = sum(
            (metric_a_values[i] - mean_a) * (metric_b_values[i] - mean_b)
            for i in range(n)
        ) / n

        stdev_a = statistics.stdev(metric_a_values) if len(metric_a_values) > 1 else 0
        stdev_b = statistics.stdev(metric_b_values) if len(metric_b_values) > 1 else 0

        if stdev_a == 0 or stdev_b == 0:
            correlation = 0.0
        else:
            correlation = covariance / (stdev_a * stdev_b)

        # Simple p-value estimation (approximate)
        t_stat = correlation * (n - 2) ** 0.5 / (1 - correlation ** 2 + 1e-10) ** 0.5
        p_value = 0.05 if abs(t_stat) > 2 else 0.5  # Simplified

        is_significant = p_value < 0.05 and abs(correlation) > 0.3

        if correlation > 0.3:
            relationship = "positive"
        elif correlation < -0.3:
            relationship = "negative"
        else:
            relationship = "no_correlation"

        analysis = CorrelationAnalysis(
            metric_a=metric_a_name,
            metric_b=metric_b_name,
            correlation_coefficient=correlation,
            p_value=p_value,
            is_significant=is_significant,
            relationship_type=relationship,
            analysis_window_minutes=window_minutes,
        )

        self.correlations.append(analysis)
        return analysis

    async def update_baseline(
        self,
        metric_name: str,
        values: List[float],
    ):
        """Update baseline statistics for a metric.

        Args:
            metric_name: Name of metric
            values: Historical values
        """
        if values:
            self.baseline_stats[metric_name] = {
                "mean": statistics.mean(values),
                "stdev": statistics.stdev(values) if len(values) > 1 else 0,
                "min": min(values),
                "max": max(values),
                "median": statistics.median(values),
            }

    async def get_analytics_report(self) -> Dict[str, Any]:
        """Generate comprehensive analytics report.

        Returns:
            Analytics summary and insights
        """
        if not self.anomalies and not self.trends and not self.correlations:
            return {
                "anomaly_count": 0,
                "trend_count": 0,
                "correlation_count": 0,
                "insights": ["No significant patterns detected"],
            }

        # Calculate insights
        insights = []

        # Anomaly insights
        if self.anomalies:
            critical_anomalies = [a for a in self.anomalies if a.severity == "high"]
            if critical_anomalies:
                insights.append(f"Detected {len(critical_anomalies)} critical anomalies")

        # Trend insights
        increasing_trends = [t for t in self.trends if t.direction == "increasing"]
        decreasing_trends = [t for t in self.trends if t.direction == "decreasing"]

        if increasing_trends:
            insights.append(f"Found {len(increasing_trends)} increasing trends")
        if decreasing_trends:
            insights.append(f"Found {len(decreasing_trends)} decreasing trends")

        # Correlation insights
        significant_corr = [c for c in self.correlations if c.is_significant]
        if significant_corr:
            insights.append(f"Identified {len(significant_corr)} significant correlations")

        return {
            "anomaly_count": len(self.anomalies),
            "critical_anomalies": len([a for a in self.anomalies if a.severity == "high"]),
            "trend_count": len(self.trends),
            "increasing_trends": len(increasing_trends),
            "decreasing_trends": len(decreasing_trends),
            "correlation_count": len(self.correlations),
            "significant_correlations": len(significant_corr),
            "insights": insights,
            "recent_anomalies": [a.to_dict() for a in self.anomalies[-10:]],
            "active_trends": [t.to_dict() for t in self.trends[-10:]],
        }
