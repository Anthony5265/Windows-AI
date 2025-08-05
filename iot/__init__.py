from __future__ import annotations

from typing import Dict, List

from .models import Device, DeviceAdapter
from .mqtt import MQTTAdapter
from .matter import MatterAdapter
from .zigbee import ZigbeeAdapter
from .home_assistant import HomeAssistantAdapter
from .adapters import ZeroconfAdapter
from .automation import WorkflowAutomation

ADAPTERS: Dict[str, DeviceAdapter] = {
    "mqtt": MQTTAdapter(),
    "matter": MatterAdapter(),
    "zigbee": ZigbeeAdapter(),
    "home_assistant": HomeAssistantAdapter(),
    "zeroconf": ZeroconfAdapter(),
}


def discover_devices(protocol: str) -> List[Device]:
    """Discover devices for *protocol* using the corresponding adapter."""
    adapter = ADAPTERS[protocol]
    return adapter.discover()


def pair_device(protocol: str, device: Device) -> bool:
    """Pair *device* using the protocol's adapter."""
    adapter = ADAPTERS[protocol]
    return adapter.pair(device)


__all__ = [
    "Device",
    "DeviceAdapter",
    "MQTTAdapter",
    "MatterAdapter",
    "ZigbeeAdapter",
    "HomeAssistantAdapter",
    "ZeroconfAdapter",
    "discover_devices",
    "pair_device",
    "WorkflowAutomation",
    "ADAPTERS",
]
