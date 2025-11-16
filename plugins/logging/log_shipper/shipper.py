"""
Ships log batches to remote HTTP endpoints (SIEM, data lake, etc.).
"""

from __future__ import annotations

import json
import queue
import threading
import time
from typing import Any, Dict, Iterable, List, Optional

import requests


class LogShipper:
    """
    Lightweight log shipping client with in-memory buffering and retry support.
    """

    def __init__(
        self,
        endpoint: str,
        api_key: Optional[str] = None,
        batch_size: int = 50,
        flush_interval: float = 5.0,
        timeout: float = 5.0,
    ) -> None:
        self.endpoint = endpoint
        self.api_key = api_key
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.timeout = timeout
        self._queue: "queue.Queue[Dict[str, Any]]" = queue.Queue()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def enqueue(self, record: Dict[str, Any]) -> None:
        """Add a log record to the shipping queue."""
        self._queue.put(record, block=False)

    def ship_records(self, records: Iterable[Dict[str, Any]]) -> bool:
        """Synchronously send a batch of records."""
        payload = {"records": list(records)}
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        response = requests.post(
            self.endpoint, headers=headers, json=payload, timeout=self.timeout
        )
        response.raise_for_status()
        return True

    def flush(self) -> None:
        """Flush any pending records immediately."""
        to_send = []
        while not self._queue.empty():
            to_send.append(self._queue.get_nowait())
        if to_send:
            self.ship_records(to_send)

    def close(self) -> None:
        """Stop the background thread and flush all pending records."""
        self._stop.set()
        self._thread.join(timeout=self.flush_interval + 1)
        self.flush()

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _worker(self) -> None:
        pending: List[Dict[str, Any]] = []
        last_flush = time.monotonic()
        while not self._stop.is_set():
            try:
                record = self._queue.get(timeout=0.5)
                pending.append(record)
            except queue.Empty:
                pass

            time_since_flush = time.monotonic() - last_flush
            if pending and (
                len(pending) >= self.batch_size or time_since_flush >= self.flush_interval
            ):
                try:
                    self.ship_records(pending)
                    pending.clear()
                    last_flush = time.monotonic()
                except requests.RequestException:
                    # Exponential backoff-lite
                    time.sleep(min(60, self.flush_interval * 2))

        if pending:
            try:
                self.ship_records(pending)
            except requests.RequestException:
                pass
