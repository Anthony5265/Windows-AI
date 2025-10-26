import logging
import subprocess
import pytest

from installer import env

def test_conda_env_creation_failure_logs_and_raises(tmp_path, monkeypatch, caplog):
    config_dir = tmp_path / "config"
    monkeypatch.setattr(env, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(env, "BASE_DIR", config_dir / "venvs")
    monkeypatch.setattr(env, "ENV_RECORD_FILE", config_dir / "envs.json")
    monkeypatch.setattr(env, "_use_conda", lambda: True)

    def fail(cmd, **kwargs):
        raise subprocess.CalledProcessError(returncode=1, cmd=cmd, stderr="boom")

    monkeypatch.setattr(subprocess, "check_call", fail)

    with caplog.at_level(logging.ERROR):
        with pytest.raises(RuntimeError) as excinfo:
            env.create_env("broken")

    expected_cmd = ["conda", "create", "-y", "-p", str(env.BASE_DIR / "broken"), "python"]
    assert str(expected_cmd) in caplog.text
    assert "boom" in caplog.text
    error_msg = str(excinfo.value)
    assert "Failed to create environment" in error_msg
    assert str(expected_cmd) in error_msg
    assert "boom" in error_msg
