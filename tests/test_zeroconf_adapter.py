from unittest.mock import MagicMock, patch

from iot.adapters.zeroconf import ZeroconfAdapter


def test_zeroconf_discover_simulated_devices():
    adapter = ZeroconfAdapter()

    fake_info = MagicMock()
    fake_info.name = "TestDevice._http._tcp.local."
    fake_info.properties = {b"id": b"device-1"}

    zc_instance = MagicMock()
    zc_instance.get_service_info.return_value = fake_info

    def fake_browser(zc, service_type, listener):
        listener.add_service(zc, service_type, fake_info.name)
        return MagicMock()

    with patch("iot.adapters.zeroconf.Zeroconf", return_value=zc_instance), \
         patch("iot.adapters.zeroconf.ServiceBrowser", side_effect=fake_browser):
        devices = adapter.discover()

    assert len(devices) == 1
    device = devices[0]
    assert device.id == "device-1"
    assert device.name == "TestDevice"
    assert device.protocol == adapter.protocol
    zc_instance.close.assert_called_once()
    zc_instance.get_service_info.assert_called_with("_http._tcp.local.", fake_info.name)
