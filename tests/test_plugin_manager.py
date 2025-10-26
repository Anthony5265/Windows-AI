import hashlib
import os
import shutil
import subprocess

import pytest

from plugins.manager import SANDBOX_DIR, Plugin, PluginManager, load_catalog


def test_catalog_loads_default_manifest():
    """Catalog should load and include the core plugins."""
    plugins = load_catalog()
    names = [p.name for p in plugins]
    assert {
        "CustomChain",
        "Ollama",
        "sentence-transformers",
        "llama-index",
    }.issubset(names)

    plugin_map = {p.name: p for p in plugins}
    assert plugin_map["Ollama"].command == "npm install -g ollama"
    assert (
        plugin_map["sentence-transformers"].command
        == "pip install sentence-transformers"
    )
    assert plugin_map["llama-index"].command == "pip install llama-index"

    # ensure at least one paid plugin exists
    assert any(p.paid for p in plugins)


def test_plugin_manager_initializes():
    """Plugin manager should initialize with a non-empty catalog."""
    manager = PluginManager()
    assert manager.plugins  # catalog should not be empty


def test_catalog_includes_ml_frameworks():
    """Catalog should include popular ML frameworks."""
    plugins = load_catalog()
    names = [p.name for p in plugins]
    assert "torch" in names
    assert "transformers" in names


def test_install_transformers_installs_torch_first(monkeypatch):
    """Installing transformers should install torch first."""
    manager = PluginManager()
    plugin = manager.get_plugin("transformers")
    assert plugin is not None

    calls: list[list[str]] = []

    def fake_run(args, shell, check, cwd, env):
        calls.append(args)

    monkeypatch.setattr(subprocess, "run", fake_run)
    manager.install(plugin)

    assert calls == [
        ["pip", "install", "torch"],
        ["pip", "install", "transformers"],
    ]


def test_install_runs_absolute_command(monkeypatch):
    """Installation should execute absolute commands safely."""
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
    """Shell usage should be rejected when command is unsafe."""
    plugin = Plugin(name="Unsafe", description="", command="echo hello")
    manager = PluginManager()
    with pytest.raises(ValueError):
        manager.install(plugin)


def test_install_rejects_bad_signature():
    """Installation should fail when signature verification fails."""
    echo_path = shutil.which("echo")
    assert echo_path
    plugin = Plugin(
        name="Signed", description="", command=f"{echo_path} hi", signature="deadbeef"
    )
    manager = PluginManager()
    with pytest.raises(ValueError):
        manager.install(plugin)


def test_dependencies_install_first(monkeypatch):
    """Dependencies must be installed before the main plugin."""
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


@pytest.mark.parametrize(
    "name, package",
    [
        ("Transformers", "transformers"),
        ("Torch", "torch"),
        ("TensorFlow", "tensorflow"),
        ("LangChain", "langchain"),
    ],
)
def test_framework_plugins_install(monkeypatch, name, package):
    """Framework plugins from the catalog should install via pip."""
    manager = PluginManager()
    plugin = manager.get_plugin(name)
    assert plugin is not None

    calls = []

    def fake_run(args, shell, check, cwd, env):
        calls.append(args)

    monkeypatch.setattr(subprocess, "run", fake_run)
    manager.install(plugin)

    assert calls == [["pip", "install", package]]

