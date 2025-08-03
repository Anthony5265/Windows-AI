from __future__ import annotations

import os
import shutil
from typing import List


def discover_models(path: str, extension: str = ".model") -> List[str]:
    """Return a list of model files in *path* matching *extension*."""

    return [
        os.path.join(path, name)
        for name in os.listdir(path)
        if name.endswith(extension)
    ]


def download_model(src: str, dest: str) -> str:
    """Copy a model file from *src* to *dest* and return destination path."""

    shutil.copyfile(src, dest)
    return dest
