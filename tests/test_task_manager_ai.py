from windows_ai.task_manager import TaskManagerAI


class DummyModel:
    def generate(self, prompt: str) -> str:
        return f"ANALYSIS:{prompt}"


class DummyProcess:
    def __init__(self, name: str, cpu: float, mem: float):
        self.info = {"name": name}
        self._cpu = cpu
        self._mem = mem

    def cpu_percent(self, interval=None) -> float:  # pragma: no cover - simple wrapper
        return self._cpu

    def memory_percent(self) -> float:  # pragma: no cover - simple wrapper
        return self._mem


class DummyPsutil:
    def process_iter(self, attrs):  # pragma: no cover - deterministic
        return [
            DummyProcess("proc1", 1.0, 2.0),
            DummyProcess("proc2", 3.0, 4.0),
        ]


def test_analyze_processes_records_prompt(monkeypatch):
    model = DummyModel()
    tm = TaskManagerAI(model)
    # Stub psutil so metrics are deterministic
    monkeypatch.setattr("windows_ai.task_manager.psutil", DummyPsutil())
    result = tm.analyze_processes(["proc1", "proc2"])
    expected = "analyze: proc1 (cpu=1.0, mem=2.0), proc2 (cpu=3.0, mem=4.0)"
    assert result == f"ANALYSIS:{expected}"
    assert tm.get_queries() == [expected]

