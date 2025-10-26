import hashlib
import subprocess

from plugins.manager import Plugin, PluginManager


def make_plugin(name: str, *, deps=None):
    deps = deps or []
    return Plugin(
        name=name,
        description="",
        command=f"pip install {name.lower()}",
        dependencies=deps,
        signature=hashlib.sha256(name.encode()).hexdigest(),
    )


def test_uninstall_removes_plugin_and_dependencies(monkeypatch):
    dep = make_plugin("Dep")
    main = make_plugin("Main", deps=["Dep"])
    manager = PluginManager()
    manager.plugins = [dep, main]

    # Install plugins without executing real commands
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: None)
    manager.install(main)
    assert manager._installed == {"Dep", "Main"}

    calls = []

    def fake_run(args, shell, check, cwd, env):
        calls.append(args)

    monkeypatch.setattr(subprocess, "run", fake_run)
    manager.uninstall(main)

    assert calls == [
        ["pip", "uninstall", "dep", "-y"],
        ["pip", "uninstall", "main", "-y"],
    ]
    assert manager._installed == set()


def test_uninstall_keeps_shared_dependency(monkeypatch):
    dep = make_plugin("Dep")
    main1 = make_plugin("Main1", deps=["Dep"])
    main2 = make_plugin("Main2", deps=["Dep"])
    manager = PluginManager()
    manager.plugins = [dep, main1, main2]

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: None)
    manager.install(main1)
    manager.install(main2)
    assert manager._installed == {"Dep", "Main1", "Main2"}

    calls = []

    def fake_run(args, shell, check, cwd, env):
        calls.append(args)

    monkeypatch.setattr(subprocess, "run", fake_run)
    manager.uninstall(main1)

    assert calls == [["pip", "uninstall", "main1", "-y"]]
    assert manager._installed == {"Dep", "Main2"}


def test_uninstall_noop_when_not_installed(monkeypatch):
    """Uninstalling a plugin that isn't installed should do nothing."""

    plugin = make_plugin("Ghost")
    manager = PluginManager()
    manager.plugins = [plugin]

    calls = []

    def fake_run(args, shell, check, cwd, env):
        calls.append(args)

    monkeypatch.setattr(subprocess, "run", fake_run)
    manager.uninstall(plugin)

    assert calls == []
    assert manager._installed == set()
