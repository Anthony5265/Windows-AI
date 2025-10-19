from datetime import datetime

from eco.scheduler import EcoScheduler


def test_next_run_in_off_peak():
    sched = EcoScheduler(windows=[(22, 6)])
    now = datetime(2024, 1, 1, 23, 0)
    assert sched.is_off_peak(now)
    assert sched.next_run(now) == now


def test_next_run_before_window():
    sched = EcoScheduler(windows=[(22, 6)])
    now = datetime(2024, 1, 1, 20, 0)
    expected = datetime(2024, 1, 1, 22, 0)
    assert sched.next_run(now) == expected


def test_next_run_after_window():
    sched = EcoScheduler(windows=[(22, 6)])
    now = datetime(2024, 1, 1, 7, 0)
    expected = datetime(2024, 1, 1, 22, 0)
    assert sched.next_run(now) == expected


def test_overlapping_windows():
    sched = EcoScheduler(windows=[(1, 5), (4, 8)])
    assert sched.is_off_peak(datetime(2024, 1, 1, 4, 30))
    now = datetime(2024, 1, 1, 0, 0)
    expected = datetime(2024, 1, 1, 1, 0)
    assert sched.next_run(now) == expected


def test_cross_midnight_windows():
    sched = EcoScheduler(windows=[(22, 2), (3, 5)])
    assert sched.is_off_peak(datetime(2024, 1, 1, 23, 30))
    assert sched.is_off_peak(datetime(2024, 1, 2, 4, 0))
    now = datetime(2024, 1, 2, 2, 30)
    expected = datetime(2024, 1, 2, 3, 0)
    assert sched.next_run(now) == expected


def test_cross_midnight_overlapping_windows():
    sched = EcoScheduler(windows=[(23, 2), (0, 4)])
    overlap = datetime(2024, 1, 1, 1, 30)
    assert sched.is_off_peak(overlap)
    assert sched.next_run(overlap) == overlap
    now = datetime(2024, 1, 1, 22, 30)
    expected = datetime(2024, 1, 1, 23, 0)
    assert sched.next_run(now) == expected
