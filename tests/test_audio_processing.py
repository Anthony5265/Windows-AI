"""Tests for the audio processing utilities."""

import domains.audio_processing as ap
import pytest


@pytest.mark.parametrize(
    "duration, expected_mode, transcript",
    [
        (2, "local", "local transcript"),
        (10, "remote", "remote transcript"),
    ],
)
def test_processing_path(duration, expected_mode, transcript, monkeypatch):
    """Verify that audio is routed locally or remotely based on duration."""

    audio = {"data": b"123", "duration": duration}
    if expected_mode == "remote":
        monkeypatch.setattr(ap, "_call_remote_api", lambda audio: transcript)

    processed = ap.input_processor(audio)
    assert processed["use_remote"] is (expected_mode == "remote")

    plan = ap.task_planner(processed)
    assert plan["steps"][0]["mode"] == expected_mode

    results = ap.executor(plan)
    assert results["results"][0]["mode"] == expected_mode

    aggregated = ap.result_aggregator(results)
    assert aggregated["transcript"] == transcript
    assert aggregated["modes"] == [expected_mode]

