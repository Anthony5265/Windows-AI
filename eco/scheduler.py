"""Utilities for deferring work to off‑peak hours."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from threading import Timer
from typing import Callable, Optional


@dataclass
class EcoScheduler:
    """Schedule callables for execution during off‑peak hours.

    Off‑peak hours are defined by one or more ``(start_hour, end_hour)``
    windows.  Each window can span midnight (e.g. ``22 → 6``).  The
    :meth:`next_run` method computes the next eligible run time and
    :meth:`schedule` uses :class:`threading.Timer` to execute a callable when
    a window opens.
    """

    windows: list[tuple[int, int]] = field(default_factory=lambda: [(22, 6)])

    def is_off_peak(self, dt: datetime) -> bool:
        for start_hour, end_hour in self.windows:
            start = time(start_hour, 0)
            end = time(end_hour, 0)
            if start_hour < end_hour:
                if start <= dt.time() < end:
                    return True
            else:
                if dt.time() >= start or dt.time() < end:
                    return True
        return False

    def next_run(self, now: Optional[datetime] = None) -> datetime:
        now = now or datetime.now()
        if self.is_off_peak(now):
            return now
        candidates = []
        for start_hour, _ in self.windows:
            start_time = time(start_hour, 0)
            run_day = now.date()
            if now.time() < start_time:
                candidates.append(datetime.combine(run_day, start_time))
            else:
                candidates.append(
                    datetime.combine(run_day + timedelta(days=1), start_time)
                )
        return min(candidates)

    def schedule(self, func: Callable[[], None], now: Optional[datetime] = None) -> Timer:
        """Schedule ``func`` to run at the next off‑peak time."""

        now = now or datetime.now()
        run_at = self.next_run(now)
        delay = (run_at - now).total_seconds()
        timer = Timer(delay, func)
        timer.daemon = True
        timer.start()
        return timer
