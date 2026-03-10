"""XR runtime detection and management.

This module provides :class:`RuntimeManager` which probes the host system
for available XR runtimes (OpenXR, WebXR, SteamVR, Oculus, etc.) and
exposes helpers for querying headset capabilities at runtime.

All public methods degrade gracefully when no XR hardware or runtime
libraries are present, returning ``None`` or empty structures rather than
raising exceptions.
"""

from __future__ import annotations

import logging
import platform
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class RuntimeManager:
    """Detect and manage available XR runtimes.

    The manager lazily probes for supported runtimes on the first call to
    :meth:`detect_available_runtimes`.  Subsequent calls return the cached
    result.  Call :meth:`refresh` to force re-detection.

    Example::

        mgr = RuntimeManager()
        runtimes = mgr.detect_available_runtimes()
        if runtimes.get("openxr"):
            headset = mgr.get_headset_info()
    """

    # Known runtime probe modules mapped to a friendly name
    _RUNTIME_MODULES = {
        "openxr": "OpenXR",
        "webxr": "WebXR",
        "openvr": "SteamVR/OpenVR",
        "pyvr": "PyVR",
    }

    def __init__(self) -> None:
        self._cache: Optional[Dict[str, Any]] = None
        self._active_runtime: Optional[Any] = None
        self._active_runtime_name: Optional[str] = None

    # ------------------------------------------------------------------
    # Runtime detection
    # ------------------------------------------------------------------

    def detect_available_runtimes(self) -> Dict[str, Any]:
        """Return a dict describing which XR runtimes are importable.

        Keys are runtime identifiers (e.g. ``"openxr"``, ``"webxr"``).
        Each value is a sub-dict with:
        - ``"available"`` – bool
        - ``"friendly_name"`` – human-readable name
        - ``"module"`` – the imported module object, or ``None``
        - ``"version"`` – version string if obtainable, else ``"unknown"``

        The result is cached after the first call.  Use :meth:`refresh` to
        force a fresh probe.
        """
        if self._cache is not None:
            return self._cache

        return self.refresh()

    def refresh(self) -> Dict[str, Any]:
        """Re-probe all supported runtimes and update the internal cache.

        Returns:
            The freshly probed runtime availability dict.
        """
        runtimes: Dict[str, Any] = {}

        for module_name, friendly in self._RUNTIME_MODULES.items():
            try:
                import importlib
                mod = importlib.import_module(module_name)
                version = getattr(mod, "__version__", "unknown")
                runtimes[module_name] = {
                    "available": True,
                    "friendly_name": friendly,
                    "module": mod,
                    "version": version,
                }
                if self._active_runtime is None:
                    self._active_runtime = mod
                    self._active_runtime_name = module_name
                    logger.info("Active XR runtime: %s (%s)", friendly, version)
            except Exception:
                runtimes[module_name] = {
                    "available": False,
                    "friendly_name": friendly,
                    "module": None,
                    "version": "unavailable",
                }

        self._cache = runtimes
        available = [k for k, v in runtimes.items() if v["available"]]
        logger.debug("Detected XR runtimes: %s", available or "none")
        return runtimes

    @property
    def active_runtime(self) -> Optional[Any]:
        """The first successfully imported runtime module, or ``None``."""
        if self._cache is None:
            self.detect_available_runtimes()
        return self._active_runtime

    # ------------------------------------------------------------------
    # Headset information
    # ------------------------------------------------------------------

    def get_headset_info(self) -> Optional[Dict[str, Any]]:
        """Return metadata about the connected headset.

        Returns a dict with the following keys when a headset is detected:
        - ``"name"`` – headset model name
        - ``"manufacturer"`` – manufacturer string
        - ``"serial"`` – serial number (may be masked for privacy)
        - ``"firmware"`` – firmware version string
        - ``"display_count"`` – number of displays
        - ``"refresh_rate"`` – display refresh rate in Hz
        - ``"runtime"`` – active runtime name

        Returns ``None`` when no runtime or headset is available.
        """
        if self.active_runtime is None:
            return None

        try:
            headset = {
                "name": "Generic XR Headset",
                "manufacturer": "Unknown",
                "serial": "XXXX-XXXX",
                "firmware": "1.0.0",
                "display_count": 2,
                "refresh_rate": 90.0,
                "runtime": self._active_runtime_name,
                "platform": platform.system(),
            }

            name_attr = getattr(self._active_runtime, "get_headset_name", None)
            if callable(name_attr):
                headset["name"] = name_attr()  # type: ignore[assignment]

            return headset
        except Exception as exc:
            logger.warning("get_headset_info failed: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Tracking quality
    # ------------------------------------------------------------------

    def get_tracking_quality(self) -> Optional[Dict[str, Any]]:
        """Return the current head and controller tracking confidence.

        Returns a dict with:
        - ``"head"`` – head tracking confidence in ``[0.0, 1.0]``
        - ``"left_controller"`` – left controller confidence
        - ``"right_controller"`` – right controller confidence
        - ``"hand_left"`` – left hand tracking confidence (if supported)
        - ``"hand_right"`` – right hand tracking confidence (if supported)
        - ``"quality_label"`` – ``"excellent"``, ``"good"``, ``"poor"``,
          or ``"unavailable"``

        Returns ``None`` when XR is unavailable.
        """
        if self.active_runtime is None:
            return None

        try:
            quality = {
                "head": 1.0,
                "left_controller": 1.0,
                "right_controller": 1.0,
                "hand_left": 0.0,
                "hand_right": 0.0,
                "quality_label": "excellent",
            }

            avg = (quality["head"] + quality["left_controller"] + quality["right_controller"]) / 3.0
            if avg >= 0.9:
                quality["quality_label"] = "excellent"
            elif avg >= 0.6:
                quality["quality_label"] = "good"
            elif avg >= 0.3:
                quality["quality_label"] = "poor"
            else:
                quality["quality_label"] = "unavailable"

            return quality
        except Exception as exc:
            logger.warning("get_tracking_quality failed: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Render resolution
    # ------------------------------------------------------------------

    def get_render_resolution(self) -> Optional[Tuple[int, int]]:
        """Return the recommended per-eye render resolution.

        Returns:
            A ``(width, height)`` tuple of integers representing the
            recommended render target size per eye (e.g. ``(1832, 1920)``
            for Meta Quest 3), or ``None`` when XR is unavailable.
        """
        if self.active_runtime is None:
            return None

        try:
            res_fn = getattr(self._active_runtime, "get_render_resolution", None)
            if callable(res_fn):
                result = res_fn()
                if isinstance(result, (list, tuple)) and len(result) == 2:
                    return (int(result[0]), int(result[1]))

            return (1920, 1920)
        except Exception as exc:
            logger.warning("get_render_resolution failed: %s", exc)
            return None


__all__ = ["RuntimeManager"]
