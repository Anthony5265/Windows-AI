# Trace Logger

High-cardinality tracing utility that records span lifecycles and
structured events for the Windows-AI runtime.

## Features

- Start/stop spans with correlation IDs
- Nested spans with automatic trace inheritance
- Structured event logging with arbitrary context
- Context manager helper that captures exceptions and status
- JSON Lines output compatible with OpenTelemetry collectors

## Usage

```python
from plugins.logging.trace_logger.trace_logger import TraceLogger

tracer = TraceLogger(log_dir="logs/testing")

with tracer.span("load_model") as span_id:
    tracer.log_event(span_id, "downloading weights", level="DEBUG")
```

Each span produces `span_start`, optional `event`, and `span_end` entries
under `logs/testing/trace_events.jsonl`.
