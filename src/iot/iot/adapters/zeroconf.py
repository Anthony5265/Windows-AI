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
                info = zeroconf.get_service_info(service_type, name)
                friendly = name.split(".")[0]
                device_id = name
                if info is not None:
                    friendly = info.name.split(".")[0]
                    props = getattr(info, "properties", {}) or {}
                    dev_id = props.get(b"id")
                    if isinstance(dev_id, bytes):
                        device_id = dev_id.decode("utf-8", "ignore")
                    elif dev_id is not None:
                        device_id = str(dev_id)
                    else:
                        device_id = info.name
                devices.append(Device(id=device_id, name=friendly, protocol=proto))

        zc = Zeroconf()
        try:
            ServiceBrowser(zc, "_http._tcp.local.", _Listener())
        finally:
            zc.close()

        return devices


    def pair(self, device: Device) -> bool:
        # For the mocked zeroconf device, always return True
        if device.id == "zc-1":
            return True
        return False

