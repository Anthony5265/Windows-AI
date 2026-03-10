"""Hardware profiling helpers.

This module provides :func:`profile_hardware` which gathers CPU, memory,
disk, and GPU information using only the Python standard library.  Optional
third-party packages (``psutil``, ``GPUtil``) are used when present but are
never required.
"""

from __future__ import annotations

import logging
import os
import platform
import sys
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional dependency probes
# ---------------------------------------------------------------------------

try:
    import psutil as _psutil  # type: ignore
    _HAS_PSUTIL = True
except Exception:
    _psutil = None  # type: ignore[assignment]
    _HAS_PSUTIL = False

try:
    import GPUtil as _gputil  # type: ignore
    _HAS_GPUTIL = True
except Exception:
    _gputil = None  # type: ignore[assignment]
    _HAS_GPUTIL = False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def profile_hardware() -> Dict[str, Any]:
    """Return a profile of the available hardware.

    The returned dictionary contains the following top-level keys:

    - ``"cpu"``   – CPU information (model, cores, frequency, load)
    - ``"memory"`` – RAM information (total, available, percent used)
    - ``"disk"``  – Primary disk information (total, free, percent used)
    - ``"gpu"``   – List of GPU descriptors (name, vram, load, temperature)
    - ``"os"``    – Operating-system information
    - ``"python"`` – Python runtime details

    All values degrade gracefully: if a piece of information cannot be
    gathered the corresponding field is set to a safe default string or
    numeric value rather than raising an exception.

    Example::

        from optimization.profiling import profile_hardware

        info = profile_hardware()
        print(info["cpu"]["model"])
        print(info["memory"]["total_gb"])
    """
    return {
        "cpu": _profile_cpu(),
        "memory": _profile_memory(),
        "disk": _profile_disk(),
        "gpu": _profile_gpu(),
        "os": _profile_os(),
        "python": _profile_python(),
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _profile_cpu() -> Dict[str, Any]:
    """Gather CPU metadata."""
    info: Dict[str, Any] = {
        "model": "unknown",
        "physical_cores": 1,
        "logical_cores": 1,
        "frequency_mhz": 0.0,
        "load_percent": 0.0,
        "architecture": platform.machine() or "unknown",
    }

    try:
        import multiprocessing
        info["logical_cores"] = multiprocessing.cpu_count()
    except Exception:
        pass

    if _HAS_PSUTIL:
        try:
            info["physical_cores"] = _psutil.cpu_count(logical=False) or 1
            info["logical_cores"] = _psutil.cpu_count(logical=True) or 1
            freq = _psutil.cpu_freq()
            if freq:
                info["frequency_mhz"] = round(freq.current, 1)
            info["load_percent"] = _psutil.cpu_percent(interval=0.1)
        except Exception as exc:
            logger.debug("psutil CPU probe failed: %s", exc)

    # Model name via platform on Windows/Linux
    try:
        if platform.system() == "Windows":
            import subprocess
            out = subprocess.check_output(
                ["wmic", "cpu", "get", "name"],
                stderr=subprocess.DEVNULL,
                timeout=5,
            ).decode(errors="replace")
            lines = [l.strip() for l in out.splitlines() if l.strip() and l.strip() != "Name"]
            if lines:
                info["model"] = lines[0]
        elif platform.system() == "Linux":
            with open("/proc/cpuinfo", encoding="utf-8") as fh:
                for line in fh:
                    if line.startswith("model name"):
                        info["model"] = line.split(":", 1)[1].strip()
                        break
        elif platform.system() == "Darwin":
            import subprocess
            out = subprocess.check_output(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                stderr=subprocess.DEVNULL,
                timeout=5,
            ).decode(errors="replace").strip()
            if out:
                info["model"] = out
    except Exception as exc:
        logger.debug("CPU model probe failed: %s", exc)

    return info


def _profile_memory() -> Dict[str, Any]:
    """Gather RAM metadata."""
    info: Dict[str, Any] = {
        "total_gb": 0.0,
        "available_gb": 0.0,
        "used_gb": 0.0,
        "percent_used": 0.0,
    }

    if _HAS_PSUTIL:
        try:
            vm = _psutil.virtual_memory()
            gb = 1024 ** 3
            info["total_gb"] = round(vm.total / gb, 2)
            info["available_gb"] = round(vm.available / gb, 2)
            info["used_gb"] = round(vm.used / gb, 2)
            info["percent_used"] = vm.percent
        except Exception as exc:
            logger.debug("psutil memory probe failed: %s", exc)
    else:
        # Fallback: /proc/meminfo on Linux
        try:
            with open("/proc/meminfo", encoding="utf-8") as fh:
                lines = {
                    l.split(":")[0]: int(l.split(":")[1].strip().split()[0])
                    for l in fh
                    if ":" in l
                }
            total_kb = lines.get("MemTotal", 0)
            avail_kb = lines.get("MemAvailable", 0)
            gb = 1024 ** 2
            info["total_gb"] = round(total_kb / gb, 2)
            info["available_gb"] = round(avail_kb / gb, 2)
            info["used_gb"] = round((total_kb - avail_kb) / gb, 2)
            if total_kb:
                info["percent_used"] = round(100.0 * (total_kb - avail_kb) / total_kb, 1)
        except Exception as exc:
            logger.debug("/proc/meminfo probe failed: %s", exc)

    return info


def _profile_disk(path: str = "/") -> Dict[str, Any]:
    """Gather disk usage metadata for *path*."""
    info: Dict[str, Any] = {
        "path": path,
        "total_gb": 0.0,
        "free_gb": 0.0,
        "used_gb": 0.0,
        "percent_used": 0.0,
    }

    # Use platform root on Windows
    if platform.system() == "Windows":
        path = os.path.splitdrive(sys.executable)[0] + "\\"

    try:
        usage = os.statvfs(path) if hasattr(os, "statvfs") else None
        if usage:
            gb = 1024 ** 3
            total = usage.f_frsize * usage.f_blocks
            free = usage.f_frsize * usage.f_bavail
            used = total - free
            info["total_gb"] = round(total / gb, 2)
            info["free_gb"] = round(free / gb, 2)
            info["used_gb"] = round(used / gb, 2)
            if total:
                info["percent_used"] = round(100.0 * used / total, 1)
    except Exception as exc:
        logger.debug("os.statvfs disk probe failed: %s", exc)

    if _HAS_PSUTIL:
        try:
            du = _psutil.disk_usage(path)
            gb = 1024 ** 3
            info["total_gb"] = round(du.total / gb, 2)
            info["free_gb"] = round(du.free / gb, 2)
            info["used_gb"] = round(du.used / gb, 2)
            info["percent_used"] = du.percent
        except Exception as exc:
            logger.debug("psutil disk probe failed: %s", exc)

    return info


def _profile_gpu() -> List[Dict[str, Any]]:
    """Gather GPU metadata.  Returns a list (one entry per GPU)."""
    gpus: List[Dict[str, Any]] = []

    if _HAS_GPUTIL:
        try:
            for g in _gputil.getGPUs():
                gpus.append({
                    "name": g.name,
                    "vram_total_mb": round(g.memoryTotal, 1),
                    "vram_used_mb": round(g.memoryUsed, 1),
                    "load_percent": round(g.load * 100, 1),
                    "temperature_c": g.temperature,
                    "driver": g.driver,
                })
        except Exception as exc:
            logger.debug("GPUtil probe failed: %s", exc)

    if not gpus:
        # Minimal GPU detection via wmic / nvidia-smi / sysfs
        gpus.extend(_probe_gpu_fallback())

    if not gpus:
        gpus.append({
            "name": "generic",
            "vram_total_mb": 0,
            "vram_used_mb": 0,
            "load_percent": 0.0,
            "temperature_c": 0,
            "driver": "unknown",
        })

    return gpus


def _probe_gpu_fallback() -> List[Dict[str, Any]]:
    """Attempt to detect GPUs using platform CLI tools."""
    gpus: List[Dict[str, Any]] = []
    try:
        import subprocess

        if platform.system() == "Windows":
            out = subprocess.check_output(
                ["wmic", "path", "win32_VideoController", "get", "name"],
                stderr=subprocess.DEVNULL,
                timeout=5,
            ).decode(errors="replace")
            for line in out.splitlines():
                line = line.strip()
                if line and line != "Name":
                    gpus.append({
                        "name": line,
                        "vram_total_mb": 0,
                        "vram_used_mb": 0,
                        "load_percent": 0.0,
                        "temperature_c": 0,
                        "driver": "unknown",
                    })
        else:
            out = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=name,memory.total,memory.used,utilization.gpu,temperature.gpu,driver_version",
                 "--format=csv,noheader,nounits"],
                stderr=subprocess.DEVNULL,
                timeout=5,
            ).decode(errors="replace")
            for line in out.splitlines():
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 6:
                    gpus.append({
                        "name": parts[0],
                        "vram_total_mb": _try_float(parts[1]),
                        "vram_used_mb": _try_float(parts[2]),
                        "load_percent": _try_float(parts[3]),
                        "temperature_c": _try_float(parts[4]),
                        "driver": parts[5],
                    })
    except Exception:
        pass
    return gpus


def _profile_os() -> Dict[str, Any]:
    """Gather operating-system metadata."""
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor() or "unknown",
        "hostname": platform.node() or "unknown",
    }


def _profile_python() -> Dict[str, Any]:
    """Gather Python runtime metadata."""
    return {
        "version": platform.python_version(),
        "implementation": platform.python_implementation(),
        "executable": sys.executable,
        "64bit": sys.maxsize > 2 ** 32,
    }


def _try_float(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

