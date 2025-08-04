from datetime import datetime

from eco.scheduler import EcoScheduler


def test_next_run_in_off_peak():
    sched = EcoScheduler(start_hour=22, end_hour=6)
    now = datetime(2024, 1, 1, 23, 0)
    assert sched.is_off_peak(now)
    assert sched.next_run(now) == now


def test_next_run_before_window():
    sched = EcoScheduler(start_hour=22, end_hour=6)
    now = datetime(2024, 1, 1, 20, 0)
    expected = datetime(2024, 1, 1, 22, 0)
    assert sched.next_run(now) == expected


def test_next_run_after_window():
    sched = EcoScheduler(start_hour=22, end_hour=6)
    now = datetime(2024, 1, 1, 7, 0)
    expected = datetime(2024, 1, 1, 22, 0)
    assert sched.next_run(now) == expected
