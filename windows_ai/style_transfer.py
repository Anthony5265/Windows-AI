"""
Style Transfer System — color/style transfer using histogram matching,
color palette extraction, Gram matrix statistics, luminance transfer,
color transfer in LAB space. Uses only stdlib + numpy.
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
import logging
import uuid
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class StyleTransferResult:
    result_id: str
    data: Dict[str, Any]
    confidence: float


def _rgb_to_lab(img: np.ndarray) -> np.ndarray:
    """Approximate RGB [0-255] -> LAB conversion via linearised sRGB -> XYZ -> LAB."""
    rgb = img.astype(np.float64) / 255.0
    mask = rgb > 0.04045
    rgb[mask] = ((rgb[mask] + 0.055) / 1.055) ** 2.4
    rgb[~mask] = rgb[~mask] / 12.92
    M = np.array([[0.4124564, 0.3575761, 0.1804375],
                  [0.2126729, 0.7151522, 0.0721750],
                  [0.0193339, 0.1191920, 0.9503041]])
    xyz = rgb @ M.T
    ref = np.array([0.95047, 1.0, 1.08883])
    xyz /= ref
    mask = xyz > 0.008856
    xyz[mask] = xyz[mask] ** (1.0 / 3.0)
    xyz[~mask] = 7.787 * xyz[~mask] + 16.0 / 116.0
    L = 116.0 * xyz[..., 1] - 16.0
    a = 500.0 * (xyz[..., 0] - xyz[..., 1])
    b = 200.0 * (xyz[..., 1] - xyz[..., 2])
    return np.stack([L, a, b], axis=-1)


def _lab_to_rgb(lab: np.ndarray) -> np.ndarray:
    """Approximate LAB -> RGB [0-255]."""
    L, a, b = lab[..., 0], lab[..., 1], lab[..., 2]
    fy = (L + 16.0) / 116.0
    fx = a / 500.0 + fy
    fz = fy - b / 200.0
    xyz = np.stack([fx, fy, fz], axis=-1)
    mask = xyz > 0.206893
    xyz[mask] = xyz[mask] ** 3
    xyz[~mask] = (xyz[~mask] - 16.0 / 116.0) / 7.787
    ref = np.array([0.95047, 1.0, 1.08883])
    xyz *= ref
    M_inv = np.array([[ 3.2404542, -1.5371385, -0.4985314],
                      [-0.9692660,  1.8760108,  0.0415560],
                      [ 0.0556434, -0.2040259,  1.0572252]])
    rgb = xyz @ M_inv.T
    rgb = np.clip(rgb, 0, None)
    mask = rgb > 0.0031308
    rgb[mask] = 1.055 * rgb[mask] ** (1.0 / 2.4) - 0.055
    rgb[~mask] = 12.92 * rgb[~mask]
    return np.clip(rgb * 255.0, 0, 255).astype(np.uint8)


def color_transfer_lab(source: np.ndarray, target: np.ndarray) -> np.ndarray:
    """Reinhard et al. colour transfer in LAB space."""
    src_lab = _rgb_to_lab(source)
    tgt_lab = _rgb_to_lab(target)
    for ch in range(3):
        s_mean, s_std = src_lab[..., ch].mean(), src_lab[..., ch].std() + 1e-8
        t_mean, t_std = tgt_lab[..., ch].mean(), tgt_lab[..., ch].std() + 1e-8
        src_lab[..., ch] = (src_lab[..., ch] - s_mean) * (t_std / s_std) + t_mean
    return _lab_to_rgb(src_lab)


def histogram_match_channel(src: np.ndarray, ref: np.ndarray) -> np.ndarray:
    """Match histogram of a single-channel image to reference."""
    s_vals, s_idx, s_counts = np.unique(src.ravel(), return_inverse=True, return_counts=True)
    r_vals, r_counts = np.unique(ref.ravel(), return_counts=True)
    s_cdf = np.cumsum(s_counts).astype(np.float64)
    s_cdf /= s_cdf[-1]
    r_cdf = np.cumsum(r_counts).astype(np.float64)
    r_cdf /= r_cdf[-1]
    interp = np.interp(s_cdf, r_cdf, r_vals)
    return interp[s_idx].reshape(src.shape).astype(src.dtype)


def histogram_match(source: np.ndarray, reference: np.ndarray) -> np.ndarray:
    """Per-channel histogram matching for colour images."""
    if source.ndim == 2:
        return histogram_match_channel(source, reference)
    result = np.empty_like(source)
    for ch in range(source.shape[2]):
        result[..., ch] = histogram_match_channel(source[..., ch], reference[..., ch])
    return result


def extract_palette(img: np.ndarray, n_colors: int = 5) -> np.ndarray:
    """Simple k-means palette extraction. Returns (n_colors, 3)."""
    pixels = img.reshape(-1, 3).astype(np.float64)
    rng = np.random.RandomState(42)
    idx = rng.choice(len(pixels), size=min(n_colors, len(pixels)), replace=False)
    centers = pixels[idx].copy()
    for _ in range(20):
        dists = np.linalg.norm(pixels[:, None] - centers[None, :], axis=2)
        labels = dists.argmin(axis=1)
        new_centers = np.array([pixels[labels == k].mean(axis=0) if np.any(labels == k)
                                else centers[k] for k in range(n_colors)])
        if np.allclose(new_centers, centers, atol=1.0):
            break
        centers = new_centers
    return np.clip(centers, 0, 255).astype(np.uint8)


def gram_matrix(features: np.ndarray) -> np.ndarray:
    """Compute Gram matrix from (C, H*W) feature map."""
    G = features @ features.T
    return G / features.shape[1]


def compute_style_statistics(img: np.ndarray) -> Dict[str, Any]:
    """Compute style statistics (channel means, stds, Gram of colour channels)."""
    if img.ndim == 2:
        img = np.stack([img] * 3, axis=-1)
    h, w, c = img.shape
    flat = img.reshape(-1, c).astype(np.float64).T  # (C, N)
    return {
        "channel_means": flat.mean(axis=1).tolist(),
        "channel_stds": flat.std(axis=1).tolist(),
        "gram": gram_matrix(flat).tolist(),
    }


def luminance_transfer(source: np.ndarray, target: np.ndarray) -> np.ndarray:
    """Transfer luminance from target onto source while keeping source colour."""
    src_lab = _rgb_to_lab(source)
    tgt_lab = _rgb_to_lab(target)
    s_L = src_lab[..., 0]
    t_L = tgt_lab[..., 0]
    s_mean, s_std = s_L.mean(), s_L.std() + 1e-8
    t_mean, t_std = t_L.mean(), t_L.std() + 1e-8
    src_lab[..., 0] = np.clip((s_L - s_mean) * (t_std / s_std) + t_mean, 0, 100)
    return _lab_to_rgb(src_lab)


class StyleTransferSystem:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[StyleTransferResult] = []
        logger.info("StyleTransfer initialized")

    def process(self, input_data: Any) -> StyleTransferResult:
        src = np.asarray(input_data.get("source", np.zeros((8, 8, 3))), dtype=np.uint8)
        tgt = np.asarray(input_data.get("target", np.zeros((8, 8, 3))), dtype=np.uint8)
        transferred = color_transfer_lab(src, tgt)
        palette = extract_palette(tgt)
        stats = compute_style_statistics(tgt)
        result = StyleTransferResult(
            result_id=str(uuid.uuid4()),
            data={"shape": list(transferred.shape), "palette": palette.tolist(), "style_stats": stats},
            confidence=0.85,
        )
        self.results.append(result)
        return result

    def transfer_color(self, source: np.ndarray, target: np.ndarray) -> np.ndarray:
        return color_transfer_lab(source, target)

    def match_histogram(self, source: np.ndarray, reference: np.ndarray) -> np.ndarray:
        return histogram_match(source, reference)

    def get_palette(self, img: np.ndarray, n: int = 5) -> np.ndarray:
        return extract_palette(img, n)

    def transfer_luminance(self, source: np.ndarray, target: np.ndarray) -> np.ndarray:
        return luminance_transfer(source, target)


_style_transfer: Optional[StyleTransferSystem] = None
def get_style_transfer() -> Optional[StyleTransferSystem]: return _style_transfer
def initialize_style_transfer(data_dir) -> StyleTransferSystem:
    global _style_transfer
    _style_transfer = StyleTransferSystem(data_dir)
    return _style_transfer
