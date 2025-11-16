# Log Archiver

Ensures log directories do not grow unbounded by moving older files into an
`archive/` tree and gzipping them for long-term retention.

## Example
```python
from plugins.logging.log_archiver.archiver import LogArchiver

archiver = LogArchiver(source_dir=\"logs\", archive_dir=\"logs/archive\", default_max_age_days=14)
archived_files = archiver.archive()          # moves + compresses logs older than 14 days
archiver.cleanup_archives(max_total_gb=2.0)  # optional quota enforcement
```

Pair this with `LogAggregator`/`LogAnalyzer` to keep only actionable data inside
the live directories while preserving audit trails for compliance.
