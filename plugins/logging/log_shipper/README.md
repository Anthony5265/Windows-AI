# Log Shipper

Simple HTTP-based shipper that batches local log entries and sends them to a SIEM
or data lake endpoint. It keeps a background thread alive, flushes on a schedule,
and retries failed uploads with exponential backoff.

```python
from plugins.logging.log_shipper.shipper import LogShipper

shipper = LogShipper(
    endpoint=\"https://logs.internal/api/v1/ingest\",
    api_key=\"super-secret\",
    batch_size=25,
    flush_interval=2.0,
)

shipper.enqueue({\"timestamp\": \"2025-11-15T18:04:00Z\", \"message\": \"Started backend\"})
shipper.enqueue({\"timestamp\": \"2025-11-15T18:05:45Z\", \"message\": \"API error\", \"severity\": \"high\"})

# When the application shuts down:
shipper.close()
```
