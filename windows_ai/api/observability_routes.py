"""
Observability API Routes
Expose tracing, metrics, and logging through REST endpoints
"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/observability", tags=["Observability"])

# --- Singleton instances (created lazily) ---
_tracer = None
_metrics = None
_slogger = None


def _get_tracer():
    global _tracer
    if _tracer is None:
        from windows_ai.observability.tracing import Tracer
        _tracer = Tracer(service_name="windows-ai-api")
    return _tracer


def _get_metrics():
    global _metrics
    if _metrics is None:
        from windows_ai.observability.metrics import MetricsCollector
        _metrics = MetricsCollector()
    return _metrics


def _get_slogger():
    global _slogger
    if _slogger is None:
        from windows_ai.observability.structured_logging import StructuredLogger
        _slogger = StructuredLogger(service="windows-ai-api", output="none")
    return _slogger


# ---------------------------------------------------------------------- #
# Tracing endpoints                                                       #
# ---------------------------------------------------------------------- #

@router.get("/traces/recent")
async def get_recent_traces(limit: int = Query(default=50, ge=1, le=500)):
    """Get recent spans."""
    return {"status": "success", "spans": _get_tracer().get_recent_spans(limit)}


@router.get("/traces/{trace_id}")
async def get_trace(trace_id: str):
    """Get all spans for a specific trace."""
    spans = _get_tracer().get_trace(trace_id)
    if not spans:
        raise HTTPException(status_code=404, detail="Trace not found")
    return {"status": "success", "trace_id": trace_id, "spans": spans}


@router.get("/traces/slow")
async def get_slow_traces(
    threshold_ms: float = Query(default=1000, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
):
    """Get spans slower than threshold."""
    return {"status": "success", "spans": _get_tracer().get_slow_spans(threshold_ms, limit)}


@router.get("/traces/errors")
async def get_error_traces(limit: int = Query(default=50, ge=1, le=500)):
    """Get spans with error status."""
    return {"status": "success", "spans": _get_tracer().get_error_spans(limit)}


@router.get("/traces/stats")
async def get_trace_stats():
    """Get tracer statistics."""
    return {"status": "success", **_get_tracer().stats()}


@router.delete("/traces")
async def clear_traces():
    """Clear all recorded spans."""
    count = _get_tracer().clear()
    return {"status": "success", "cleared": count}


# ---------------------------------------------------------------------- #
# Metrics endpoints                                                        #
# ---------------------------------------------------------------------- #

@router.get("/metrics")
async def get_all_metrics():
    """Get all collected metrics."""
    return {"status": "success", "metrics": _get_metrics().get_all()}


@router.get("/metrics/stats")
async def get_metrics_stats():
    """Get metrics collector statistics."""
    return {"status": "success", **_get_metrics().stats()}


class MetricIncrementRequest(BaseModel):
    name: str
    amount: float = 1.0


@router.post("/metrics/counter/increment")
async def increment_counter(req: MetricIncrementRequest):
    """Increment a counter."""
    counter = _get_metrics().counter(req.name)
    counter.inc(req.amount)
    return {"status": "success", "name": req.name, "value": counter.value}


class GaugeSetRequest(BaseModel):
    name: str
    value: float


@router.post("/metrics/gauge/set")
async def set_gauge(req: GaugeSetRequest):
    """Set a gauge value."""
    gauge = _get_metrics().gauge(req.name)
    gauge.set(req.value)
    return {"status": "success", "name": req.name, "value": gauge.value}


class HistogramObserveRequest(BaseModel):
    name: str
    value: float


@router.post("/metrics/histogram/observe")
async def observe_histogram(req: HistogramObserveRequest):
    """Record a histogram observation."""
    hist = _get_metrics().histogram(req.name)
    hist.observe(req.value)
    return {"status": "success", "name": req.name, "count": hist.count}


@router.delete("/metrics")
async def reset_metrics():
    """Reset all metrics."""
    _get_metrics().reset()
    return {"status": "success", "message": "All metrics reset"}


# ---------------------------------------------------------------------- #
# Logging endpoints                                                        #
# ---------------------------------------------------------------------- #

@router.get("/logs")
async def get_logs(
    limit: int = Query(default=100, ge=1, le=1000),
    level: Optional[str] = Query(default=None),
):
    """Get recent log entries."""
    entries = _get_slogger().get_entries(limit=limit, level=level)
    return {"status": "success", "entries": entries, "count": len(entries)}


@router.get("/logs/errors")
async def get_error_logs(limit: int = Query(default=50, ge=1, le=500)):
    """Get recent error log entries."""
    return {"status": "success", "entries": _get_slogger().get_errors(limit)}


@router.get("/logs/search")
async def search_logs(
    q: str = Query(..., min_length=1),
    limit: int = Query(default=50, ge=1, le=500),
):
    """Search log entries by keyword."""
    results = _get_slogger().search(q, limit)
    return {"status": "success", "query": q, "entries": results, "count": len(results)}


@router.get("/logs/stats")
async def get_log_stats():
    """Get logger statistics."""
    return {"status": "success", **_get_slogger().stats()}


@router.delete("/logs")
async def clear_logs():
    """Clear all log entries."""
    count = _get_slogger().clear()
    return {"status": "success", "cleared": count}


# ---------------------------------------------------------------------- #
# Combined dashboard                                                       #
# ---------------------------------------------------------------------- #

@router.get("/dashboard")
async def get_dashboard():
    """Get combined observability dashboard data."""
    return {
        "status": "success",
        "tracing": _get_tracer().stats(),
        "metrics": _get_metrics().stats(),
        "logging": _get_slogger().stats(),
    }
