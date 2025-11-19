"""
Configuration/change management logger.
"""

from __future__ import annotations

import difflib
import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from plugins.logging.base import JsonLogStore


class ChangeLogger:
    """
    Tracks configuration edits and produces machine-readable diffs.
    """

    def __init__(self, log_dir: str = "logs/change"):
        self.log_dir = Path(log_dir)
        self.store = JsonLogStore(self.log_dir / "change_log.jsonl")

    def log_change(
        self,
        component: str,
        item: str,
        actor: str,
        previous_value: Any,
        new_value: Any,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Persist a change event with structured diff information."""
        record = {
            "id": str(uuid.uuid4()),
            "timestamp": time.time(),
            "component": component,
            "item": item,
            "actor": actor,
            "reason": reason,
            "diff": self._render_diff(previous_value, new_value),
            "metadata": metadata or {},
        }
        self.store.append(record)
        return record

    def history(self, component: Optional[str] = None, item: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return change history filtered by component/item."""
        records = self.store.read_all()
        if component:
            records = [rec for rec in records if rec.get("component") == component]
        if item:
            records = [rec for rec in records if rec.get("item") == item]
        return records

    def _render_diff(self, previous_value: Any, new_value: Any) -> Dict[str, Any]:
        if isinstance(previous_value, dict) and isinstance(new_value, dict):
            return self._dict_diff(previous_value, new_value)
        prev_text = self._value_to_text(previous_value)
        new_text = self._value_to_text(new_value)
        diff = "\n".join(
            difflib.unified_diff(
                prev_text.splitlines(),
                new_text.splitlines(),
                fromfile="previous",
                tofile="new",
                lineterm="",
            )
        )
        return {"type": "text", "value": diff}

    def _dict_diff(self, previous: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
        added = {k: new[k] for k in new.keys() - previous.keys()}
        removed = {k: previous[k] for k in previous.keys() - new.keys()}
        changed = {
            k: {"from": previous[k], "to": new[k]}
            for k in previous.keys() & new.keys()
            if previous[k] != new[k]
        }
        return {"type": "dict", "added": added, "removed": removed, "changed": changed}

    def _value_to_text(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        return json.dumps(value, indent=2, sort_keys=True)
