"""Utilities for deferring work to off‑peak hours."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from threading import Timer
from typing import Callable, Iterable, List, Optional, Tuple


@dataclass
class EcoScheduler:
    """Schedule callables for execution during off‑peak hours.

    Off‑peak hours are defined by one or more ``(start_hour, end_hour)``
    windows.  Each window may span midnight (e.g. ``22 → 6``).  The
    :meth:`next_run` method computes the next eligible run time and
    :meth:`schedule` uses :class:`threading.Timer` to execute a callable when a
    window opens.
    """

    windows: List[Tuple[int, int]]

    def __init__(
        self,
        windows: Optional[Iterable[Tuple[int, int]]] = None,
        *,
        start_hour: int = 22,
        end_hour: int = 6,
    ) -> None:
        self.windows = list(windows) if windows is not None else [(start_hour, end_hour)]

    # ------------------------------------------------------------------
    # Backwards compatibility helpers for existing code using the old API
    @property
    def start_hour(self) -> int:
        return self.windows[0][0]

    @start_hour.setter
    def start_hour(self, value: int) -> None:
        _, end = self.windows[0]
        self.windows[0] = (value, end)

    @property
    def end_hour(self) -> int:
        return self.windows[0][1]

    @end_hour.setter
    def end_hour(self, value: int) -> None:
        start, _ = self.windows[0]
        self.windows[0] = (start, value)

    # ------------------------------------------------------------------
    def is_off_peak(self, dt: datetime) -> bool:
        t = dt.time()
        for start_hour, end_hour in self.windows:
            start = time(start_hour, 0)
            end = time(end_hour, 0)
            if start_hour < end_hour:
                if start <= t < end:
                    return True
            else:  # window spans midnight
                if t >= start or t < end:
                    return True
        return False

    def next_run(self, now: Optional[datetime] = None) -> datetime:
        now = now or datetime.now()
        if self.is_off_peak(now):
            return now

        candidates: List[datetime] = []
        for start_hour, _ in self.windows:
            start_time = time(start_hour, 0)
            run_day = now.date()
            if now.time() >= start_time:
                run_day += timedelta(days=1)
            candidates.append(datetime.combine(run_day, start_time))
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
