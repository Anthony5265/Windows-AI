from __future__ import annotations

from .models import Device, DeviceAdapter


class ZigbeeAdapter(DeviceAdapter):
    """Adapter for Zigbee devices."""

    protocol = "zigbee"

    def discover(self):
        return [Device(id="zigbee-1", name="Zigbee Plug", protocol=self.protocol)]
