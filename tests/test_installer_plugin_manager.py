import json
import subprocess

import pytest

from installer.plugins.manager import PluginManager


def test_install_failure_triggers_rollback(tmp_path, monkeypatch):
    catalog = tmp_path / "catalog.json"
    catalog.write_text(
        json.dumps(
            {
                "plugins": [
                    {
                        "name": "Good",
                        "description": "",
                        "command": "pip install goodpkg",
                    },
                    {
                        "name": "Bad",
                        "description": "",
                        "command": "pip install badpkg",
                    },
                ]
            }
        )
    )
    state = tmp_path / "state.json"
    manager = PluginManager(catalog_path=catalog, state_path=state)

    calls: list[list[str]] = []

    def fake_run(args, shell=False, check=False, **kwargs):
        calls.append(args)
        if args[-1] == "badpkg":
            raise subprocess.CalledProcessError(1, args)

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(subprocess.CalledProcessError):
        installed = []
        try:
            for plugin in manager.plugins:
                manager.install(plugin)
                installed.append(plugin)
        except Exception:
            manager.rollback(installed)
            raise

    assert calls == [
        ["pip", "install", "goodpkg"],
        ["pip", "install", "badpkg"],
        ["pip", "uninstall", "-y", "goodpkg"],
    ]
    assert json.loads(state.read_text()) == {"installed": []}

