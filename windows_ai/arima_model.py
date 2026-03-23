"""
ARIMAModel System — ARIMA(p,d,q) time series forecasting
Implements differencing, autoregressive (Yule-Walker), moving average, and forecasting.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import logging
import math
import uuid

logger = logging.getLogger(__name__)

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


@dataclass
class ARIMAModelResult:
    result_id: str
    predictions: List[float]
    confidence_intervals: List[Tuple[float, float]]
    metrics: Dict[str, float]


class ARIMAModelSystem:
    """ARIMA(p,d,q) forecasting system with real Yule-Walker AR estimation."""

    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[ARIMAModelResult] = []
        self.ar_coeffs: List[float] = []
        self.ma_coeffs: List[float] = []
        self.d: int = 0
        self.residual_std: float = 1.0
        logger.info("ARIMAModel initialized")

    def _difference(self, data: List[float], d: int) -> List[float]:
        """Apply differencing d times to make series stationary."""
        result = list(data)
        for _ in range(d):
            result = [result[i] - result[i - 1] for i in range(1, len(result))]
        return result

    def _undifference(self, diffed: List[float], original: List[float], d: int) -> List[float]:
        """Reverse differencing to get original scale."""
        result = list(diffed)
        for step in range(d):
            base = original[-(d - step)]
            cumulative = [base]
            for v in result:
                cumulative.append(cumulative[-1] + v)
            result = cumulative[1:]
        return result

    def _autocorrelation(self, data: List[float], max_lag: int) -> List[float]:
        """Compute autocorrelation function up to max_lag."""
        n = len(data)
        mean = sum(data) / n
        var = sum((x - mean) ** 2 for x in data) / n
        if var == 0:
            return [1.0] + [0.0] * max_lag
        acf = []
        for lag in range(max_lag + 1):
            cov = sum((data[i] - mean) * (data[i + lag] - mean) for i in range(n - lag)) / n
            acf.append(cov / var)
        return acf

    def _yule_walker(self, acf: List[float], p: int) -> List[float]:
        """Solve Yule-Walker equations for AR coefficients using Levinson-Durbin."""
        if p == 0:
            return []
        coeffs = [0.0] * p
        coeffs[0] = acf[1] / acf[0] if acf[0] != 0 else 0.0
        error = acf[0] * (1 - coeffs[0] ** 2)
        for k in range(1, p):
            lam = acf[k + 1]
            for j in range(k):
                lam -= coeffs[j] * acf[k - j]
            if error == 0:
                break
            gamma = lam / error
            new_coeffs = [0.0] * (k + 1)
            for j in range(k):
                new_coeffs[j] = coeffs[j] - gamma * coeffs[k - 1 - j]
            new_coeffs[k] = gamma
            coeffs = new_coeffs + [0.0] * (p - k - 1)
            error *= (1 - gamma ** 2)
        return coeffs[:p]

    def _estimate_ma(self, data: List[float], ar_coeffs: List[float], q: int) -> List[float]:
        """Estimate MA coefficients from residuals autocorrelation."""
        p = len(ar_coeffs)
        residuals = []
        for t in range(p, len(data)):
            pred = sum(ar_coeffs[j] * data[t - j - 1] for j in range(p))
            residuals.append(data[t] - pred)
        if len(residuals) < q + 2:
            return [0.0] * q
        res_acf = self._autocorrelation(residuals, q)
        ma = [res_acf[k] / res_acf[0] if res_acf[0] != 0 else 0.0 for k in range(1, q + 1)]
        return ma

    def _compute_residual_std(self, data: List[float], ar_coeffs: List[float]) -> float:
        """Compute standard deviation of model residuals."""
        p = len(ar_coeffs)
        if p >= len(data):
            return 1.0
        residuals = []
        for t in range(p, len(data)):
            pred = sum(ar_coeffs[j] * data[t - j - 1] for j in range(p))
            residuals.append(data[t] - pred)
        if not residuals:
            return 1.0
        mean_r = sum(residuals) / len(residuals)
        var_r = sum((r - mean_r) ** 2 for r in residuals) / len(residuals)
        return math.sqrt(var_r) if var_r > 0 else 1.0

    def _adf_test_simple(self, data: List[float]) -> bool:
        """Simple stationarity test: check if variance of first/second half differs significantly."""
        n = len(data)
        if n < 10:
            return True
        half = n // 2
        mean1 = sum(data[:half]) / half
        mean2 = sum(data[half:]) / (n - half)
        var1 = sum((x - mean1) ** 2 for x in data[:half]) / half
        var2 = sum((x - mean2) ** 2 for x in data[half:]) / (n - half)
        total_var = sum((x - sum(data) / n) ** 2 for x in data) / n
        if total_var == 0:
            return True
        mean_diff_ratio = abs(mean1 - mean2) / math.sqrt(total_var + 1e-10)
        return mean_diff_ratio < 1.5

    def _select_order(self, data: List[float], max_p: int = 5, max_q: int = 3) -> Tuple[int, int]:
        """Select p, q using AIC-like criterion."""
        n = len(data)
        best_aic = float("inf")
        best_p, best_q = 1, 0
        acf = self._autocorrelation(data, max_p + 1)
        for p in range(1, min(max_p + 1, n // 3)):
            ar = self._yule_walker(acf, p)
            residuals = []
            for t in range(p, n):
                pred = sum(ar[j] * data[t - j - 1] for j in range(p))
                residuals.append(data[t] - pred)
            if not residuals:
                continue
            sse = sum(r ** 2 for r in residuals)
            k = p
            aic = n * math.log(sse / n + 1e-10) + 2 * k
            if aic < best_aic:
                best_aic = aic
                best_p = p
                best_q = min(max_q, p // 2)
        return best_p, best_q

    def fit(self, data: List[float], p: int = None, d: int = None, q: int = None):
        """Fit ARIMA model to data. Auto-selects p,d,q if not provided."""
        if len(data) < 5:
            self.ar_coeffs = []
            self.ma_coeffs = []
            self.d = 0
            self.residual_std = 1.0
            return
        if d is None:
            d = 0
            test_data = list(data)
            for attempt in range(3):
                if self._adf_test_simple(test_data):
                    break
                test_data = self._difference(test_data, 1)
                d += 1
        self.d = d
        diffed = self._difference(data, d)
        if len(diffed) < 5:
            self.ar_coeffs = []
            self.ma_coeffs = []
            self.residual_std = 1.0
            return
        if p is None or q is None:
            auto_p, auto_q = self._select_order(diffed)
            p = p if p is not None else auto_p
            q = q if q is not None else auto_q
        acf = self._autocorrelation(diffed, p + 1)
        self.ar_coeffs = self._yule_walker(acf, p)
        self.ma_coeffs = self._estimate_ma(diffed, self.ar_coeffs, q)
        self.residual_std = self._compute_residual_std(diffed, self.ar_coeffs)

    def forecast(self, historical_data: List[float], horizon: int = 10) -> ARIMAModelResult:
        """Fit model and generate forecasts with confidence intervals."""
        self.fit(historical_data)
        diffed = self._difference(historical_data, self.d)
        p = len(self.ar_coeffs)
        q = len(self.ma_coeffs)
        history = list(diffed)
        residuals = [0.0] * max(q, 1)
        predictions_diff = []
        for h in range(horizon):
            pred = 0.0
            for j in range(p):
                idx = len(history) - 1 - j
                if idx >= 0:
                    pred += self.ar_coeffs[j] * history[idx]
            for j in range(q):
                idx = len(residuals) - 1 - j
                if idx >= 0:
                    pred += self.ma_coeffs[j] * residuals[idx]
            predictions_diff.append(pred)
            history.append(pred)
            residuals.append(0.0)
        predictions = self._undifference(predictions_diff, historical_data, self.d)
        cis = []
        for h in range(horizon):
            width = 1.96 * self.residual_std * math.sqrt(h + 1)
            cis.append((predictions[h] - width, predictions[h] + width))
        fitted_residuals = []
        for t in range(p, len(diffed)):
            pred = sum(self.ar_coeffs[j] * diffed[t - j - 1] for j in range(p))
            fitted_residuals.append(diffed[t] - pred)
        mae = sum(abs(r) for r in fitted_residuals) / max(len(fitted_residuals), 1)
        rmse = math.sqrt(sum(r ** 2 for r in fitted_residuals) / max(len(fitted_residuals), 1))
        result = ARIMAModelResult(
            result_id=str(uuid.uuid4()),
            predictions=predictions,
            confidence_intervals=cis,
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
