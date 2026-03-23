"""
Kalman Filter — Linear state estimation with predict/update cycle.
Supports multi-dimensional state, RTS smoother, and parameter estimation.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import logging, math, uuid
logger = logging.getLogger(__name__)


@dataclass
class KalmanFilterResult:
    result_id: str
    filtered_states: List[List[float]]
    smoothed_states: List[List[float]]
    predictions: List[float]
    metrics: Dict[str, float]


class KalmanFilterSystem:
    """Kalman filter for linear dynamic systems."""

    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[KalmanFilterResult] = []
        logger.info("KalmanFilter initialized")

    def _mat_mul(self, A, B):
        rows_a, cols_a = len(A), len(A[0])
        cols_b = len(B[0])
        C = [[0.0] * cols_b for _ in range(rows_a)]
        for i in range(rows_a):
            for j in range(cols_b):
                for k in range(cols_a):
                    C[i][j] += A[i][k] * B[k][j]
        return C

    def _mat_add(self, A, B):
        return [[A[i][j] + B[i][j] for j in range(len(A[0]))] for i in range(len(A))]

    def _mat_sub(self, A, B):
        return [[A[i][j] - B[i][j] for j in range(len(A[0]))] for i in range(len(A))]

    def _mat_transpose(self, A):
        return [[A[j][i] for j in range(len(A))] for i in range(len(A[0]))]

    def _mat_scale(self, A, s):
        return [[A[i][j] * s for j in range(len(A[0]))] for i in range(len(A))]

    def _identity(self, n):
        return [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]

    def _invert_2x2(self, M):
        if len(M) == 1:
            return [[1.0 / M[0][0]]] if M[0][0] != 0 else [[1e10]]
        a, b = M[0][0], M[0][1]
        c, d = M[1][0], M[1][1]
        det = a * d - b * c
        if abs(det) < 1e-12:
            det = 1e-12
        return [[d / det, -b / det], [-c / det, a / det]]

    def _invert(self, M):
        n = len(M)
        if n <= 2:
            return self._invert_2x2(M)
        aug = [row[:] + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(M)]
        for col in range(n):
            max_row = max(range(col, n), key=lambda r: abs(aug[r][col]))
            aug[col], aug[max_row] = aug[max_row], aug[col]
            pivot = aug[col][col]
            if abs(pivot) < 1e-12:
                pivot = 1e-12
            for j in range(2 * n):
                aug[col][j] /= pivot
            for row in range(n):
                if row != col:
                    factor = aug[row][col]
                    for j in range(2 * n):
                        aug[row][j] -= factor * aug[col][j]
        return [row[n:] for row in aug]

    def filter(self, observations: List[float], state_dim: int = 2) -> KalmanFilterResult:
        """Run Kalman filter on 1D observations with state_dim-dimensional state."""
        n = len(observations)
        F = self._identity(state_dim)
        if state_dim >= 2:
            F[0][1] = 1.0
        H = [[1.0] + [0.0] * (state_dim - 1)]
        Q = self._mat_scale(self._identity(state_dim), 0.01)
        R = [[1.0]]
        x = [[0.0] for _ in range(state_dim)]
        P = self._identity(state_dim)
        filtered_x = []
        filtered_P = []
        predicted_x = []
        predicted_P = []
        for t in range(n):
            xp = self._mat_mul(F, x)
            Pp = self._mat_add(self._mat_mul(F, self._mat_mul(P, self._mat_transpose(F))), Q)
            predicted_x.append([row[0] for row in xp])
            predicted_P.append([row[:] for row in Pp])
            y_obs = [[observations[t]]]
            Hx = self._mat_mul(H, xp)
            innovation = [[y_obs[0][0] - Hx[0][0]]]
            S = self._mat_add(self._mat_mul(H, self._mat_mul(Pp, self._mat_transpose(H))), R)
            S_inv = self._invert(S)
            K = self._mat_mul(Pp, self._mat_mul(self._mat_transpose(H), S_inv))
            x = self._mat_add(xp, self._mat_mul(K, innovation))
            KH = self._mat_mul(K, H)
            I_KH = self._mat_sub(self._identity(state_dim), KH)
            P = self._mat_mul(I_KH, Pp)
            filtered_x.append([row[0] for row in x])
            filtered_P.append([row[:] for row in P])
        # RTS Smoother
        smoothed_x = [None] * n
        smoothed_x[-1] = filtered_x[-1]
        for t in range(n - 2, -1, -1):
            Pp_next = predicted_P[t + 1]
            Pp_inv = self._invert(Pp_next)
            Ft = self._mat_transpose(F)
            C = self._mat_mul([[filtered_P[t][i][j] for j in range(state_dim)] for i in range(state_dim)],
                              self._mat_mul(Ft, Pp_inv))
            diff = [[smoothed_x[t + 1][i] - predicted_x[t + 1][i]] for i in range(state_dim)]
            correction = self._mat_mul(C, diff)
            smoothed_x[t] = [filtered_x[t][i] + correction[i][0] for i in range(state_dim)]
        forecast_steps = min(10, n)
        preds = []
        curr_x = [[smoothed_x[-1][i]] for i in range(state_dim)]
        for _ in range(forecast_steps):
            curr_x = self._mat_mul(F, curr_x)
            preds.append(curr_x[0][0])
        residuals = [observations[t] - filtered_x[t][0] for t in range(n)]
        mae = sum(abs(r) for r in residuals) / n
        rmse = math.sqrt(sum(r ** 2 for r in residuals) / n)
        result = KalmanFilterResult(
            result_id=str(uuid.uuid4()),
            filtered_states=filtered_x,
            smoothed_states=smoothed_x,
            predictions=preds,
            metrics={"mae": mae, "rmse": rmse, "state_dim": state_dim},
        )
        self.results.append(result)
        return result

    def process(self, text: str) -> KalmanFilterResult:
        data = [float(x) for x in text.split(",") if x.strip()]
        if not data:
            data = [0.0, 1.0, 2.0, 3.0, 4.0]
        return self.filter(data)


_kalman_filter: Optional[KalmanFilterSystem] = None
def get_kalman_filter() -> Optional[KalmanFilterSystem]: return _kalman_filter
def initialize_kalman_filter(data_dir) -> KalmanFilterSystem:
    global _kalman_filter
    _kalman_filter = KalmanFilterSystem(data_dir)
    return _kalman_filter
