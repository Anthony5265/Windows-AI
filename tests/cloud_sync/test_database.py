"""
Tests for Windows-AI Cloud Sync database module
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from windows_ai.cloud_sync.database import SyncDatabase
from windows_ai.cloud_sync.models import (
    DataCategory,
    SyncState,
    SyncStatus,
    SyncChange,
    SyncConflict,
    ConflictResolution,
    DeviceInfo,
)


@pytest.fixture
def temp_db():
    """Fixture providing temporary test database"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_sync.db"
        db = SyncDatabase(db_path)
        yield db


class TestSyncDatabase:
    """Test suite for SyncDatabase class"""

    def test_database_initialization(self, temp_db):
        """Test database is created and initialized"""
        assert temp_db.db_path.exists()

    def test_register_device(self, temp_db):
        """Test device registration"""
        device = DeviceInfo(
            device_name="Test Device",
            platform="Windows",
            os_version="11",
            app_version="1.0.0",
        )

        temp_db.register_device(device)

        retrieved = temp_db.get_device(device.device_id)
        assert retrieved is not None
        assert retrieved.device_name == "Test Device"
        assert retrieved.platform == "Windows"

    def test_list_devices(self, temp_db):
        """Test listing devices"""
        # Register multiple devices
        device1 = DeviceInfo(device_name="Device 1", platform="Windows", os_version="11", app_version="1.0.0")
        device2 = DeviceInfo(device_name="Device 2", platform="Linux", os_version="Ubuntu 22.04", app_version="1.0.0", is_active=False)
        device3 = DeviceInfo(device_name="Device 3", platform="macOS", os_version="13", app_version="1.0.0")

        temp_db.register_device(device1)
        temp_db.register_device(device2)
        temp_db.register_device(device3)

        # List active devices
        active_devices = temp_db.list_devices(active_only=True)
        assert len(active_devices) == 2
        assert all(d.is_active for d in active_devices)

        # List all devices
        all_devices = temp_db.list_devices(active_only=False)
        assert len(all_devices) == 3

    def test_sync_state_management(self, temp_db):
        """Test sync state get and update"""
        category = DataCategory.CONVERSATIONS

        # Get initial state
        state = temp_db.get_sync_state(category)
        assert state.category == category
        assert state.last_sync is None
        assert state.status == SyncStatus.IDLE

        # Update state
        now = datetime.utcnow()
        state.last_sync = now
        state.last_pull = now
        state.last_push = now
        state.pending_changes = 5
        state.conflicts = 2
        state.status = SyncStatus.SYNCING
        state.sync_version = 2

        temp_db.update_sync_state(state)

        # Retrieve updated state
        updated = temp_db.get_sync_state(category)
        assert updated.last_sync is not None
        assert updated.pending_changes == 5
        assert updated.conflicts == 2
        assert updated.status == SyncStatus.SYNCING
        assert updated.sync_version == 2

    def test_get_all_sync_states(self, temp_db):
        """Test getting all sync states"""
        states = temp_db.get_all_sync_states()

        assert isinstance(states, dict)
        assert len(states) == len(DataCategory)
        assert all(isinstance(k, DataCategory) for k in states.keys())
        assert all(isinstance(v, SyncState) for v in states.values())

    def test_add_to_queue(self, temp_db):
        """Test adding changes to sync queue"""
        change = SyncChange(
            category=DataCategory.CONVERSATIONS,
            operation="create",
            item_id="conv_123",
            data={"title": "Test Conversation"},
            version=1,
        )

        temp_db.add_to_queue(change)

        pending = temp_db.get_pending_changes(DataCategory.CONVERSATIONS)
        assert len(pending) == 1
        assert pending[0].item_id == "conv_123"
        assert pending[0].operation == "create"

    def test_get_pending_changes(self, temp_db):
        """Test getting pending changes with filters"""
        # Add changes for different categories
        for i in range(5):
            change = SyncChange(
                category=DataCategory.CONVERSATIONS,
                operation="update",
                item_id=f"conv_{i}",
                data={"title": f"Conv {i}"},
            )
            temp_db.add_to_queue(change)

        for i in range(3):
            change = SyncChange(
                category=DataCategory.SETTINGS,
                operation="update",
                item_id=f"setting_{i}",
                data={"value": i},
            )
            temp_db.add_to_queue(change)

        # Get pending for specific category
        conv_pending = temp_db.get_pending_changes(DataCategory.CONVERSATIONS)
        assert len(conv_pending) == 5

        settings_pending = temp_db.get_pending_changes(DataCategory.SETTINGS)
        assert len(settings_pending) == 3

        # Get all pending with limit
        all_pending = temp_db.get_pending_changes(limit=5)
        assert len(all_pending) == 5

    def test_mark_change_synced(self, temp_db):
        """Test marking changes as synced"""
        change = SyncChange(
            category=DataCategory.CONVERSATIONS,
            operation="create",
            item_id="conv_test",
            data={"title": "Test"},
        )
        temp_db.add_to_queue(change)

        # Verify it's pending
        pending = temp_db.get_pending_changes(DataCategory.CONVERSATIONS)
        assert len(pending) == 1

        # Mark as synced
        temp_db.mark_change_synced(change.change_id)

        # Verify it's no longer pending
        pending = temp_db.get_pending_changes(DataCategory.CONVERSATIONS)
        assert len(pending) == 0

    def test_increment_retry_count(self, temp_db):
        """Test incrementing retry count for failed syncs"""
        change = SyncChange(
            category=DataCategory.CONVERSATIONS,
            operation="create",
            item_id="conv_retry",
            data={"title": "Retry Test"},
        )
        temp_db.add_to_queue(change)

        # Increment retry count
        temp_db.increment_retry_count(change.change_id, "Connection timeout")

        # Verify retry count increased
        pending = temp_db.get_pending_changes(DataCategory.CONVERSATIONS)
        assert len(pending) == 1
        assert pending[0].retry_count == 1
        assert pending[0].last_error == "Connection timeout"

    def test_clear_synced_changes(self, temp_db):
        """Test clearing old synced changes"""
        # Add and sync some old changes
        for i in range(10):
            change = SyncChange(
                category=DataCategory.CONVERSATIONS,
                operation="update",
                item_id=f"conv_{i}",
                data={"title": f"Conv {i}"},
                timestamp=datetime.utcnow() - timedelta(days=8),  # 8 days old
            )
            temp_db.add_to_queue(change)
            temp_db.mark_change_synced(change.change_id)

        # Add recent synced change
        recent_change = SyncChange(
            category=DataCategory.CONVERSATIONS,
            operation="update",
            item_id="conv_recent",
            data={"title": "Recent"},
        )
        temp_db.add_to_queue(recent_change)
        temp_db.mark_change_synced(recent_change.change_id)

        # Clear old synced changes (older than 7 days)
        cleared = temp_db.clear_synced_changes(older_than_days=7)
        assert cleared == 10  # Should clear 10 old changes

    def test_add_conflict(self, temp_db):
        """Test adding conflict"""
        conflict = SyncConflict(
            category=DataCategory.CONVERSATIONS,
            item_id="conv_conflict",
            local_version=1,
            remote_version=2,
            local_data={"title": "Local Title"},
            remote_data={"title": "Remote Title"},
        )

        temp_db.add_conflict(conflict)

        conflicts = temp_db.get_unresolved_conflicts(DataCategory.CONVERSATIONS)
        assert len(conflicts) == 1
        assert conflicts[0].item_id == "conv_conflict"

    def test_get_unresolved_conflicts(self, temp_db):
        """Test getting unresolved conflicts"""
        # Add conflicts for different categories
        conflict1 = SyncConflict(
            category=DataCategory.CONVERSATIONS,
            item_id="conv_1",
            local_version=1,
            remote_version=2,
        )
        conflict2 = SyncConflict(
            category=DataCategory.CONVERSATIONS,
            item_id="conv_2",
            local_version=1,
            remote_version=2,
        )
        conflict3 = SyncConflict(
            category=DataCategory.SETTINGS,
            item_id="setting_1",
            local_version=1,
            remote_version=2,
        )

        temp_db.add_conflict(conflict1)
        temp_db.add_conflict(conflict2)
        temp_db.add_conflict(conflict3)

        # Get conflicts for specific category
        conv_conflicts = temp_db.get_unresolved_conflicts(DataCategory.CONVERSATIONS)
        assert len(conv_conflicts) == 2

        # Get all conflicts
        all_conflicts = temp_db.get_unresolved_conflicts()
        assert len(all_conflicts) == 3

    def test_resolve_conflict(self, temp_db):
        """Test resolving conflict"""
        conflict = SyncConflict(
            category=DataCategory.CONVERSATIONS,
            item_id="conv_resolve",
            local_version=1,
            remote_version=2,
        )
        temp_db.add_conflict(conflict)

        # Verify it's unresolved
        unresolved = temp_db.get_unresolved_conflicts()
        assert len(unresolved) == 1

        # Resolve conflict
        temp_db.resolve_conflict(conflict.conflict_id, ConflictResolution.SERVER_WINS)

        # Verify it's resolved
        unresolved = temp_db.get_unresolved_conflicts()
        assert len(unresolved) == 0

    def test_save_conversation(self, temp_db):
        """Test saving conversation"""
        temp_db.save_conversation(
            conversation_id="conv_123",
            title="Test Conversation",
            messages=[
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi!"},
            ],
            model="gpt-4",
            metadata={"tags": ["test"]},
            version=1,
        )

        conv = temp_db.get_conversation("conv_123")
        assert conv is not None
        assert conv["title"] == "Test Conversation"
        assert len(conv["messages"]) == 2
        assert conv["model"] == "gpt-4"

    def test_get_conversation(self, temp_db):
        """Test getting conversation by ID"""
        temp_db.save_conversation(
            conversation_id="conv_get",
            title="Get Test",
            messages=[],
            model="gpt-4",
        )

        conv = temp_db.get_conversation("conv_get")
        assert conv is not None
        assert conv["conversation_id"] == "conv_get"

        # Non-existent conversation
        missing = temp_db.get_conversation("non_existent")
        assert missing is None

    def test_list_conversations(self, temp_db):
        """Test listing conversations"""
        # Add multiple conversations
        for i in range(10):
            temp_db.save_conversation(
                conversation_id=f"conv_{i}",
                title=f"Conversation {i}",
                messages=[],
                model="gpt-4",
            )

        # List all
        conversations = temp_db.list_conversations(limit=100)
        assert len(conversations) == 10

        # List with limit
        conversations = temp_db.list_conversations(limit=5)
        assert len(conversations) == 5

    def test_list_conversations_since(self, temp_db):
        """Test listing conversations updated since a timestamp"""
        # Add old conversations
        for i in range(5):
            temp_db.save_conversation(
                conversation_id=f"old_{i}",
                title=f"Old {i}",
                messages=[],
                model="gpt-4",
            )

        import time
        time.sleep(0.1)  # Small delay
        cutoff = datetime.utcnow()
        time.sleep(0.1)

        # Add new conversations
        for i in range(3):
            temp_db.save_conversation(
                conversation_id=f"new_{i}",
                title=f"New {i}",
                messages=[],
                model="gpt-4",
            )

        # List only new conversations
        new_conversations = temp_db.list_conversations(since=cutoff)
        assert len(new_conversations) == 3

    def test_delete_conversation(self, temp_db):
        """Test soft-deleting conversation"""
        temp_db.save_conversation(
            conversation_id="conv_delete",
            title="To Delete",
            messages=[],
            model="gpt-4",
        )

        # Verify it exists
        conv = temp_db.get_conversation("conv_delete")
        assert conv is not None

        # Delete it
        temp_db.delete_conversation("conv_delete")

        # Verify it's gone
        conv = temp_db.get_conversation("conv_delete")
        assert conv is None

    def test_conversation_version_tracking(self, temp_db):
        """Test conversation version tracking"""
        # Save initial version
        temp_db.save_conversation(
            conversation_id="conv_version",
            title="Version Test",
            messages=[{"role": "user", "content": "v1"}],
            model="gpt-4",
            version=1,
        )

        conv = temp_db.get_conversation("conv_version")
        assert conv["version"] == 1

        # Update with new version
        temp_db.save_conversation(
            conversation_id="conv_version",
            title="Version Test Updated",
            messages=[{"role": "user", "content": "v2"}],
            model="gpt-4",
            version=2,
        )

        conv = temp_db.get_conversation("conv_version")
        assert conv["version"] == 2
        assert conv["title"] == "Version Test Updated"
