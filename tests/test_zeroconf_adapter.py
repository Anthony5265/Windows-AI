from unittest.mock import MagicMock, patch

from iot import Device, pair_device
from iot.adapters.zeroconf import ZeroconfAdapter


def test_zeroconf_discover_simulated_devices():
    adapter = ZeroconfAdapter()

    def fake_browser(zc, service_type, listener):
        listener.add_service(zc, service_type, "TestDevice._http._tcp.local.")
        return MagicMock()

    zc_instance = MagicMock()
    with patch("iot.adapters.zeroconf.Zeroconf", return_value=zc_instance), \
         patch("iot.adapters.zeroconf.ServiceBrowser", side_effect=fake_browser):
        devices = adapter.discover()

    assert len(devices) == 1
    device = devices[0]
    assert device.id == "TestDevice._http._tcp.local."
    assert device.name == "TestDevice"
    assert device.protocol == adapter.protocol
    assert pair_device("zeroconf", device) is True
    wrong = Device(id="x", name="x", protocol="other")
    assert pair_device("zeroconf", wrong) is False
    zc_instance.close.assert_called_once()
