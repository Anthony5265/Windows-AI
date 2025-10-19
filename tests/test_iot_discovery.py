import pytest

from iot import ADAPTERS, Device, discover_devices, pair_device


def _mock_zeroconf(monkeypatch):
    import zeroconf
    import iot.adapters.zeroconf as zc_adapter

    class FakeInfo:
        name = "ZCDevice._http._tcp.local."
        properties = {b"id": b"zc-1"}

    class FakeZeroconf:
        def get_service_info(self, type_, name):
            return FakeInfo()

        def close(self):
            pass

    def fake_service_browser(zc, stype, listener):
        listener.add_service(zc, stype, FakeInfo().name)

    monkeypatch.setattr(zeroconf, "Zeroconf", lambda: FakeZeroconf())
    monkeypatch.setattr(zeroconf, "ServiceBrowser", fake_service_browser)
    monkeypatch.setattr(zc_adapter, "Zeroconf", lambda: FakeZeroconf())
    monkeypatch.setattr(zc_adapter, "ServiceBrowser", fake_service_browser)


def test_discover_devices_returns_devices(monkeypatch):
    _mock_zeroconf(monkeypatch)
    for proto in ADAPTERS:
        devices = discover_devices(proto)
        assert devices, f"no devices for {proto}"
        for dev in devices:
            assert dev.protocol == proto


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
