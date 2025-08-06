import importlib
import json


def test_catalog_path_env_override(tmp_path, monkeypatch):
    catalog = tmp_path / "catalog.json"
    catalog.write_text(
        json.dumps({"plugins": [{"name": "Alt", "description": "", "command": "echo hi"}]})
    )

    monkeypatch.setenv("WINDOWS_AI_PLUGIN_CATALOG", str(catalog))

    from installer.plugins import manager as manager_module

    importlib.reload(manager_module)

    plugins = manager_module.load_catalog()
    assert [p.name for p in plugins] == ["Alt"]
