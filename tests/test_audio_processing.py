import domains.audio_processing as ap


def test_local_processing():
    audio = {"data": b"123", "duration": 2}
    processed = ap.input_processor(audio)
    assert processed["use_remote"] is False

    plan = ap.task_planner(processed)
    assert plan["steps"][0]["mode"] == "local"

    results = ap.executor(plan)
    assert results["results"][0]["mode"] == "local"

    aggregated = ap.result_aggregator(results)
    assert aggregated["transcript"] == "local transcript"
    assert aggregated["modes"] == ["local"]


def test_remote_processing(monkeypatch):
    audio = {"data": b"123", "duration": 10}
    processed = ap.input_processor(audio)
    assert processed["use_remote"] is True

    plan = ap.task_planner(processed)
    assert plan["steps"][0]["mode"] == "remote"

    monkeypatch.setattr(ap, "_call_remote_api", lambda audio: "remote transcript")
    results = ap.executor(plan)
    assert results["results"][0]["mode"] == "remote"

    aggregated = ap.result_aggregator(results)
    assert aggregated["transcript"] == "remote transcript"
    assert aggregated["modes"] == ["remote"]
