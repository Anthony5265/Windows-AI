"""
Anomaly Detection for Time Series — Z-score, IQR, moving average, seasonal decomposition.
Ensemble scoring across multiple detection methods.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import logging, math, uuid
logger = logging.getLogger(__name__)


@dataclass
class AnomalyDetectionTsResult:
    result_id: str
    anomalies: List[int]
    scores: List[float]
    method_results: Dict[str, List[int]]
    metrics: Dict[str, float]


class AnomalyDetectionTsSystem:
    """Time series anomaly detection with multiple methods."""

    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[AnomalyDetectionTsResult] = []
        logger.info("AnomalyDetectionTs initialized")

    def _zscore_detect(self, data: List[float], threshold: float = 3.0) -> Tuple[List[int], List[float]]:
        n = len(data)
        mean = sum(data) / n
        std = math.sqrt(sum((x - mean) ** 2 for x in data) / n)
        if std == 0:
            return [], [0.0] * n
        scores = [abs(x - mean) / std for x in data]
        anomalies = [i for i, s in enumerate(scores) if s > threshold]
        return anomalies, scores

    def _iqr_detect(self, data: List[float], factor: float = 1.5) -> Tuple[List[int], List[float]]:
        sorted_d = sorted(data)
        n = len(sorted_d)
        q1 = sorted_d[n // 4]
        q3 = sorted_d[3 * n // 4]
        iqr = q3 - q1
        lower = q1 - factor * iqr
        upper = q3 + factor * iqr
        anomalies = []
        scores = []
        for i, x in enumerate(data):
            if x < lower or x > upper:
                anomalies.append(i)
                scores.append(max(abs(x - lower), abs(x - upper)) / (iqr + 1e-10))
            else:
                scores.append(0.0)
        return anomalies, scores

    def _moving_avg_detect(self, data: List[float], window: int = 5, threshold: float = 2.0) -> Tuple[List[int], List[float]]:
        n = len(data)
        anomalies = []
        scores = [0.0] * n
        for i in range(window, n):
            wnd = data[i - window:i]
            ma = sum(wnd) / window
            std = math.sqrt(sum((x - ma) ** 2 for x in wnd) / window)
            if std == 0:
                std = 1e-10
            score = abs(data[i] - ma) / std
            scores[i] = score
            if score > threshold:
                anomalies.append(i)
        return anomalies, scores

    def _seasonal_detect(self, data: List[float], period: int = 7, threshold: float = 2.5) -> Tuple[List[int], List[float]]:
        n = len(data)
        if n < period * 2:
            return [], [0.0] * n
        seasonal = [0.0] * period
        counts = [0] * period
        for i, x in enumerate(data):
            seasonal[i % period] += x
            counts[i % period] += 1
        seasonal = [s / c if c > 0 else 0 for s, c in zip(seasonal, counts)]
        residuals = [data[i] - seasonal[i % period] for i in range(n)]
        mean_r = sum(residuals) / n
        std_r = math.sqrt(sum((r - mean_r) ** 2 for r in residuals) / n)
        if std_r == 0:
            return [], [0.0] * n
        scores = [abs(r - mean_r) / std_r for r in residuals]
        anomalies = [i for i, s in enumerate(scores) if s > threshold]
        return anomalies, scores

    def detect(self, data: List[float], methods: List[str] = None) -> AnomalyDetectionTsResult:
        """Run anomaly detection with ensemble of methods."""
        if methods is None:
            methods = ["zscore", "iqr", "moving_avg", "seasonal"]
        n = len(data)
        method_results = {}
        all_scores = [[0.0] * n for _ in methods]
        for idx, method in enumerate(methods):
            if method == "zscore":
                anoms, scores = self._zscore_detect(data)
            elif method == "iqr":
                anoms, scores = self._iqr_detect(data)
            elif method == "moving_avg":
                anoms, scores = self._moving_avg_detect(data)
            elif method == "seasonal":
                anoms, scores = self._seasonal_detect(data)
            else:
                anoms, scores = [], [0.0] * n
            method_results[method] = anoms
            all_scores[idx] = scores
        # Ensemble: average normalized scores
        ensemble_scores = [0.0] * n
        for idx in range(len(methods)):
            max_s = max(all_scores[idx]) if all_scores[idx] else 1.0
            if max_s == 0:
                max_s = 1.0
            for i in range(n):
                ensemble_scores[i] += all_scores[idx][i] / max_s
        ensemble_scores = [s / len(methods) for s in ensemble_scores]
        threshold = 0.5
        anomalies = [i for i, s in enumerate(ensemble_scores) if s > threshold]
        result = AnomalyDetectionTsResult(
            result_id=str(uuid.uuid4()),
            anomalies=anomalies,
            scores=ensemble_scores,
            method_results=method_results,
            metrics={"total_anomalies": len(anomalies), "anomaly_rate": len(anomalies) / n if n else 0},
        )
        self.results.append(result)
        return result

    def process(self, text: str) -> AnomalyDetectionTsResult:
        data = [float(x) for x in text.split(",") if x.strip()]
        if not data:
            data = [1, 2, 1, 2, 100, 1, 2, 1]
        return self.detect(data)


_anomaly_detection_ts: Optional[AnomalyDetectionTsSystem] = None
def get_anomaly_detection_ts() -> Optional[AnomalyDetectionTsSystem]: return _anomaly_detection_ts
def initialize_anomaly_detection_ts(data_dir) -> AnomalyDetectionTsSystem:
    global _anomaly_detection_ts
    _anomaly_detection_ts = AnomalyDetectionTsSystem(data_dir)
    return _anomaly_detection_ts
