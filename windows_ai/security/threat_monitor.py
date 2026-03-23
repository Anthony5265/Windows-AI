"""Threat monitoring and anomaly detection for Windows AI.

Provides real-time monitoring of system activity for suspicious patterns.
Uses keyword-based heuristics, rate-based anomaly detection, and
configurable alert thresholds.
"""

from __future__ import annotations

import re
import time
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Iterable, List, Optional

logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    """Severity level for detected threats."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ThreatAlert:
    """A single threat detection alert."""
    level: ThreatLevel
    category: str
    description: str
    source: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ThreatMonitor:
    """Comprehensive threat monitoring system.

    Features
    --------
    * **Keyword scanning** – flag known-bad terms in text payloads.
    * **Rate anomaly detection** – detect unusual request bursts.
    * **IP reputation tracking** – track per-IP error counts.
    * **Alert callbacks** – register handlers for real-time alerting.
    * **Alert history** – maintain an in-memory log of recent alerts.
    """

    # Default suspicious keywords grouped by category
    DEFAULT_KEYWORDS: Dict[str, List[str]] = {
        "injection": [
            "sql injection", "xss", "script injection", "command injection",
            "ldap injection", "xpath injection",
        ],
        "malware": [
            "malware", "ransomware", "trojan", "keylogger", "rootkit",
            "backdoor", "worm", "spyware",
        ],
        "attack": [
            "attack", "exploit", "vulnerability", "zero-day", "brute force",
            "denial of service", "ddos", "phishing",
        ],
        "data_exfil": [
            "data exfiltration", "data leak", "credential dump",
            "password dump", "unauthorized access",
        ],
    }

    def __init__(
        self,
        keywords: Optional[Iterable[str]] = None,
        *,
        rate_window_seconds: float = 60.0,
        rate_threshold: int = 100,
        max_alerts: int = 1000,
    ):
        # Build flat keyword list for backward-compat ``analyze()``
        if keywords is not None:
            self.keywords = list(keywords)
        else:
            self.keywords = [
                kw for group in self.DEFAULT_KEYWORDS.values() for kw in group
            ]

        self._keyword_categories = dict(self.DEFAULT_KEYWORDS)
        self._rate_window = rate_window_seconds
        self._rate_threshold = rate_threshold
        self._max_alerts = max_alerts

        # State
        self._alerts: List[ThreatAlert] = []
        self._request_log: Dict[str, List[float]] = defaultdict(list)
        self._ip_error_counts: Dict[str, int] = defaultdict(int)
        self._callbacks: List[Callable[[ThreatAlert], None]] = []

    # ------------------------------------------------------------------
    # Keyword scanning (original API preserved)
    # ------------------------------------------------------------------

    def analyze(self, text: str) -> List[str]:
        """Return a list of suspicious keywords found in *text*."""
        hits = [
            kw
            for kw in self.keywords
            if re.search(rf"\b{re.escape(kw)}\b", text, re.IGNORECASE)
        ]
        return hits

    def analyze_categorized(self, text: str) -> Dict[str, List[str]]:
        """Scan *text* and return hits grouped by threat category."""
        results: Dict[str, List[str]] = {}
        for category, kws in self._keyword_categories.items():
            hits = [
                kw for kw in kws
                if re.search(rf"\b{re.escape(kw)}\b", text, re.IGNORECASE)
            ]
            if hits:
                results[category] = hits
        return results

    # ------------------------------------------------------------------
    # Rate anomaly detection
    # ------------------------------------------------------------------

    def record_request(self, client_id: str) -> Optional[ThreatAlert]:
        """Record a request and return an alert if rate is anomalous."""
        now = time.time()
        log = self._request_log[client_id]
        log.append(now)
        # Prune old entries
        cutoff = now - self._rate_window
        self._request_log[client_id] = [t for t in log if t > cutoff]

        if len(self._request_log[client_id]) > self._rate_threshold:
            alert = ThreatAlert(
                level=ThreatLevel.HIGH,
                category="rate_anomaly",
                description=(
                    f"Client {client_id} exceeded {self._rate_threshold} "
                    f"requests in {self._rate_window}s "
                    f"(actual: {len(self._request_log[client_id])})"
                ),
                source=client_id,
                metadata={"count": len(self._request_log[client_id])},
            )
            self._emit_alert(alert)
            return alert
        return None

    # ------------------------------------------------------------------
    # IP reputation
    # ------------------------------------------------------------------

    def record_error(self, client_id: str) -> Optional[ThreatAlert]:
        """Track errors per client and alert on high error rates."""
        self._ip_error_counts[client_id] += 1
        count = self._ip_error_counts[client_id]
        if count >= 50:
            alert = ThreatAlert(
                level=ThreatLevel.MEDIUM,
                category="ip_reputation",
                description=f"Client {client_id} has {count} errors",
                source=client_id,
                metadata={"error_count": count},
            )
            self._emit_alert(alert)
            return alert
        return None

    # ------------------------------------------------------------------
    # Full payload scan
    # ------------------------------------------------------------------

    def scan_payload(self, text: str, source: str = "unknown") -> List[ThreatAlert]:
        """Perform a full scan of a text payload and return any alerts."""
        alerts: List[ThreatAlert] = []
        categorized = self.analyze_categorized(text)
        for category, hits in categorized.items():
            level = (
                ThreatLevel.CRITICAL
                if category in ("injection", "data_exfil")
                else ThreatLevel.HIGH
                if category == "attack"
                else ThreatLevel.MEDIUM
            )
            alert = ThreatAlert(
                level=level,
                category=category,
                description=f"Detected keywords: {', '.join(hits)}",
                source=source,
                metadata={"keywords": hits},
            )
            self._emit_alert(alert)
            alerts.append(alert)
        return alerts

    # ------------------------------------------------------------------
    # Alert management
    # ------------------------------------------------------------------

    def on_alert(self, callback: Callable[[ThreatAlert], None]) -> None:
        """Register a callback invoked on every new alert."""
        self._callbacks.append(callback)

    def _emit_alert(self, alert: ThreatAlert) -> None:
        self._alerts.append(alert)
        if len(self._alerts) > self._max_alerts:
            self._alerts = self._alerts[-self._max_alerts:]

        logger.warning("Threat alert [%s/%s]: %s", alert.level.value, alert.category, alert.description)
        for cb in self._callbacks:
            try:
                cb(alert)
            except Exception:
                logger.exception("Alert callback failed")

    def get_alerts(
        self,
        *,
        level: Optional[ThreatLevel] = None,
        category: Optional[str] = None,
        limit: int = 50,
    ) -> List[ThreatAlert]:
        """Retrieve recent alerts, optionally filtered."""
        alerts = self._alerts
        if level is not None:
            alerts = [a for a in alerts if a.level == level]
        if category is not None:
            alerts = [a for a in alerts if a.category == category]
        return alerts[-limit:]

    def clear_alerts(self) -> int:
        """Clear all stored alerts. Returns the number cleared."""
        count = len(self._alerts)
        self._alerts.clear()
        return count

    def stats(self) -> Dict[str, Any]:
        """Return monitoring statistics."""
        return {
            "total_alerts": len(self._alerts),
            "tracked_clients": len(self._request_log),
            "clients_with_errors": len(self._ip_error_counts),
            "alert_breakdown": {
                level.value: sum(1 for a in self._alerts if a.level == level)
                for level in ThreatLevel
            },
        }

