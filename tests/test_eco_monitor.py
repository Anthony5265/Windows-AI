from datetime import datetime
import time

from eco.monitor import EcoMonitor
from eco.scheduler import EcoScheduler
from eco.tracker import PowerInfo


def test_sample_returns_power_info():
    monitor = EcoMonitor()
    info = monitor.sample()
    assert isinstance(info, PowerInfo)


def test_schedule_uses_scheduler():
    calls: list[int] = []

    def task() -> None:
        calls.append(1)

    sched = EcoScheduler(windows=[(0, 23)])
    monitor = EcoMonitor(scheduler=sched)
    monitor.schedule(task, now=datetime(2024, 1, 1, 1, 0))
    time.sleep(0.1)
    assert calls
