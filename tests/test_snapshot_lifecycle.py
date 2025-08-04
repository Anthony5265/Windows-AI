import json
import subprocess

from installer import snapshot


def test_snapshot_record_and_restore(tmp_path, monkeypatch):
    # Redirect snapshot location to temporary directory
    monkeypatch.setattr(snapshot, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(snapshot, "SNAPSHOT_FILE", tmp_path / "snapshot.json")

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

    monkeypatch.setattr(subprocess, "run", fake_run)
    snapshot.restore()
    assert calls[0] == ["nssm", "remove", "svc", "confirm"]
    assert "Remove-NetFirewallRule" in calls[1][-1]
    assert not snapshot.SNAPSHOT_FILE.exists()
