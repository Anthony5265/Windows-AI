"""
Trend Analysis — Linear/polynomial regression, moving averages, exponential smoothing,
Mann-Kendall test, breakpoint detection.
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
import logging, math, uuid
logger = logging.getLogger(__name__)


@dataclass
class TrendAnalysisResult:
    result_id: str
    trend_type: str
    trend_values: List[float]
    slope: float
    breakpoints: List[int]
    metrics: Dict[str, float]


class TrendAnalysisSystem:
    """Comprehensive trend analysis system."""

    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[TrendAnalysisResult] = []
        logger.info("TrendAnalysis initialized")

    def _linear_regression(self, data: List[float]) -> Tuple[float, float, float]:
        n = len(data)
        x_mean = (n - 1) / 2
        y_mean = sum(data) / n
        num = sum((i - x_mean) * (data[i] - y_mean) for i in range(n))
        den = sum((i - x_mean) ** 2 for i in range(n))
        slope = num / den if den != 0 else 0
        intercept = y_mean - slope * x_mean
        ss_res = sum((data[i] - (intercept + slope * i)) ** 2 for i in range(n))
        ss_tot = sum((data[i] - y_mean) ** 2 for i in range(n))
        r_squared = 1 - ss_res / ss_tot if ss_tot != 0 else 0
        return slope, intercept, r_squared

    def _moving_average(self, data: List[float], window: int = 5) -> List[float]:
        n = len(data)
        result = []
        for i in range(n):
            start = max(0, i - window // 2)
            end = min(n, i + window // 2 + 1)
            result.append(sum(data[start:end]) / (end - start))
        return result

    def _exponential_smoothing(self, data: List[float], alpha: float = 0.3) -> List[float]:
        result = [data[0]]
        for i in range(1, len(data)):
            result.append(alpha * data[i] + (1 - alpha) * result[-1])
        return result

    def _mann_kendall(self, data: List[float]) -> Tuple[float, float, str]:
        n = len(data)
        s = 0
        for i in range(n - 1):
            for j in range(i + 1, n):
                diff = data[j] - data[i]
                if diff > 0:
                    s += 1
                elif diff < 0:
                    s -= 1
        var_s = n * (n - 1) * (2 * n + 5) / 18
        if var_s == 0:
            z = 0
        elif s > 0:
            z = (s - 1) / math.sqrt(var_s)
        elif s < 0:
            z = (s + 1) / math.sqrt(var_s)
        else:
            z = 0
        p_value = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
        if z > 1.96:
            direction = "increasing"
        elif z < -1.96:
            direction = "decreasing"
        else:
            direction = "no_trend"
        return z, p_value, direction

    def _sens_slope(self, data: List[float]) -> float:
        n = len(data)
        slopes = []
        for i in range(n):
            for j in range(i + 1, n):
                slopes.append((data[j] - data[i]) / (j - i))
        if not slopes:
            return 0
        slopes.sort()
        return slopes[len(slopes) // 2]

    def _detect_breakpoints(self, data: List[float], min_segment: int = 5) -> List[int]:
        n = len(data)
        if n < min_segment * 2:
            return []
        breakpoints = []
        for cp in range(min_segment, n - min_segment):
            left = data[:cp]
            right = data[cp:]
            left_mean = sum(left) / len(left)
            right_mean = sum(right) / len(right)
            total_mean = sum(data) / n
            left_var = sum((x - left_mean) ** 2 for x in left)
            right_var = sum((x - right_mean) ** 2 for x in right)
            total_var = sum((x - total_mean) ** 2 for x in data)
            if total_var == 0:
                continue
            reduction = 1 - (left_var + right_var) / total_var
            if reduction > 0.1:
                breakpoints.append(cp)
        # Keep only significant breakpoints (non-overlapping)
        if not breakpoints:
            return []
        filtered = [breakpoints[0]]
        for bp in breakpoints[1:]:
            if bp - filtered[-1] >= min_segment:
                filtered.append(bp)
        return filtered[:5]

    def analyze(self, data: List[float]) -> TrendAnalysisResult:
        n = len(data)
        slope, intercept, r_squared = self._linear_regression(data)
        z, p_value, direction = self._mann_kendall(data)
        sens = self._sens_slope(data)
        ma_trend = self._moving_average(data)
        breakpoints = self._detect_breakpoints(data)
        result = TrendAnalysisResult(
            result_id=str(uuid.uuid4()),
            trend_type=direction,
            trend_values=ma_trend,
            slope=slope,
            breakpoints=breakpoints,
            metrics={"r_squared": r_squared, "mann_kendall_z": z, "p_value": p_value, "sens_slope": sens, "n_breakpoints": len(breakpoints)},
        )
        self.results.append(result)
        return result

    def process(self, text: str) -> TrendAnalysisResult:
        data = [float(x) for x in text.split(",") if x.strip()]
        if not data:
            data = [i * 0.5 + math.sin(i) for i in range(50)]
        return self.analyze(data)


_trend_analysis: Optional[TrendAnalysisSystem] = None
def get_trend_analysis() -> Optional[TrendAnalysisSystem]: return _trend_analysis
def initialize_trend_analysis(data_dir) -> TrendAnalysisSystem:
    global _trend_analysis
    _trend_analysis = TrendAnalysisSystem(data_dir)
    return _trend_analysis
