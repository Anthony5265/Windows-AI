"""
Optical Flow System — Lucas-Kanade with pyramidal approach, Sobel gradients,
flow field estimation, flow visualization, motion detection, magnitude/direction
analysis. Uses only stdlib + numpy.
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
import logging
import uuid
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class OpticalFlowResult:
    result_id: str
    data: Dict[str, Any]
    confidence: float


def _gaussian_kernel(size: int = 5, sigma: float = 1.0) -> np.ndarray:
    ax = np.arange(size) - size // 2
    xx, yy = np.meshgrid(ax, ax)
    kernel = np.exp(-(xx ** 2 + yy ** 2) / (2 * sigma ** 2))
    return kernel / kernel.sum()


def _convolve2d(img: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    kh, kw = kernel.shape
    ph, pw = kh // 2, kw // 2
    padded = np.pad(img, ((ph, ph), (pw, pw)), mode='reflect')
    out = np.zeros_like(img, dtype=np.float64)
    for i in range(kh):
        for j in range(kw):
            out += kernel[i, j] * padded[i:i + img.shape[0], j:j + img.shape[1]]
    return out


def sobel_x(img: np.ndarray) -> np.ndarray:
    k = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float64)
    return _convolve2d(img, k)


def sobel_y(img: np.ndarray) -> np.ndarray:
    k = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float64)
    return _convolve2d(img, k)


def _downsample(img: np.ndarray, factor: int = 2) -> np.ndarray:
    g = _gaussian_kernel(5, 1.0)
    smoothed = _convolve2d(img, g)
    return smoothed[::factor, ::factor]


def _upsample(flow: np.ndarray, target_shape: Tuple[int, int], factor: int = 2) -> np.ndarray:
    h, w = target_shape
    y_idx = np.clip((np.arange(h) / factor).astype(int), 0, flow.shape[0] - 1)
    x_idx = np.clip((np.arange(w) / factor).astype(int), 0, flow.shape[1] - 1)
    return flow[np.ix_(y_idx, x_idx)] * factor


def lucas_kanade(prev: np.ndarray, curr: np.ndarray,
                 window: int = 7) -> Tuple[np.ndarray, np.ndarray]:
    """Single-scale Lucas-Kanade optical flow."""
    prev_f = prev.astype(np.float64)
    curr_f = curr.astype(np.float64)
    Ix = sobel_x(prev_f)
    Iy = sobel_y(prev_f)
    It = curr_f - prev_f
    h, w = prev.shape
    half = window // 2
    u = np.zeros((h, w), dtype=np.float64)
    v = np.zeros((h, w), dtype=np.float64)
    for y in range(half, h - half):
        for x in range(half, w - half):
            ix = Ix[y - half:y + half + 1, x - half:x + half + 1].ravel()
            iy = Iy[y - half:y + half + 1, x - half:x + half + 1].ravel()
            it = It[y - half:y + half + 1, x - half:x + half + 1].ravel()
            A = np.column_stack([ix, iy])
            AtA = A.T @ A
            det = AtA[0, 0] * AtA[1, 1] - AtA[0, 1] * AtA[1, 0]
            if abs(det) > 1e-6:
                b = -A.T @ it
                u[y, x] = (AtA[1, 1] * b[0] - AtA[0, 1] * b[1]) / det
                v[y, x] = (AtA[0, 0] * b[1] - AtA[1, 0] * b[0]) / det
    return u, v


def pyramidal_lucas_kanade(prev: np.ndarray, curr: np.ndarray,
                           levels: int = 3, window: int = 7) -> Tuple[np.ndarray, np.ndarray]:
    """Pyramidal Lucas-Kanade optical flow."""
    prev_pyr = [prev.astype(np.float64)]
    curr_pyr = [curr.astype(np.float64)]
    for _ in range(1, levels):
        prev_pyr.append(_downsample(prev_pyr[-1]))
        curr_pyr.append(_downsample(curr_pyr[-1]))
    u = np.zeros(prev_pyr[-1].shape, dtype=np.float64)
    v = np.zeros(prev_pyr[-1].shape, dtype=np.float64)
    for lev in range(levels - 1, -1, -1):
        if u.shape != prev_pyr[lev].shape:
            u = _upsample(u, prev_pyr[lev].shape)
            v = _upsample(v, prev_pyr[lev].shape)
        h, w = prev_pyr[lev].shape
        warped = np.zeros_like(curr_pyr[lev])
        for y in range(h):
            for x in range(w):
                sy = int(round(y + v[y, x]))
                sx = int(round(x + u[y, x]))
                if 0 <= sy < h and 0 <= sx < w:
                    warped[y, x] = curr_pyr[lev][sy, sx]
                else:
                    warped[y, x] = curr_pyr[lev][y, x]
        du, dv = lucas_kanade(prev_pyr[lev], warped, window)
        u += du
        v += dv
    return u, v


def flow_magnitude(u: np.ndarray, v: np.ndarray) -> np.ndarray:
    return np.sqrt(u ** 2 + v ** 2)


def flow_direction(u: np.ndarray, v: np.ndarray) -> np.ndarray:
    return np.arctan2(v, u)


def flow_to_color(u: np.ndarray, v: np.ndarray) -> np.ndarray:
    """Convert flow field to HSV-inspired RGB visualisation (H, W, 3) uint8."""
    mag = flow_magnitude(u, v)
    angle = flow_direction(u, v)
    max_mag = mag.max() + 1e-8
    norm_mag = mag / max_mag
    hue = (angle + np.pi) / (2 * np.pi)
    h, w = u.shape
    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    # Simple HSV -> RGB
    hi = (hue * 6).astype(int) % 6
    f = hue * 6 - hi
    v_ch = (norm_mag * 255).astype(np.uint8)
    p = np.zeros_like(v_ch)
    q = (norm_mag * (1 - f) * 255).astype(np.uint8)
    t = (norm_mag * f * 255).astype(np.uint8)
    for i in range(6):
        mask = hi == i
        if i == 0:   rgb[mask] = np.stack([v_ch[mask], t[mask], p[mask]], axis=-1)
        elif i == 1: rgb[mask] = np.stack([q[mask], v_ch[mask], p[mask]], axis=-1)
        elif i == 2: rgb[mask] = np.stack([p[mask], v_ch[mask], t[mask]], axis=-1)
        elif i == 3: rgb[mask] = np.stack([p[mask], q[mask], v_ch[mask]], axis=-1)
        elif i == 4: rgb[mask] = np.stack([t[mask], p[mask], v_ch[mask]], axis=-1)
        else:        rgb[mask] = np.stack([v_ch[mask], p[mask], q[mask]], axis=-1)
    return rgb


def detect_motion(u: np.ndarray, v: np.ndarray,
                  threshold: float = 1.0) -> np.ndarray:
    """Return binary motion mask."""
    return (flow_magnitude(u, v) > threshold).astype(np.uint8)


def flow_statistics(u: np.ndarray, v: np.ndarray) -> Dict[str, float]:
    mag = flow_magnitude(u, v)
    ang = flow_direction(u, v)
    return {
        "mean_magnitude": float(mag.mean()),
        "max_magnitude": float(mag.max()),
        "std_magnitude": float(mag.std()),
        "mean_direction": float(ang.mean()),
        "motion_area_fraction": float((mag > 1.0).mean()),
    }


class OpticalFlowSystem:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[OpticalFlowResult] = []
        self.levels = 3
        self.window = 7
        logger.info("OpticalFlow initialized")

    def process(self, input_data: Any) -> OpticalFlowResult:
        prev = np.asarray(input_data.get("prev", np.zeros((32, 32))), dtype=np.float64)
        curr = np.asarray(input_data.get("curr", np.zeros((32, 32))), dtype=np.float64)
        if prev.ndim == 3: prev = prev.mean(axis=2)
        if curr.ndim == 3: curr = curr.mean(axis=2)
        u, v = pyramidal_lucas_kanade(prev, curr, self.levels, self.window)
        stats = flow_statistics(u, v)
        result = OpticalFlowResult(
            result_id=str(uuid.uuid4()), data=stats,
            confidence=min(1.0, stats["mean_magnitude"] / 10.0),
        )
        self.results.append(result)
        return result

    def compute(self, prev: np.ndarray, curr: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        return pyramidal_lucas_kanade(prev, curr, self.levels, self.window)

    def visualize(self, u: np.ndarray, v: np.ndarray) -> np.ndarray:
        return flow_to_color(u, v)


_optical_flow: Optional[OpticalFlowSystem] = None
def get_optical_flow() -> Optional[OpticalFlowSystem]: return _optical_flow
def initialize_optical_flow(data_dir) -> OpticalFlowSystem:
    global _optical_flow
    _optical_flow = OpticalFlowSystem(data_dir)
    return _optical_flow
