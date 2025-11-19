"""
Advanced trace logging with span support for Windows-AI.
"""

from __future__ import annotations

import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
import threading

from plugins.logging.base import JsonLogStore


class TraceLogger:
    """
    Lightweight distributed tracing helper used by the Windows-AI runtime.
    """

    def __init__(self, log_dir: str = "logs/trace", service_name: str = "windows-ai"):
        self.log_dir = Path(log_dir)
        self.service_name = service_name
        self.store = JsonLogStore(self.log_dir / "trace_events.jsonl")
        self._active_spans: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def start_span(
        self,
        name: str,
        trace_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Start a new tracing span."""
        span_id = str(uuid.uuid4())
        parent = self._active_spans.get(parent_id) if parent_id else None
        resolved_trace_id = trace_id or (parent["trace_id"] if parent else str(uuid.uuid4()))
        span_data = {
            "span_id": span_id,
            "trace_id": resolved_trace_id,
            "parent_id": parent_id,
            "name": name,
            "metadata": metadata or {},
            "service": self.service_name,
            "start_time": time.time(),
            "start_perf": time.perf_counter(),
        }
        with self._lock:
            self._active_spans[span_id] = span_data
        self.store.append(
            {
                "type": "span_start",
                **{k: v for k, v in span_data.items() if k != "start_perf"},
            }
        )
        return span_id

    def end_span(
        self,
        span_id: str,
        status: str = "ok",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Complete a span and record duration."""
        with self._lock:
            span = self._active_spans.pop(span_id, None)
        if not span:
            raise KeyError(f"Span {span_id} is not active")

        duration_ms = (time.perf_counter() - span["start_perf"]) * 1000
        record = {
            "type": "span_end",
            "span_id": span_id,
            "trace_id": span["trace_id"],
            "parent_id": span["parent_id"],
            "name": span["name"],
            "service": span["service"],
            "start_time": span["start_time"],
            "duration_ms": round(duration_ms, 3),
            "status": status,
            "metadata": {**span["metadata"], **(metadata or {})},
            "timestamp": time.time(),
        }
        self.store.append(record)
        return record

    def log_event(
        self,
        span_id: Optional[str],
        message: str,
        level: str = "INFO",
        **context: Any,
    ) -> Dict[str, Any]:
        """Associate an event with a span (or trace) and persist it."""
        span = self._active_spans.get(span_id) if span_id else None
        record = {
            "type": "event",
            "span_id": span_id,
            "trace_id": span["trace_id"] if span else context.get("trace_id"),
            "message": message,
            "level": level,
            "service": self.service_name,
            "timestamp": time.time(),
            "context": context,
        }
        self.store.append(record)
        return record

    @contextmanager
    def span(
        self,
        name: str,
        trace_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Iterable[str]:
        """Context manager helper for spans."""
        span_id = self.start_span(name, trace_id=trace_id, parent_id=parent_id, metadata=metadata)
        try:
            yield span_id
            self.end_span(span_id, status="ok")
        except Exception as exc:
            self.end_span(span_id, status="error", metadata={"exception": repr(exc)})
            raise

    def active_spans(self) -> List[Dict[str, Any]]:
        """Return currently active spans."""
        with self._lock:
            return [span.copy() for span in self._active_spans.values()]

    def export_trace(self, trace_id: str) -> List[Dict[str, Any]]:
        """Return all entries for a trace."""
        return [
            record
            for record in self.store.iter_records()
            if record.get("trace_id") == trace_id
        ]
