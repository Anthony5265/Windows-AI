"""
Time-series anomaly detection using deterministic statistical methods.

The module provides Z-score, IQR, moving-average, and seasonal detectors with
an ensemble result. It intentionally does not fabricate input data: callers
must provide a non-empty finite numeric series.
"""
from dataclasses import dataclass
import logging
import math
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AnomalyDetectionTsResult:
    result_id: str
    anomalies: List[int]
    scores: List[float]
    method_results: Dict[str, List[int]]
    metrics: Dict[str, float]


class AnomalyDetectionTsSystem:
    """Time-series anomaly detection with multiple deterministic methods."""

    _METHODS = ("zscore", "iqr", "moving_avg", "seasonal")

    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[AnomalyDetectionTsResult] = []
        logger.info("AnomalyDetectionTs initialized")

    @staticmethod
    def _validate_data(data: Sequence[float]) -> List[float]:
        if isinstance(data, (str, bytes)):
            raise TypeError("data must be a sequence of numbers")
        values = list(data)
        if not values:
            raise ValueError("data must not be empty")
        if not all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in values):
            raise TypeError("data must contain only numeric values")
        if not all(math.isfinite(float(x)) for x in values):
            raise ValueError("data must contain only finite values")
        return [float(x) for x in values]

    @staticmethod
    def _validate_threshold(value: float, name: str) -> float:
        value = float(value)
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} must be a finite value greater than zero")
        return value

    def _zscore_detect(self, data: List[float], threshold: float = 3.0) -> Tuple[List[int], List[float]]:
        threshold = self._validate_threshold(threshold, "threshold")
        n = len(data)
        mean = sum(data) / n
        std = math.sqrt(sum((x - mean) ** 2 for x in data) / n)
        if std == 0:
            return [], [0.0] * n
        scores = [abs(x - mean) / std for x in data]
        return [i for i, s in enumerate(scores) if s > threshold], scores

    def _iqr_detect(self, data: List[float], factor: float = 1.5) -> Tuple[List[int], List[float]]:
        factor = self._validate_threshold(factor, "factor")
        sorted_d = sorted(data)
        n = len(sorted_d)
        q1 = sorted_d[(n - 1) // 4]
        q3 = sorted_d[(3 * (n - 1)) // 4]
        iqr = q3 - q1
        lower, upper = q1 - factor * iqr, q3 + factor * iqr
        scale = max(iqr, math.ulp(max(abs(q1), abs(q3), 1.0)))
        scores = [max(0.0, (lower - x) / scale, (x - upper) / scale) for x in data]
        return [i for i, x in enumerate(data) if x < lower or x > upper], scores

    def _moving_avg_detect(self, data: List[float], window: int = 5, threshold: float = 2.0) -> Tuple[List[int], List[float]]:
        threshold = self._validate_threshold(threshold, "threshold")
        if not isinstance(window, int) or isinstance(window, bool) or window < 1:
            raise ValueError("window must be a positive integer")
        if window >= len(data):
            return [], [0.0] * len(data)
        scores = [0.0] * len(data)
        anomalies: List[int] = []
        for i in range(window, len(data)):
            wnd = data[i - window:i]
            ma = sum(wnd) / window
            std = math.sqrt(sum((x - ma) ** 2 for x in wnd) / window)
            score = abs(data[i] - ma) / std if std else (float("inf") if data[i] != ma else 0.0)
            scores[i] = score
            if score > threshold:
                anomalies.append(i)
        return anomalies, scores

    def _seasonal_detect(self, data: List[float], period: int = 7, threshold: float = 2.5) -> Tuple[List[int], List[float]]:
        threshold = self._validate_threshold(threshold, "threshold")
        if not isinstance(period, int) or isinstance(period, bool) or period < 2:
            raise ValueError("period must be an integer of at least 2")
        n = len(data)
        if n < period * 2:
            return [], [0.0] * n
        seasonal = [0.0] * period
        counts = [0] * period
        for i, x in enumerate(data):
            seasonal[i % period] += x
            counts[i % period] += 1
        seasonal = [s / c for s, c in zip(seasonal, counts)]
        residuals = [data[i] - seasonal[i % period] for i in range(n)]
        mean_r = sum(residuals) / n
        std_r = math.sqrt(sum((r - mean_r) ** 2 for r in residuals) / n)
        if std_r == 0:
            return [], [0.0] * n
        scores = [abs(r - mean_r) / std_r for r in residuals]
        return [i for i, s in enumerate(scores) if s > threshold], scores

    def detect(self, data: List[float], methods: Optional[List[str]] = None) -> AnomalyDetectionTsResult:
        """Run the requested anomaly detectors and combine their normalized scores."""
        values = self._validate_data(data)
        selected = list(self._METHODS if methods is None else methods)
        if not selected:
            raise ValueError("methods must contain at least one detector")
        if len(set(selected)) != len(selected):
            raise ValueError("methods must not contain duplicates")
        unknown = set(selected) - set(self._METHODS)
        if unknown:
            raise ValueError(f"unknown detection methods: {sorted(unknown)}")

        n = len(values)
        method_results: Dict[str, List[int]] = {}
        all_scores: List[List[float]] = []
        for method in selected:
            if method == "zscore":
                anoms, scores = self._zscore_detect(values)
            elif method == "iqr":
                anoms, scores = self._iqr_detect(values)
            elif method == "moving_avg":
                anoms, scores = self._moving_avg_detect(values)
            else:
                anoms, scores = self._seasonal_detect(values)
            method_results[method] = anoms
            all_scores.append(scores)

        ensemble_scores = [0.0] * n
        for scores in all_scores:
            finite_scores = [s for s in scores if math.isfinite(s)]
            max_score = max(finite_scores, default=0.0)
            if max_score == 0:
                normalized = [0.0] * n
            else:
                normalized = [min(s / max_score, 1.0) if math.isfinite(s) else 1.0 for s in scores]
            ensemble_scores = [a + b for a, b in zip(ensemble_scores, normalized)]
        ensemble_scores = [s / len(selected) for s in ensemble_scores]
        anomalies = [i for i, s in enumerate(ensemble_scores) if s > 0.5]
        result = AnomalyDetectionTsResult(
            result_id=str(uuid.uuid4()),
            anomalies=anomalies,
            scores=ensemble_scores,
            method_results=method_results,
            metrics={"total_anomalies": float(len(anomalies)), "anomaly_rate": len(anomalies) / n},
        )
        self.results.append(result)
        return result

    def process(self, text: str) -> AnomalyDetectionTsResult:
        """Parse a comma-separated numeric series; reject missing/invalid input."""
        if not isinstance(text, str) or not text.strip():
            raise ValueError("text must contain a comma-separated numeric series")
        try:
            data = [float(x.strip()) for x in text.split(",") if x.strip()]
        except ValueError as exc:
            raise ValueError("text contains a non-numeric value") from exc
        return self.detect(data)


_anomaly_detection_ts: Optional[AnomalyDetectionTsSystem] = None


def get_anomaly_detection_ts() -> Optional[AnomalyDetectionTsSystem]:
    return _anomaly_detection_ts


def initialize_anomaly_detection_ts(data_dir) -> AnomalyDetectionTsSystem:
    global _anomaly_detection_ts
    _anomaly_detection_ts = AnomalyDetectionTsSystem(data_dir)
    return _anomaly_detection_ts
