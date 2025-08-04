import pytest
from updater import Updater


def test_rollback_restores_snapshot(tmp_path, monkeypatch):
    install_dir = tmp_path / "install"
    install_dir.mkdir()
    marker = install_dir / "data.txt"
    marker.write_text("v1")

    updater = Updater(base_url="https://example.com", install_dir=install_dir)

    def fail_install(self, package):
        raise RuntimeError("install failed")

    def dummy_uninstall(self):
        pass

    monkeypatch.setattr(Updater, "run_install", fail_install)
    monkeypatch.setattr(Updater, "run_uninstall", dummy_uninstall)

    with pytest.raises(RuntimeError):
        updater.apply_update(tmp_path / "pkg.zip")

    assert marker.read_text() == "v1"
