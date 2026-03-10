from __future__ import annotations

from typing import List

from .models import Device, DeviceAdapter
from .mqtt import MQTTAdapter


class HomeAssistantAdapter(DeviceAdapter):
    """Adapter for Home Assistant devices.

    Uses the MQTT adapter to query Home Assistant MQTT discovery and maps
    results into Home Assistant protocol devices.
    """

    protocol = "home_assistant"

    def discover(self) -> List[Device]:
        mqtt_adapter = MQTTAdapter()
        mqtt_devices = mqtt_adapter.discover()
        devices: List[Device] = []
        for dev in mqtt_devices:
            devices.append(Device(id=dev.id.replace("mqtt-", "ha-"), name=dev.name, protocol=self.protocol))
        if not devices:
            devices.append(Device(id="ha-1", name="Home Assistant Device", protocol=self.protocol))
        return devices
