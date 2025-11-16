import json
from types import SimpleNamespace

import pytest

from plugins.logging.access_logger.access_logger import AccessLogger
from plugins.logging.change_logger.change_logger import ChangeLogger
from plugins.logging.performance_logger.performance_logger import PerformanceLogger
from plugins.logging.security_logger.security_logger import SecurityLogger
from plugins.logging.trace_logger.trace_logger import TraceLogger


def _read_jsonl(path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def test_trace_logger_records_spans_and_errors(tmp_path):
    tracer = TraceLogger(log_dir=tmp_path / "trace")

    with tracer.span("unit-test") as span_id:
        tracer.log_event(span_id, "step-one", level="DEBUG", stage="start")

    with pytest.raises(RuntimeError):
        with tracer.span("failure"):
            raise RuntimeError("boom")

    records = tracer.store.read_all()
    types = [entry["type"] for entry in records]
    assert "span_start" in types and "span_end" in types
    assert any(entry.get("status") == "error" for entry in records if entry["type"] == "span_end")


def test_security_logger_detects_tampering(tmp_path):
    logger = SecurityLogger(log_dir=tmp_path / "sec")
    logger.log_event("token_issued", actor="svc", target="user")
    logger.flag_alert("intrusion", "critical", "ids", "endpoint-1", "suspicious activity")
    assert logger.verify_chain()

    log_file = tmp_path / "sec" / "security_events.jsonl"
    with log_file.open("a", encoding="utf-8") as handle:
        handle.write('{"event_type":"tampered","chain_hash":"00"}\n')

    assert not logger.verify_chain()


class _DummyProcess:
    def __init__(self):
        self._cpu = 0.0
        self._rss = 1024

    def cpu_times(self):
        self._cpu += 0.05
        return SimpleNamespace(user=self._cpu, system=0.05)

    def memory_info(self):
        self._rss += 64
        return SimpleNamespace(rss=self._rss)


def test_performance_logger_tracks_metrics(tmp_path):
    perf = PerformanceLogger(log_dir=tmp_path / "perf", process=_DummyProcess())
    with perf.track_operation("load_models", threshold_ms=0.01):
        pass

    metrics_file = tmp_path / "perf" / "performance_metrics.jsonl"
    entries = _read_jsonl(metrics_file)
    assert any(entry["type"] == "metric" and entry["name"] == "load_models" for entry in entries)
    summary = perf.summary("load_models")
    assert summary and summary["count"] == 1


def test_access_logger_flags_bruteforce(tmp_path):
    logger = AccessLogger(log_dir=tmp_path / "access", deny_threshold=2, window_seconds=60)
    first = logger.log_access("demo", "settings", "update", "denied")
    second = logger.log_access("demo", "settings", "update", "denied")
    assert first.get("alert") is None
    assert second.get("alert") == "possible_bruteforce"
    report = logger.report()
    assert report["deny"] == 2 and report["total"] == 2


def test_change_logger_emits_diffs(tmp_path):
    logger = ChangeLogger(log_dir=tmp_path / "changes")
    record = logger.log_change(
        component="watchdog",
        item="interval",
        actor="ops",
        previous_value={"interval": 30, "enabled": True},
        new_value={"interval": 15, "enabled": True},
    )
    assert record["diff"]["type"] == "dict"
    assert "interval" in record["diff"]["changed"]

    record_text = logger.log_change(
        component="wizard",
        item="banner",
        actor="designer",
        previous_value="Hello",
        new_value="Hello World",
    )
    assert record_text["diff"]["type"] == "text"
    history = logger.history(component="wizard")
    assert len(history) == 1
