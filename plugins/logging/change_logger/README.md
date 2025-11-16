# Change Logger

Tracks configuration and policy updates for Windows-AI subsystems.
Provides both dictionary-aware diffs and plain-text unified diffs.

## Sample

```python
from plugins.logging.change_logger.change_logger import ChangeLogger

logger = ChangeLogger()
logger.log_change(
    component="watchdog",
    item="config.json",
    actor="automation-bot",
    previous_value={"interval": 30},
    new_value={"interval": 15},
    reason="Reduce detection latency"
)
```

All events land in `logs/change/change_log.jsonl`, ready for review
or ingestion into dashboards.
