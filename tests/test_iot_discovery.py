"""
IoT Device Discovery tests.
Tests DeviceDiscovery and DeviceManager from windows_ai/iot/.
"""

import pytest
from windows_ai.iot.device_manager import DeviceManager, Device
from windows_ai.iot.discovery import DeviceDiscovery, DiscoveredDevice


@pytest.fixture
def device_manager(tmp_path):
    """Create a DeviceManager with isolated tmp storage."""
    return DeviceManager(storage_path=str(tmp_path / "devices.json"))


def test_device_creation():
    """Test Device can be created with required fields."""
    device = Device(device_id="test-001", device_type="sensor")
    assert device.device_id == "test-001"
    assert device.device_type == "sensor"


def test_device_to_dict():
    """Test Device serialization to dictionary."""
    device = Device(device_id="test-001", device_type="sensor", name="Temp Sensor")
    result = device.to_dict()
    assert isinstance(result, dict)
    assert result["device_id"] == "test-001"
    assert result["device_type"] == "sensor"


def test_device_update_status():
    """Test Device status update."""
    device = Device(device_id="test-001", device_type="sensor")
    device.update_status("online")
    assert device.status == "online"


def test_device_manager_creation():
    """Test DeviceManager can be created."""
    dm = DeviceManager()
    assert dm is not None


def test_device_manager_register_device(device_manager):
    """Test registering a device with DeviceManager."""
    result = device_manager.register_device("dev-001", "sensor", name="Temperature Sensor")
    assert result["status"] == "success"
    assert "device" in result


def test_device_manager_get_device(device_manager):
    """Test retrieving a registered device."""
    device_manager.register_device("dev-002", "actuator", name="Light Switch")
    result = device_manager.get_device("dev-002")
    assert result["status"] == "success"
    assert result["device"]["device_id"] == "dev-002"


def test_device_manager_list_devices(device_manager):
    """Test listing all registered devices."""
    device_manager.register_device("dev-003", "sensor")
    device_manager.register_device("dev-004", "actuator")
    result = device_manager.list_devices()
    assert result["status"] == "success"
    assert len(result["devices"]) >= 2


def test_device_manager_unregister_device(device_manager):
    """Test unregistering a device."""
    device_manager.register_device("dev-005", "sensor")
    result = device_manager.unregister_device("dev-005")
    assert result["status"] == "success"
    # Device should no longer be found
    result = device_manager.get_device("dev-005")
    assert result["status"] == "error"


def test_device_manager_update_status(device_manager):
    """Test updating device status."""
    device_manager.register_device("dev-006", "sensor")
    result = device_manager.update_device_status("dev-006", "online")
    assert result["status"] == "success"


def test_device_manager_create_group(device_manager):
    """Test creating a device group."""
    device_manager.register_device("dev-007", "sensor")
    device_manager.register_device("dev-008", "sensor")
    result = device_manager.create_device_group("sensors", ["dev-007", "dev-008"])
    assert result["status"] == "success"


def test_device_manager_get_statistics(device_manager):
    """Test getting device statistics."""
    device_manager.register_device("dev-009", "sensor")
    result = device_manager.get_device_statistics()
    assert isinstance(result, dict)


def test_device_discovery_creation():
    """Test DeviceDiscovery can be created."""
    discovery = DeviceDiscovery()
    assert discovery is not None


def test_discovered_device_creation():
    """Test DiscoveredDevice dataclass."""
    device = DiscoveredDevice(
        device_id="disc-001",
        device_type="sensor",
        name="Test Sensor",
        protocol="mdns",
        ip_address="192.168.1.100",
    )
    assert device.device_id == "disc-001"
    assert device.protocol == "mdns"


def test_discovered_device_to_dict():
    """Test DiscoveredDevice serialization."""
    device = DiscoveredDevice(
        device_id="disc-002",
        device_type="actuator",
        name="Smart Light",
        protocol="ssdp",
    )
    result = device.to_dict()
    assert isinstance(result, dict)
    assert result["device_id"] == "disc-002"


def test_device_discovery_get_statistics():
    """Test DeviceDiscovery statistics."""
    discovery = DeviceDiscovery()
    stats = discovery.get_discovery_statistics()
    assert isinstance(stats, dict)
