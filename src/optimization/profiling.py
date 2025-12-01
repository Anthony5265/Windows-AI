"""Hardware profiling helpers."""

from __future__ import annotations

from typing import Dict


def profile_hardware() -> Dict[str, str]:
    """Return a simple profile of available hardware.

    This stub demonstrates how hardware profiling might work. In a real
    application this would gather CPU, GPU and other metrics.
    """
    return {
        "cpu": "generic",
        "gpu": "generic",
    }
