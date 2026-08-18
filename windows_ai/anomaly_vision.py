"""Deterministic image-anomaly feature extraction for Windows AI."""

from dataclasses import dataclass
from datetime import datetime, timezone
import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence
import uuid

logger = logging.getLogger(__name__)


@dataclass
class AnomalyVisionResult:
    result_id: str
    data: Dict[str, Any]
    confidence: float
    timestamp: datetime = datetime.now(timezone.utc)


class AnomalyVisionSystem:
    """Small dependency-free vision feature extractor with deterministic output."""

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[AnomalyVisionResult] = []
        self._config = {"initialized": True, "version": "1.1.0"}
        self._cache: Dict[str, Dict[str, Any]] = {}
        logger.info("AnomalyVision initialized")

    @staticmethod
    def _validate_image(image: Sequence[Sequence[Any]]) -> None:
        if not isinstance(image, (list, tuple)) or not image:
            raise ValueError("image must be a non-empty rectangular matrix")
        width = len(image[0]) if isinstance(image[0], (list, tuple)) else 0
        if width == 0:
            raise ValueError("image must contain non-empty rows")
        for row in image:
            if not isinstance(row, (list, tuple)) or len(row) != width:
                raise ValueError("image must be rectangular")
            for value in row:
                if isinstance(value, (list, tuple)):
                    if len(value) < 3:
                        raise ValueError("RGB pixels require at least three channels")
                    channels = value[:3]
                else:
                    channels = (value,)
                if not all(isinstance(channel, (int, float)) and math.isfinite(channel) for channel in channels):
                    raise ValueError("image pixels must contain finite numeric values")

    def _to_grayscale(self, image):
        self._validate_image(image)
        if isinstance(image[0][0], (list, tuple)):
            return [[0.299 * float(p[0]) + 0.587 * float(p[1]) + 0.114 * float(p[2]) for p in row] for row in image]
        return [[float(p) for p in row] for row in image]

    def _convolve2d(self, image, kernel):
        if not kernel or not kernel[0] or any(len(row) != len(kernel[0]) for row in kernel):
            raise ValueError("kernel must be a non-empty rectangular matrix")
        h, w = len(image), len(image[0]) if image else 0
        kh, kw = len(kernel), len(kernel[0])
        if kh % 2 == 0 or kw % 2 == 0:
            raise ValueError("kernel dimensions must be odd")
        pad_h, pad_w = kh // 2, kw // 2
        result = [[0.0] * w for _ in range(h)]
        for i in range(pad_h, h - pad_h):
            for j in range(pad_w, w - pad_w):
                result[i][j] = sum(
                    image[i - pad_h + ki][j - pad_w + kj] * kernel[ki][kj]
                    for ki in range(kh) for kj in range(kw)
                )
        return result

    def _sobel_edges(self, image):
        gx_kernel = [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]
        gy_kernel = [[-1, -2, -1], [0, 0, 0], [1, 2, 1]]
        gx, gy = self._convolve2d(image, gx_kernel), self._convolve2d(image, gy_kernel)
        return [[math.hypot(gx[i][j], gy[i][j]) for j in range(len(image[0]))] for i in range(len(image))]

    def _histogram(self, image, bins=256):
        if not isinstance(bins, int) or bins <= 0:
            raise ValueError("bins must be a positive integer")
        hist = [0] * bins
        for row in image:
            for value in row:
                normalized = max(0.0, min(255.0, float(value)))
                hist[min(int(normalized * bins / 256), bins - 1)] += 1
        return hist

    def _threshold(self, image, thresh=128):
        if not math.isfinite(float(thresh)):
            raise ValueError("thresh must be finite")
        return [[255 if p > thresh else 0 for p in row] for row in image]

    def _gaussian_blur(self, image, sigma=1.0):
        sigma = float(sigma)
        if not math.isfinite(sigma) or sigma <= 0:
            raise ValueError("sigma must be a positive finite number")
        size = max(3, int(6 * sigma) | 1)
        half = size // 2
        kernel = []
        total = 0.0
        for i in range(size):
            row = []
            for j in range(size):
                x, y = i - half, j - half
                value = math.exp(-(x * x + y * y) / (2 * sigma * sigma))
                row.append(value)
                total += value
            kernel.append(row)
        return self._convolve2d(image, [[value / total for value in row] for row in kernel])

    def _connected_components(self, binary_image):
        h, w = len(binary_image), len(binary_image[0]) if binary_image else 0
        labels = [[0] * w for _ in range(h)]
        current_label = 0
        for i in range(h):
            for j in range(w):
                if binary_image[i][j] <= 0 or labels[i][j]:
                    continue
                current_label += 1
                stack = [(i, j)]
                while stack:
                    ci, cj = stack.pop()
                    if not (0 <= ci < h and 0 <= cj < w) or binary_image[ci][cj] <= 0 or labels[ci][cj]:
                        continue
                    labels[ci][cj] = current_label
                    stack.extend(((ci - 1, cj), (ci + 1, cj), (ci, cj - 1), (ci, cj + 1)))
        return labels, current_label

    def _bounding_boxes(self, labels, n_components):
        boxes = {}
        for i, row in enumerate(labels):
            for j, label in enumerate(row):
                if 0 < label <= n_components:
                    if label not in boxes:
                        boxes[label] = [i, j, i, j]
                    else:
                        box = boxes[label]
                        box[0], box[1] = min(box[0], i), min(box[1], j)
                        box[2], box[3] = max(box[2], i), max(box[3], j)
        return [boxes[label] for label in sorted(boxes)]

    def process(self, image) -> AnomalyVisionResult:
        """Analyze an image and return deterministic anomaly-oriented features."""
        gray = self._to_grayscale(image)
        edges = self._sobel_edges(gray)
        threshold = sum(sum(row) for row in gray) / (len(gray) * len(gray[0]))
        binary = self._threshold(gray, threshold)
        labels, count = self._connected_components(binary)
        boxes = self._bounding_boxes(labels, count)
        edge_mean = sum(sum(row) for row in edges) / (len(edges) * len(edges[0]))
        variance = sum((pixel - threshold) ** 2 for row in gray for pixel in row) / (len(gray) * len(gray[0]))
        confidence = max(0.0, min(1.0, 0.5 + min(0.5, math.sqrt(variance) / 255.0)))
        result = AnomalyVisionResult(
            result_id=str(uuid.uuid4()),
            data={"status": "processed", "mean_intensity": threshold, "variance": variance, "edge_mean": edge_mean, "components": count, "bounding_boxes": boxes},
            confidence=confidence,
            timestamp=datetime.now(timezone.utc),
        )
        self.results.append(result)
        return result


_anomaly_vision: Optional[AnomalyVisionSystem] = None


def get_anomaly_vision() -> Optional[AnomalyVisionSystem]:
    return _anomaly_vision


def initialize_anomaly_vision(data_dir) -> AnomalyVisionSystem:
    global _anomaly_vision
    _anomaly_vision = AnomalyVisionSystem(Path(data_dir))
    return _anomaly_vision
