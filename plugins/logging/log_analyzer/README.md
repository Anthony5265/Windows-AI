# Log Analyzer

Wraps `LogAggregator` with higher-level utilities: keyword search,
frequency/timeline summaries, and a basic anomaly detector that spots spikes in
event volumes.

```python
from plugins.logging.log_aggregator.aggregator import LogAggregator
from plugins.logging.log_analyzer.analyzer import LogAnalyzer

aggregator = LogAggregator()
aggregator.discover(Path(\"logs\"))  # register JSONL sources

analyzer = LogAnalyzer(aggregator)
analyzer.refresh_from_sources()

errors = analyzer.search(\"error\", fields=[\"message\", \"reason\"])
counts = analyzer.counts_by(\"severity\")
spikes = analyzer.detect_spikes(field=\"severity\", threshold_stddev=3.0)
```

Use this class inside monitoring workflows or even inside notebooks to build
lightweight dashboards while the dedicated observability stack is still being
implemented.
