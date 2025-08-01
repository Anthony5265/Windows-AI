import sys
import types
from installer import system_info


def test_detect_system_non_windows(monkeypatch):
    monkeypatch.setattr(system_info.platform, "platform", lambda: "TestOS")
    monkeypatch.setattr(system_info.platform, "python_version", lambda: "3.11.0")
    monkeypatch.setattr(system_info.os, "cpu_count", lambda: 8)
    monkeypatch.setattr(system_info.platform, "system", lambda: "Linux")

    vm = types.SimpleNamespace(total=8 * 1024 ** 3)
    psutil_mod = types.SimpleNamespace(virtual_memory=lambda: vm)
    monkeypatch.setitem(sys.modules, "psutil", psutil_mod)

    info = system_info.detect_system()
    assert info["platform"] == "TestOS"
    assert info["python_version"] == "3.11.0"
    assert info["cpu_count"] == 8
    assert info["memory_gb"] == 8.0
    assert info["gpu_model"] is None
    assert info["gpu_vram_gb"] is None


def test_detect_system_windows_wmi(monkeypatch):
    monkeypatch.setattr(system_info.platform, "platform", lambda: "Windows-10")
    monkeypatch.setattr(system_info.platform, "python_version", lambda: "3.11.0")
    monkeypatch.setattr(system_info.os, "cpu_count", lambda: 4)
    monkeypatch.setattr(system_info.platform, "system", lambda: "Windows")

    vm = types.SimpleNamespace(total=16 * 1024 ** 3)
    psutil_mod = types.SimpleNamespace(virtual_memory=lambda: vm)
    monkeypatch.setitem(sys.modules, "psutil", psutil_mod)

    class DummyGPU:
        Name = "Test GPU"
        AdapterRAM = 4 * 1024 ** 3

    class DummyWMI:
        def Win32_VideoController(self):
            return [DummyGPU()]

    wmi_mod = types.SimpleNamespace(WMI=lambda: DummyWMI())
    monkeypatch.setitem(sys.modules, "wmi", wmi_mod)

    info = system_info.detect_system()
    assert info["gpu_model"] == "Test GPU"
    assert info["gpu_vram_gb"] == 4.0
