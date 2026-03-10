"""
Windows AI Optimization Module
Performance optimization, profiling, and hardware tuning.
"""
from __future__ import annotations

import os
import sys

# Add repo root to path so top-level optimization package is importable
_repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

try:
    from optimization.profiling import profile_hardware
    from optimization.tuning import Tuner, apply, revert, PROFILES
except ImportError:

    def profile_hardware() -> dict:
        """Return hardware profile (fallback when optimization package not available)."""
        return {"status": "unavailable", "error": "optimization module not found"}

    class Tuner:  # type: ignore[no-redef]
        """Stub Tuner when optimization package is unavailable."""

        def __init__(self, profile: str = "balanced") -> None:
            self.profile = profile

        def apply(self) -> None:
            pass

        def revert(self) -> None:
            pass

    def apply(profile: str = "balanced") -> None:
        pass

    def revert() -> None:
        pass

    PROFILES = ["balanced", "performance", "eco"]

__all__ = ["profile_hardware", "Tuner", "apply", "revert", "PROFILES"]
