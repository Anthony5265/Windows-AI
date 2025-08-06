"""Expose system information utilities to tests and consumers.

This module wraps :func:`windows_ai.system_info_core.detect_system` and
augments the result with a best-effort lookup of operating system
accessibility settings. The goal is to expose features like screen reader
usage or high-contrast themes to higher level components so they can adapt
their behaviour accordingly.  The implementation is intentionally forgiving –
failures to query the platform are silently ignored and sensible defaults are
returned instead.
"""

from __future__ import annotations

import ctypes
import logging
import platform
import subprocess
from typing import Any, Dict

from .system_info_core import detect_system as _detect_system


logger = logging.getLogger(__name__)

try:  # optional dependency used for XR runtime detection
    from xr import load_runtime
except Exception:  # pragma: no cover - xr package optional
    def load_runtime():  # type: ignore[misc]
        return None


def _detect_accessibility() -> Dict[str, bool]:
    """Return a dictionary describing basic OS accessibility settings.

    The keys ``screen_reader`` and ``high_contrast`` are provided.  When the
    settings cannot be detected the values default to ``False``.  Only a small
    subset of platforms are supported but the function is written to fail
    silently so it can run in minimal test environments.
    """

    settings: Dict[str, bool] = {
        "screen_reader": False,
        "high_contrast": False,
    }

    system = platform.system()
    if system == "Windows":
        try:  # pragma: no cover - Windows only
            SPI_GETSCREENREADER = 0x0046
            SPI_GETHIGHCONTRAST = 0x0042
            HCF_HIGHCONTRASTON = 0x00000001

            screen_reader = ctypes.c_uint()
            ctypes.windll.user32.SystemParametersInfoW(
                SPI_GETSCREENREADER, 0, ctypes.byref(screen_reader), 0
            )
            settings["screen_reader"] = bool(screen_reader.value)

            class HIGHCONTRAST(ctypes.Structure):
                _fields_ = [
                    ("cbSize", ctypes.c_uint),
                    ("dwFlags", ctypes.c_uint),
                    ("lpszDefaultScheme", ctypes.c_wchar_p),
                ]

            hc = HIGHCONTRAST()
            hc.cbSize = ctypes.sizeof(HIGHCONTRAST)
            ctypes.windll.user32.SystemParametersInfoW(
                SPI_GETHIGHCONTRAST, hc.cbSize, ctypes.byref(hc), 0
            )
            settings["high_contrast"] = bool(hc.dwFlags & HCF_HIGHCONTRASTON)
        except Exception as exc:
            logger.debug(
                "Failed to query accessibility via SystemParametersInfo on %s: %s",
                system,
                exc,
            )
    elif system == "Darwin":
        try:  # pragma: no cover - macOS only
            out = subprocess.check_output(
                [
                    "defaults",
                    "read",
                    "com.apple.universalaccess",
                    "VoiceOverEnabled",
                ]
            )
            settings["screen_reader"] = out.strip() == b"1"
        except Exception as exc:
            logger.debug(
                "Failed to read VoiceOverEnabled on %s: %s",
                system,
                exc,
            )
        try:
            out = subprocess.check_output(
                [
                    "defaults",
                    "read",
                    "com.apple.universalaccess",
                    "increaseContrast",
                ]
            )
            settings["high_contrast"] = out.strip() == b"1"
        except Exception as exc:
            logger.debug(
                "Failed to read increaseContrast on %s: %s",
                system,
                exc,
            )
    else:  # Linux/other
        try:  # pragma: no cover - optional dependencies
            out = subprocess.check_output(
                [
                    "gsettings",
                    "get",
                    "org.gnome.desktop.interface",
                    "high-contrast",
                ],
                stderr=subprocess.DEVNULL,
            )
            settings["high_contrast"] = out.decode().strip().lower() in {
                "true",
                "1",
            }
        except Exception as exc:
            logger.debug(
                "Failed to query high-contrast via gsettings on %s: %s",
                system,
                exc,
            )
        try:
            out = subprocess.check_output(
                [
                    "gsettings",
                    "get",
                    "org.gnome.desktop.a11y.applications",
                    "screen-reader-enabled",
                ],
                stderr=subprocess.DEVNULL,
            )
            settings["screen_reader"] = out.decode().strip().lower() in {
                "true",
                "1",
            }
        except Exception as exc:
            logger.debug(
                "Failed to query screen-reader via gsettings on %s: %s",
                system,
                exc,
            )

    return settings


def _detect_xr_hardware() -> Dict[str, Any]:
    """Return information about XR hardware/driver availability.

    The function performs a best-effort import of either an OpenXR or WebXR
    runtime via :func:`xr.load_runtime`.  When a runtime is available the
    returned dictionary contains ``xr_capable`` set to ``True`` and
    ``xr_runtime`` with the module name.  Missing runtimes are represented as
    ``xr_capable`` being ``False`` and ``xr_runtime`` as ``None``.  All errors
    are swallowed so the detection works in minimal environments without XR
    support.
    """

    info: Dict[str, Any] = {"xr_capable": False, "xr_runtime": None}
    try:
        runtime = load_runtime()
        if runtime:
            info["xr_capable"] = True
            info["xr_runtime"] = getattr(runtime, "__name__", str(runtime))
    except Exception as exc:
        logger.debug(
            "Failed to load XR runtime on %s: %s",
            platform.system(),
            exc,
        )
    return info


def detect_system() -> Dict[str, Any]:
    """Return system information including basic accessibility settings."""

    info: Dict[str, Any] = _detect_system()
    if info.get("gpu_name") is None:
        info["gpu_name"] = "unknown"

    info.update(_detect_accessibility())
    info.update(_detect_xr_hardware())
    return info


__all__ = ["detect_system"]

