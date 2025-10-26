import pytest

from installer import model_selector


def test_select_preset_minimal(monkeypatch):
    def fake_detect():
        return {"gpu_name": "RTX", "gpu_vram_gb": 8, "ram_total_gb": 16}

    monkeypatch.setattr(model_selector.system_info, "detect_system", fake_detect)

    specs = {"requires_gpu": True}
    assert model_selector.select_preset("minimal", specs) == "remote"


def test_select_preset_full_hybrid(monkeypatch):
    def fake_detect():
        return {"gpu_name": None, "gpu_vram_gb": None, "ram_total_gb": 16}

    monkeypatch.setattr(model_selector.system_info, "detect_system", fake_detect)

    specs = {"requires_gpu": True}
    assert model_selector.select_preset("full", specs) == "hybrid"


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


def test_gui_preset_integration(monkeypatch, tk_root):
    from installer.gui_installer import GUIInstaller

    gui = GUIInstaller(root=tk_root)
    gui.preset = "full"

    monkeypatch.setattr(
        "installer.gui_installer.system_info.detect_system",
        lambda: {"gpu_name": "RTX", "gpu_vram_gb": 8, "ram_total_gb": 16},
    )

    def fake_select(preset, specs):
        assert preset == "full"
        return "local"

    monkeypatch.setattr(
        "installer.gui_installer.model_selector.select_preset", fake_select
    )

    gui._detect_worker()
    tk_root.update()

    assert gui.backend == "local"
