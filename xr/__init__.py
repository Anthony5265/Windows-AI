"""Utilities for working with XR runtimes.

This package provides a very small abstraction over potential XR
runtimes.  It attempts to import Python bindings for OpenXR or WebXR and
returns whichever is available.  The imports are intentionally wrapped in
try/except blocks so the package can be imported on systems that do not
have XR hardware or libraries installed.
"""

from __future__ import annotations

from typing import Any, Optional


def load_spatial_ui() -> Optional["spatial_ui.GestureVoiceController"]:
    """Return a gesture/voice controller when XR hardware is available.

    The function attempts to load an XR runtime using :func:`load_runtime`.
    When a runtime is present the :mod:`xr.spatial_ui` module is imported and
    a :class:`~xr.spatial_ui.GestureVoiceController` instance is returned. If
    no compatible runtime is detected ``None`` is returned so callers can
    fall back to traditional input methods.
    """

    runtime = load_runtime()
    if runtime is None:
        return None
    from .spatial_ui import GestureVoiceController

    return GestureVoiceController(runtime)


def load_runtime() -> Optional[Any]:
    """Return an OpenXR or WebXR module if one is available.

    The function first tries to import :mod:`openxr` and falls back to
    :mod:`webxr`.  When neither library can be imported ``None`` is
    returned.  Consumers can check the return value to determine if XR
    features should be enabled.
    """

    try:  # pragma: no cover - optional dependency
        import openxr  # type: ignore
        return openxr
    except Exception:
        try:  # pragma: no cover - optional dependency
            import webxr  # type: ignore
            return webxr
        except Exception:
            return None


__all__ = ["load_runtime", "load_spatial_ui"]
