from __future__ import annotations

from .models import Device, DeviceAdapter


class HomeAssistantAdapter(DeviceAdapter):
    """Adapter for Home Assistant devices."""

    protocol = "home_assistant"

    def discover(self):
        return [Device(id="ha-1", name="Home Assistant Device", protocol=self.protocol)]
