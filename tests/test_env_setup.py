import types

from installer import env_setup


def test_resolve_conflicts_auto():
    packages, conflicts = env_setup.resolve_conflicts(["pkg==1", "pkg==2"])
    assert conflicts == {"pkg": ["pkg==1", "pkg==2"]}
    assert packages == ["pkg==2"]


def test_setup_all_creates_envs(tmp_path, monkeypatch):
    # ensure no external entry points are discovered
    dummy_eps = types.SimpleNamespace(select=lambda group: [])
    monkeypatch.setattr(env_setup.plugins.registry, "entry_points", lambda: dummy_eps)

    plugin_a = tmp_path / "a.py"
    plugin_a.write_text(
        """
from installer.plugins.registry import PluginRegistry

def register(registry: PluginRegistry):
    registry.add_dependency('demo-one')
"""
    )

    plugin_b = tmp_path / "b.py"
    plugin_b.write_text(
        """
from installer.plugins.registry import PluginRegistry

def register(registry: PluginRegistry):
    registry.add_dependency('demo-two==1')
"""
    )

    created = {}
    installed = {}

    def fake_create_env(name: str):
        path = tmp_path / name
        created[name] = path
        return path

    def fake_install_packages(path, packages):
        installed[path.name] = list(packages)

    monkeypatch.setattr(env_setup.env, "create_env", fake_create_env)
    monkeypatch.setattr(env_setup.env, "install_packages", fake_install_packages)

    env_setup.setup_all(search_path=tmp_path)

    assert set(created) == {"a", "b"}
    assert installed == {"a": ["demo-one"], "b": ["demo-two==1"]}
