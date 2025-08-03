import pytest

from security import AuditLogger, PermissionManager


def test_permission_enforcement(tmp_path):
    log_path = tmp_path / "audit.log"
    logger = AuditLogger(log_path)
    manager = PermissionManager(audit_logger=logger)

    manager.grant("PluginA", "network")
    manager.require("PluginA", "network")  # should not raise

    with pytest.raises(PermissionError):
        manager.require("PluginA", "filesystem")

    log = log_path.read_text(encoding="utf-8")
    assert "DENIED" in log and "filesystem" in log
