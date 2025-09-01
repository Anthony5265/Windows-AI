from __future__ import annotations

import os
import shutil
from typing import List

import requests

try:  # pragma: no cover - module may be unavailable in some environments
    from huggingface_hub import snapshot_download
except Exception:  # pragma: no cover
    snapshot_download = None


def discover_models(path: str, extension: str = ".model") -> List[str]:
    """Return a list of model files in *path* matching *extension*.

    If *path* does not exist an empty list is returned.
    """

    if not os.path.isdir(path):
        return []

    return [
        os.path.join(path, name)
        for name in os.listdir(path)
        if name.endswith(extension)
    ]


def download_model(src: str, dest: str) -> str:
    """Copy a model file from *src* to *dest* and return destination path.

    Any copy errors result in an empty string being returned.  The destination
    directory is created if it does not already exist.
    """

    os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
    try:
        shutil.copyfile(src, dest)
    except OSError:
        return ""
    return dest


def fetch_llm(model_id: str, dest: str) -> str:
    """Download a language model identified by *model_id* to *dest*.

    *model_id* may be a direct HTTP(S) URL or a Hugging Face repository ID.  If
    a URL is provided the file is written to *dest*.  For Hugging Face IDs the
    model snapshot is downloaded into *dest* as a directory.

    Returns the destination path on success or an empty string on failure.
    """

    try:
        if model_id.startswith(("http://", "https://")):
            os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
            with requests.get(model_id, stream=True, timeout=30) as resp:
                resp.raise_for_status()
                with open(dest, "wb") as fh:
                    for chunk in resp.iter_content(chunk_size=8192):
                        fh.write(chunk)
            return dest

        if snapshot_download is None:
            raise ImportError("huggingface_hub is required for non-URL downloads")

        os.makedirs(dest, exist_ok=True)
        return snapshot_download(
            repo_id=model_id,
            local_dir=dest,
            local_dir_use_symlinks=False,
        )
    except Exception:
        return ""
