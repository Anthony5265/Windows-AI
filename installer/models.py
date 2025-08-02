from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List
import urllib.request


@dataclass
class ModelInfo:
    """Metadata describing a downloadable model."""

    name: str
    url: str
    checksum: str
    requires_gpu: bool = False
    min_ram_gb: float | None = None
    min_vram_gb: float | None = None


# Default registry with placeholder models. In a real application these
# would point to actual model files hosted online.
MODEL_REGISTRY: Dict[str, ModelInfo] = {
    "tiny-cpu": ModelInfo(
        name="tiny-cpu",
        url="https://example.com/tiny-cpu.bin",
        checksum="0" * 64,
        requires_gpu=False,
        min_ram_gb=4,
    ),
    "medium-gpu": ModelInfo(
        name="medium-gpu",
        url="https://example.com/medium-gpu.bin",
        checksum="0" * 64,
        requires_gpu=True,
        min_ram_gb=8,
        min_vram_gb=4,
    ),
}


def list_models() -> List[ModelInfo]:
    """Return all known models."""

    return list(MODEL_REGISTRY.values())


def get_model(name: str) -> ModelInfo:
    """Fetch a model from the registry by ``name``."""

    return MODEL_REGISTRY[name]


def compatible_models(info: Dict[str, float | str | None]) -> List[ModelInfo]:
    """Return models compatible with the detected ``info``."""

    results: List[ModelInfo] = []
    for model in list_models():
        if model.requires_gpu and not info.get("gpu_name"):
            continue
        if model.min_ram_gb and (info.get("ram_total_gb") or 0) < model.min_ram_gb:
            continue
        if model.min_vram_gb and (info.get("gpu_vram_gb") or 0) < model.min_vram_gb:
            continue
        results.append(model)
    return results


def verify_checksum(path: str | Path, expected: str) -> bool:
    """Check the SHA256 hash of ``path`` against ``expected``."""

    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest().lower() == expected.lower()


def download_model(
    name: str,
    dest_dir: str | Path,
    progress: Callable[[int, int], None] | None = None,
) -> Path:
    """Download a model and verify its checksum.

    Parameters
    ----------
    name:
        Identifier of the model to fetch.
    dest_dir:
        Directory where the model will be stored.
    progress:
        Optional callback receiving ``bytes_downloaded`` and ``total_bytes``.

    Returns
    -------
    pathlib.Path
        Path to the downloaded file.
    """

    info = get_model(name)
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    filename = Path(info.url).name
    dest_path = dest_dir / filename

    with urllib.request.urlopen(info.url) as resp:
        total = int(resp.getheader("Content-Length", 0))
        downloaded = 0
        with open(dest_path, "wb") as fh:
            while True:
                chunk = resp.read(8192)
                if not chunk:
                    break
                fh.write(chunk)
                downloaded += len(chunk)
                if progress:
                    progress(downloaded, total)

    if info.checksum and not verify_checksum(dest_path, info.checksum):
        raise ValueError("Checksum mismatch for model " + name)

    return dest_path
