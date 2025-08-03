from __future__ import annotations

from .models import Device, DeviceAdapter


class MQTTAdapter(DeviceAdapter):
    """Adapter for MQTT devices."""

    protocol = "mqtt"

    def discover(self):
        return [Device(id="mqtt-1", name="MQTT Sensor", protocol=self.protocol)]
