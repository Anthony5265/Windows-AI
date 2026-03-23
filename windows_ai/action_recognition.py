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


def _sobel(img: np.ndarray, axis: int) -> np.ndarray:
    kx = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float64)
    ky = kx.T
    k = kx if axis == 1 else ky
    ph, pw = 1, 1
    padded = np.pad(img, ((ph, ph), (pw, pw)), mode='reflect')
    out = np.zeros_like(img, dtype=np.float64)
    for i in range(3):
        for j in range(3):
            out += k[i, j] * padded[i:i + img.shape[0], j:j + img.shape[1]]
    return out


def compute_optical_flow_simple(prev: np.ndarray, curr: np.ndarray,
                                window: int = 5) -> Tuple[np.ndarray, np.ndarray]:
    """Lucas-Kanade optical flow (single scale)."""
    Ix = _sobel(prev, axis=1)
    Iy = _sobel(prev, axis=0)
    It = curr.astype(np.float64) - prev.astype(np.float64)
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
    mag = np.sqrt(u ** 2 + v ** 2)
    angle = np.arctan2(v, u) + np.pi
    bins = np.linspace(0, 2 * np.pi, n_bins + 1)
    hist = np.zeros(n_bins)
    for i in range(n_bins):
        mask = (angle >= bins[i]) & (angle < bins[i + 1])
        hist[i] = mag[mask].sum()
    total = hist.sum()
    if total > 0:
        hist /= total
    return hist


def motion_energy_image(frames: List[np.ndarray]) -> np.ndarray:
    """Binary Motion Energy Image from a sequence of gray frames."""
    mei = np.zeros_like(frames[0], dtype=np.float64)
    for i in range(1, len(frames)):
        diff = np.abs(frames[i].astype(np.float64) - frames[i - 1].astype(np.float64))
        mei = np.maximum(mei, diff)
    return mei


def motion_history_image(frames: List[np.ndarray], tau: float = 0.8) -> np.ndarray:
    """Motion History Image with exponential decay."""
    mhi = np.zeros_like(frames[0], dtype=np.float64)
    for i in range(1, len(frames)):
        diff = np.abs(frames[i].astype(np.float64) - frames[i - 1].astype(np.float64))
        motion = diff > 15.0
        mhi[motion] = 1.0
        mhi[~motion] *= tau
    return mhi


def _hu_moments(img: np.ndarray) -> np.ndarray:
    """Compute first 4 Hu moments from a single-channel image."""
    y, x = np.mgrid[:img.shape[0], :img.shape[1]]
    m00 = img.sum() + 1e-12
    cx = (x * img).sum() / m00
    cy = (y * img).sum() / m00
    dx = x - cx
    dy = y - cy
    mu20 = (dx ** 2 * img).sum() / m00
    mu02 = (dy ** 2 * img).sum() / m00
    mu11 = (dx * dy * img).sum() / m00
    mu30 = (dx ** 3 * img).sum() / m00
    return np.array([mu20 + mu02, (mu20 - mu02) ** 2 + 4 * mu11 ** 2,
                     (mu30) ** 2, mu20 * mu02])


def extract_temporal_features(frames: List[np.ndarray]) -> np.ndarray:
    """Extract a feature vector from a sequence of gray frames."""
    features = []
    if len(frames) < 2:
        return np.zeros(24)
    mei = motion_energy_image(frames)
    mhi = motion_history_image(frames)
    features.extend(_hu_moments(mei).tolist())
    features.extend(_hu_moments(mhi).tolist())
    flow_hists = []
    step = max(1, len(frames) // 4)
    for i in range(1, len(frames), step):
        u, v = compute_optical_flow_simple(frames[i - 1], frames[i])
        flow_hists.append(flow_histogram(u, v, n_bins=8))
    if flow_hists:
        avg_hist = np.mean(flow_hists, axis=0)
    else:
        avg_hist = np.zeros(8)
    features.extend(avg_hist.tolist())
    mag_series = []
    for i in range(1, len(frames)):
        diff = np.abs(frames[i].astype(np.float64) - frames[i - 1].astype(np.float64)).mean()
        mag_series.append(diff)
    mag_series = np.array(mag_series) if mag_series else np.zeros(1)
    features.extend([mag_series.mean(), mag_series.std(), mag_series.max(),
                     float(np.argmax(mag_series)) / max(len(mag_series), 1)])
    return np.array(features[:24]) if len(features) >= 24 else np.pad(features, (0, 24 - len(features)))


def classify_action(features: np.ndarray) -> Tuple[str, float]:
    """Rule-based action classification from temporal features."""
    motion_mean = features[16] if len(features) > 16 else 0
    motion_std = features[17] if len(features) > 17 else 0
    motion_max = features[18] if len(features) > 18 else 0
    flow_hist = features[8:16] if len(features) > 15 else np.zeros(8)
    vertical_energy = flow_hist[1] + flow_hist[5] if len(flow_hist) > 5 else 0
    horizontal_energy = flow_hist[0] + flow_hist[4] if len(flow_hist) > 4 else 0
    if motion_mean < 2.0:
        if vertical_energy < 0.1:
            return "sitting", 0.7
        return "standing", 0.65
    if motion_max > 40 and motion_std > 10:
        return "jumping", 0.6
    if horizontal_energy > 0.4:
        if motion_mean > 15:
            return "running", 0.7
        return "walking", 0.65
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
        gray_frames = [np.asarray(f, dtype=np.float64) for f in frames]
        if gray_frames and gray_frames[0].ndim == 3:
            gray_frames = [f.mean(axis=2) for f in gray_frames]
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
        gray = [f.mean(axis=2) if f.ndim == 3 else f for f in frames]
        feats = extract_temporal_features(gray)
        return classify_action(feats)


_action_recognition: Optional[ActionRecognitionSystem] = None
def get_action_recognition() -> Optional[ActionRecognitionSystem]: return _action_recognition
def initialize_action_recognition(data_dir) -> ActionRecognitionSystem:
    global _action_recognition
    _action_recognition = ActionRecognitionSystem(data_dir)
    return _action_recognition
