from types import SimpleNamespace

import windows_ai.task_manager as task_manager
from windows_ai.task_manager import TaskManagerAI


class DummyModel:
    def generate(self, prompt: str) -> str:
        return f"ANALYSIS:{prompt}"


def test_analyze_processes_records_prompt(monkeypatch):
    class FakeProcess:
        def __init__(self, name, cpu, mem):
            self.info = {
                "name": name,
                "cpu_percent": cpu,
                "memory_info": SimpleNamespace(rss=mem),
            }

    def fake_process_iter(attrs=None):
        yield FakeProcess("proc1", 10.0, 100 * 1024 * 1024)
        yield FakeProcess("proc2", 20.0, 200 * 1024 * 1024)

    fake_psutil = SimpleNamespace(process_iter=fake_process_iter)
    monkeypatch.setattr(task_manager, "psutil", fake_psutil)

    model = DummyModel()
    tm = TaskManagerAI(model)

    result = tm.analyze_processes(["proc1", "proc2"])
    expected_prompt = (
        "analyze: proc1 (cpu=10.0%, mem=100.0MB), proc2 (cpu=20.0%, mem=200.0MB)"
    )
    assert result == f"ANALYSIS:{expected_prompt}"
    assert tm.get_queries() == [expected_prompt]
