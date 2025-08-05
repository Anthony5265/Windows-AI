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
    sched = EcoScheduler(windows=[(1, 4), (3, 5)])
    inside_overlap = datetime(2024, 1, 1, 3, 30)
    assert sched.is_off_peak(inside_overlap)
    after = datetime(2024, 1, 1, 5, 30)
    expected = datetime(2024, 1, 2, 1, 0)
    assert sched.next_run(after) == expected


def test_cross_midnight_windows():
    sched = EcoScheduler(windows=[(22, 4), (6, 8)])
    between_windows = datetime(2024, 1, 1, 5, 0)
    expected = datetime(2024, 1, 1, 6, 0)
    assert not sched.is_off_peak(between_windows)
    assert sched.next_run(between_windows) == expected
    in_first_window = datetime(2024, 1, 1, 23, 0)
    assert sched.is_off_peak(in_first_window)
