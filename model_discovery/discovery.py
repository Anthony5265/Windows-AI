from __future__ import annotations

import os
import shutil
from typing import List


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
