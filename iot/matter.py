from __future__ import annotations

from .models import Device, DeviceAdapter


class MatterAdapter(DeviceAdapter):
    """Adapter for Matter devices."""

    protocol = "matter"

    def discover(self):
        return [Device(id="matter-1", name="Matter Light", protocol=self.protocol)]
