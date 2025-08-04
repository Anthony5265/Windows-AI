from windows_ai.system_info import detect_system

def test_detect_system_non_windows():
    info = detect_system()
    assert info["cpu_count"] > 0
    # CI runners expose a virtual GPU string; just ensure field present
    assert "gpu_name" in info and info["gpu_name"] is not None
    assert "screen_reader" in info and "high_contrast" in info
