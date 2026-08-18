"""
Action Recognition System — temporal feature extraction, optical flow
histograms, motion energy images, pose sequence classification.
Predefined actions: walking, running, waving, sitting, standing.
Uses only stdlib + numpy.
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
import logging
import uuid
import numpy as np

logger = logging.getLogger(__name__)

ACTIONS = ["walking", "running", "waving", "sitting", "standing", "jumping", "unknown"]

@dataclass
class ActionRecognitionResult:
    result_id: str
    data: Dict[str, Any]
    confidence: float


def _validate_gray_frame(frame: np.ndarray, name: str = "frame") -> np.ndarray:
    arr = np.asarray(frame)
    if arr.ndim != 2:
        raise ValueError(f"{name} must be a 2D grayscale image, got shape {arr.shape}")
    if arr.size == 0:
        raise ValueError(f"{name} must not be empty")
    if not np.issubdtype(arr.dtype, np.number):
        raise TypeError(f"{name} must contain numeric values")
    arr = arr.astype(np.float64, copy=False)
    if not np.isfinite(arr).all():
        raise ValueError(f"{name} contains non-finite values")
    return arr


def _validate_frame_sequence(frames: List[np.ndarray]) -> List[np.ndarray]:
    if not frames:
        raise ValueError("at least one frame is required")
    gray_frames = []
    for index, frame in enumerate(frames):
        arr = np.asarray(frame)
        if arr.ndim == 3:
            if arr.shape[2] not in (1, 3, 4):
                raise ValueError(f"frame {index} has unsupported channel count {arr.shape[2]}")
            arr = arr[..., :3].mean(axis=2) if arr.shape[2] > 1 else arr[..., 0]
        gray_frames.append(_validate_gray_frame(arr, f"frame {index}"))
    shape = gray_frames[0].shape
    if any(frame.shape != shape for frame in gray_frames[1:]):
        raise ValueError("all frames must have identical dimensions")
    return gray_frames


def _sobel(img: np.ndarray, axis: int) -> np.ndarray:
    if axis not in (0, 1):
        raise ValueError("axis must be 0 or 1")
    img = _validate_gray_frame(img)
    kx = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float64)
    ky = kx.T
    k = kx if axis == 1 else ky
    padded = np.pad(img, ((1, 1), (1, 1)), mode="reflect")
    out = np.zeros_like(img, dtype=np.float64)
    for i in range(3):
        for j in range(3):
            out += k[i, j] * padded[i:i + img.shape[0], j:j + img.shape[1]]
    return out


def compute_optical_flow_simple(prev: np.ndarray, curr: np.ndarray,
                                window: int = 5) -> Tuple[np.ndarray, np.ndarray]:
    """Lucas-Kanade optical flow (single scale)."""
    prev = _validate_gray_frame(prev, "prev")
    curr = _validate_gray_frame(curr, "curr")
    if prev.shape != curr.shape:
        raise ValueError("prev and curr must have identical dimensions")
    if window < 3 or window % 2 == 0:
        raise ValueError("window must be an odd integer >= 3")
    if min(prev.shape) < window:
        raise ValueError("window must not exceed the smallest image dimension")
    Ix = _sobel(prev, axis=1)
    Iy = _sobel(prev, axis=0)
    It = curr - prev
    h, w = prev.shape
    half = window // 2
    u = np.zeros((h, w), dtype=np.float64)
    v = np.zeros((h, w), dtype=np.float64)
    for y in range(half, h - half, 2):
        for x in range(half, w - half, 2):
            ix = Ix[y - half:y + half + 1, x - half:x + half + 1].ravel()
            iy = Iy[y - half:y + half + 1, x - half:x + half + 1].ravel()
            it = It[y - half:y + half + 1, x - half:x + half + 1].ravel()
            A = np.column_stack([ix, iy])
            AtA = A.T @ A
            if np.linalg.det(AtA) > 1e-6:
                flow = np.linalg.solve(AtA, -A.T @ it)
                u[y, x] = flow[0]
                v[y, x] = flow[1]
    return u, v


def flow_histogram(u: np.ndarray, v: np.ndarray, n_bins: int = 8) -> np.ndarray:
    """Histogram of flow orientations weighted by magnitude."""
    u = np.asarray(u, dtype=np.float64)
    v = np.asarray(v, dtype=np.float64)
    if u.ndim != 2 or v.ndim != 2 or u.shape != v.shape:
        raise ValueError("u and v must be 2D arrays with identical dimensions")
    if not np.isfinite(u).all() or not np.isfinite(v).all():
        raise ValueError("flow arrays contain non-finite values")
    if n_bins < 1:
        raise ValueError("n_bins must be positive")
    mag = np.hypot(u, v)
    angle = np.mod(np.arctan2(v, u), 2 * np.pi)
    bins = np.linspace(0, 2 * np.pi, n_bins + 1)
    hist, _ = np.histogram(angle, bins=bins, weights=mag)
    hist = hist.astype(np.float64)
    total = hist.sum()
    if total > 0:
        hist /= total
    return hist


def motion_energy_image(frames: List[np.ndarray]) -> np.ndarray:
    """Motion Energy Image from a sequence of gray frames."""
    gray = _validate_frame_sequence(frames)
    mei = np.zeros_like(gray[0], dtype=np.float64)
    for i in range(1, len(gray)):
        diff = np.abs(gray[i] - gray[i - 1])
        mei = np.maximum(mei, diff)
    return mei


def motion_history_image(frames: List[np.ndarray], tau: float = 0.8) -> np.ndarray:
    """Motion History Image with exponential decay."""
    gray = _validate_frame_sequence(frames)
    if not 0 < tau <= 1:
        raise ValueError("tau must be in the interval (0, 1]")
    mhi = np.zeros_like(gray[0], dtype=np.float64)
    for i in range(1, len(gray)):
        diff = np.abs(gray[i] - gray[i - 1])
        motion = diff > 15.0
        mhi[~motion] *= tau
        mhi[motion] = 1.0
    return mhi


def _hu_moments(img: np.ndarray) -> np.ndarray:
    """Compute first 4 Hu-style moments from a single-channel image."""
    img = _validate_gray_frame(img, "img")
    y, x = np.mgrid[:img.shape[0], :img.shape[1]]
    m00 = img.sum()
    if m00 <= 0:
        return np.zeros(4, dtype=np.float64)
    cx = (x * img).sum() / m00
    cy = (y * img).sum() / m00
    dx = x - cx
    dy = y - cy
    mu20 = (dx ** 2 * img).sum() / m00
    mu02 = (dy ** 2 * img).sum() / m00
    mu11 = (dx * dy * img).sum() / m00
    mu30 = (dx ** 3 * img).sum() / m00
    return np.array([mu20 + mu02, (mu20 - mu02) ** 2 + 4 * mu11 ** 2,
                     mu30 ** 2, mu20 * mu02])


def extract_temporal_features(frames: List[np.ndarray]) -> np.ndarray:
    """Extract a fixed-length feature vector from a sequence of gray frames."""
    gray = _validate_frame_sequence(frames)
    if len(gray) < 2:
        return np.zeros(24, dtype=np.float64)
    features = []
    mei = motion_energy_image(gray)
    mhi = motion_history_image(gray)
    features.extend(_hu_moments(mei).tolist())
    features.extend(_hu_moments(mhi).tolist())
    flow_hists = []
    step = max(1, len(gray) // 4)
    for i in range(1, len(gray), step):
        u, v = compute_optical_flow_simple(gray[i - 1], gray[i])
        flow_hists.append(flow_histogram(u, v, n_bins=8))
    avg_hist = np.mean(flow_hists, axis=0) if flow_hists else np.zeros(8)
    features.extend(avg_hist.tolist())
    mag_series = np.array([
        np.abs(gray[i] - gray[i - 1]).mean() for i in range(1, len(gray))
    ], dtype=np.float64)
    features.extend([mag_series.mean(), mag_series.std(), mag_series.max(),
                     float(np.argmax(mag_series)) / max(len(mag_series), 1)])
    return np.array(features[:24], dtype=np.float64)


def classify_action(features: np.ndarray) -> Tuple[str, float]:
    """Rule-based action classification from temporal features."""
    features = np.asarray(features, dtype=np.float64)
    if features.ndim != 1 or len(features) < 20 or not np.isfinite(features).all():
        raise ValueError("features must be a finite one-dimensional vector of length >= 20")
    motion_mean, motion_std, motion_max = features[16:19]
    flow_hist = features[8:16]
    vertical_energy = flow_hist[1] + flow_hist[5]
    horizontal_energy = flow_hist[0] + flow_hist[4]
    if motion_mean < 2.0:
        return ("sitting", 0.7) if vertical_energy < 0.1 else ("standing", 0.65)
    if motion_max > 40 and motion_std > 10:
        return "jumping", 0.6
    if horizontal_energy > 0.4:
        return ("running", 0.7) if motion_mean > 15 else ("walking", 0.65)
    if vertical_energy > 0.35 and motion_std > 5:
        return "waving", 0.6
    if motion_mean > 10:
        return "running", 0.55
    if motion_mean > 4:
        return "walking", 0.55
    return "unknown", 0.3


class ActionRecognitionSystem:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[ActionRecognitionResult] = []
        logger.info("ActionRecognition initialized")

    def process(self, input_data: Any) -> ActionRecognitionResult:
        frames = input_data if isinstance(input_data, list) else [input_data]
        gray_frames = _validate_frame_sequence(frames)
        feats = extract_temporal_features(gray_frames)
        action, conf = classify_action(feats)
        result = ActionRecognitionResult(
            result_id=str(uuid.uuid4()),
            data={"action": action, "features": feats.tolist(), "num_frames": len(gray_frames)},
            confidence=conf,
        )
        self.results.append(result)
        return result

    def recognize(self, frames: List[np.ndarray]) -> Tuple[str, float]:
        gray = _validate_frame_sequence(frames)
        feats = extract_temporal_features(gray)
        return classify_action(feats)


_action_recognition: Optional[ActionRecognitionSystem] = None

def get_action_recognition() -> Optional[ActionRecognitionSystem]:
    return _action_recognition

def initialize_action_recognition(data_dir) -> ActionRecognitionSystem:
    global _action_recognition
    _action_recognition = ActionRecognitionSystem(data_dir)
    return _action_recognition
