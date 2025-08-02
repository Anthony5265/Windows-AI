from installer import model_selector


def test_select_backend_local(monkeypatch):
    def fake_detect():
        return {"gpu_name": "RTX", "gpu_vram_gb": 8, "ram_total_gb": 16}

    monkeypatch.setattr(model_selector.system_info, "detect_system", fake_detect)

    specs = {"requires_gpu": True, "min_vram_gb": 4, "min_ram_gb": 8}
    assert model_selector.select_backend("text", specs) == "local"


def test_select_backend_remote_no_gpu(monkeypatch):
    def fake_detect():
        return {"gpu_name": None, "gpu_vram_gb": None, "ram_total_gb": 16}

    monkeypatch.setattr(model_selector.system_info, "detect_system", fake_detect)

    specs = {"requires_gpu": True}
    assert model_selector.select_backend("text", specs) == "remote"


def test_select_backend_remote_low_ram(monkeypatch):
    def fake_detect():
        return {"gpu_name": "RTX", "gpu_vram_gb": 8, "ram_total_gb": 4}

    monkeypatch.setattr(model_selector.system_info, "detect_system", fake_detect)

    specs = {"min_ram_gb": 8}
    assert model_selector.select_backend("text", specs) == "remote"
