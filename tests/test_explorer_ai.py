import json
from windows_ai.explorer import ExplorerAI


class DummyModel:
    def generate(self, prompt: str) -> str:
        data = json.loads(prompt)
        recommendations = []
        for info in data["files"]:
            if info["extension"] == ".tmp":
                action = "delete"
            elif info["size"] > 1024:
                action = "compress"
            else:
                action = "keep"
            # The dummy model only returns the action; the ExplorerAI combines
            # this with metadata when producing the final summary.
            recommendations.append({"name": info["name"], "action": action})
        return json.dumps(recommendations)


def test_suggest_cleanup_records_prompt(tmp_path):
    model = DummyModel()
    explorer = ExplorerAI(model)

    tmp_file = tmp_path / "old.tmp"
    tmp_file.write_text("old")

    big_file = tmp_path / "big.log"
    big_file.write_bytes(b"x" * 2048)

    result = explorer.suggest_cleanup([str(tmp_file), str(big_file)])
    assert result == [
        {
            "name": str(tmp_file),
            "size": tmp_file.stat().st_size,
            "extension": ".tmp",
            "action": "delete",
        },
        {
            "name": str(big_file),
            "size": big_file.stat().st_size,
            "extension": ".log",
            "action": "compress",
        },
    ]
    assert result["summary"] == {"delete": 1, "compress": 1}

    logs = explorer.get_logs()
    assert len(logs) == 1
    prompt = json.loads(logs[0])
    assert prompt == {
        "files": [
            {
                "name": str(tmp_file),
                "size": tmp_file.stat().st_size,
                "extension": ".tmp",
            },
            {
                "name": str(big_file),
                "size": big_file.stat().st_size,
                "extension": ".log",
            },
        ]
    }


def test_suggest_cleanup_missing_file(tmp_path):
    model = DummyModel()
    explorer = ExplorerAI(model)

    existing = tmp_path / "keep.txt"
    existing.write_text("keep")

    missing = tmp_path / "missing.tmp"  # not created

    result = explorer.suggest_cleanup([str(existing), str(missing)])
    assert result == [{"name": str(existing), "action": "keep"}]

    logs = explorer.get_logs()
    assert len(logs) == 1
    prompt = json.loads(logs[0])
    assert prompt == {
        "files": [
            {
                "name": str(existing),
                "size": existing.stat().st_size,
                "extension": ".txt",
            }
        ]
    }
