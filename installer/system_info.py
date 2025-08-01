"""Utility functions for detecting system information.

This module contains helpers that query the running machine for basic
hardware and software details.  On Windows platforms an effort is made to
also detect the installed GPU, system memory and disk capacity.
"""
from __future__ import annotations

import os
import platform
import shutil
import subprocess
from typing import Any, Dict


def detect_system() -> Dict[str, Any]:
    """Return basic information about the host system.

    The function reports CPU, GPU, memory and disk statistics.  On Windows,
    the :mod:`wmi` module is used when available; other platforms fall back
    to :mod:`psutil` or shell commands.  Optional dependencies are handled
    gracefully so the script can still run on minimal installations.
    """

    info: Dict[str, Any] = {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "cpu_count": os.cpu_count(),
        "gpu_name": None,
        "gpu_vram_gb": None,
        "ram_total_gb": None,
        "ram_free_gb": None,
        "disk_total_gb": None,
        "disk_free_gb": None,
    }

    try:  # pragma: no cover - psutil optional
        import psutil  # type: ignore
    except Exception:  # pragma: no cover - psutil optional
        psutil = None  # type: ignore

    if platform.system() == "Windows":
        try:  # pragma: no cover - dependency optional and Windows-specific
            import wmi  # type: ignore

            c = wmi.WMI()
            try:
                gpu_info = c.Win32_VideoController()
                if gpu_info:
                    info["gpu_name"] = gpu_info[0].Name  # type: ignore[attr-defined]
                    ram = getattr(gpu_info[0], "AdapterRAM", None)
                    if ram:
                        info["gpu_vram_gb"] = round(int(ram) / (1024 ** 3), 2)
            except Exception:
                pass

            try:
                os_info = c.Win32_OperatingSystem()[0]
                total_kb = int(getattr(os_info, "TotalVisibleMemorySize", 0))
                free_kb = int(getattr(os_info, "FreePhysicalMemory", 0))
                info["ram_total_gb"] = round(total_kb / (1024 ** 2), 2)
                info["ram_free_gb"] = round(free_kb / (1024 ** 2), 2)
            except Exception:
                pass

            try:
                disks = c.Win32_LogicalDisk(DriveType=3)
                total = sum(int(d.Size or 0) for d in disks)
                free = sum(int(d.FreeSpace or 0) for d in disks)
                if total:
                    info["disk_total_gb"] = round(total / (1024 ** 3), 2)
                    info["disk_free_gb"] = round(free / (1024 ** 3), 2)
            except Exception:
                pass
        except Exception:
            pass

    if psutil:
        try:
            vm = psutil.virtual_memory()
            info["ram_total_gb"] = info["ram_total_gb"] or round(
                vm.total / (1024 ** 3), 2
            )
            info["ram_free_gb"] = info["ram_free_gb"] or round(
                vm.available / (1024 ** 3), 2
            )
        except Exception:
            pass
        try:
            disk = psutil.disk_usage("/")
            info["disk_total_gb"] = info["disk_total_gb"] or round(
                disk.total / (1024 ** 3), 2
            )
            info["disk_free_gb"] = info["disk_free_gb"] or round(
                disk.free / (1024 ** 3), 2
            )
        except Exception:
            pass

    if not info["gpu_name"]:
        try:  # pragma: no cover - dependency optional
            if shutil.which("nvidia-smi"):
                out = subprocess.check_output(
                    ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                    stderr=subprocess.DEVNULL,
                )
                info["gpu_name"] = out.decode().splitlines()[0].strip()
        except Exception:
            pass
        if not info["gpu_name"] and shutil.which("lspci"):
            try:
                out = subprocess.check_output(["lspci"], stderr=subprocess.DEVNULL)
                for line in out.decode().splitlines():
                    if "vga" in line.lower():
                        info["gpu_name"] = line.split(":")[-1].strip()
                        break
            except Exception:
                pass

    if not info["gpu_name"]:
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
                    info["gpu_name"] = nvmlDeviceGetName(handle).decode("utf-8")
                    mem = nvmlDeviceGetMemoryInfo(handle)
                    info["gpu_vram_gb"] = round(mem.total / (1024 ** 3), 2)
            finally:
                nvmlShutdown()
        except Exception:
            pass

    return info
