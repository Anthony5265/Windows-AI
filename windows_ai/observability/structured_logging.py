"""
Structured Logging for Windows AI
JSON-based structured logging with context propagation
"""
from __future__ import annotations

import json
import logging
import sys
import time
import threading
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class StructuredLogger:
    """JSON-based structured logger with context propagation.

    Usage::

        slog = StructuredLogger(service="api-server")
        slog.info("Request received", method="GET", path="/chat", user_id="abc")
        slog.error("Failed to process", error="timeout", duration_ms=5200)

        # With context
        with slog.context(request_id="req-123"):
            slog.info("Processing")   # automatically includes request_id
    """

    def __init__(
        self,
        service: str = "windows-ai",
        output: str = "stderr",
        min_level: str = "INFO",
        max_entries: int = 10000,
    ):
        self.service = service
        self.output = output
        self.min_level = getattr(logging, min_level.upper(), logging.INFO)
        self.max_entries = max_entries
        self._context: threading.local = threading.local()
        self._entries: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._callbacks: List = []

    # ---- Context management ----

    class _ContextManager:
        def __init__(self, slog: "StructuredLogger", ctx: Dict[str, Any]):
            self._slog = slog
            self._ctx = ctx
            self._prev: Dict[str, Any] = {}

        def __enter__(self):
            self._prev = getattr(self._slog._context, "data", {}).copy()
            current = self._prev.copy()
            current.update(self._ctx)
            self._slog._context.data = current
            return self

        def __exit__(self, *args):
            self._slog._context.data = self._prev

    def context(self, **kwargs: Any) -> "_ContextManager":
        """Push additional context fields for the duration of the block."""
        return self._ContextManager(self, kwargs)

    def _get_context(self) -> Dict[str, Any]:
        return getattr(self._context, "data", {})

    # ---- Logging methods ----

    def _log(self, level: str, message: str, **fields: Any) -> Dict[str, Any]:
        level_num = getattr(logging, level.upper(), logging.INFO)
        if level_num < self.min_level:
            return {}

        entry: Dict[str, Any] = {
            "timestamp": time.time(),
            "level": level.upper(),
            "message": message,
            "service": self.service,
        }
        # Merge context + explicit fields
        entry.update(self._get_context())
        entry.update(fields)

        with self._lock:
            self._entries.append(entry)
            if len(self._entries) > self.max_entries:
                self._entries = self._entries[-self.max_entries:]

        # Output
        self._emit(entry)

        # Callbacks
        for cb in self._callbacks:
            try:
                cb(entry)
            except Exception:
                pass

        return entry

    def debug(self, message: str, **fields: Any) -> Dict[str, Any]:
        return self._log("debug", message, **fields)

    def info(self, message: str, **fields: Any) -> Dict[str, Any]:
        return self._log("info", message, **fields)

    def warning(self, message: str, **fields: Any) -> Dict[str, Any]:
        return self._log("warning", message, **fields)

    def error(self, message: str, **fields: Any) -> Dict[str, Any]:
        return self._log("error", message, **fields)

    def critical(self, message: str, **fields: Any) -> Dict[str, Any]:
        return self._log("critical", message, **fields)

    def _emit(self, entry: Dict[str, Any]) -> None:
        """Write entry to output."""
        line = json.dumps(entry, default=str)
        if self.output == "stderr":
            print(line, file=sys.stderr)
        elif self.output == "stdout":
            print(line)
        # "none" => silent (in-memory only)

    # ---- Query & export ----

    def add_callback(self, callback) -> None:
        """Register a callback invoked on each log entry."""
        self._callbacks.append(callback)

    def get_entries(self, limit: int = 100, level: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve recent entries, optionally filtered by level."""
        with self._lock:
            entries = self._entries[-limit:]
        if level:
            entries = [e for e in entries if e.get("level") == level.upper()]
        return entries

    def get_errors(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent error and critical entries."""
        with self._lock:
            return [e for e in self._entries if e.get("level") in ("ERROR", "CRITICAL")][-limit:]

    def search(self, keyword: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search entries by keyword in message."""
        kw = keyword.lower()
        with self._lock:
            return [e for e in self._entries if kw in e.get("message", "").lower()][-limit:]

    def clear(self) -> int:
        """Clear all entries."""
        with self._lock:
            count = len(self._entries)
            self._entries.clear()
            return count

    def stats(self) -> Dict[str, Any]:
        """Get logger statistics."""
        with self._lock:
            level_counts: Dict[str, int] = {}
            for e in self._entries:
                lev = e.get("level", "UNKNOWN")
                level_counts[lev] = level_counts.get(lev, 0) + 1
            return {
                "service": self.service,
                "total_entries": len(self._entries),
                "max_entries": self.max_entries,
                "level_breakdown": level_counts,
            }
