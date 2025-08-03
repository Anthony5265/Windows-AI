import shutil
import subprocess

import pytest

from installer.plugins.manager import Plugin, PluginManager, load_catalog


def test_catalog_loads_default_manifest():
    plugins = load_catalog()
    names = [p.name for p in plugins]
    assert "LangChain" in names
    # ensure at least one paid plugin exists
    assert any(p.paid for p in plugins)


def test_plugin_manager_initializes():
    manager = PluginManager()
    assert manager.plugins  # catalog should not be empty


def test_install_runs_absolute_command(monkeypatch):
    echo_path = shutil.which("echo")
    assert echo_path
    plugin = Plugin(name="Echo", description="", command=f"{echo_path} hello")
    manager = PluginManager()

    recorded: dict[str, object] = {}

    def fake_run(args, shell, check):
        recorded["args"] = args
        recorded["shell"] = shell
        recorded["check"] = check

    monkeypatch.setattr(subprocess, "run", fake_run)
    manager.install(plugin)

    assert recorded["args"] == [echo_path, "hello"]
    assert recorded["shell"] is False
    assert recorded["check"] is True


def test_install_rejects_unsafe_command():
    plugin = Plugin(name="Unsafe", description="", command="echo hello")
    manager = PluginManager()
    with pytest.raises(ValueError):
        manager.install(plugin)
