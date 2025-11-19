"""
Higher-level analytics built on top of aggregated log streams.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from statistics import mean, pstdev
from typing import Any, Dict, Iterable, List, Optional, Sequence

from plugins.logging.log_aggregator.aggregator import LogAggregator

ISO_FORMATS = ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ")


def _parse_ts(value: str) -> Optional[datetime]:
    for fmt in ISO_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


class LogAnalyzer:
    """
    Provides simple search, grouping, and spike-detection primitives.
    """

    def __init__(self, aggregator: Optional[LogAggregator] = None):
        self.aggregator = aggregator or LogAggregator()
        self._records: List[Dict[str, Any]] = []

    def ingest(self, records: Iterable[Dict[str, Any]]) -> None:
        for record in records:
            self._records.append(record)

    def refresh_from_sources(self) -> None:
        """Refresh internal cache from the attached aggregator."""
        self._records = list(self.aggregator.iter_records())

    def search(self, keyword: str, fields: Optional[Sequence[str]] = None) -> List[Dict[str, Any]]:
        """Return records containing ``keyword`` inside the selected fields."""
        keyword_lower = keyword.lower()
        results: List[Dict[str, Any]] = []
        for record in self._records:
            keys = fields or record.keys()
            for key in keys:
                value = str(record.get(key, "")).lower()
                if keyword_lower in value:
                    results.append(record)
                    break
        return results

    def counts_by(self, field: str) -> Dict[str, int]:
        """Frequency of a field across the cached records."""
        return Counter(str(record.get(field)) for record in self._records if field in record)

    def timeline(self, bucket: str = "hour") -> Dict[str, int]:
        """Group counts per minute/hour/day based on the ``timestamp`` field."""
        allowed = {"minute", "hour", "day"}
        if bucket not in allowed:
            raise ValueError(f"bucket must be one of {allowed}")

        groups: Dict[str, int] = defaultdict(int)
        for record in self._records:
            timestamp = record.get("timestamp")
            if not timestamp:
                continue
            dt = _parse_ts(str(timestamp))
            if not dt:
                continue
            if bucket == "minute":
                label = dt.strftime("%Y-%m-%d %H:%M")
            elif bucket == "hour":
                label = dt.strftime("%Y-%m-%d %H:00")
            else:
                label = dt.strftime("%Y-%m-%d")
            groups[label] += 1
        return dict(sorted(groups.items()))

    def detect_spikes(self, field: str, threshold_stddev: float = 2.5) -> List[Dict[str, Any]]:
        """
        Detect anomalies by counting ``field`` occurrences per hour
        and highlighting buckets whose counts exceed ``threshold_stddev``.
        """
        timeline = self.timeline(bucket="hour")
        if not timeline:
            return []
        values = list(timeline.values())
        avg = mean(values)
        stddev = pstdev(values) if len(values) > 1 else 0
        if stddev == 0:
            return []
        anomalies = []
        for bucket_label, count in timeline.items():
            z_score = (count - avg) / stddev
            if z_score >= threshold_stddev:
                anomalies.append({"bucket": bucket_label, "count": count, "z_score": z_score})
        return anomalies
