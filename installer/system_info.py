"""Utility functions for detecting system information."""
from __future__ import annotations

import os
import platform
from typing import Dict, Any


def detect_system() -> Dict[str, Any]:
    """Return basic information about the host system.

    The function tries to use ``psutil`` for memory metrics, but the
    dependency is optional so the script can still run on minimal
    installations.
    """
    info: Dict[str, Any] = {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "cpu_count": os.cpu_count(),
    }
    try:
        import psutil  # type: ignore

        info["memory_gb"] = round(psutil.virtual_memory().total / (1024 ** 3), 2)
    except Exception:
        info["memory_gb"] = None
    return info
