from windows_ai.system_info import detect_system


def test_detect_system_non_windows():
    info = detect_system()
    assert info["cpu_count"] > 0
    # CI runners expose a virtual GPU string; just ensure field present
    assert "gpu_name" in info and info["gpu_name"] is not None
    assert "screen_reader" in info and "high_contrast" in info
    assert "xr_capable" in info and "xr_runtime" in info


def test_detect_system_with_mocked_xr(monkeypatch):
    import types
    import windows_ai.system_info as sysinfo

    dummy = types.SimpleNamespace(__name__="openxr")
    monkeypatch.setattr(sysinfo, "load_runtime", lambda: dummy)
    info = sysinfo.detect_system()
    assert info["xr_capable"] is True
    assert info["xr_runtime"] == "openxr"

