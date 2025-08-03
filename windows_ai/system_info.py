"""Expose system information utilities to tests and consumers."""

from installer.system_info import detect_system as _detect_system


def detect_system():
    """Return system information ensuring GPU name field is populated."""

    info = _detect_system()
    if info.get("gpu_name") is None:
        info["gpu_name"] = "unknown"
    return info
