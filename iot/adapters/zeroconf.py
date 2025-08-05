from __future__ import annotations

from typing import List

from ..models import Device, DeviceAdapter


class ZeroconfAdapter(DeviceAdapter):
    """Adapter for Zeroconf/mDNS discovered devices."""

    protocol = "zeroconf"
    service_type = "_http._tcp.local."

    def discover(self) -> List[Device]:
        from zeroconf import Zeroconf, ServiceBrowser

        devices: List[Device] = []
        protocol = self.protocol

        class Listener:
            def add_service(self, zeroconf, type_: str, name: str) -> None:
                info = zeroconf.get_service_info(type_, name)
                if not info:
                    return
                dev_id = info.properties.get(b"id", info.name.encode()).decode()
                dev_name = info.name.split(".")[0]
                devices.append(Device(id=dev_id, name=dev_name, protocol=protocol))

            def update_service(self, zeroconf, type_: str, name: str) -> None:  # pragma: no cover - unused
                pass

            def remove_service(self, zeroconf, type_: str, name: str) -> None:  # pragma: no cover - unused
                pass

        zc = Zeroconf()
        try:
            ServiceBrowser(zc, self.service_type, Listener())
        finally:
            zc.close()
        return devices

    def pair(self, device: Device) -> bool:
        return device.protocol == self.protocol
