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


def test_auto_model_selection(monkeypatch, tk_root):
    from installer.gui_installer import GUIInstaller

    gui = GUIInstaller(root=tk_root)

    monkeypatch.setattr(
        "installer.gui_installer.system_info.detect_system",
        lambda: {"ram_total_gb": 16},
    )

    calls = {}

    def fake_select(task, specs):
        calls["specs"] = specs
        return "local"

    monkeypatch.setattr(
        "installer.gui_installer.model_selector.select_backend", fake_select
    )

    gui._detect_worker()
    tk_root.update()

    assert gui.backend == "local"
    assert calls["specs"] == gui.model_specs
    text = gui.info.get("1.0", tk.END)
    assert "Recommended backend: local" in text


def test_manual_mode(monkeypatch, tk_root):
    from installer.gui_installer import GUIInstaller

    gui = GUIInstaller(root=tk_root)
    gui.auto_select = False
    gui.backend = "remote"

    monkeypatch.setattr(
        "installer.gui_installer.system_info.detect_system",
        lambda: {"ram_total_gb": 16},
    )

    def fail_select(*args, **kwargs):
        raise AssertionError("auto selection should not run")

    monkeypatch.setattr(
        "installer.gui_installer.model_selector.select_backend", fail_select
    )

    gui._detect_worker()
    tk_root.update()

    assert gui.backend == "remote"
    text = gui.info.get("1.0", tk.END)
    assert "Manual backend: remote" in text


def test_advanced_configuration(monkeypatch, tk_root):
    from installer.gui_installer import GUIInstaller

    gui = GUIInstaller(root=tk_root)
    gui.model_specs["min_ram_gb"] = 32

    monkeypatch.setattr(
        "installer.gui_installer.system_info.detect_system",
        lambda: {"ram_total_gb": 16},
    )

    def fake_select(task, specs):
        assert specs["min_ram_gb"] == 32
        return "remote"

    monkeypatch.setattr(
        "installer.gui_installer.model_selector.select_backend", fake_select
    )

    gui._detect_worker()
    tk_root.update()

    assert gui.backend == "remote"
    text = gui.info.get("1.0", tk.END)
    assert "Recommended backend: remote" in text
