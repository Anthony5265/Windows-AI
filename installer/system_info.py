"""Utility functions for detecting system information.

This module contains helpers that query the running machine for basic
hardware and software details.  On Windows platforms an effort is made to
also detect the installed GPU and the amount of dedicated video memory.
"""
from __future__ import annotations

import os
import platform
from typing import Any, Dict


def detect_system() -> Dict[str, Any]:
    """Return basic information about the host system.

    The function tries to use ``psutil`` for memory metrics and, on Windows
    hosts, attempts to determine the GPU model and VRAM size.  Optional
    dependencies are handled gracefully so the script can still run on
    minimal installations.
    """

    info: Dict[str, Any] = {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "cpu_count": os.cpu_count(),
        "gpu_model": None,
        "gpu_vram_gb": None,
    }

    try:
        import psutil  # type: ignore

        info["memory_gb"] = round(psutil.virtual_memory().total / (1024 ** 3), 2)
    except Exception:
        info["memory_gb"] = None

    if platform.system() == "Windows":
        # Try querying GPU details using ``wmi``.
        try:  # pragma: no cover - dependency optional and Windows-specific
            import wmi  # type: ignore

            gpu_info = wmi.WMI().Win32_VideoController()
            if gpu_info:
                info["gpu_model"] = gpu_info[0].Name  # type: ignore[attr-defined]
                ram = getattr(gpu_info[0], "AdapterRAM", None)
                if ram:
                    info["gpu_vram_gb"] = round(int(ram) / (1024 ** 3), 2)
        except Exception:
            # Fall back to ``pynvml`` which can also report GPU information on
            # systems with NVIDIA hardware.
            try:  # pragma: no cover - dependency optional
                from pynvml import (
                    nvmlDeviceGetCount,
                    nvmlDeviceGetHandleByIndex,
                    nvmlDeviceGetMemoryInfo,
                    nvmlDeviceGetName,
                    nvmlInit,
                    nvmlShutdown,
                )

                nvmlInit()
                try:
                    if nvmlDeviceGetCount() > 0:
                        handle = nvmlDeviceGetHandleByIndex(0)
                        info["gpu_model"] = (
                            nvmlDeviceGetName(handle).decode("utf-8")
                        )
                        mem = nvmlDeviceGetMemoryInfo(handle)
                        info["gpu_vram_gb"] = round(mem.total / (1024 ** 3), 2)
                finally:
                    nvmlShutdown()
            except Exception:
                pass

    return info
