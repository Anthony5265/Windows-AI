import hashlib
import os
import shutil
import subprocess

import pytest

from plugins.manager import SANDBOX_DIR, Plugin, PluginManager, load_catalog


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

    def fake_run(args, shell, check, cwd, env):
        recorded["args"] = args
        recorded["shell"] = shell
        recorded["check"] = check
        recorded["cwd"] = cwd
        recorded["env"] = env

    monkeypatch.setattr(subprocess, "run", fake_run)
    manager.install(plugin)

    assert recorded["args"] == [echo_path, "hello"]
    assert recorded["shell"] is False
    assert recorded["check"] is True
    assert recorded["cwd"] == str(SANDBOX_DIR)
    assert recorded["env"] == {"PATH": os.environ.get("PATH", "")}


def test_install_rejects_unsafe_command():
    plugin = Plugin(name="Unsafe", description="", command="echo hello")
    manager = PluginManager()
    with pytest.raises(ValueError):
        manager.install(plugin)


def test_install_rejects_bad_signature():
    echo_path = shutil.which("echo")
    assert echo_path
    plugin = Plugin(
        name="Signed", description="", command=f"{echo_path} hi", signature="deadbeef"
    )
    manager = PluginManager()
    with pytest.raises(ValueError):
        manager.install(plugin)


def test_dependencies_install_first(monkeypatch):
    echo_path = shutil.which("echo")
    assert echo_path
    dep = Plugin(
        name="Dep",
        description="",
        command=f"{echo_path} dep",
        signature=hashlib.sha256("Dep".encode()).hexdigest(),
    )
    main = Plugin(
        name="Main",
        description="",
        command=f"{echo_path} main",
        dependencies=["Dep"],
        signature=hashlib.sha256("Main".encode()).hexdigest(),
    )
    manager = PluginManager()
    manager.plugins = [dep, main]

    calls: list[list[str]] = []

    def fake_run(args, shell, check, cwd, env):
        calls.append(args)

    monkeypatch.setattr(subprocess, "run", fake_run)
    manager.install(main)

    assert calls == [[echo_path, "dep"], [echo_path, "main"]]

