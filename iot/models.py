from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class Device:
    """Represents a discoverable IoT device."""

    id: str
    name: str
    protocol: str


class DeviceAdapter:
    """Base class for IoT protocol adapters."""

    protocol: str

    def discover(self) -> List[Device]:
        """Return a list of devices found by the adapter."""
        raise NotImplementedError

    def pair(self, device: Device) -> bool:
        """Pair with *device* and return True on success."""
        return device.protocol == self.protocol
