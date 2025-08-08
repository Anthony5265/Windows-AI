import json
import subprocess
from types import SimpleNamespace

from installer import snapshot


def test_snapshot_record_and_restore(tmp_path, monkeypatch):
    # Redirect snapshot location to temporary directory
    monkeypatch.setattr(snapshot, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(snapshot, "SNAPSHOT_FILE", tmp_path / "snapshot.json")
    monkeypatch.setattr(snapshot, "SNAPSHOT_LOG", tmp_path / "snapshot.log")

    # Ensure restore believes required commands exist
    monkeypatch.setattr(snapshot.shutil, "which", lambda cmd: cmd)

    snapshot.create_snapshot()
    assert snapshot.SNAPSHOT_FILE.exists()
    data = json.loads(snapshot.SNAPSHOT_FILE.read_text())
    assert data == {"services": [], "firewall_rules": []}

    snapshot.record_service("svc")
    snapshot.record_firewall_rule("rule")
    data = json.loads(snapshot.SNAPSHOT_FILE.read_text())
    assert data["services"] == ["svc"]
    assert data["firewall_rules"] == ["rule"]

    calls = []

    def fake_run(cmd, check=False):  # noqa: D401 - simple spy
        calls.append(cmd)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    snapshot.restore()
    assert calls[0] == ["nssm", "remove", "svc", "confirm"]
    assert "Remove-NetFirewallRule" in calls[1][-1]
    assert not snapshot.SNAPSHOT_FILE.exists()


def test_restore_warns_when_nssm_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(snapshot, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(snapshot, "SNAPSHOT_FILE", tmp_path / "snapshot.json")
    monkeypatch.setattr(snapshot, "SNAPSHOT_LOG", tmp_path / "snapshot.log")

    snapshot.create_snapshot()
    snapshot.record_service("svc")

    # nssm missing, pwsh present
    monkeypatch.setattr(snapshot.shutil, "which", lambda cmd: None if cmd == "nssm" else cmd)

    calls = []

    def fake_run(cmd, check=False):  # noqa: D401 - simple spy
        calls.append(cmd)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    snapshot.restore()
    assert calls == []
    assert "nssm not found" in snapshot.SNAPSHOT_LOG.read_text()
    assert not snapshot.SNAPSHOT_FILE.exists()


def test_restore_warns_when_pwsh_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(snapshot, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(snapshot, "SNAPSHOT_FILE", tmp_path / "snapshot.json")
    monkeypatch.setattr(snapshot, "SNAPSHOT_LOG", tmp_path / "snapshot.log")

    snapshot.create_snapshot()
    snapshot.record_firewall_rule("rule")

    # pwsh missing, nssm present
    monkeypatch.setattr(snapshot.shutil, "which", lambda cmd: None if cmd == "pwsh" else cmd)

    calls = []

    def fake_run(cmd, check=False):  # noqa: D401 - simple spy
        calls.append(cmd)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    snapshot.restore()
    assert calls == []
    assert "pwsh not found" in snapshot.SNAPSHOT_LOG.read_text()
    assert not snapshot.SNAPSHOT_FILE.exists()
