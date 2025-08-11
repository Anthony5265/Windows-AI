import threading
import time
from pathlib import Path

import pytest

try:
    import tkinter as tk
except Exception:  # pragma: no cover - tkinter optional
    tk = None  # type: ignore


@pytest.fixture
def tk_root():
    if tk is None:
        pytest.skip("tkinter not available")
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("tkinter cannot open display")
    root.withdraw()
    yield root
    root.destroy()


def test_cancel_install(monkeypatch, tk_root):
    import installer.gui as gui_module
    from installer.plugins.registry import PluginRegistry

    monkeypatch.setattr(gui_module.tk, "Tk", lambda: tk_root)

    registry = PluginRegistry(dependencies={"a": set(), "b": set()})
    monkeypatch.setattr(gui_module.plugins, "discover_plugins", lambda: registry)
    monkeypatch.setattr(gui_module.system_info, "detect_system", lambda: {})
    monkeypatch.setattr(gui_module.model_selector, "select_backend", lambda *args, **kwargs: "local")
    monkeypatch.setattr(gui_module.models, "compatible_models", lambda info: [])

    calls = []
    wait_event = threading.Event()

    def fake_create_env(name):
        calls.append(name)
        return Path("/tmp")

    def fake_install_packages(path, deps):
        wait_event.wait()

    monkeypatch.setattr(gui_module.env, "create_env", fake_create_env)
    monkeypatch.setattr(gui_module.env, "install_packages", fake_install_packages)

    messages = {}

    def fake_showinfo(title, message):
        messages["title"] = title
        messages["message"] = message

    monkeypatch.setattr(gui_module.messagebox, "showinfo", fake_showinfo)

    gui = gui_module.InstallerGUI()

    assert str(gui.cancel_btn["state"]) == "disabled"
    gui.install_selected()
    tk_root.update()
    assert str(gui.cancel_btn["state"]) == "normal"

    gui.cancel_btn.invoke()
    wait_event.set()
    for _ in range(20):
        tk_root.update()
        time.sleep(0.01)

    assert calls == ["a"]
    assert messages["title"] == "Install"
    assert "Installation cancelled" in messages["message"]
    assert str(gui.install_btn["state"]) == "disabled"
    assert str(gui.api_btn["state"]) == "disabled"
    assert str(gui.ask_btn["state"]) == "disabled"
    assert str(gui.cancel_btn["state"]) == "disabled"
