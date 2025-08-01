import sys
import types
from installer import system_info


def test_detect_system_non_windows(monkeypatch):
    monkeypatch.setattr(system_info.platform, "platform", lambda: "TestOS")
    monkeypatch.setattr(system_info.platform, "python_version", lambda: "3.11.0")
    monkeypatch.setattr(system_info.os, "cpu_count", lambda: 8)
    monkeypatch.setattr(system_info.platform, "system", lambda: "Linux")

    vm = types.SimpleNamespace(total=8 * 1024 ** 3, available=2 * 1024 ** 3)
    disk = types.SimpleNamespace(total=100 * 1024 ** 3, free=20 * 1024 ** 3)
    psutil_mod = types.SimpleNamespace(
        virtual_memory=lambda: vm, disk_usage=lambda _: disk
    )
    monkeypatch.setitem(sys.modules, "psutil", psutil_mod)

    info = system_info.detect_system()
    assert info["platform"] == "TestOS"
    assert info["python_version"] == "3.11.0"
    assert info["cpu_count"] == 8
    assert info["ram_total_gb"] == 8.0
    assert info["ram_free_gb"] == 2.0
    assert info["disk_total_gb"] == 100.0
    assert info["disk_free_gb"] == 20.0
    assert info["gpu_name"] is None
    assert info["gpu_vram_gb"] is None


def test_detect_system_windows_wmi(monkeypatch):
    monkeypatch.setattr(system_info.platform, "platform", lambda: "Windows-10")
    monkeypatch.setattr(system_info.platform, "python_version", lambda: "3.11.0")
    monkeypatch.setattr(system_info.os, "cpu_count", lambda: 4)
    monkeypatch.setattr(system_info.platform, "system", lambda: "Windows")

    vm = types.SimpleNamespace(total=16 * 1024 ** 3, available=8 * 1024 ** 3)
    disk = types.SimpleNamespace(total=500 * 1024 ** 3, free=200 * 1024 ** 3)
    psutil_mod = types.SimpleNamespace(
        virtual_memory=lambda: vm, disk_usage=lambda _: disk
    )
    monkeypatch.setitem(sys.modules, "psutil", psutil_mod)

    class DummyGPU:
        Name = "Test GPU"
        AdapterRAM = 4 * 1024 ** 3

    class DummyOS:
        TotalVisibleMemorySize = 16 * 1024 * 1024
        FreePhysicalMemory = 8 * 1024 * 1024

    class DummyDisk:
        Size = 500 * 1024 ** 3
        FreeSpace = 200 * 1024 ** 3

    class DummyWMI:
        def Win32_VideoController(self):
            return [DummyGPU()]

        def Win32_OperatingSystem(self):
            return [DummyOS()]

        def Win32_LogicalDisk(self, DriveType=3):  # noqa: N802 - case from WMI
            return [DummyDisk()]

    wmi_mod = types.SimpleNamespace(WMI=lambda: DummyWMI())
    monkeypatch.setitem(sys.modules, "wmi", wmi_mod)

    info = system_info.detect_system()
    assert info["gpu_name"] == "Test GPU"
    assert info["gpu_vram_gb"] == 4.0
    assert info["ram_total_gb"] == 16.0
    assert info["ram_free_gb"] == 8.0
    assert info["disk_total_gb"] == 500.0
    assert info["disk_free_gb"] == 200.0
