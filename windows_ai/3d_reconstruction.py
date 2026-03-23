"""
3D Reconstruction System — Structure from Motion basics.

Feature point triangulation, camera matrix estimation, point cloud
generation from stereo pairs, mesh surface reconstruction approximation.
Uses only stdlib + numpy.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import logging
import uuid

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class Reconstruction3DResult:
    result_id: str
    data: Dict[str, Any]
    confidence: float


@dataclass
class PointCloud:
    """3-D point cloud with optional per-point colour."""
    points: np.ndarray          # (N, 3)
    colors: Optional[np.ndarray] = None  # (N, 3) 0-255


@dataclass
class CameraMatrix:
    """Intrinsic + extrinsic camera parameters."""
    K: np.ndarray               # 3x3 intrinsic
    R: np.ndarray               # 3x3 rotation
    t: np.ndarray               # 3x1 translation

    @property
    def projection(self) -> np.ndarray:
        """Return 3x4 projection matrix P = K [R | t]."""
        Rt = np.hstack([self.R, self.t.reshape(3, 1)])
        return self.K @ Rt


def _default_intrinsic(width: int = 640, height: int = 480) -> np.ndarray:
    f = max(width, height)
    return np.array([[f, 0, width / 2],
                     [0, f, height / 2],
                     [0, 0, 1]], dtype=np.float64)


def _sobel_x(img: np.ndarray) -> np.ndarray:
    k = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float64)
    return _convolve2d(img, k)


def _sobel_y(img: np.ndarray) -> np.ndarray:
    k = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float64)
    return _convolve2d(img, k)


def _convolve2d(img: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    kh, kw = kernel.shape
    ph, pw = kh // 2, kw // 2
    padded = np.pad(img, ((ph, ph), (pw, pw)), mode='reflect')
    out = np.zeros_like(img, dtype=np.float64)
    for i in range(kh):
        for j in range(kw):
            out += kernel[i, j] * padded[i:i + img.shape[0], j:j + img.shape[1]]
    return out


def _harris_corners(gray: np.ndarray, k: float = 0.04,
                    threshold: float = 0.01, max_points: int = 500) -> np.ndarray:
    """Detect Harris corners – returns (N, 2) array of (row, col)."""
    Ix = _sobel_x(gray)
    Iy = _sobel_y(gray)
    Ixx = Ix * Ix
    Iyy = Iy * Iy
    Ixy = Ix * Iy
    # Gaussian weighting via box blur
    w = 5
    for M in (Ixx, Iyy, Ixy):
        _box_blur_inplace(M, w)
    det = Ixx * Iyy - Ixy ** 2
    trace = Ixx + Iyy
    R = det - k * trace ** 2
    thresh = threshold * R.max() if R.max() > 0 else 0
    coords = np.argwhere(R > thresh)
    if len(coords) > max_points:
        scores = R[coords[:, 0], coords[:, 1]]
        idx = np.argsort(scores)[-max_points:]
        coords = coords[idx]
    return coords


def _box_blur_inplace(img: np.ndarray, w: int) -> None:
    """Simple in-place box blur."""
    kernel = np.ones((w, w), dtype=np.float64) / (w * w)
    blurred = _convolve2d(img, kernel)
    np.copyto(img, blurred)


def _ncc_match(patch1: np.ndarray, patch2: np.ndarray) -> float:
    """Normalised cross-correlation between two patches."""
    p1 = patch1.ravel().astype(np.float64)
    p2 = patch2.ravel().astype(np.float64)
    p1 -= p1.mean()
    p2 -= p2.mean()
    n1 = np.linalg.norm(p1)
    n2 = np.linalg.norm(p2)
    if n1 < 1e-8 or n2 < 1e-8:
        return -1.0
    return float(np.dot(p1, p2) / (n1 * n2))


def match_features(gray1: np.ndarray, gray2: np.ndarray,
                   patch_size: int = 11, ncc_thresh: float = 0.7,
                   max_points: int = 300) -> Tuple[np.ndarray, np.ndarray]:
    """Match Harris corners between two images via NCC.
    Returns (pts1, pts2) each (M, 2) in (row, col) format."""
    kp1 = _harris_corners(gray1, max_points=max_points)
    kp2 = _harris_corners(gray2, max_points=max_points)
    half = patch_size // 2
    h, w = gray1.shape

    def _valid(pts, shape):
        return pts[(pts[:, 0] >= half) & (pts[:, 0] < shape[0] - half) &
                   (pts[:, 1] >= half) & (pts[:, 1] < shape[1] - half)]

    kp1 = _valid(kp1, gray1.shape)
    kp2 = _valid(kp2, gray2.shape)
    if len(kp1) == 0 or len(kp2) == 0:
        return np.zeros((0, 2)), np.zeros((0, 2))

    matched1, matched2 = [], []
    for pt1 in kp1:
        r1, c1 = pt1
        p1 = gray1[r1 - half:r1 + half + 1, c1 - half:c1 + half + 1]
        best_score, best_idx = -1.0, -1
        for j, pt2 in enumerate(kp2):
            r2, c2 = pt2
            p2 = gray2[r2 - half:r2 + half + 1, c2 - half:c2 + half + 1]
            s = _ncc_match(p1, p2)
            if s > best_score:
                best_score, best_idx = s, j
        if best_score >= ncc_thresh:
            matched1.append(pt1)
            matched2.append(kp2[best_idx])
    if not matched1:
        return np.zeros((0, 2)), np.zeros((0, 2))
    return np.array(matched1), np.array(matched2)


def triangulate_points(P1: np.ndarray, P2: np.ndarray,
                       pts1: np.ndarray, pts2: np.ndarray) -> np.ndarray:
    """Linear triangulation via DLT for each pair of correspondences.
    pts are (N, 2) in (x, y) = (col, row) convention for projection.
    Returns (N, 3) world coordinates."""
    N = pts1.shape[0]
    points_3d = np.zeros((N, 3))
    for i in range(N):
        x1, y1 = pts1[i]
        x2, y2 = pts2[i]
        A = np.array([
            x1 * P1[2] - P1[0],
            y1 * P1[2] - P1[1],
            x2 * P2[2] - P2[0],
            y2 * P2[2] - P2[1],
        ])
        _, _, Vt = np.linalg.svd(A)
        X = Vt[-1]
        points_3d[i] = X[:3] / (X[3] + 1e-12)
    return points_3d


def estimate_fundamental(pts1: np.ndarray, pts2: np.ndarray) -> np.ndarray:
    """8-point algorithm for fundamental matrix. pts (N,2) in (x,y)."""
    assert pts1.shape[0] >= 8
    N = pts1.shape[0]
    A = np.zeros((N, 9))
    for i in range(N):
        x1, y1 = pts1[i]
        x2, y2 = pts2[i]
        A[i] = [x2 * x1, x2 * y1, x2, y2 * x1, y2 * y1, y2, x1, y1, 1]
    _, _, Vt = np.linalg.svd(A)
    F = Vt[-1].reshape(3, 3)
    U, S, Vt2 = np.linalg.svd(F)
    S[2] = 0
    return U @ np.diag(S) @ Vt2


def essential_from_fundamental(F: np.ndarray, K: np.ndarray) -> np.ndarray:
    return K.T @ F @ K


def decompose_essential(E: np.ndarray) -> List[Tuple[np.ndarray, np.ndarray]]:
    """Return up to 4 (R, t) candidates from essential matrix."""
    U, _, Vt = np.linalg.svd(E)
    if np.linalg.det(U) < 0:
        U = -U
    if np.linalg.det(Vt) < 0:
        Vt = -Vt
    W = np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]], dtype=np.float64)
    t = U[:, 2]
    R1 = U @ W @ Vt
    R2 = U @ W.T @ Vt
    return [(R1, t), (R1, -t), (R2, t), (R2, -t)]


def reconstruct_stereo(gray1: np.ndarray, gray2: np.ndarray,
                       K: Optional[np.ndarray] = None) -> PointCloud:
    """Full SfM pipeline for a stereo pair."""
    if K is None:
        K = _default_intrinsic(gray1.shape[1], gray1.shape[0])
    pts1_rc, pts2_rc = match_features(gray1, gray2, max_points=200)
    if pts1_rc.shape[0] < 8:
        logger.warning("Not enough matches for reconstruction")
        return PointCloud(points=np.zeros((0, 3)))
    # Convert (row, col) -> (x, y)
    pts1_xy = pts1_rc[:, ::-1].astype(np.float64)
    pts2_xy = pts2_rc[:, ::-1].astype(np.float64)
    F = estimate_fundamental(pts1_xy, pts2_xy)
    E = essential_from_fundamental(F, K)
    candidates = decompose_essential(E)
    P1 = K @ np.hstack([np.eye(3), np.zeros((3, 1))])
    best_cloud, best_count = None, -1
    for R, t in candidates:
        P2 = K @ np.hstack([R, t.reshape(3, 1)])
        cloud = triangulate_points(P1, P2, pts1_xy, pts2_xy)
        in_front = np.sum(cloud[:, 2] > 0)
        if in_front > best_count:
            best_count = in_front
            best_cloud = cloud
    return PointCloud(points=best_cloud if best_cloud is not None else np.zeros((0, 3)))


def approximate_mesh(cloud: PointCloud, grid_res: int = 32) -> Dict[str, np.ndarray]:
    """Simple voxel-grid surface approximation.
    Returns vertices and triangle indices."""
    pts = cloud.points
    if len(pts) == 0:
        return {"vertices": np.zeros((0, 3)), "triangles": np.zeros((0, 3), dtype=int)}
    mn = pts.min(axis=0)
    mx = pts.max(axis=0)
    span = mx - mn + 1e-8
    idx = ((pts - mn) / span * (grid_res - 1)).astype(int)
    idx = np.clip(idx, 0, grid_res - 1)
    occ = np.zeros((grid_res, grid_res, grid_res), dtype=bool)
    occ[idx[:, 0], idx[:, 1], idx[:, 2]] = True
    verts, tris = [], []
    step = span / grid_res
    for x in range(grid_res - 1):
        for y in range(grid_res - 1):
            for z in range(grid_res - 1):
                if occ[x, y, z]:
                    vi = len(verts)
                    base = mn + np.array([x, y, z]) * step
                    verts.extend([base, base + step * [1, 0, 0],
                                  base + step * [1, 1, 0], base + step * [0, 1, 0]])
                    tris.append([vi, vi + 1, vi + 2])
                    tris.append([vi, vi + 2, vi + 3])
    if not verts:
        return {"vertices": np.zeros((0, 3)), "triangles": np.zeros((0, 3), dtype=int)}
    return {"vertices": np.array(verts), "triangles": np.array(tris, dtype=int)}


class Reconstruction3DSystem:
    """Module-level 3-D reconstruction system."""

    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[Reconstruction3DResult] = []
        self.K: Optional[np.ndarray] = None
        logger.info("Reconstruction3D initialized")

    def set_intrinsic(self, K: np.ndarray) -> None:
        self.K = K.copy()

    def process(self, input_data: Any) -> Reconstruction3DResult:
        """Process a stereo pair supplied as a dict with 'left' and 'right' gray images."""
        if isinstance(input_data, dict):
            left = np.asarray(input_data.get("left", np.zeros((64, 64))), dtype=np.float64)
            right = np.asarray(input_data.get("right", np.zeros((64, 64))), dtype=np.float64)
        else:
            left = right = np.zeros((64, 64), dtype=np.float64)
        cloud = reconstruct_stereo(left, right, K=self.K)
        mesh = approximate_mesh(cloud)
        result = Reconstruction3DResult(
            result_id=str(uuid.uuid4()),
            data={
                "num_points": int(cloud.points.shape[0]),
                "num_vertices": int(mesh["vertices"].shape[0]),
                "num_triangles": int(mesh["triangles"].shape[0]),
                "bounds_min": cloud.points.min(axis=0).tolist() if len(cloud.points) else [],
                "bounds_max": cloud.points.max(axis=0).tolist() if len(cloud.points) else [],
            },
            confidence=min(1.0, cloud.points.shape[0] / 100.0),
        )
        self.results.append(result)
        return result

    def reconstruct(self, gray1: np.ndarray, gray2: np.ndarray) -> PointCloud:
        return reconstruct_stereo(gray1, gray2, K=self.K)

    def build_mesh(self, cloud: PointCloud, grid_res: int = 32) -> Dict[str, np.ndarray]:
        return approximate_mesh(cloud, grid_res)


_3d_reconstruction: Optional[Reconstruction3DSystem] = None


def get_3d_reconstruction() -> Optional[Reconstruction3DSystem]:
    return _3d_reconstruction


def initialize_3d_reconstruction(data_dir) -> Reconstruction3DSystem:
    global _3d_reconstruction
    _3d_reconstruction = Reconstruction3DSystem(data_dir)
    return _3d_reconstruction
