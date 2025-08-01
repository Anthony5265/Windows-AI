import json

from installer import env


def test_create_env_records_path(tmp_path, monkeypatch):
    # Redirect configuration paths to a temporary directory
    config_dir = tmp_path / "config"
    monkeypatch.setattr(env, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(env, "BASE_DIR", config_dir / "venvs")
    monkeypatch.setattr(env, "ENV_RECORD_FILE", config_dir / "envs.json")
    monkeypatch.setattr(env, "_use_conda", lambda: False)

    env_path = env.create_env("sample-plugin")
    assert env_path.exists()

    data = json.loads(env.ENV_RECORD_FILE.read_text())
    assert data["sample-plugin"] == str(env_path)


def test_discover_plugins_groups_dependencies(tmp_path):
    # Create a temporary plugin
    plugin_file = tmp_path / "my_plugin.py"
    plugin_file.write_text(
        """
def register(registry):
    registry.add_dependency('demo-package')
"""
    )

    from installer import plugins

    registry = plugins.discover_plugins(tmp_path)
    assert registry.dependencies == {"my_plugin": {"demo-package"}}

