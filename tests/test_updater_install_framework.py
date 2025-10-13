from pathlib import Path
import subprocess
import sys

from updater import Updater


def test_install_framework_downloads_models(tmp_path, monkeypatch):
    up = Updater(base_url="https://example.com", install_dir=tmp_path)

    run_calls: list[tuple[list[str], dict]] = []

    def fake_run(cmd, check, env):  # type: ignore[override]
        run_calls.append((cmd, env))

    monkeypatch.setattr(subprocess, "run", fake_run)

    downloads: list[tuple[str, Path]] = []

    def fake_download(self, url, dest, progress=None, checksum=None):  # type: ignore[override]
        downloads.append((url, Path(dest)))
        Path(dest).write_bytes(b"data")
        return Path(dest)

    monkeypatch.setattr(Updater, "download", fake_download)

    model_url = "https://example.com/model.bin"
    up.install_framework("pkg", "1.0", model_urls=[model_url])

    assert run_calls, "pip was not invoked"
    cmd, env = run_calls[0]
    assert cmd == [sys.executable, "-m", "pip", "install", "pkg==1.0"]
    assert env["PIP_DISABLE_PIP_VERSION_CHECK"] == "1"
    assert env["PYTHONPATH"] == ""

    models_dir = tmp_path / "models"
    assert downloads == [(model_url, models_dir / "model.bin")]

