import pytest

from plugins.manager import Plugin, PluginManager


def test_uninstall_runs_command_and_updates_state(monkeypatch):
    plugin = Plugin(name="Foo", description="", command="pip install Foo")
    manager = PluginManager()
    manager.plugins = [plugin]

    calls = []

    def fake_run(args):
        calls.append(args)

    monkeypatch.setattr(manager, "sandbox_run", fake_run)

    manager.install(plugin)
    assert plugin.name in manager._installed

    manager.uninstall(plugin)
    assert plugin.name not in manager._installed
    assert calls == [["pip", "install", "Foo"], ["pip", "uninstall", "-y", "Foo"]]


def test_uninstall_removes_unused_dependencies(monkeypatch):
    dep = Plugin(name="Dep", description="", command="pip install Dep")
    main = Plugin(name="Main", description="", command="pip install Main", dependencies=["Dep"])
    manager = PluginManager()
    manager.plugins = [dep, main]

    calls = []
    monkeypatch.setattr(manager, "sandbox_run", lambda args: calls.append(args))

    manager.install(main)
    assert manager._installed == {"Dep", "Main"}

    manager.uninstall(main)
    assert manager._installed == set()
    assert calls == [
        ["pip", "install", "Dep"],
        ["pip", "install", "Main"],
        ["pip", "uninstall", "-y", "Main"],
        ["pip", "uninstall", "-y", "Dep"],
    ]


def test_uninstall_retains_shared_dependencies(monkeypatch):
    dep = Plugin(name="Dep", description="", command="pip install Dep")
    one = Plugin(name="One", description="", command="pip install One", dependencies=["Dep"])
    two = Plugin(name="Two", description="", command="pip install Two", dependencies=["Dep"])
    manager = PluginManager()
    manager.plugins = [dep, one, two]

    calls = []
    monkeypatch.setattr(manager, "sandbox_run", lambda args: calls.append(args))

    manager.install(one)
    manager.install(two)
    assert manager._installed == {"Dep", "One", "Two"}

    calls.clear()
    manager.uninstall(one)
    assert manager._installed == {"Dep", "Two"}
    assert calls == [["pip", "uninstall", "-y", "One"]]

    calls.clear()
    manager.uninstall(two)
    assert manager._installed == set()
    assert calls == [
        ["pip", "uninstall", "-y", "Two"],
        ["pip", "uninstall", "-y", "Dep"],
    ]
