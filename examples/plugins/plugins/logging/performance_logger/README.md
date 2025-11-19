# Performance Logger

Captures latency, CPU time, and memory deltas for Windows-AI operations.
Useful when validating Tier 1 performance requirements and budgets.

## Highlights

- `track_operation()` context manager wraps critical sections
- Writes JSON metrics with optional tags and alerting thresholds
- Works with live `psutil.Process` objects or injected stubs for testing
- Summaries provide quick averages/min/max for any metric name

```python
from plugins.logging.performance_logger.performance_logger import PerformanceLogger

perf = PerformanceLogger()
with perf.track_operation("load_models", threshold_ms=500):
    load_models()

print(perf.summary("load_models"))
```
