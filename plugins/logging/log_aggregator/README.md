# Log Aggregator

Utility class that discovers JSON Lines logs (e.g. from the access, compliance,
or monitoring plugins) and produces merged streams for dashboards or analytics.

## Capabilities
- Register explicit sources or automatically discover `*.jsonl` files.
- Iterate through log events in chronological order.
- Retrieve rolling tails for troubleshooting sessions.
- Filter and count events across fields (severity, type, resource, etc.).

## Example
```python
from pathlib import Path
from plugins.logging.log_aggregator.aggregator import LogAggregator

aggregator = LogAggregator()
aggregator.discover(Path(\"logs\"))       # recursively registers jsonl files
recent = aggregator.tail(limit=50)       # grab most recent entries
counts = aggregator.summarize(\"type\")   # count by record type
errors = aggregator.filter(severity=\"high\")  # filter helpers
```
