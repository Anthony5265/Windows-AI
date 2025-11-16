"""
Alert orchestration for logging plugins.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from plugins.logging.base import JsonLogStore


AlertPredicate = Callable[[Dict[str, Any]], bool]


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


@dataclass
class AlertRule:
    name: str
    predicate: AlertPredicate
    severity: str = "medium"
    description: Optional[str] = None
    debounce_seconds: int = 300
    metadata: Dict[str, Any] = field(default_factory=dict)


class AlertManager:
    """
    Evaluates log entries against registered rules and emits alerts.
    """

    def __init__(
        self,
        log_dir: str = "logs/alerts",
        notifier: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> None:
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.store = JsonLogStore(self.log_dir / "alerts.jsonl")
        self.notifier = notifier
        self.rules: List[AlertRule] = []
        self._last_triggered: Dict[str, datetime] = {}

    def register_rule(self, rule: AlertRule) -> None:
        self.rules.append(rule)

    def evaluate(self, record: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Evaluate a log record against all rules and emit zero or more alerts.
        """
        alerts: List[Dict[str, Any]] = []
        for rule in self.rules:
            if not rule.predicate(record):
                continue
            if not self._should_trigger(rule):
                continue

            alert = {
                "rule": rule.name,
                "severity": rule.severity,
                "description": rule.description or "",
                "metadata": rule.metadata,
                "record": record,
                "timestamp": _utcnow().isoformat(),
            }
            self.store.append(alert)
            alerts.append(alert)
            self._last_triggered[rule.name] = _utcnow()
            if self.notifier:
                self.notifier(alert)
        return alerts

    def replay(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Evaluate a batch of historical records."""
        emitted: List[Dict[str, Any]] = []
        for record in records:
            emitted.extend(self.evaluate(record))
        return emitted

    def _should_trigger(self, rule: AlertRule) -> bool:
        last = self._last_triggered.get(rule.name)
        if not last:
            return True
        return _utcnow() - last >= timedelta(seconds=rule.debounce_seconds)
