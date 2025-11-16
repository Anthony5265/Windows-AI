# Access Logger

Records Windows-AI authorization decisions and detects sudden bursts of
denied requests that might indicate brute-force activity.

## What it captures

- User, resource, action, decision (allowed/denied)
- Optional IP address and metadata
- Rolling window alerting for repeated denials
- Compact JSON Lines output for downstream analytics

```python
from plugins.logging.access_logger.access_logger import AccessLogger

logger = AccessLogger(deny_threshold=3)
for _ in range(3):
    logger.log_access("demo", "settings", "update", "denied")
print(logger.report())
```
