"""
Distributed Tracing for Windows AI
OpenTelemetry-compatible tracing with span propagation
"""
from __future__ import annotations

import logging
import time
import uuid
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SpanContext:
    """Context for trace propagation across services."""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    baggage: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "baggage": self.baggage,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SpanContext":
        return cls(
            trace_id=data["trace_id"],
            span_id=data["span_id"],
            parent_span_id=data.get("parent_span_id"),
            baggage=data.get("baggage", {}),
        )


@dataclass
class SpanEvent:
    """An event recorded within a span."""
    name: str
    timestamp: float
    attributes: Dict[str, Any] = field(default_factory=dict)


class Span:
    """A single unit of work within a trace."""

    def __init__(
        self,
        name: str,
        context: SpanContext,
        kind: str = "internal",
        attributes: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.context = context
        self.kind = kind  # internal, server, client, producer, consumer
        self.attributes: Dict[str, Any] = attributes or {}
        self.events: List[SpanEvent] = []
        self.status: str = "ok"
        self.status_message: str = ""
        self.start_time: float = time.time()
        self.end_time: Optional[float] = None
        self._children: List[Span] = []

    def set_attribute(self, key: str, value: Any) -> "Span":
        """Set a span attribute."""
        self.attributes[key] = value
        return self

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> "Span":
        """Record an event within this span."""
        self.events.append(SpanEvent(
            name=name,
            timestamp=time.time(),
            attributes=attributes or {},
        ))
        return self

    def set_status(self, status: str, message: str = "") -> "Span":
        """Set span status (ok, error)."""
        self.status = status
        self.status_message = message
        return self

    def end(self) -> None:
        """End this span."""
        self.end_time = time.time()

    @property
    def duration_ms(self) -> float:
        """Duration in milliseconds."""
        end = self.end_time or time.time()
        return (end - self.start_time) * 1000

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "context": self.context.to_dict(),
            "kind": self.kind,
            "attributes": self.attributes,
            "events": [{"name": e.name, "timestamp": e.timestamp, "attributes": e.attributes} for e in self.events],
            "status": self.status,
            "status_message": self.status_message,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
        }


class Tracer:
    """Distributed tracer that manages spans across the application.

    Usage::

        tracer = Tracer(service_name="windows-ai-api")

        with tracer.start_span("process_request") as span:
            span.set_attribute("user_id", "abc")
            result = do_work()
            span.add_event("work_done")
    """

    def __init__(self, service_name: str = "windows-ai", max_spans: int = 10000):
        self.service_name = service_name
        self.max_spans = max_spans
        self._spans: List[Span] = []
        self._exporters: List[Callable[[Span], None]] = []
        self._lock = threading.Lock()
        self._active_span: threading.local = threading.local()

    @contextmanager
    def start_span(
        self,
        name: str,
        kind: str = "internal",
        attributes: Optional[Dict[str, Any]] = None,
        parent: Optional[Span] = None,
    ):
        """Start a new span as a context manager."""
        # Determine parent
        if parent is None:
            parent = getattr(self._active_span, "current", None)

        # Build context
        trace_id = parent.context.trace_id if parent else uuid.uuid4().hex
        span_id = uuid.uuid4().hex[:16]
        parent_span_id = parent.context.span_id if parent else None

        ctx = SpanContext(trace_id=trace_id, span_id=span_id, parent_span_id=parent_span_id)
        span = Span(name=name, context=ctx, kind=kind, attributes=attributes)
        span.set_attribute("service.name", self.service_name)

        # Set as active
        previous = getattr(self._active_span, "current", None)
        self._active_span.current = span

        try:
            yield span
        except Exception as exc:
            span.set_status("error", str(exc))
            span.add_event("exception", {"exception.type": type(exc).__name__, "exception.message": str(exc)})
            raise
        finally:
            span.end()
            self._active_span.current = previous
            self._record_span(span)

    def _record_span(self, span: Span) -> None:
        """Record a finished span."""
        with self._lock:
            self._spans.append(span)
            if len(self._spans) > self.max_spans:
                self._spans = self._spans[-self.max_spans:]

        # Export
        for exporter in self._exporters:
            try:
                exporter(span)
            except Exception as e:
                logger.debug(f"Span export error: {e}")

    def add_exporter(self, exporter: Callable[[Span], None]) -> None:
        """Add a span exporter callback."""
        self._exporters.append(exporter)

    def get_trace(self, trace_id: str) -> List[Dict[str, Any]]:
        """Get all spans for a trace."""
        with self._lock:
            return [s.to_dict() for s in self._spans if s.context.trace_id == trace_id]

    def get_recent_spans(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent spans."""
        with self._lock:
            return [s.to_dict() for s in self._spans[-limit:]]

    def get_slow_spans(self, threshold_ms: float = 1000, limit: int = 50) -> List[Dict[str, Any]]:
        """Get spans slower than threshold."""
        with self._lock:
            slow = [s for s in self._spans if s.duration_ms > threshold_ms]
            slow.sort(key=lambda s: s.duration_ms, reverse=True)
            return [s.to_dict() for s in slow[:limit]]

    def get_error_spans(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get spans with errors."""
        with self._lock:
            errors = [s for s in self._spans if s.status == "error"]
            return [s.to_dict() for s in errors[-limit:]]

    def clear(self) -> int:
        """Clear all recorded spans."""
        with self._lock:
            count = len(self._spans)
            self._spans.clear()
            return count

    def stats(self) -> Dict[str, Any]:
        """Get tracer statistics."""
        with self._lock:
            total = len(self._spans)
            errors = sum(1 for s in self._spans if s.status == "error")
            avg_duration = (
                sum(s.duration_ms for s in self._spans) / total if total else 0
            )
            return {
                "service_name": self.service_name,
                "total_spans": total,
                "error_spans": errors,
                "average_duration_ms": round(avg_duration, 2),
                "max_spans": self.max_spans,
            }
