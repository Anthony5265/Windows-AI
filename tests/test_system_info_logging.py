import logging

import pytest

import windows_ai.system_info as sysinfo


def test_accessibility_logs_failure(monkeypatch, caplog):
    monkeypatch.setattr(sysinfo.platform, "system", lambda: "Linux")

    def fake_check_output(cmd, stderr=None):
        if "high-contrast" in cmd:
            raise RuntimeError("fail")
        return b"false"

    monkeypatch.setattr(sysinfo.subprocess, "check_output", fake_check_output)

    with caplog.at_level(logging.DEBUG, logger="windows_ai.system_info"):
        sysinfo._detect_accessibility()

    assert any(
        "Linux" in record.getMessage() and "high-contrast" in record.getMessage()
        for record in caplog.records
    )


def test_xr_runtime_logs_failure(monkeypatch, caplog):
    monkeypatch.setattr(sysinfo.platform, "system", lambda: "Linux")

    def fake_load_runtime():
        raise RuntimeError("no runtime")

    monkeypatch.setattr(sysinfo, "load_runtime", fake_load_runtime)

    with caplog.at_level(logging.DEBUG, logger="windows_ai.system_info"):
        sysinfo._detect_xr_hardware()

    assert any(
        "Linux" in record.getMessage() and "XR runtime" in record.getMessage()
        for record in caplog.records
    )
