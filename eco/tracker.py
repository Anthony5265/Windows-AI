"""Energy usage tracking helpers.

The :class:`EnergyTracker` class uses optional ``psutil`` readings to provide
basic information about the system's power state.  When the dependency is not
available or the platform lacks support the tracker gracefully falls back to
returning ``None`` values.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

try:  # pragma: no cover - psutil optional
    import psutil  # type: ignore
except Exception:  # pragma: no cover - psutil optional
    psutil = None  # type: ignore


@dataclass
class PowerInfo:
    """Simple container for power readings."""

    percent: Optional[float]
    secs_left: Optional[int]
    power_plugged: Optional[bool]


class EnergyTracker:
    """Track energy usage via OS APIs when available."""

    def current(self) -> PowerInfo:
        """Return current power information.

        The data is sourced from :func:`psutil.sensors_battery` when available.
        Missing values are represented by ``None``.
        """

        if not psutil:
            return PowerInfo(None, None, None)
        try:
            batt = psutil.sensors_battery()
        except Exception:
            batt = None
        if not batt:
            return PowerInfo(None, None, None)
        return PowerInfo(batt.percent, batt.secsleft, batt.power_plugged)
