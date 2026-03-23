"""
Prophet-like Forecasting — Piecewise linear trend, Fourier seasonality, changepoint detection.
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
import logging, math, uuid
logger = logging.getLogger(__name__)


@dataclass
class ProphetForecastingResult:
    result_id: str
    predictions: List[float]
    trend: List[float]
    seasonal: List[float]
    changepoints: List[int]
    metrics: Dict[str, float]


class ProphetForecastingSystem:
    """Prophet-like decomposable time series model."""

    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[ProphetForecastingResult] = []
        logger.info("ProphetForecasting initialized")

    def _detect_changepoints(self, data: List[float], n_changepoints: int = 5) -> List[int]:
        n = len(data)
        if n < 10:
            return []
        candidates = [int(n * i / (n_changepoints + 1)) for i in range(1, n_changepoints + 1)]
        changes = []
        for cp in candidates:
            if cp < 2 or cp >= n - 2:
                continue
            left_slope = (data[cp] - data[max(0, cp - 3)]) / 3
            right_slope = (data[min(n - 1, cp + 3)] - data[cp]) / 3
            if abs(right_slope - left_slope) > abs(sum(data) / n) * 0.1:
                changes.append(cp)
        return changes

    def _fit_piecewise_trend(self, data: List[float], changepoints: List[int]) -> List[float]:
        n = len(data)
        segments = [0] + sorted(changepoints) + [n]
        trend = [0.0] * n
        for seg_idx in range(len(segments) - 1):
            start, end = segments[seg_idx], segments[seg_idx + 1]
            if end <= start:
                continue
            seg_data = data[start:end]
            seg_n = len(seg_data)
            x_mean = (seg_n - 1) / 2
            y_mean = sum(seg_data) / seg_n
            num = sum((i - x_mean) * (seg_data[i] - y_mean) for i in range(seg_n))
            den = sum((i - x_mean) ** 2 for i in range(seg_n))
            slope = num / den if den != 0 else 0
            intercept = y_mean - slope * x_mean
            for i in range(seg_n):
                trend[start + i] = intercept + slope * i
        return trend

    def _fourier_seasonality(self, n: int, period: float, order: int = 3) -> List[float]:
        seasonal = [0.0] * n
        for k in range(1, order + 1):
            for t in range(n):
                seasonal[t] += math.sin(2 * math.pi * k * t / period)
                seasonal[t] += math.cos(2 * math.pi * k * t / period)
        # Normalize
        max_s = max(abs(s) for s in seasonal) if seasonal else 1
        if max_s > 0:
            seasonal = [s / max_s for s in seasonal]
        return seasonal

    def _fit_seasonal_amplitude(self, residuals: List[float], seasonal_pattern: List[float]) -> Tuple[float, List[float]]:
        n = len(residuals)
        num = sum(residuals[i] * seasonal_pattern[i] for i in range(n))
        den = sum(seasonal_pattern[i] ** 2 for i in range(n))
        amplitude = num / den if den != 0 else 0
        return amplitude, [amplitude * s for s in seasonal_pattern]

    def forecast(self, data: List[float], horizon: int = 10, period: float = 7.0) -> ProphetForecastingResult:
        n = len(data)
        if n < 4:
            return ProphetForecastingResult(str(uuid.uuid4()), [data[-1] if data else 0] * horizon, [], [], [], {})
        changepoints = self._detect_changepoints(data)
        trend = self._fit_piecewise_trend(data, changepoints)
        residuals = [data[i] - trend[i] for i in range(n)]
        seasonal_pattern = self._fourier_seasonality(n, period)
        amplitude, seasonal = self._fit_seasonal_amplitude(residuals, seasonal_pattern)
        final_residuals = [residuals[i] - seasonal[i] for i in range(n)]
        # Forecast trend
        if n >= 2:
            end_slope = (trend[-1] - trend[-min(5, n)]) / min(5, n)
        else:
            end_slope = 0
        future_trend = [trend[-1] + end_slope * (i + 1) for i in range(horizon)]
        future_seasonal = [amplitude * s for s in self._fourier_seasonality(horizon, period, order=3)]
        predictions = [future_trend[i] + future_seasonal[i] for i in range(horizon)]
        mae = sum(abs(r) for r in final_residuals) / n
        rmse = math.sqrt(sum(r ** 2 for r in final_residuals) / n)
        result = ProphetForecastingResult(
            result_id=str(uuid.uuid4()),
            predictions=predictions,
            trend=trend,
            seasonal=seasonal,
            changepoints=changepoints,
            metrics={"mae": mae, "rmse": rmse, "n_changepoints": len(changepoints)},
        )
        self.results.append(result)
        return result

    def process(self, text: str) -> ProphetForecastingResult:
        data = [float(x) for x in text.split(",") if x.strip()]
        if not data:
            data = [i + math.sin(i) for i in range(50)]
        return self.forecast(data)


_prophet_forecasting: Optional[ProphetForecastingSystem] = None
def get_prophet_forecasting() -> Optional[ProphetForecastingSystem]: return _prophet_forecasting
def initialize_prophet_forecasting(data_dir) -> ProphetForecastingSystem:
    global _prophet_forecasting
    _prophet_forecasting = ProphetForecastingSystem(data_dir)
    return _prophet_forecasting
