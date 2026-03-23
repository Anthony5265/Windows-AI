"""
LSTM Forecasting — Simple LSTM-like recurrent neural network from scratch.
Implements forget/input/output gates, forward pass, and sequence prediction using numpy.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import logging, math, uuid
logger = logging.getLogger(__name__)

try:
    import numpy as np
    HAS_NP = True
except ImportError:
    HAS_NP = False


def _sigmoid(x):
    return 1.0 / (1.0 + math.exp(-max(-500, min(500, x))))


def _tanh(x):
    return math.tanh(max(-500, min(500, x)))


@dataclass
class LSTMForecastingResult:
    result_id: str
    predictions: List[float]
    training_loss: List[float]
    metrics: Dict[str, float]


class LSTMCell:
    """Single LSTM cell with forget, input, output gates."""

    def __init__(self, input_size: int, hidden_size: int):
        self.input_size = input_size
        self.hidden_size = hidden_size
        scale = 0.1
        # Weights: [input_size + hidden_size] -> hidden_size for each gate
        total_in = input_size + hidden_size
        self.Wf = [[scale * (hash((i, j, 'f')) % 1000 - 500) / 500 for j in range(hidden_size)] for i in range(total_in)]
        self.Wi = [[scale * (hash((i, j, 'i')) % 1000 - 500) / 500 for j in range(hidden_size)] for i in range(total_in)]
        self.Wc = [[scale * (hash((i, j, 'c')) % 1000 - 500) / 500 for j in range(hidden_size)] for i in range(total_in)]
        self.Wo = [[scale * (hash((i, j, 'o')) % 1000 - 500) / 500 for j in range(hidden_size)] for i in range(total_in)]
        self.bf = [0.0] * hidden_size
        self.bi = [0.0] * hidden_size
        self.bc = [0.0] * hidden_size
        self.bo = [0.0] * hidden_size

    def _matmul(self, x: List[float], W: List[List[float]], b: List[float]) -> List[float]:
        result = list(b)
        for j in range(len(b)):
            for i in range(len(x)):
                result[j] += x[i] * W[i][j]
        return result

    def forward(self, x: List[float], h_prev: List[float], c_prev: List[float]) -> Tuple[List[float], List[float]]:
        combined = x + h_prev
        fg = [_sigmoid(v) for v in self._matmul(combined, self.Wf, self.bf)]
        ig = [_sigmoid(v) for v in self._matmul(combined, self.Wi, self.bi)]
        cg = [_tanh(v) for v in self._matmul(combined, self.Wc, self.bc)]
        og = [_sigmoid(v) for v in self._matmul(combined, self.Wo, self.bo)]
        c_new = [fg[j] * c_prev[j] + ig[j] * cg[j] for j in range(self.hidden_size)]
        h_new = [og[j] * _tanh(c_new[j]) for j in range(self.hidden_size)]
        return h_new, c_new


class LSTMForecastingSystem:
    """LSTM-based time series forecaster."""

    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[LSTMForecastingResult] = []
        self.hidden_size = 8
        self.lookback = 5
        self.cell = LSTMCell(1, self.hidden_size)
        self.output_weights = [0.01 * (hash(('out', i)) % 1000 - 500) / 500 for i in range(self.hidden_size)]
        self.output_bias = 0.0
        logger.info("LSTMForecasting initialized")

    def _normalize(self, data: List[float]) -> Tuple[List[float], float, float]:
        mn = min(data) if data else 0
        mx = max(data) if data else 1
        rng = mx - mn if mx != mn else 1.0
        return [(x - mn) / rng for x in data], mn, rng

    def _denormalize(self, val: float, mn: float, rng: float) -> float:
        return val * rng + mn

    def _predict_one(self, sequence: List[float]) -> float:
        h = [0.0] * self.hidden_size
        c = [0.0] * self.hidden_size
        for val in sequence:
            h, c = self.cell.forward([val], h, c)
        out = self.output_bias + sum(h[i] * self.output_weights[i] for i in range(self.hidden_size))
        return _sigmoid(out)

    def _train(self, data: List[float], epochs: int = 50, lr: float = 0.01) -> List[float]:
        norm_data, mn, rng = self._normalize(data)
        losses = []
        for epoch in range(epochs):
            total_loss = 0.0
            count = 0
            for t in range(self.lookback, len(norm_data)):
                seq = norm_data[t - self.lookback:t]
                target = norm_data[t]
                pred = self._predict_one(seq)
                error = pred - target
                total_loss += error ** 2
                count += 1
                # Simple gradient update on output weights
                h = [0.0] * self.hidden_size
                cv = [0.0] * self.hidden_size
                for val in seq:
                    h, cv = self.cell.forward([val], h, cv)
                for i in range(self.hidden_size):
                    self.output_weights[i] -= lr * error * h[i]
                self.output_bias -= lr * error
            losses.append(total_loss / max(count, 1))
        return losses

    def forecast(self, historical_data: List[float], horizon: int = 10) -> LSTMForecastingResult:
        if len(historical_data) < self.lookback + 2:
            preds = [historical_data[-1] if historical_data else 0.0] * horizon
            return LSTMForecastingResult(str(uuid.uuid4()), preds, [], {"mae": 0, "rmse": 0})
        losses = self._train(historical_data, epochs=30)
        norm_data, mn, rng = self._normalize(historical_data)
        current_seq = list(norm_data[-self.lookback:])
        predictions = []
        for _ in range(horizon):
            pred_norm = self._predict_one(current_seq)
            predictions.append(self._denormalize(pred_norm, mn, rng))
            current_seq = current_seq[1:] + [pred_norm]
        mae = losses[-1] if losses else 0
        result = LSTMForecastingResult(
            result_id=str(uuid.uuid4()),
            predictions=predictions,
            training_loss=losses[-10:],
            metrics={"final_loss": losses[-1] if losses else 0, "epochs": 30, "hidden_size": self.hidden_size},
        )
        self.results.append(result)
        return result


_lstm_forecasting: Optional[LSTMForecastingSystem] = None
def get_lstm_forecasting() -> Optional[LSTMForecastingSystem]: return _lstm_forecasting
def initialize_lstm_forecasting(data_dir) -> LSTMForecastingSystem:
    global _lstm_forecasting
    _lstm_forecasting = LSTMForecastingSystem(data_dir)
    return _lstm_forecasting
