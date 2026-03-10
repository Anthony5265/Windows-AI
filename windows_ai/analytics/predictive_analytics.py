"""Predictive analytics and forecasting.

Time-series forecasting and predictive alerting.
"""

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ForecastModel(str, Enum):
    """Forecasting models."""
    SIMPLE_EXPONENTIAL = "simple_exponential"
    DOUBLE_EXPONENTIAL = "double_exponential"
    LINEAR = "linear"
    SEASONAL = "seasonal"


@dataclass
class Forecast:
    """Time-series forecast."""
    metric_name: str
    model_type: ForecastModel
    forecast_points: List[Tuple[datetime, float]]
    confidence_interval_lower: List[float]
    confidence_interval_upper: List[float]
    mean_absolute_error: float
    root_mean_square_error: float
    created_at: datetime
    valid_until: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metric": self.metric_name,
            "model": self.model_type.value,
            "forecast_points": [
                {"timestamp": ts.isoformat(), "value": val}
                for ts, val in self.forecast_points
            ],
            "mae": f"{self.mean_absolute_error:.2f}",
            "rmse": f"{self.root_mean_square_error:.2f}",
            "created_at": self.created_at.isoformat(),
            "valid_until": self.valid_until.isoformat(),
        }


@dataclass
class PredictiveAlert:
    """Alert based on predictive threshold."""
    metric_name: str
    predicted_threshold_breach_at: datetime
    confidence: float
    recommendation: str
    alert_id: str
    created_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metric": self.metric_name,
            "predicted_breach_at": self.predicted_threshold_breach_at.isoformat(),
            "confidence": f"{self.confidence:.1f}%",
            "recommendation": self.recommendation,
            "alert_id": self.alert_id,
            "created_at": self.created_at.isoformat(),
        }


class PredictiveAnalytics:
    """Predictive analytics engine."""

    def __init__(self):
        """Initialize predictive analytics."""
        self.forecasts: Dict[str, Forecast] = {}
        self.predictive_alerts: List[PredictiveAlert] = []
        self.thresholds: Dict[str, float] = {
            "api_latency_p99_ms": 2000,
            "error_rate_pct": 5,
            "cpu_usage_pct": 85,
            "memory_usage_pct": 90,
            "db_connections": 100,
        }

    async def forecast_metric(
        self,
        metric_name: str,
        values: List[float],
        timestamps: List[datetime],
        forecast_points: int = 12,
        model: ForecastModel = ForecastModel.SIMPLE_EXPONENTIAL,
    ) -> Optional[Forecast]:
        """Forecast metric values.

        Args:
            metric_name: Name of metric
            values: Historical values
            timestamps: Corresponding timestamps
            forecast_points: Number of points to forecast
            model: Forecasting model to use

        Returns:
            Forecast or None
        """
        if len(values) < 4:
            return None

        if model == ForecastModel.SIMPLE_EXPONENTIAL:
            return await self._forecast_simple_exponential(
                metric_name, values, timestamps, forecast_points
            )
        elif model == ForecastModel.LINEAR:
            return await self._forecast_linear(
                metric_name, values, timestamps, forecast_points
            )
        else:
            return await self._forecast_simple_exponential(
                metric_name, values, timestamps, forecast_points
            )

    async def _forecast_simple_exponential(
        self,
        metric_name: str,
        values: List[float],
        timestamps: List[datetime],
        forecast_points: int,
    ) -> Forecast:
        """Simple exponential smoothing forecast."""
        alpha = 0.3  # Smoothing factor

        # Initialize with first value
        smoothed = [values[0]]

        # Apply exponential smoothing
        for i in range(1, len(values)):
            smoothed.append(alpha * values[i] + (1 - alpha) * smoothed[-1])

        # Generate forecast
        last_smoothed = smoothed[-1]
        forecast_values = [last_smoothed] * forecast_points

        # Generate timestamps for forecast
        if len(timestamps) >= 2:
            interval = (timestamps[-1] - timestamps[-2]).total_seconds()
        else:
            interval = 60

        forecast_ts = [
            timestamps[-1] + timedelta(seconds=interval * (i + 1))
            for i in range(forecast_points)
        ]

        # Calculate errors
        mae = sum(abs(values[i] - smoothed[i]) for i in range(len(values))) / len(values)
        rmse = (sum((values[i] - smoothed[i]) ** 2 for i in range(len(values))) / len(values)) ** 0.5

        # Confidence intervals
        std_error = rmse / (len(values) ** 0.5)
        ci_lower = [v - 1.96 * std_error for v in forecast_values]
        ci_upper = [v + 1.96 * std_error for v in forecast_values]

        forecast = Forecast(
            metric_name=metric_name,
            model_type=ForecastModel.SIMPLE_EXPONENTIAL,
            forecast_points=list(zip(forecast_ts, forecast_values)),
            confidence_interval_lower=ci_lower,
            confidence_interval_upper=ci_upper,
            mean_absolute_error=mae,
            root_mean_square_error=rmse,
            created_at=datetime.now(),
            valid_until=datetime.now() + timedelta(hours=1),
        )

        self.forecasts[metric_name] = forecast
        return forecast

    async def _forecast_linear(
        self,
        metric_name: str,
        values: List[float],
        timestamps: List[datetime],
        forecast_points: int,
    ) -> Forecast:
        """Linear trend forecast."""
        n = len(values)
        x_vals = list(range(n))
        mean_x = sum(x_vals) / n
        mean_y = sum(values) / n

        # Calculate slope
        slope_num = sum((x_vals[i] - mean_x) * (values[i] - mean_y) for i in range(n))
        slope_den = sum((x - mean_x) ** 2 for x in x_vals)

        if slope_den == 0:
            slope = 0
        else:
            slope = slope_num / slope_den

        intercept = mean_y - slope * mean_x

        # Generate forecast
        forecast_x = list(range(n, n + forecast_points))
        forecast_values = [slope * x + intercept for x in forecast_x]

        # Generate timestamps
        if len(timestamps) >= 2:
            interval = (timestamps[-1] - timestamps[-2]).total_seconds()
        else:
            interval = 60

        forecast_ts = [
            timestamps[-1] + timedelta(seconds=interval * (i + 1))
            for i in range(forecast_points)
        ]

        # Calculate errors
        fitted = [slope * x + intercept for x in x_vals]
        mae = sum(abs(values[i] - fitted[i]) for i in range(n)) / n
        rmse = (sum((values[i] - fitted[i]) ** 2 for i in range(n)) / n) ** 0.5

        # Confidence intervals
        std_error = rmse / (n ** 0.5)
        ci_lower = [v - 1.96 * std_error for v in forecast_values]
        ci_upper = [v + 1.96 * std_error for v in forecast_values]

        forecast = Forecast(
            metric_name=metric_name,
            model_type=ForecastModel.LINEAR,
            forecast_points=list(zip(forecast_ts, forecast_values)),
            confidence_interval_lower=ci_lower,
            confidence_interval_upper=ci_upper,
            mean_absolute_error=mae,
            root_mean_square_error=rmse,
            created_at=datetime.now(),
            valid_until=datetime.now() + timedelta(hours=1),
        )

        self.forecasts[metric_name] = forecast
        return forecast

    async def predict_threshold_breach(
        self,
        metric_name: str,
        forecast: Forecast,
        threshold: Optional[float] = None,
    ) -> Optional[PredictiveAlert]:
        """Predict when metric will breach threshold.

        Args:
            metric_name: Name of metric
            forecast: Forecast for metric
            threshold: Threshold value (uses default if None)

        Returns:
            Predictive alert or None
        """
        if threshold is None:
            threshold = self.thresholds.get(metric_name)

        if threshold is None:
            return None

        for ts, value in forecast.forecast_points:
            if value >= threshold:
                # Calculate confidence based on forecast error
                confidence = max(0, 100 - forecast.root_mean_square_error * 10)

                alert_id = f"{metric_name}_{ts.timestamp()}"

                alert = PredictiveAlert(
                    metric_name=metric_name,
                    predicted_threshold_breach_at=ts,
                    confidence=confidence,
                    recommendation=f"Consider scaling resources or investigating {metric_name}",
                    alert_id=alert_id,
                    created_at=datetime.now(),
                )

                self.predictive_alerts.append(alert)
                return alert

        return None

    async def get_predictive_summary(self) -> Dict[str, Any]:
        """Get predictive analytics summary.

        Returns:
            Summary of predictions and alerts
        """
        return {
            "forecasts_count": len(self.forecasts),
            "forecast_metrics": list(self.forecasts.keys()),
            "predictive_alerts_count": len(self.predictive_alerts),
            "recent_alerts": [
                alert.to_dict()
                for alert in self.predictive_alerts[-5:]
            ],
            "forecast_accuracy": self._calculate_average_accuracy(),
        }

    def _calculate_average_accuracy(self) -> str:
        """Calculate average forecast accuracy."""
        if not self.forecasts:
            return "N/A"

        total_rmse = sum(f.root_mean_square_error for f in self.forecasts.values())
        avg_rmse = total_rmse / len(self.forecasts)

        # Convert to percentage accuracy (assuming 100% is 0 RMSE)
        accuracy = max(0, 100 - avg_rmse * 10)

        return f"{accuracy:.1f}%"

    async def register_threshold(self, metric_name: str, threshold: float):
        """Register a metric threshold for breach prediction.

        Args:
            metric_name: Name of metric
            threshold: Threshold value
        """
        self.thresholds[metric_name] = threshold
