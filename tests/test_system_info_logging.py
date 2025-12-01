import logging

import windows_ai.system_info as sysinfo


def _raise(*args, **kwargs):
    raise RuntimeError("boom")


def test_accessibility_logs(monkeypatch, caplog):
    monkeypatch.setattr(sysinfo.platform, "system", lambda: "TestOS")
    monkeypatch.setattr(sysinfo.subprocess, "check_output", _raise)
    with caplog.at_level(logging.DEBUG, logger=sysinfo.logger.name):
        settings = sysinfo._detect_accessibility()
    assert settings == {"screen_reader": False, "high_contrast": False}
    msgs = [record.message for record in caplog.records]
    assert any("TestOS" in m and "high_contrast" in m for m in msgs)
    assert any("TestOS" in m and "screen_reader" in m for m in msgs)


def test_xr_hardware_logs(monkeypatch, caplog):
    monkeypatch.setattr(sysinfo.platform, "system", lambda: "TestOS")

    def fail_runtime():
        raise RuntimeError("boom")

    monkeypatch.setattr(sysinfo, "load_runtime", fail_runtime)
    with caplog.at_level(logging.DEBUG, logger=sysinfo.logger.name):
        info = sysinfo._detect_xr_hardware()
    assert info == {"xr_capable": False, "xr_runtime": None}
    assert any("TestOS" in r.message and "XR runtime" in r.message for r in caplog.records)
