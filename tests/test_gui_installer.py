import pytest


try:
    import tkinter as tk
    from tkinter import ttk
except Exception:  # pragma: no cover - tkinter optional
    tk = None  # type: ignore
    ttk = None  # type: ignore


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

    def fake_select(preset, specs):
        calls["specs"] = specs
        calls["preset"] = preset
        return "local"

    monkeypatch.setattr(
        "installer.gui_installer.model_selector.select_preset", fake_select
    )

    gui._detect_worker()
    tk_root.update()

    assert gui.backend == "local"
    assert calls["specs"] == gui.model_specs
    assert calls["preset"] == gui.preset
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
        "installer.gui_installer.model_selector.select_preset", fail_select
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

    def fake_select(preset, specs):
        assert specs["min_ram_gb"] == 32
        assert preset == gui.preset
        return "remote"

    monkeypatch.setattr(
        "installer.gui_installer.model_selector.select_preset", fake_select
    )

    gui._detect_worker()
    tk_root.update()

    assert gui.backend == "remote"
    text = gui.info.get("1.0", tk.END)
    assert "Recommended backend: remote" in text


def test_parse_float_valid(monkeypatch, tk_root):
    from installer.gui_installer import GUIInstaller

    called = {}
    monkeypatch.setattr(
        "installer.gui_installer.messagebox.showerror", lambda *a, **k: called.setdefault("called", True)
    )

    assert GUIInstaller._parse_float("3.5", "Min VRAM") == 3.5
    assert "called" not in called


def test_parse_float_invalid(monkeypatch, tk_root):
    from installer.gui_installer import GUIInstaller

    called = {}
    monkeypatch.setattr(
        "installer.gui_installer.messagebox.showerror", lambda *a, **k: called.setdefault("called", True)
    )

    with pytest.raises(ValueError):
        GUIInstaller._parse_float("not-a-number", "Min RAM")
    assert called.get("called") is True


def _open_config(gui, tk_root):
    gui.open_config()
    tk_root.update()
    top = next(c for c in tk_root.winfo_children() if isinstance(c, tk.Toplevel))
    specs_frame = next(
        c
        for c in top.winfo_children()
        if any(isinstance(g, ttk.Entry) for g in c.winfo_children())
    )
    entries = [w for w in specs_frame.winfo_children() if isinstance(w, ttk.Entry)]
    vram_entry, ram_entry = entries
    apply_button = next(
        c for c in top.winfo_children() if isinstance(c, ttk.Button)
    )
    return top, vram_entry, ram_entry, apply_button


def test_apply_config_valid(monkeypatch, tk_root):
    from installer.gui_installer import GUIInstaller

    gui = GUIInstaller(root=tk_root)
    top, vram_entry, ram_entry, apply_button = _open_config(gui, tk_root)

    vram_entry.delete(0, tk.END)
    vram_entry.insert(0, "6")
    ram_entry.delete(0, tk.END)
    ram_entry.insert(0, "12")

    called = {}
    monkeypatch.setattr(
        "installer.gui_installer.messagebox.showerror",
        lambda *a, **k: called.setdefault("called", True),
    )

    apply_button.invoke()
    tk_root.update()

    assert "called" not in called
    assert gui.model_specs["min_vram_gb"] == 6.0
    assert gui.model_specs["min_ram_gb"] == 12.0
    assert top.winfo_exists() == 0


def test_apply_config_invalid(monkeypatch, tk_root):
    from installer.gui_installer import GUIInstaller

    gui = GUIInstaller(root=tk_root)
    top, vram_entry, _, apply_button = _open_config(gui, tk_root)

    vram_entry.delete(0, tk.END)
    vram_entry.insert(0, "bad")

    called = {}
    monkeypatch.setattr(
        "installer.gui_installer.messagebox.showerror",
        lambda *a, **k: called.setdefault("called", True),
    )

    apply_button.invoke()
    tk_root.update()

    assert called.get("called") is True
    assert gui.model_specs["min_vram_gb"] == 4.0
    assert gui.backend is None
    assert top.winfo_exists() == 1
    top.destroy()
