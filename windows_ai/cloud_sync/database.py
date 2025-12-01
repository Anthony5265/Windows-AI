"""
SQLite database for Windows-AI Cloud Sync state management
"""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Iterator

from .models import (
    DataCategory,
    SyncState,
    SyncConflict,
    SyncChange,
    DeviceInfo,
    ConflictResolution,
    SyncStatus,
)


class SyncDatabase:
    """Manages local sync state and queue in SQLite database"""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_database()

    @contextmanager
    def _get_connection(self) -> Iterator[sqlite3.Connection]:
        """Context manager for database connections"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _initialize_database(self) -> None:
        """Create database schema if it doesn't exist"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Device information table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS devices (
                    device_id TEXT PRIMARY KEY,
                    device_name TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    os_version TEXT NOT NULL,
                    app_version TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    sync_priority INTEGER NOT NULL DEFAULT 100,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Sync state table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sync_state (
                    category TEXT PRIMARY KEY,
                    last_sync TEXT,
                    last_pull TEXT,
                    last_push TEXT,
                    pending_changes INTEGER NOT NULL DEFAULT 0,
                    conflicts INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'idle',
                    error_message TEXT,
                    sync_version INTEGER NOT NULL DEFAULT 1,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Sync queue for offline changes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sync_queue (
                    change_id TEXT PRIMARY KEY,
                    category TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    data TEXT,
                    version INTEGER NOT NULL DEFAULT 1,
                    timestamp TEXT NOT NULL,
                    synced INTEGER NOT NULL DEFAULT 0,
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    last_error TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Conflicts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conflicts (
                    conflict_id TEXT PRIMARY KEY,
                    category TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    local_version INTEGER NOT NULL,
                    remote_version INTEGER NOT NULL,
                    local_data TEXT,
                    remote_data TEXT,
                    local_timestamp TEXT,
                    remote_timestamp TEXT,
                    resolution TEXT,
                    resolved INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            """)

            # Conversations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    conversation_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    messages TEXT NOT NULL,
                    model TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    version INTEGER NOT NULL DEFAULT 1,
                    metadata TEXT,
                    synced INTEGER NOT NULL DEFAULT 0,
                    deleted INTEGER NOT NULL DEFAULT 0
                )
            """)

            # Settings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    category TEXT PRIMARY KEY,
                    settings TEXT NOT NULL,
                    version INTEGER NOT NULL DEFAULT 1,
                    updated_at TEXT NOT NULL,
                    synced INTEGER NOT NULL DEFAULT 0
                )
            """)

            # Automations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS automations (
                    automation_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    config TEXT NOT NULL,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    version INTEGER NOT NULL DEFAULT 1,
                    synced INTEGER NOT NULL DEFAULT 0,
                    deleted INTEGER NOT NULL DEFAULT 0
                )
            """)

            # Create indexes for better query performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sync_queue_category
                ON sync_queue(category, synced)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_conflicts_resolved
                ON conflicts(resolved, created_at)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversations_updated
                ON conversations(updated_at, deleted)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_automations_updated
                ON automations(updated_at, deleted)
            """)

            conn.commit()

    # ========== Device Management ==========

    def register_device(self, device: DeviceInfo) -> None:
        """Register or update device information"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO devices
                (device_id, device_name, platform, os_version, app_version,
                 last_seen, is_active, sync_priority)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                device.device_id,
                device.device_name,
                device.platform,
                device.os_version,
                device.app_version,
                device.last_seen.isoformat(),
                1 if device.is_active else 0,
                device.sync_priority,
            ))

    def get_device(self, device_id: str) -> Optional[DeviceInfo]:
        """Get device information by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM devices WHERE device_id = ?", (device_id,))
            row = cursor.fetchone()
            if row:
                return DeviceInfo(
                    device_id=row["device_id"],
                    device_name=row["device_name"],
                    platform=row["platform"],
                    os_version=row["os_version"],
                    app_version=row["app_version"],
                    last_seen=datetime.fromisoformat(row["last_seen"]),
                    is_active=bool(row["is_active"]),
                    sync_priority=row["sync_priority"],
                )
            return None

    def list_devices(self, active_only: bool = True) -> List[DeviceInfo]:
        """List all registered devices"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM devices"
            if active_only:
                query += " WHERE is_active = 1"
            query += " ORDER BY sync_priority ASC, last_seen DESC"
            cursor.execute(query)
            return [
                DeviceInfo(
                    device_id=row["device_id"],
                    device_name=row["device_name"],
                    platform=row["platform"],
                    os_version=row["os_version"],
                    app_version=row["app_version"],
                    last_seen=datetime.fromisoformat(row["last_seen"]),
                    is_active=bool(row["is_active"]),
                    sync_priority=row["sync_priority"],
                )
                for row in cursor.fetchall()
            ]

    # ========== Sync State Management ==========

    def get_sync_state(self, category: DataCategory) -> SyncState:
        """Get sync state for a data category"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sync_state WHERE category = ?", (category.value,))
            row = cursor.fetchone()
            if row:
                return SyncState(
                    category=category,
                    last_sync=datetime.fromisoformat(row["last_sync"]) if row["last_sync"] else None,
                    last_pull=datetime.fromisoformat(row["last_pull"]) if row["last_pull"] else None,
                    last_push=datetime.fromisoformat(row["last_push"]) if row["last_push"] else None,
                    pending_changes=row["pending_changes"],
                    conflicts=row["conflicts"],
                    status=SyncStatus(row["status"]),
                    error_message=row["error_message"],
                    sync_version=row["sync_version"],
                )
            return SyncState(category=category)

    def update_sync_state(self, state: SyncState) -> None:
        """Update sync state for a data category"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO sync_state
                (category, last_sync, last_pull, last_push, pending_changes,
                 conflicts, status, error_message, sync_version, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                state.category.value,
                state.last_sync.isoformat() if state.last_sync else None,
                state.last_pull.isoformat() if state.last_pull else None,
                state.last_push.isoformat() if state.last_push else None,
                state.pending_changes,
                state.conflicts,
                state.status.value,
                state.error_message,
                state.sync_version,
                datetime.utcnow().isoformat(),
            ))

    def get_all_sync_states(self) -> Dict[DataCategory, SyncState]:
        """Get sync states for all categories"""
        states = {}
        for category in DataCategory:
            states[category] = self.get_sync_state(category)
        return states

    # ========== Sync Queue Management ==========

    def add_to_queue(self, change: SyncChange) -> None:
        """Add a change to the sync queue"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO sync_queue
                (change_id, category, operation, item_id, data, version,
                 timestamp, synced, retry_count, last_error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                change.change_id,
                change.category.value,
                change.operation,
                change.item_id,
                json.dumps(change.data) if change.data else None,
                change.version,
                change.timestamp.isoformat(),
                1 if change.synced else 0,
                change.retry_count,
                change.last_error,
            ))

    def get_pending_changes(
        self, category: Optional[DataCategory] = None, limit: int = 100
    ) -> List[SyncChange]:
        """Get pending changes from the sync queue"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM sync_queue WHERE synced = 0"
            params: tuple = ()
            if category:
                query += " AND category = ?"
                params = (category.value,)
            query += " ORDER BY timestamp ASC LIMIT ?"
            params = params + (limit,)
            cursor.execute(query, params)
            return [
                SyncChange(
                    change_id=row["change_id"],
                    category=DataCategory(row["category"]),
                    operation=row["operation"],
                    item_id=row["item_id"],
                    data=json.loads(row["data"]) if row["data"] else None,
                    version=row["version"],
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    synced=bool(row["synced"]),
                    retry_count=row["retry_count"],
                    last_error=row["last_error"],
                )
                for row in cursor.fetchall()
            ]

    def mark_change_synced(self, change_id: str) -> None:
        """Mark a change as successfully synced"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE sync_queue SET synced = 1 WHERE change_id = ?",
                (change_id,)
            )

    def increment_retry_count(self, change_id: str, error: str) -> None:
        """Increment retry count for a failed sync attempt"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE sync_queue
                SET retry_count = retry_count + 1, last_error = ?
                WHERE change_id = ?
            """, (error, change_id))

    def clear_synced_changes(self, older_than_days: int = 7) -> int:
        """Clear old synced changes from the queue"""
        cutoff = datetime.utcnow().timestamp() - (older_than_days * 86400)
        cutoff_iso = datetime.fromtimestamp(cutoff).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM sync_queue
                WHERE synced = 1 AND timestamp < ?
            """, (cutoff_iso,))
            return cursor.rowcount

    # ========== Conflict Management ==========

    def add_conflict(self, conflict: SyncConflict) -> None:
        """Record a sync conflict"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO conflicts
                (conflict_id, category, item_id, local_version, remote_version,
                 local_data, remote_data, local_timestamp, remote_timestamp,
                 resolution, resolved, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                conflict.conflict_id,
                conflict.category.value,
                conflict.item_id,
                conflict.local_version,
                conflict.remote_version,
                json.dumps(conflict.local_data) if conflict.local_data else None,
                json.dumps(conflict.remote_data) if conflict.remote_data else None,
                conflict.local_timestamp.isoformat() if conflict.local_timestamp else None,
                conflict.remote_timestamp.isoformat() if conflict.remote_timestamp else None,
                conflict.resolution.value if conflict.resolution else None,
                1 if conflict.resolved else 0,
                conflict.created_at.isoformat(),
            ))

    def get_unresolved_conflicts(
        self, category: Optional[DataCategory] = None
    ) -> List[SyncConflict]:
        """Get all unresolved conflicts"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM conflicts WHERE resolved = 0"
            params: tuple = ()
            if category:
                query += " AND category = ?"
                params = (category.value,)
            query += " ORDER BY created_at ASC"
            cursor.execute(query, params)
            return [
                SyncConflict(
                    conflict_id=row["conflict_id"],
                    category=DataCategory(row["category"]),
                    item_id=row["item_id"],
                    local_version=row["local_version"],
                    remote_version=row["remote_version"],
                    local_data=json.loads(row["local_data"]) if row["local_data"] else None,
                    remote_data=json.loads(row["remote_data"]) if row["remote_data"] else None,
                    local_timestamp=datetime.fromisoformat(row["local_timestamp"]) if row["local_timestamp"] else None,
                    remote_timestamp=datetime.fromisoformat(row["remote_timestamp"]) if row["remote_timestamp"] else None,
                    resolution=ConflictResolution(row["resolution"]) if row["resolution"] else None,
                    resolved=bool(row["resolved"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                )
                for row in cursor.fetchall()
            ]

    def resolve_conflict(
        self, conflict_id: str, resolution: ConflictResolution
    ) -> None:
        """Mark a conflict as resolved with the given strategy"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE conflicts
                SET resolved = 1, resolution = ?
                WHERE conflict_id = ?
            """, (resolution.value, conflict_id))

    # ========== Conversation Management ==========

    def save_conversation(
        self,
        conversation_id: str,
        title: str,
        messages: List[Dict[str, Any]],
        model: str,
        metadata: Optional[Dict[str, Any]] = None,
        version: int = 1,
    ) -> None:
        """Save or update a conversation"""
        now = datetime.utcnow().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO conversations
                (conversation_id, title, messages, model, created_at, updated_at,
                 version, metadata, synced)
                VALUES (?, ?, ?, ?, COALESCE((SELECT created_at FROM conversations WHERE conversation_id = ?), ?), ?, ?, ?, 0)
            """, (
                conversation_id,
                title,
                json.dumps(messages),
                model,
                conversation_id,
                now,
                now,
                version,
                json.dumps(metadata) if metadata else "{}",
            ))

    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get a conversation by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM conversations WHERE conversation_id = ? AND deleted = 0",
                (conversation_id,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    "conversation_id": row["conversation_id"],
                    "title": row["title"],
                    "messages": json.loads(row["messages"]),
                    "model": row["model"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "version": row["version"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                }
            return None

    def list_conversations(
        self, since: Optional[datetime] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List conversations, optionally filtered by update time"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM conversations WHERE deleted = 0"
            params: tuple = ()
            if since:
                query += " AND updated_at > ?"
                params = (since.isoformat(),)
            query += " ORDER BY updated_at DESC LIMIT ?"
            params = params + (limit,)
            cursor.execute(query, params)
            return [
                {
                    "conversation_id": row["conversation_id"],
                    "title": row["title"],
                    "messages": json.loads(row["messages"]),
                    "model": row["model"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "version": row["version"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                }
                for row in cursor.fetchall()
            ]

    def delete_conversation(self, conversation_id: str) -> None:
        """Mark a conversation as deleted (soft delete)"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE conversations
                SET deleted = 1, updated_at = ?, synced = 0
                WHERE conversation_id = ?
            """, (datetime.utcnow().isoformat(), conversation_id))
