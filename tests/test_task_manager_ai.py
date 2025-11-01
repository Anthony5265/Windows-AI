from types import SimpleNamespace

import windows_ai.task_manager as task_manager
from windows_ai.task_manager import TaskManagerAI


class DummyModel:
    def generate(self, prompt: str) -> str:
        return f"ANALYSIS:{prompt}"


def test_analyze_processes_records_prompt(monkeypatch):
    def fake_process_iter(attrs=None):
        class FakeProcess:
            def __init__(self, name, cpu, mem):
                self.info = {"name": name}
                self._cpu = cpu
                self._mem = mem

            def cpu_percent(self, interval=None):
                return self._cpu

            def memory_info(self):
                return SimpleNamespace(rss=self._mem)

        yield FakeProcess("proc1", 10.0, 100 * 1024 * 1024)
        yield FakeProcess("proc2", 20.0, 200 * 1024 * 1024)

    fake_psutil = SimpleNamespace(process_iter=fake_process_iter)
    monkeypatch.setattr(task_manager, "psutil", fake_psutil)

    model = DummyModel()
    tm = TaskManagerAI(model)
    # Stub psutil so metrics are deterministic
    monkeypatch.setattr(task_manager, "psutil", fake_psutil)

    result = tm.analyze_processes(["proc1", "proc2"])
    expected = (
        "analyze: proc1 (cpu=10.0%, mem=100.0MB), "
        "proc2 (cpu=20.0%, mem=200.0MB)"
    )
    expected_prompt = "".join(expected)
    assert result == f"ANALYSIS:{expected_prompt}"
    assert tm.get_queries() == [expected_prompt]
