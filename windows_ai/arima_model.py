"""
ARIMAModel System — ARIMA(p,d,q) time series forecasting.
Implements differencing, autoregressive estimation, moving-average approximation,
and forecasting with confidence intervals.
"""
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import logging
import math
import uuid

logger = logging.getLogger(__name__)


@dataclass
class ARIMAModelResult:
    result_id: str
    predictions: List[float]
    confidence_intervals: List[Tuple[float, float]]
    metrics: Dict[str, float]


class ARIMAModelSystem:
    """ARIMA(p,d,q) forecasting system with deterministic parameter estimation."""

    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if not self.data_dir.is_dir():
            raise ValueError("data_dir must be a directory")
        self.results: List[ARIMAModelResult] = []
        self.ar_coeffs: List[float] = []
        self.ma_coeffs: List[float] = []
        self.d: int = 0
        self.residual_std: float = 1.0
        logger.info("ARIMAModel initialized")

    def _difference(self, data: List[float], d: int) -> List[float]:
        if d < 0:
            raise ValueError("d must be non-negative")
        result = list(data)
        for _ in range(d):
            result = [result[i] - result[i - 1] for i in range(1, len(result))]
        return result

    def _undifference(self, diffed: List[float], original: List[float], d: int) -> List[float]:
        result = list(diffed)
        if d == 0:
            return result
        if len(original) < d:
            raise ValueError("original data is too short to reverse differencing")
        for order in range(d, 0, -1):
            base_series = list(original)
            for _ in range(order - 1):
                base_series = [base_series[i] - base_series[i - 1] for i in range(1, len(base_series))]
            base = base_series[-1]
            cumulative = [base]
            for value in result:
                cumulative.append(cumulative[-1] + value)
            result = cumulative[1:]
        return result

    def _autocorrelation(self, data: List[float], max_lag: int) -> List[float]:
        if not data or max_lag < 0 or max_lag >= len(data):
            raise ValueError("data must be non-empty and max_lag must be within the data length")
        n = len(data)
        mean = sum(data) / n
        var = sum((x - mean) ** 2 for x in data) / n
        if var == 0:
            return [1.0] + [0.0] * max_lag
        return [sum((data[i] - mean) * (data[i + lag] - mean) for i in range(n - lag)) / n / var for lag in range(max_lag + 1)]

    def _yule_walker(self, acf: List[float], p: int) -> List[float]:
        if p < 0 or len(acf) < p + 1:
            raise ValueError("invalid AR order for supplied autocorrelation data")
        if p == 0:
            return []
        coeffs = [0.0] * p
        coeffs[0] = acf[1] / acf[0] if acf[0] != 0 else 0.0
        error = acf[0] * (1 - coeffs[0] ** 2)
        for k in range(1, p):
            lam = acf[k + 1] - sum(coeffs[j] * acf[k - j] for j in range(k))
            if error <= 0 or not math.isfinite(error):
                break
            gamma = max(-0.999999, min(0.999999, lam / error))
            new_coeffs = [0.0] * (k + 1)
            for j in range(k):
                new_coeffs[j] = coeffs[j] - gamma * coeffs[k - 1 - j]
            new_coeffs[k] = gamma
            coeffs = new_coeffs + [0.0] * (p - k - 1)
            error *= max(0.0, 1 - gamma ** 2)
        return coeffs[:p]

    def _estimate_ma(self, data: List[float], ar_coeffs: List[float], q: int) -> List[float]:
        if q < 0:
            raise ValueError("q must be non-negative")
        p = len(ar_coeffs)
        residuals = [data[t] - sum(ar_coeffs[j] * data[t - j - 1] for j in range(p)) for t in range(p, len(data))]
        if q == 0:
            return []
        if len(residuals) < q + 2:
            return [0.0] * q
        res_acf = self._autocorrelation(residuals, q)
        return [res_acf[k] / res_acf[0] if res_acf[0] != 0 else 0.0 for k in range(1, q + 1)]

    def _compute_residual_std(self, data: List[float], ar_coeffs: List[float]) -> float:
        p = len(ar_coeffs)
        if p >= len(data):
            return 1.0
        residuals = [data[t] - sum(ar_coeffs[j] * data[t - j - 1] for j in range(p)) for t in range(p, len(data))]
        if not residuals:
            return 1.0
        mean_r = sum(residuals) / len(residuals)
        variance = sum((r - mean_r) ** 2 for r in residuals) / len(residuals)
        return math.sqrt(variance) if variance > 0 else 1.0

    def _adf_test_simple(self, data: List[float]) -> bool:
        n = len(data)
        if n < 10:
            return True
        half = n // 2
        mean1 = sum(data[:half]) / half
        mean2 = sum(data[half:]) / (n - half)
        var1 = sum((x - mean1) ** 2 for x in data[:half]) / half
        var2 = sum((x - mean2) ** 2 for x in data[half:]) / (n - half)
        total_mean = sum(data) / n
        total_var = sum((x - total_mean) ** 2 for x in data) / n
        if total_var == 0:
            return True
        return abs(mean1 - mean2) / math.sqrt(total_var) < 1.5 and max(var1, var2) <= max(total_var * 4, 1e-12)

    def _select_order(self, data: List[float], max_p: int = 5, max_q: int = 3) -> Tuple[int, int]:
        if len(data) < 3:
            return 0, 0
        n = len(data)
        best_aic = float("inf")
        best_p, best_q = 1, 0
        max_allowed_p = min(max_p, max(0, n // 3 - 1))
        if max_allowed_p == 0:
            return 0, 0
        acf = self._autocorrelation(data, max_allowed_p + 1)
        for p in range(1, max_allowed_p + 1):
            ar = self._yule_walker(acf, p)
            residuals = [data[t] - sum(ar[j] * data[t - j - 1] for j in range(p)) for t in range(p, n)]
            if not residuals:
                continue
            sse = sum(r ** 2 for r in residuals)
            k = p
            aic = n * math.log(sse / n + 1e-12) + 2 * k
            if aic < best_aic:
                best_aic, best_p = aic, p
                best_q = min(max_q, p // 2)
        return best_p, best_q

    def fit(self, data: List[float], p: int = None, d: int = None, q: int = None):
        if not isinstance(data, list) or not data:
            raise ValueError("data must be a non-empty list")
        if any(not isinstance(value, (int, float)) or not math.isfinite(value) for value in data):
            raise ValueError("data must contain only finite numeric values")
        if p is not None and (not isinstance(p, int) or p < 0):
            raise ValueError("p must be a non-negative integer")
        if d is not None and (not isinstance(d, int) or d < 0 or d > 2):
            raise ValueError("d must be an integer between 0 and 2")
        if q is not None and (not isinstance(q, int) or q < 0):
            raise ValueError("q must be a non-negative integer")
        if len(data) < 5:
            self.ar_coeffs, self.ma_coeffs, self.d, self.residual_std = [], [], 0, 1.0
            return
        if d is None:
            d = 0
            test_data = list(data)
            for _ in range(3):
                if self._adf_test_simple(test_data):
                    break
                test_data = self._difference(test_data, 1)
                d += 1
        self.d = d
        diffed = self._difference(data, d)
        if len(diffed) < 5:
            self.ar_coeffs, self.ma_coeffs, self.residual_std = [], [], 1.0
            return
        if p is None or q is None:
            auto_p, auto_q = self._select_order(diffed)
            p = auto_p if p is None else p
            q = auto_q if q is None else q
        if p >= len(diffed):
            raise ValueError("p must be smaller than the differenced data length")
        acf = self._autocorrelation(diffed, p + 1) if p else [1.0]
        self.ar_coeffs = self._yule_walker(acf, p)
        self.ma_coeffs = self._estimate_ma(diffed, self.ar_coeffs, q)
        self.residual_std = self._compute_residual_std(diffed, self.ar_coeffs)

    def forecast(self, historical_data: List[float], horizon: int = 10) -> ARIMAModelResult:
        if not isinstance(horizon, int) or horizon < 1 or horizon > 10000:
            raise ValueError("horizon must be an integer between 1 and 10000")
        self.fit(historical_data)
        diffed = self._difference(historical_data, self.d)
        p, q = len(self.ar_coeffs), len(self.ma_coeffs)
        history = list(diffed)
        residuals = [0.0] * max(q, 1)
        predictions_diff = []
        for _ in range(horizon):
            pred = sum(self.ar_coeffs[j] * history[len(history) - 1 - j] for j in range(p) if len(history) - 1 - j >= 0)
            pred += sum(self.ma_coeffs[j] * residuals[len(residuals) - 1 - j] for j in range(q) if len(residuals) - 1 - j >= 0)
            predictions_diff.append(pred)
            history.append(pred)
            residuals.append(0.0)
        predictions = self._undifference(predictions_diff, historical_data, self.d)
        cis = []
        for h, prediction in enumerate(predictions):
            width = 1.96 * self.residual_std * math.sqrt(h + 1)
            cis.append((prediction - width, prediction + width))
        fitted_residuals = [diffed[t] - sum(self.ar_coeffs[j] * diffed[t - j - 1] for j in range(p)) for t in range(p, len(diffed))]
        mae = sum(abs(r) for r in fitted_residuals) / max(len(fitted_residuals), 1)
        rmse = math.sqrt(sum(r ** 2 for r in fitted_residuals) / max(len(fitted_residuals), 1))
        result = ARIMAModelResult(
            result_id=str(uuid.uuid4()), predictions=predictions, confidence_intervals=cis,
            metrics={"mae": mae, "rmse": rmse, "p": len(self.ar_coeffs), "d": self.d, "q": len(self.ma_coeffs)},
        )
        self.results.append(result)
        return result


_arima_model: Optional[ARIMAModelSystem] = None


def get_arima_model() -> Optional[ARIMAModelSystem]:
    return _arima_model


def initialize_arima_model(data_dir) -> ARIMAModelSystem:
    global _arima_model
    _arima_model = ARIMAModelSystem(data_dir)
    return _arima_model
