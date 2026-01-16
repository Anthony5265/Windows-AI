import pytest

from iot import Device, pair_device
from iot.mqtt import MQTTAdapter


def test_mqtt_discover_fallback(monkeypatch):
    # Force adapter to skip broker connection for deterministic test
    monkeypatch.setattr(MQTTAdapter, "_try_connect", lambda self: False)
    adapter = MQTTAdapter()
    devices = adapter.discover()
    assert devices, "no devices discovered"
    assert any(d.protocol == "mqtt" for d in devices)


def test_mqtt_pairing_protocol_match(monkeypatch):
    adapter = MQTTAdapter()
    device = Device(id="mqtt-1", name="Sensor", protocol="mqtt")
    assert adapter.pair(device) is True
    wrong = Device(id="x", name="x", protocol="other")
    assert adapter.pair(wrong) is False
