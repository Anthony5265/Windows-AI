from windows_ai.task_manager import TaskManagerAI


class DummyModel:
    def generate(self, prompt: str) -> str:
        return f"ANALYSIS:{prompt}"


def test_analyze_processes_records_prompt():
    model = DummyModel()
    tm = TaskManagerAI(model)
    result = tm.analyze_processes(["proc1", "proc2"])
    assert result == "ANALYSIS:analyze: proc1, proc2"
    assert tm.get_queries() == ["analyze: proc1, proc2"]
