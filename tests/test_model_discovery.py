from model_discovery.discovery import discover_models, download_model


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
    dest = tmp_path / "dest.model"
    result = download_model(str(src), str(dest))
    assert result == ""
    assert not dest.exists()
