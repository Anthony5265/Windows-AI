import pytest

from iot import ADAPTERS, discover_devices


def test_discover_devices_returns_devices():
    for proto in ADAPTERS:
        devices = discover_devices(proto)
        assert devices, f"no devices for {proto}"
        for dev in devices:
            assert dev.protocol == proto


def test_discover_invalid_protocol():
    with pytest.raises(KeyError):
        discover_devices("invalid")
