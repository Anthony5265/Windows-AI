import pytest

from iot import ADAPTERS, Device, discover_devices, pair_device


def _mock_zeroconf(monkeypatch):
    import iot.adapters.zeroconf as zc

    class FakeZeroconf:
        def close(self):
            pass

    def fake_service_browser(zc_instance, service_type, listener):
        listener.add_service(zc_instance, service_type, "ZCDevice._http._tcp.local.")

    monkeypatch.setattr(zc, "Zeroconf", lambda: FakeZeroconf())
    monkeypatch.setattr(zc, "ServiceBrowser", fake_service_browser)


def test_discover_devices_returns_devices(monkeypatch):
    _mock_zeroconf(monkeypatch)
    devices = discover_devices("zeroconf")
    assert devices, "no devices for zeroconf"
    for dev in devices:
        assert dev.protocol == "zeroconf"


def test_discover_invalid_protocol():
    with pytest.raises(KeyError):
        discover_devices("invalid")


def test_zeroconf_pairing(monkeypatch):
    _mock_zeroconf(monkeypatch)
    devices = discover_devices("zeroconf")
    device = devices[0]
    assert pair_device("zeroconf", device) is True

    wrong = Device(id="x", name="x", protocol="other")
    assert pair_device("zeroconf", wrong) is False
