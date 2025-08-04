"""Utilities for deferring work to off‑peak hours."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from threading import Timer
from typing import Callable, Optional


@dataclass
class EcoScheduler:
    """Schedule callables for execution during off‑peak hours.

    Off‑peak hours are defined by a start hour and an end hour.  The window can
    span midnight (e.g. 22 → 6).  The :meth:`next_run` method computes the next
    eligible run time and :meth:`schedule` uses :class:`threading.Timer` to
    execute a callable when the window opens.
    """

    start_hour: int = 22
    end_hour: int = 6

    def is_off_peak(self, dt: datetime) -> bool:
        start = time(self.start_hour, 0)
        end = time(self.end_hour, 0)
        if self.start_hour < self.end_hour:
            return start <= dt.time() < end
        return dt.time() >= start or dt.time() < end

    def next_run(self, now: Optional[datetime] = None) -> datetime:
        now = now or datetime.now()
        if self.is_off_peak(now):
            return now
        start_time = time(self.start_hour, 0)
        run_day = now.date()
        if now.time() >= start_time:
            run_day += timedelta(days=1)
        return datetime.combine(run_day, start_time)

    def schedule(self, func: Callable[[], None], now: Optional[datetime] = None) -> Timer:
        """Schedule ``func`` to run at the next off‑peak time."""

        now = now or datetime.now()
        run_at = self.next_run(now)
        delay = (run_at - now).total_seconds()
        timer = Timer(delay, func)
        timer.daemon = True
        timer.start()
        return timer
