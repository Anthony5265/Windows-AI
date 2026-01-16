from __future__ import annotations

from typing import Dict, List

from .models import Device, DeviceAdapter
from .mqtt import MQTTAdapter
from .matter import MatterAdapter
from .zigbee import ZigbeeAdapter
from .home_assistant import HomeAssistantAdapter
from .adapters.zeroconf import ZeroconfAdapter
from .automation import WorkflowAutomation


# Registry of protocol adapters.  Adapters can be added at runtime via
# :func:`register_adapter`, allowing external packages to provide their own
# implementations.
ADAPTERS: Dict[str, DeviceAdapter] = {}


def register_adapter(protocol: str, adapter: DeviceAdapter) -> None:
    """Register an *adapter* for *protocol*.

    Existing adapters with the same protocol will be replaced, enabling a simple
    plug-in style architecture for new IoT protocols.
    """

    ADAPTERS[protocol] = adapter


# Register built-in adapters
register_adapter("mqtt", MQTTAdapter())
register_adapter("matter", MatterAdapter())
register_adapter("zigbee", ZigbeeAdapter())
register_adapter("home_assistant", HomeAssistantAdapter())
register_adapter("zeroconf", ZeroconfAdapter())


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
    "register_adapter",
    "discover_devices",
    "pair_device",
    "WorkflowAutomation",
    "ADAPTERS",
]
