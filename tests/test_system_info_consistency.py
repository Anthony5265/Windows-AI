from installer import system_info as installer_info
from windows_ai import system_info as windows_info
from windows_ai import system_info_core as core_info


def test_detect_system_consistency(monkeypatch):
    sample = {
        "platform": "dummy",
        "python_version": "0",
        "cpu_count": 1,
        "gpu_name": "gpu",
        "gpu_vram_gb": 0.0,
        "ram_total_gb": 0.0,
        "ram_free_gb": 0.0,
        "disk_total_gb": 0.0,
        "disk_free_gb": 0.0,
    }

    # Ensure all modules use the same core implementation
    monkeypatch.setattr(core_info, "detect_system", lambda: sample.copy())
    monkeypatch.setattr(installer_info, "detect_system", core_info.detect_system)
    monkeypatch.setattr(windows_info, "_detect_system", core_info.detect_system)

    installer_result = installer_info.detect_system()
    core_result = core_info.detect_system()
    windows_result = windows_info.detect_system()

    assert installer_result == sample
    assert core_result == sample
    for key, value in sample.items():
        assert windows_result[key] == value
