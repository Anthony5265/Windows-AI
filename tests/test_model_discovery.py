import os
from model_discovery.discovery import discover_models, download_model, fetch_llm


def test_discover_models(tmp_path):
    (tmp_path / "a.model").write_text("x")
    (tmp_path / "b.txt").write_text("y")
    models = discover_models(str(tmp_path))
    assert len(models) == 1
    assert models[0].endswith("a.model")


def test_download_model(tmp_path):
    src = tmp_path / "src.model"
    src.write_text("data")
    dest = tmp_path / "sub" / "dest.model"
    download_model(str(src), str(dest))
    assert dest.read_text() == "data"


def test_discover_models_missing_path(tmp_path):
    missing = tmp_path / "missing"
    assert discover_models(str(missing)) == []


def test_download_model_failure(tmp_path):
    src = tmp_path / "missing.model"
    dest = tmp_path / "sub" / "dest.model"
    result = download_model(str(src), str(dest))
    assert result == ""
    assert dest.parent.exists()
    assert not dest.exists()


def test_fetch_llm_url(tmp_path, monkeypatch):
    dest = tmp_path / "model.bin"

    class FakeResponse:
        def __init__(self, content):
            self._content = content

        def iter_content(self, chunk_size=8192):
            yield self._content

        def raise_for_status(self):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

    def fake_get(url, stream=True, timeout=30):
        return FakeResponse(b"data")

    from model_discovery import discovery

    monkeypatch.setattr(discovery.requests, "get", fake_get)

    fetch_llm("https://example.com/model.bin", str(dest))
    assert dest.read_bytes() == b"data"


def test_fetch_llm_huggingface(tmp_path, monkeypatch):
    from model_discovery import discovery

    def fake_snapshot_download(repo_id, local_dir, local_dir_use_symlinks=False):
        os.makedirs(local_dir, exist_ok=True)
        path = os.path.join(local_dir, "weights.bin")
        with open(path, "w") as fh:
            fh.write("x")
        return local_dir

    monkeypatch.setattr(discovery, "snapshot_download", fake_snapshot_download)

    dest = tmp_path / "model"
    result = fetch_llm("dummy/model", str(dest))
    assert result == str(dest)
    assert (dest / "weights.bin").read_text() == "x"
