"""Energy usage monitoring with off-peak scheduling."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from threading import Timer
from typing import Callable, Optional

from .tracker import EnergyTracker, PowerInfo
from .scheduler import EcoScheduler


@dataclass
class EcoMonitor:
    """Combine :class:`EnergyTracker` and :class:`EcoScheduler`.

    The monitor keeps a small in-memory history of power readings and
    exposes a convenience wrapper for scheduling callables during off-peak
    hours.
    """

    tracker: EnergyTracker = field(default_factory=EnergyTracker)
    scheduler: EcoScheduler = field(default_factory=EcoScheduler)
    history: list[PowerInfo] = field(default_factory=list, init=False)

    def sample(self) -> PowerInfo:
        """Record and return the current power information."""

        info = self.tracker.current()
        self.history.append(info)
        return info

    def schedule(self, func: Callable[[], None], now: Optional[datetime] = None) -> Timer:
        """Schedule ``func`` for the next off-peak window."""

        return self.scheduler.schedule(func, now=now)
