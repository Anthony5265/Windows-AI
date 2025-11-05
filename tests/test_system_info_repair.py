import windows_ai.system_info as sysinfo


def test_auto_repair_missing_fields(monkeypatch):
    def bad_detect():
        return {"cpu_count": 0}

    monkeypatch.setattr(sysinfo, "_detect_system", bad_detect)
    info = sysinfo.detect_system()
    assert info["cpu_count"] == 1
    assert info["gpu_name"] == "unknown"
    assert info["xr_capable"] is False
    assert "screen_reader" in info and "high_contrast" in info
