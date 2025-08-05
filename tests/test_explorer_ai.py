from windows_ai.explorer import ExplorerAI


class DummyModel:
    def generate(self, prompt: str) -> str:
        return f"RESULT:{prompt}"


def test_suggest_cleanup_records_prompt_and_actions(tmp_path):
    model = DummyModel()
    explorer = ExplorerAI(model)

    small = tmp_path / "a.txt"
    small.write_text("hi")
    log_file = tmp_path / "b.log"
    log_file.write_text("log")
    large = tmp_path / "c.bin"
    large.write_bytes(b"0" * (1_000_001))

    result = explorer.suggest_cleanup([str(small), str(log_file), str(large)])

    prompt = (
        f"cleanup: {small} ({small.stat().st_size} bytes, .txt), "
        f"{log_file} ({log_file.stat().st_size} bytes, .log), "
        f"{large} ({large.stat().st_size} bytes, .bin)"
    )

    assert result["suggestion"] == f"RESULT:{prompt}"
    assert explorer.get_logs() == [prompt]
    assert result["actions"] == {
        str(small): "none",
        str(log_file): "delete",
        str(large): "compress",
    }
