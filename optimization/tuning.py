"""Hardware tuning utilities."""

from __future__ import annotations

import logging
from typing import Dict

logger = logging.getLogger(__name__)

PROFILES: Dict[str, Dict[str, str]] = {
    "balanced": {"cpu": "medium", "gpu": "medium"},
    "performance": {"cpu": "high", "gpu": "high"},
    "eco": {"cpu": "low", "gpu": "low"},
}


class Tuner:
    """Apply and revert hardware tuning profiles."""

    def __init__(self) -> None:
        self.current_settings: Dict[str, str] = PROFILES["balanced"].copy()
        self.previous_settings: Dict[str, str] | None = None

    def apply(self, profile: str) -> Dict[str, str]:
        """Apply a profile and store previous settings."""
        if profile not in PROFILES:
            raise ValueError(f"Unknown profile: {profile}")
        logger.info("Applying %s profile", profile)
        self.previous_settings = self.current_settings.copy()
        self.current_settings = PROFILES[profile].copy()
        return self.current_settings

    def revert(self) -> Dict[str, str]:
        """Revert to the previously applied profile."""
        if self.previous_settings is not None:
            logger.info("Reverting to previous profile")
            self.current_settings, self.previous_settings = (
                self.previous_settings,
                None,
            )
        return self.current_settings


tuner = Tuner()


def apply(profile: str) -> Dict[str, str]:
    """Apply a tuning profile using the default tuner."""
    return tuner.apply(profile)


def revert() -> Dict[str, str]:
    """Revert to the previous tuning profile using the default tuner."""
    return tuner.revert()
