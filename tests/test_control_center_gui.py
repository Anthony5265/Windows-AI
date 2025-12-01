import builtins
import builtins
import importlib
import sys

import pytest


def test_headless_import(monkeypatch):
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name.startswith("tkinter"):
            raise ImportError
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    sys.modules.pop("tkinter", None)
    sys.modules.pop("tkinter.ttk", None)
    sys.modules.pop("control_center.gui", None)

    gui = importlib.import_module("control_center.gui")
    assert gui.tk is None
    assert gui.ttk is None
    with pytest.raises(RuntimeError):
        gui.ChatGUI()


def test_gui_launches_with_tkinter():
    gui = importlib.import_module("control_center.gui")
    if gui.tk is None:
        pytest.skip("tkinter not available")
    try:
        root = gui.tk.Tk()
    except gui.tk.TclError:
        pytest.skip("tkinter cannot open display")
    root.withdraw()
    try:
        gui.ChatGUI(root=root)
    finally:
        root.destroy()


def test_snapshot_buttons_invoke_snapshot(monkeypatch):
    gui = importlib.import_module("control_center.gui")
    if gui.tk is None:
        pytest.skip("tkinter not available")
    try:
        root = gui.tk.Tk()
    except gui.tk.TclError:
        pytest.skip("tkinter cannot open display")
    root.withdraw()
    called = {"create": 0, "restore": 0}
    monkeypatch.setattr(gui.snapshot, "create_snapshot", lambda: called.__setitem__("create", 1))
    monkeypatch.setattr(gui.snapshot, "restore", lambda: called.__setitem__("restore", 1))
    try:
        app = gui.ChatGUI(root=root)
        app._create_snapshot()
        app._restore_snapshot()
    finally:
        root.destroy()
    assert called == {"create": 1, "restore": 1}
