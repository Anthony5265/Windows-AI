"""Active-learning primitives for Windows AI.

The module intentionally contains algorithmic building blocks rather than a
model-training framework.  Runtime integrations can compose these primitives
without introducing another orchestration layer.
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple
import logging
import math
import uuid

logger = logging.getLogger(__name__)


@dataclass
class ActiveLearningResult:
    result_id: str
    output: str
    confidence: float


class ActiveLearningSystem:
    """Small, deterministic active-learning utility collection."""

    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[ActiveLearningResult] = []
        self._config = {"initialized": True, "version": "1.1.0"}
        self._cache: Dict[str, Any] = {}
        logger.info("ActiveLearning initialized")

    @staticmethod
    def _validate_vectors(a: Sequence[float], b: Sequence[float]) -> None:
        if len(a) != len(b):
            raise ValueError("vectors must have the same dimensionality")
        if not a:
            raise ValueError("vectors must not be empty")
        if not all(math.isfinite(float(x)) for x in a) or not all(math.isfinite(float(x)) for x in b):
            raise ValueError("vectors must contain only finite values")

    def _euclidean_distance(self, a: Sequence[float], b: Sequence[float]) -> float:
        self._validate_vectors(a, b)
        return math.sqrt(sum((float(ai) - float(bi)) ** 2 for ai, bi in zip(a, b)))

    def _cosine_similarity(self, a: Sequence[float], b: Sequence[float]) -> float:
        self._validate_vectors(a, b)
        dot = sum(float(ai) * float(bi) for ai, bi in zip(a, b))
        na = math.sqrt(sum(float(ai) ** 2 for ai in a))
        nb = math.sqrt(sum(float(bi) ** 2 for bi in b))
        return dot / (na * nb) if na and nb else 0.0

    @staticmethod
    def _softmax(logits: Sequence[float]) -> List[float]:
        if not logits or not all(math.isfinite(float(x)) for x in logits):
            raise ValueError("logits must contain at least one finite value")
        max_l = max(float(x) for x in logits)
        exps = [math.exp(float(l) - max_l) for l in logits]
        total = sum(exps)
        return [e / total for e in exps]

    @staticmethod
    def _cross_entropy(probs: Sequence[float], target_idx: int) -> float:
        if not probs or not 0 <= target_idx < len(probs):
            raise ValueError("target_idx must reference a probability")
        if not all(0.0 <= float(p) <= 1.0 and math.isfinite(float(p)) for p in probs):
            raise ValueError("probabilities must be finite and within [0, 1]")
        return -math.log(max(float(probs[target_idx]), 1e-12))

    @staticmethod
    def _gradient_descent_step(weights: Sequence[float], gradients: Sequence[float], lr: float = 0.01) -> List[float]:
        if len(weights) != len(gradients):
            raise ValueError("weights and gradients must have the same dimensionality")
        if not math.isfinite(lr) or lr <= 0:
            raise ValueError("lr must be a positive finite number")
        if not all(math.isfinite(float(x)) for x in weights + gradients):
            raise ValueError("weights and gradients must contain finite values")
        return [float(w) - lr * float(g) for w, g in zip(weights, gradients)]

    def _kmeans(self, data: Sequence[Sequence[float]], k: int = 3, max_iter: int = 50) -> Tuple[List[List[float]], List[List[Sequence[float]]]]:
        if not data:
            raise ValueError("data must not be empty")
        if not 1 <= k <= len(data):
            raise ValueError("k must be between 1 and the number of data points")
        if max_iter < 1:
            raise ValueError("max_iter must be positive")
        dimension = len(data[0])
        if dimension == 0 or any(len(point) != dimension for point in data):
            raise ValueError("all data points must have the same non-zero dimensionality")
        if not all(math.isfinite(float(value)) for point in data for value in point):
            raise ValueError("data must contain only finite values")

        # Deterministic initialization without mutating process-global RNG state.
        centroids = [list(map(float, data[i])) for i in range(k)]
        clusters: List[List[Sequence[float]]] = [[] for _ in range(k)]
        for _ in range(max_iter):
            clusters = [[] for _ in range(k)]
            for point in data:
                index = min(range(k), key=lambda i: self._euclidean_distance(point, centroids[i]))
                clusters[index].append(point)
            new_centroids = [
                [sum(float(point[d]) for point in cluster) / len(cluster) for d in range(dimension)]
                if cluster else centroids[i]
                for i, cluster in enumerate(clusters)
            ]
            if new_centroids == centroids:
                break
            centroids = new_centroids
        return centroids, clusters

    @staticmethod
    def _confusion_matrix(y_true: Sequence[int], y_pred: Sequence[int], n_classes: int = 2) -> List[List[int]]:
        if len(y_true) != len(y_pred):
            raise ValueError("y_true and y_pred must have equal lengths")
        if n_classes < 1:
            raise ValueError("n_classes must be positive")
        cm = [[0] * n_classes for _ in range(n_classes)]
        for target, prediction in zip(y_true, y_pred):
            if not 0 <= target < n_classes or not 0 <= prediction < n_classes:
                raise ValueError("class labels must be within n_classes")
            cm[target][prediction] += 1
        return cm

    @staticmethod
    def _accuracy(y_true: Sequence[Any], y_pred: Sequence[Any]) -> float:
        if len(y_true) != len(y_pred):
            raise ValueError("y_true and y_pred must have equal lengths")
        return sum(t == p for t, p in zip(y_true, y_pred)) / len(y_true) if y_true else 0.0

    @staticmethod
    def _feature_importance(data: Sequence[Sequence[float]], labels: Sequence[Any], n_features: Optional[int] = None) -> List[float]:
        if not data:
            return []
        if len(labels) != len(data):
            raise ValueError("labels must have one entry per data point")
        width = len(data[0])
        count = width if n_features is None else n_features
        if not 0 < count <= width or any(len(row) != width for row in data):
            raise ValueError("n_features must be within the data dimensionality")
        importances: List[float] = []
        for feature in range(count):
            grouped: Dict[Any, List[float]] = {}
            for row, label in zip(data, labels):
                value = float(row[feature])
                if not math.isfinite(value):
                    raise ValueError("data must contain only finite values")
                grouped.setdefault(label, []).append(value)
            means = [sum(values) / len(values) for values in grouped.values() if values]
            mean = sum(means) / len(means) if means else 0.0
            importances.append(sum((value - mean) ** 2 for value in means) / len(means) if means else 0.0)
        total = sum(importances)
        return [importance / total for importance in importances] if total else [0.0] * len(importances)

    def process(self, text: str) -> ActiveLearningResult:
        """Record deterministic processing metadata without fabricating model output."""
        if not isinstance(text, str) or not text.strip():
            raise ValueError("text must be a non-empty string")
        normalized = " ".join(text.split())
        confidence = 1.0 if normalized else 0.0
        result = ActiveLearningResult(
            result_id=str(uuid.uuid4()),
            output=f"Processed: {normalized[:50]}",
            confidence=confidence,
        )
        self.results.append(result)
        return result


_active_learning: Optional[ActiveLearningSystem] = None


def get_active_learning() -> Optional[ActiveLearningSystem]:
    return _active_learning


def initialize_active_learning(data_dir) -> ActiveLearningSystem:
    global _active_learning
    _active_learning = ActiveLearningSystem(data_dir)
    return _active_learning
