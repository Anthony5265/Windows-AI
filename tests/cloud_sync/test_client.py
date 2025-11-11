"""
Tests for Windows-AI Cloud Sync client module
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from windows_ai.cloud_sync.client import SyncClient
from windows_ai.cloud_sync.models import (
    DataCategory,
    SyncChange,
    SyncConflict,
    ConflictResolution,
    DeviceInfo,
)


@pytest.fixture
def temp_sync_client():
    """Fixture providing temporary sync client"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_sync.db"

        # Mock the protocol to avoid network calls
        with patch('windows_ai.cloud_sync.client.SyncProtocol'):
            client = SyncClient(
                db_path=db_path,
                server_url="http://localhost:8765",
                password="test_password",
                device_name="Test Device",
                sync_interval=60,
            )
            yield client
            client.close()


class TestSyncClient:
    """Test suite for SyncClient class"""

    def test_client_initialization(self, temp_sync_client):
        """Test sync client is initialized correctly"""
        assert temp_sync_client.device_info is not None
        assert temp_sync_client.device_info.device_name == "Test Device"
        assert temp_sync_client.sync_interval == 60
        assert not temp_sync_client._sync_enabled

    def test_device_info_creation(self, temp_sync_client):
        """Test device info is created with correct platform info"""
        device = temp_sync_client.device_info
        assert device.device_id is not None
        assert device.device_name == "Test Device"
        assert device.platform != ""
        assert device.is_active

    def test_queue_change(self, temp_sync_client):
        """Test queueing changes for offline sync"""
        change_id = temp_sync_client.queue_change(
            category=DataCategory.CONVERSATIONS,
            operation="create",
            item_id="conv_123",
            data={"title": "Test Conversation", "messages": []},
        )

        assert change_id is not None

        # Verify change is in queue
        status = temp_sync_client.get_queue_status()
        assert status[DataCategory.CONVERSATIONS] == 1

    def test_get_queue_status(self, temp_sync_client):
        """Test getting queue status"""
        # Add changes to queue
        temp_sync_client.queue_change(
            DataCategory.CONVERSATIONS, "create", "conv_1", {"title": "Conv 1"}
        )
        temp_sync_client.queue_change(
            DataCategory.CONVERSATIONS, "update", "conv_2", {"title": "Conv 2"}
        )
        temp_sync_client.queue_change(
            DataCategory.SETTINGS, "update", "setting_1", {"value": 123}
        )

        status = temp_sync_client.get_queue_status()

        assert status[DataCategory.CONVERSATIONS] == 2
        assert status[DataCategory.SETTINGS] == 1
        assert status[DataCategory.AUTOMATIONS] == 0

    def test_set_selective_sync(self, temp_sync_client):
        """Test setting selective sync categories"""
        categories = [DataCategory.CONVERSATIONS, DataCategory.SETTINGS]
        temp_sync_client.set_selective_sync(categories)

        assert temp_sync_client._enabled_categories == categories

        # Set to None for all categories
        temp_sync_client.set_selective_sync(None)
        assert temp_sync_client._enabled_categories is None

    def test_set_conflict_strategy(self, temp_sync_client):
        """Test setting conflict resolution strategy"""
        temp_sync_client.set_conflict_strategy(ConflictResolution.CLIENT_WINS)
        assert temp_sync_client.conflict_strategy == ConflictResolution.CLIENT_WINS

        temp_sync_client.set_conflict_strategy(ConflictResolution.SERVER_WINS)
        assert temp_sync_client.conflict_strategy == ConflictResolution.SERVER_WINS

    def test_enable_auto_resolve(self, temp_sync_client):
        """Test enabling auto-resolve for conflicts"""
        assert not temp_sync_client.auto_resolve_conflicts

        temp_sync_client.enable_auto_resolve(True)
        assert temp_sync_client.auto_resolve_conflicts

        temp_sync_client.enable_auto_resolve(False)
        assert not temp_sync_client.auto_resolve_conflicts

    def test_get_sync_status(self, temp_sync_client):
        """Test getting overall sync status"""
        status = temp_sync_client.get_sync_status()

        assert "device_id" in status
        assert "device_name" in status
        assert status["device_name"] == "Test Device"
        assert "background_sync_enabled" in status
        assert "categories" in status
        assert "pending_changes" in status

    def test_callbacks_registration(self, temp_sync_client):
        """Test registering callbacks"""
        on_sync_complete_called = False
        on_conflict_called = False
        on_error_called = False

        def on_sync_complete(results):
            nonlocal on_sync_complete_called
            on_sync_complete_called = True

        def on_conflict(conflict):
            nonlocal on_conflict_called
            on_conflict_called = True

        def on_error(error):
            nonlocal on_error_called
            on_error_called = True

        temp_sync_client.on_sync_complete(on_sync_complete)
        temp_sync_client.on_conflict(on_conflict)
        temp_sync_client.on_error(on_error)

        assert temp_sync_client._on_sync_complete is not None
        assert temp_sync_client._on_conflict is not None
        assert temp_sync_client._on_error is not None

    def test_start_stop_background_sync(self, temp_sync_client):
        """Test starting and stopping background sync"""
        assert not temp_sync_client._sync_enabled

        # Mock the sync_all method to avoid actual syncing
        temp_sync_client.sync_all = Mock(return_value={})

        temp_sync_client.start_background_sync()
        assert temp_sync_client._sync_enabled
        assert temp_sync_client._sync_thread is not None

        temp_sync_client.stop_background_sync()
        assert not temp_sync_client._sync_enabled

    def test_get_conflicts(self, temp_sync_client):
        """Test getting conflicts"""
        # Add a conflict to the database
        conflict = SyncConflict(
            category=DataCategory.CONVERSATIONS,
            item_id="conv_conflict",
            local_version=1,
            remote_version=2,
        )
        temp_sync_client.db.add_conflict(conflict)

        # Get conflicts
        conflicts = temp_sync_client.get_conflicts()
        assert len(conflicts) == 1
        assert conflicts[0].item_id == "conv_conflict"

        # Get conflicts for specific category
        conv_conflicts = temp_sync_client.get_conflicts(DataCategory.CONVERSATIONS)
        assert len(conv_conflicts) == 1

        settings_conflicts = temp_sync_client.get_conflicts(DataCategory.SETTINGS)
        assert len(settings_conflicts) == 0

    def test_context_manager(self):
        """Test sync client as context manager"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_sync.db"

            with patch('windows_ai.cloud_sync.client.SyncProtocol'):
                with SyncClient(
                    db_path=db_path,
                    server_url="http://localhost:8765",
                    password="test_password",
                ) as client:
                    assert client is not None
                    assert not client._sync_enabled

                # Client should be closed after exiting context
                # (can't easily verify this without checking internal state)


@pytest.mark.integration
class TestSyncClientIntegration:
    """Integration tests for SyncClient (requires mocking network)"""

    @patch('windows_ai.cloud_sync.protocol.SyncProtocol')
    def test_sync_category_success(self, mock_protocol_class):
        """Test successful sync of a category"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_sync.db"

            # Setup mock protocol
            mock_protocol = Mock()
            mock_protocol.sync.return_value = ([], {})
            mock_protocol.detect_conflicts.return_value = []
            mock_protocol_class.return_value = mock_protocol

            client = SyncClient(
                db_path=db_path,
                server_url="http://localhost:8765",
                password="test_password",
            )

            # Queue a change
            client.queue_change(
                DataCategory.CONVERSATIONS,
                "create",
                "conv_test",
                {"title": "Test"},
            )

            # Sync
            result = client.sync_category(DataCategory.CONVERSATIONS)

            assert result["success"]
            assert "pushed" in result
            assert "pulled" in result

            client.close()

    @patch('windows_ai.cloud_sync.protocol.SyncProtocol')
    def test_push_now(self, mock_protocol_class):
        """Test immediate push of changes"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_sync.db"

            mock_protocol = Mock()
            mock_protocol.push_changes.return_value = {"success": True}
            mock_protocol_class.return_value = mock_protocol

            client = SyncClient(
                db_path=db_path,
                server_url="http://localhost:8765",
                password="test_password",
            )

            # Queue a change
            client.queue_change(
                DataCategory.CONVERSATIONS,
                "create",
                "conv_push",
                {"title": "Push Test"},
            )

            # Push
            result = client.push_now(DataCategory.CONVERSATIONS)

            assert result["success"]
            assert result["pushed"] == 1

            client.close()

    @patch('windows_ai.cloud_sync.protocol.SyncProtocol')
    def test_pull_now(self, mock_protocol_class):
        """Test immediate pull of changes"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_sync.db"

            mock_protocol = Mock()
            mock_protocol.pull_and_decrypt_changes.return_value = []
            mock_protocol_class.return_value = mock_protocol

            client = SyncClient(
                db_path=db_path,
                server_url="http://localhost:8765",
                password="test_password",
            )

            # Pull
            result = client.pull_now(DataCategory.CONVERSATIONS)

            assert result["success"]
            assert "pulled" in result

            client.close()
