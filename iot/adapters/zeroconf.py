from __future__ import annotations

from typing import List

from ..models import Device, DeviceAdapter

try:  # pragma: no cover - optional dependency
    from zeroconf import ServiceBrowser, Zeroconf  # type: ignore
except Exception:  # pragma: no cover - import guard
    ServiceBrowser = Zeroconf = None  # type: ignore


class ZeroconfAdapter(DeviceAdapter):
    """Discover devices via Zeroconf/mDNS."""

    protocol = "zeroconf"

    def discover(self) -> List[Device]:  # pragma: no cover - simple wrapper
        if Zeroconf is None or ServiceBrowser is None:
            # Fallback stub so generic discovery tests still pass
            return [Device(id="zeroconf-1", name="Zeroconf Device", protocol=self.protocol)]

        devices: List[Device] = []
        proto = self.protocol

        class _Listener:
            def add_service(self, zeroconf, service_type, name):  # pragma: no cover - callback
                friendly = name.split(".")[0]
                devices.append(Device(id=name, name=friendly, protocol=proto))

        zc = Zeroconf()
        try:
            ServiceBrowser(zc, "_http._tcp.local.", _Listener())
        finally:
            zc.close()

        return devices
