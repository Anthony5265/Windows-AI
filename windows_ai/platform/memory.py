from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class MemoryRecord:
    content: str
    scope: str = "user"
    kind: str = "fact"
    metadata: dict[str, Any] = field(default_factory=dict)
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class MemoryStore:
    """Persistent SQLite memory store; embeddings can be layered on later without changing the API."""

    def __init__(self, path: str | Path = "memory.db") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        with self._connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS memories (id TEXT PRIMARY KEY, scope TEXT, kind TEXT, content TEXT, metadata TEXT, created_at TEXT)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_memories_scope ON memories(scope)")
            db.commit()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def add(self, record: MemoryRecord) -> MemoryRecord:
        with self._lock, self._connect() as db:
            db.execute("INSERT OR REPLACE INTO memories VALUES (?, ?, ?, ?, ?, ?)", (record.record_id, record.scope, record.kind, record.content, json.dumps(record.metadata), record.created_at))
            db.commit()
        return record

    def search(self, query: str, *, scope: str | None = None, limit: int = 10) -> list[MemoryRecord]:
        terms = [term.strip().lower() for term in query.split() if term.strip()]
        if not terms:
            return []
        clauses = ["lower(content) LIKE ?" for _ in terms]
        params: list[Any] = [f"%{term}%" for term in terms]
        where = "(" + " OR ".join(clauses) + ")"
        if scope:
            where += " AND scope = ?"
            params.append(scope)
        with self._lock, self._connect() as db:
            rows = db.execute(f"SELECT id, scope, kind, content, metadata, created_at FROM memories WHERE {where} ORDER BY created_at DESC LIMIT ?", (*params, limit)).fetchall()
        return [MemoryRecord(content=r[3], scope=r[1], kind=r[2], metadata=json.loads(r[4] or "{}"), record_id=r[0], created_at=r[5]) for r in rows]

    def delete(self, record_id: str) -> bool:
        with self._lock, self._connect() as db:
            cur = db.execute("DELETE FROM memories WHERE id = ?", (record_id,))
            db.commit()
            return cur.rowcount > 0

    def list(self, *, scope: str | None = None, limit: int = 100) -> list[MemoryRecord]:
        with self._lock, self._connect() as db:
            if scope:
                rows = db.execute("SELECT id, scope, kind, content, metadata, created_at FROM memories WHERE scope = ? ORDER BY created_at DESC LIMIT ?", (scope, limit)).fetchall()
            else:
                rows = db.execute("SELECT id, scope, kind, content, metadata, created_at FROM memories ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [MemoryRecord(content=r[3], scope=r[1], kind=r[2], metadata=json.loads(r[4] or "{}"), record_id=r[0], created_at=r[5]) for r in rows]
