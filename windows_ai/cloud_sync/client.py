"""
Main sync client for Windows-AI Cloud Sync

Provides the main interface for synchronizing data with background
scheduling, offline queue, and conflict resolution.
"""

import logging
import platform
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable

from .database import SyncDatabase
from .encryption import SyncEncryption, EncryptionKey
from .models import (
    DataCategory,
    SyncState,
    SyncStatus,
    SyncChange,
    SyncConflict,
    ConflictResolution,
    DeviceInfo,
)
# Note:
# Import the protocol module (not the class directly) so tests can patch
# windows_ai.cloud_sync.protocol.SyncProtocol and have it take effect here.
from . import protocol
# Backwards-compatible alias so tests can patch
# windows_ai.cloud_sync.client.SyncProtocol as well.
SyncProtocol = protocol.SyncProtocol


logger = logging.getLogger(__name__)


class SyncClient:
    """
    Main client for Windows-AI Cloud Sync

    Features:
    - Background sync every 5 minutes
    - Manual sync trigger
    - Selective sync (choose what to sync)
    - Bandwidth throttling
    - Offline mode with queue
    - Conflict resolution
    - Multi-device coordination
    """

    DEFAULT_SYNC_INTERVAL = 300  # 5 minutes
    MAX_BATCH_SIZE = 100

    def __init__(
        self,
        db_path: str | Path,
        server_url: str,
        password: str,
        device_name: Optional[str] = None,
        auth_token: Optional[str] = None,
        sync_interval: int = DEFAULT_SYNC_INTERVAL,
        auto_resolve_conflicts: bool = False,
        conflict_strategy: ConflictResolution = ConflictResolution.NEWEST_WINS,
    ):
        """
        Initialize sync client

        Args:
            db_path: Path to SQLite sync database
            server_url: URL of sync server
            password: Password for encryption
            device_name: Name of this device
            auth_token: Authentication token
            sync_interval: Seconds between automatic syncs
            auto_resolve_conflicts: Whether to automatically resolve conflicts
            conflict_strategy: Default conflict resolution strategy
        """
        self.db = SyncDatabase(db_path)
        self.encryption = SyncEncryption()
        self.encryption_key = self.encryption.create_key_from_password(password)
        self.sync_interval = sync_interval
        self.auto_resolve_conflicts = auto_resolve_conflicts
        self.conflict_strategy = conflict_strategy

        # Initialize device info
        self.device_info = self._get_or_create_device_info(device_name)
        self.db.register_device(self.device_info)

        # Initialize protocol
        self.protocol = protocol.SyncProtocol(
            server_url=server_url,
            encryption=self.encryption,
            encryption_key=self.encryption_key,
            device_id=self.device_info.device_id,
            auth_token=auth_token,
        )

        # Background sync state
        self._sync_thread: Optional[threading.Thread] = None
        self._sync_enabled = False
        self._stop_event = threading.Event()

        # Callbacks
        self._on_sync_complete: Optional[Callable] = None
        self._on_conflict: Optional[Callable] = None
        self._on_error: Optional[Callable] = None

        # Selective sync categories (None = sync all)
        self._enabled_categories: Optional[List[DataCategory]] = None

        logger.info(f"SyncClient initialized for device {self.device_info.device_id}")

    def _get_or_create_device_info(self, device_name: Optional[str] = None) -> DeviceInfo:
        """Get or create device information"""
        # Try to load existing device info
        existing_devices = self.db.list_devices(active_only=False)
        if existing_devices:
            device = existing_devices[0]
            device.last_seen = datetime.utcnow()
            return device

        # Create new device info
        if device_name is None:
            device_name = platform.node() or "Unknown Device"

        return DeviceInfo(
            device_name=device_name,
            platform=platform.system(),
            os_version=platform.release(),
            app_version="1.0.0",  # TODO: Get from app
            last_seen=datetime.utcnow(),
            is_active=True,
        )

    # ========== Sync Control ==========

    def start_background_sync(self) -> None:
        """Start background sync scheduler"""
        if self._sync_enabled:
            logger.warning("Background sync already running")
            return

        self._sync_enabled = True
        self._stop_event.clear()
        self._sync_thread = threading.Thread(target=self._background_sync_loop, daemon=True)
        self._sync_thread.start()
        logger.info("Background sync started")

    def stop_background_sync(self) -> None:
        """Stop background sync scheduler"""
        if not self._sync_enabled:
            return

        self._sync_enabled = False
        self._stop_event.set()
        if self._sync_thread:
            self._sync_thread.join(timeout=10)
        logger.info("Background sync stopped")

    def _background_sync_loop(self) -> None:
        """Background sync loop"""
        while self._sync_enabled:
            try:
                # Perform sync
                self.sync_all()

                # Wait for next sync or stop event
                if self._stop_event.wait(timeout=self.sync_interval):
                    break  # Stop event was set

            except Exception as e:
                logger.error(f"Background sync error: {e}")
                if self._on_error:
                    self._on_error(e)

                # Wait a bit before retry
                if self._stop_event.wait(timeout=60):
                    break

    def sync_all(self) -> Dict[DataCategory, Dict[str, Any]]:
        """
        Sync all enabled categories

        Returns:
            Dictionary mapping categories to sync results
        """
        categories = self._enabled_categories or list(DataCategory)
        results = {}

        for category in categories:
            try:
                result = self.sync_category(category)
                results[category] = result
            except Exception as e:
                logger.error(f"Failed to sync {category.value}: {e}")
                results[category] = {"error": str(e)}

        if self._on_sync_complete:
            self._on_sync_complete(results)

        return results

    def sync_category(self, category: DataCategory) -> Dict[str, Any]:
        """
        Sync a specific data category

        Args:
            category: Category to sync

        Returns:
            Sync results
        """
        logger.info(f"Syncing {category.value}")

        # Update sync state
        state = self.db.get_sync_state(category)
        state.status = SyncStatus.SYNCING
        self.db.update_sync_state(state)

        try:
            # Get pending local changes
            local_changes = self.db.get_pending_changes(category, limit=self.MAX_BATCH_SIZE)

            # Perform bidirectional sync
            remote_changes, push_response = self.protocol.sync(
                category=category,
                local_changes=local_changes,
                since=state.last_pull,
            )

            # Detect conflicts
            conflicts = self._detect_and_handle_conflicts(
                category, local_changes, remote_changes
            )

            # Apply remote changes (non-conflicting)
            applied_count = self._apply_remote_changes(category, remote_changes, conflicts)

            # Mark local changes as synced
            for change in local_changes:
                self.db.mark_change_synced(change.change_id)

            # Update sync state
            now = datetime.utcnow()
            state.last_sync = now
            state.last_pull = now
            state.last_push = now
            state.pending_changes = len(self.db.get_pending_changes(category, limit=1000))
            state.conflicts = len(self.db.get_unresolved_conflicts(category))
            state.status = SyncStatus.CONFLICT if state.conflicts > 0 else SyncStatus.IDLE
            state.error_message = None
            self.db.update_sync_state(state)

            logger.info(
                f"Sync complete for {category.value}: "
                f"pushed={len(local_changes)}, pulled={applied_count}, conflicts={len(conflicts)}"
            )

            return {
                "success": True,
                "pushed": len(local_changes),
                "pulled": applied_count,
                "conflicts": len(conflicts),
                "timestamp": now.isoformat(),
            }

        except Exception as e:
            logger.error(f"Sync failed for {category.value}: {e}")

            # Update sync state with error
            state.status = SyncStatus.ERROR
            state.error_message = str(e)
            self.db.update_sync_state(state)

            return {
                "success": False,
                "error": str(e),
            }

    def _detect_and_handle_conflicts(
        self,
        category: DataCategory,
        local_changes: List[SyncChange],
        remote_changes: List[Dict[str, Any]],
    ) -> List[SyncConflict]:
        """Detect and optionally resolve conflicts"""
        # Convert to format for conflict detection
        local_dict = [c.to_dict() for c in local_changes]
        conflicts = self.protocol.detect_conflicts(local_dict, remote_changes)

        for conflict in conflicts:
            conflict.category = category
            self.db.add_conflict(conflict)

            if self.auto_resolve_conflicts:
                self._resolve_conflict(conflict, self.conflict_strategy)
            elif self._on_conflict:
                self._on_conflict(conflict)

        return conflicts

    def _resolve_conflict(
        self,
        conflict: SyncConflict,
        resolution: ConflictResolution,
    ) -> None:
        """Resolve a conflict using the given strategy"""
        try:
            # Send resolution to server
            self.protocol.resolve_conflict(conflict, resolution)

            # Mark as resolved locally
            self.db.resolve_conflict(conflict.conflict_id, resolution)

            logger.info(f"Resolved conflict {conflict.conflict_id} with {resolution.value}")
        except Exception as e:
            logger.error(f"Failed to resolve conflict {conflict.conflict_id}: {e}")

    def _apply_remote_changes(
        self,
        category: DataCategory,
        remote_changes: List[Dict[str, Any]],
        conflicts: List[SyncConflict],
    ) -> int:
        """Apply non-conflicting remote changes"""
        conflict_ids = {c.item_id for c in conflicts}
        applied_count = 0

        for change in remote_changes:
            item_id = change.get("item_id")
            if item_id in conflict_ids:
                continue  # Skip conflicting changes

            try:
                self._apply_change(category, change)
                applied_count += 1
            except Exception as e:
                logger.error(f"Failed to apply change {item_id}: {e}")

        return applied_count

    def _apply_change(self, category: DataCategory, change: Dict[str, Any]) -> None:
        """Apply a single change to local database"""
        operation = change.get("operation", "update")
        item_id = change["item_id"]
        data = change.get("data", {})

        if category == DataCategory.CONVERSATIONS:
            if operation == "delete":
                self.db.delete_conversation(item_id)
            else:
                self.db.save_conversation(
                    conversation_id=item_id,
                    title=data.get("title", ""),
                    messages=data.get("messages", []),
                    model=data.get("model", ""),
                    metadata=data.get("metadata", {}),
                    version=change.get("version", 1),
                )
        # TODO: Add handlers for other categories

    # ========== Manual Sync Operations ==========

    def push_now(self, category: DataCategory) -> Dict[str, Any]:
        """Immediately push pending changes for a category"""
        local_changes = self.db.get_pending_changes(category)
        if not local_changes:
            return {"success": True, "pushed": 0, "message": "No changes to push"}

        try:
            response = self.protocol.push_changes(category, local_changes)
            for change in local_changes:
                self.db.mark_change_synced(change.change_id)

            return {
                "success": True,
                "pushed": len(local_changes),
                "response": response,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def pull_now(self, category: DataCategory) -> Dict[str, Any]:
        """Immediately pull remote changes for a category"""
        state = self.db.get_sync_state(category)

        try:
            remote_changes = self.protocol.pull_and_decrypt_changes(
                category,
                since=state.last_pull,
            )

            applied_count = self._apply_remote_changes(category, remote_changes, [])

            state.last_pull = datetime.utcnow()
            self.db.update_sync_state(state)

            return {
                "success": True,
                "pulled": applied_count,
                "total": len(remote_changes),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ========== Offline Queue ==========

    def queue_change(
        self,
        category: DataCategory,
        operation: str,
        item_id: str,
        data: Dict[str, Any],
    ) -> str:
        """
        Add a change to the offline queue

        Args:
            category: Data category
            operation: Operation type (create, update, delete)
            item_id: Item identifier
            data: Item data

        Returns:
            Change ID
        """
        change = SyncChange(
            category=category,
            operation=operation,
            item_id=item_id,
            data=data,
            version=data.get("version", 1),
        )
        self.db.add_to_queue(change)
        logger.debug(f"Queued {operation} for {category.value}/{item_id}")
        return change.change_id

    def get_queue_status(self) -> Dict[DataCategory, int]:
        """Get count of pending changes per category"""
        status = {}
        for category in DataCategory:
            pending = self.db.get_pending_changes(category, limit=10000)
            status[category] = len(pending)
        return status

    # ========== Conflict Management ==========

    def get_conflicts(
        self, category: Optional[DataCategory] = None
    ) -> List[SyncConflict]:
        """Get unresolved conflicts"""
        return self.db.get_unresolved_conflicts(category)

    def resolve_conflict_manually(
        self,
        conflict_id: str,
        resolution: ConflictResolution,
    ) -> bool:
        """
        Manually resolve a conflict

        Args:
            conflict_id: Conflict identifier
            resolution: Resolution strategy

        Returns:
            True if successful
        """
        conflicts = self.db.get_unresolved_conflicts()
        conflict = next((c for c in conflicts if c.conflict_id == conflict_id), None)

        if not conflict:
            return False

        self._resolve_conflict(conflict, resolution)
        return True

    # ========== Configuration ==========

    def set_selective_sync(self, categories: Optional[List[DataCategory]]) -> None:
        """
        Set which categories to sync

        Args:
            categories: List of categories to sync, or None for all
        """
        self._enabled_categories = categories
        logger.info(f"Selective sync updated: {categories}")

    def set_conflict_strategy(self, strategy: ConflictResolution) -> None:
        """Set default conflict resolution strategy"""
        self.conflict_strategy = strategy

    def enable_auto_resolve(self, enabled: bool = True) -> None:
        """Enable or disable automatic conflict resolution"""
        self.auto_resolve_conflicts = enabled

    # ========== Callbacks ==========

    def on_sync_complete(self, callback: Callable) -> None:
        """Register callback for sync completion"""
        self._on_sync_complete = callback

    def on_conflict(self, callback: Callable) -> None:
        """Register callback for conflict detection"""
        self._on_conflict = callback

    def on_error(self, callback: Callable) -> None:
        """Register callback for sync errors"""
        self._on_error = callback

    # ========== Status and Info ==========

    def get_sync_status(self) -> Dict[str, Any]:
        """Get overall sync status"""
        states = self.db.get_all_sync_states()
        devices = self.db.list_devices()

        return {
            "device_id": self.device_info.device_id,
            "device_name": self.device_info.device_name,
            "background_sync_enabled": self._sync_enabled,
            "categories": {
                category.value: state.to_dict()
                for category, state in states.items()
            },
            "devices": [d.to_dict() for d in devices],
            "pending_changes": self.get_queue_status(),
        }

    def get_device_list(self) -> List[DeviceInfo]:
        """Get list of all synced devices"""
        try:
            return self.protocol.list_devices()
        except Exception as e:
            logger.error(f"Failed to get device list: {e}")
            return self.db.list_devices()

    def ping_server(self) -> Dict[str, Any]:
        """Check server connectivity"""
        return self.protocol.ping()

    # ========== Cleanup ==========

    def close(self) -> None:
        """Close sync client and cleanup resources"""
        self.stop_background_sync()
        self.protocol.close()
        logger.info("SyncClient closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
