from windows_ai.explorer import ExplorerAI


class DummyModel:
    def generate(self, prompt: str) -> str:
        return f"RESULT:{prompt}"


def test_suggest_cleanup_records_prompt():
    model = DummyModel()
    explorer = ExplorerAI(model)
    result = explorer.suggest_cleanup(["a.txt", "b.txt"])
    assert result == "RESULT:cleanup: a.txt, b.txt"
    assert explorer.get_logs() == ["cleanup: a.txt, b.txt"]
