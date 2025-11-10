"""
Rollback Tests for Windows AI

Tests rollback functionality:
- Rollback to previous version
- Snapshot creation and restoration
- Version history tracking
- Automatic rollback on critical failures
"""

import pytest
import asyncio
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from windows_ai.rollback import SnapshotManager, VersionHistory, RollbackEngine
from windows_ai.rollback.version_history import InstallationType


class TestSnapshotManager:
    """Test snapshot creation and management"""

    @pytest.fixture
    def snapshot_manager(self, tmp_path):
        """Create snapshot manager with temp directory"""
        return SnapshotManager(snapshots_dir=tmp_path / "snapshots")

    @pytest.fixture
    def test_install_dir(self, tmp_path):
        """Create test installation directory"""
        install_dir = tmp_path / "test_install"
        install_dir.mkdir()

        # Create some test files
        (install_dir / "test_file1.txt").write_text("test data 1")
        (install_dir / "test_file2.txt").write_text("test data 2")

        subdir = install_dir / "subdir"
        subdir.mkdir()
        (subdir / "test_file3.txt").write_text("test data 3")

        return install_dir

    def test_create_snapshot(self, snapshot_manager, test_install_dir):
        """Test creating a snapshot"""
        snapshot = snapshot_manager.create_snapshot(
            version="0.5.0",
            snapshot_type="pre_update",
            install_dir=test_install_dir,
            notes="Test snapshot"
        )

        assert snapshot is not None
        assert snapshot.version == "0.5.0"
        assert snapshot.snapshot_type == "pre_update"
        assert snapshot.files_backed_up > 0

    def test_snapshot_metadata_saved(self, snapshot_manager, test_install_dir):
        """Test that snapshot metadata is saved"""
        snapshot = snapshot_manager.create_snapshot(
            version="0.5.0",
            install_dir=test_install_dir
        )

        # Create new snapshot manager instance
        new_manager = SnapshotManager(snapshots_dir=snapshot_manager.snapshots_dir)

        # Verify snapshot exists
        loaded_snapshot = new_manager.get_snapshot(snapshot.snapshot_id)
        assert loaded_snapshot is not None
        assert loaded_snapshot.snapshot_id == snapshot.snapshot_id

    def test_restore_from_snapshot(self, snapshot_manager, test_install_dir, tmp_path):
        """Test restoring from a snapshot"""
        # Create snapshot
        snapshot = snapshot_manager.create_snapshot(
            version="0.5.0",
            install_dir=test_install_dir
        )

        # Modify original files
        (test_install_dir / "test_file1.txt").write_text("modified data")
        (test_install_dir / "new_file.txt").write_text("new file")

        # Create restore target directory
        restore_dir = tmp_path / "restored"

        # Restore snapshot
        success = snapshot_manager.restore_from_snapshot(
            snapshot.snapshot_id,
            restore_dir
        )

        assert success
        assert restore_dir.exists()
        assert (restore_dir / "test_file1.txt").read_text() == "test data 1"

    def test_delete_snapshot(self, snapshot_manager, test_install_dir):
        """Test deleting a snapshot"""
        snapshot = snapshot_manager.create_snapshot(
            version="0.5.0",
            install_dir=test_install_dir
        )

        snapshot_id = snapshot.snapshot_id

        # Delete snapshot
        success = snapshot_manager.delete_snapshot(snapshot_id)
        assert success

        # Verify snapshot is gone
        assert snapshot_manager.get_snapshot(snapshot_id) is None

    def test_cleanup_old_snapshots(self, snapshot_manager, test_install_dir):
        """Test cleaning up old snapshots"""
        # Create multiple snapshots
        for i in range(10):
            snapshot_manager.create_snapshot(
                version=f"0.{i}.0",
                install_dir=test_install_dir
            )

        # Keep only 3
        snapshot_manager.cleanup_old_snapshots(keep_count=3)

        # Verify only 3 remain
        assert len(snapshot_manager.get_all_snapshots()) == 3


class TestVersionHistory:
    """Test version history tracking"""

    @pytest.fixture
    def version_history(self, tmp_path):
        """Create version history with temp file"""
        return VersionHistory(history_file=tmp_path / "version_history.json")

    def test_record_installation(self, version_history):
        """Test recording an installation"""
        record = version_history.record_installation(
            version="0.5.0",
            installation_type=InstallationType.FRESH_INSTALL,
            install_dir="C:\\Program Files\\Windows AI",
            notes="Test installation"
        )

        assert record.version == "0.5.0"
        assert record.installation_type == InstallationType.FRESH_INSTALL.value

    def test_get_current_version(self, version_history):
        """Test getting current version"""
        version_history.record_installation(
            version="0.4.0",
            installation_type=InstallationType.FRESH_INSTALL,
            install_dir="C:\\Program Files\\Windows AI"
        )

        version_history.record_installation(
            version="0.5.0",
            installation_type=InstallationType.UPGRADE,
            install_dir="C:\\Program Files\\Windows AI",
            previous_version="0.4.0"
        )

        current = version_history.get_current_version()
        assert current is not None
        assert current.version == "0.5.0"

    def test_get_previous_version(self, version_history):
        """Test getting previous version"""
        version_history.record_installation(
            version="0.4.0",
            installation_type=InstallationType.FRESH_INSTALL,
            install_dir="C:\\Program Files\\Windows AI"
        )

        version_history.record_installation(
            version="0.5.0",
            installation_type=InstallationType.UPGRADE,
            install_dir="C:\\Program Files\\Windows AI",
            previous_version="0.4.0"
        )

        previous = version_history.get_previous_version()
        assert previous is not None
        assert previous.version == "0.4.0"

    def test_can_rollback(self, version_history):
        """Test checking if rollback is possible"""
        # No versions yet
        assert not version_history.can_rollback()

        # Only one version
        version_history.record_installation(
            version="0.5.0",
            installation_type=InstallationType.FRESH_INSTALL,
            install_dir="C:\\Program Files\\Windows AI"
        )
        assert not version_history.can_rollback()

        # Two versions
        version_history.record_installation(
            version="0.6.0",
            installation_type=InstallationType.UPGRADE,
            install_dir="C:\\Program Files\\Windows AI",
            previous_version="0.5.0"
        )
        assert version_history.can_rollback()


class TestRollbackEngine:
    """Test rollback engine"""

    @pytest.fixture
    def setup_rollback_test(self, tmp_path):
        """Set up complete rollback test environment"""
        # Create snapshot manager
        snapshot_manager = SnapshotManager(snapshots_dir=tmp_path / "snapshots")

        # Create version history
        version_history = VersionHistory(history_file=tmp_path / "version_history.json")

        # Create test install directory
        install_dir = tmp_path / "install"
        install_dir.mkdir()
        (install_dir / "test_file.txt").write_text("version 0.4.0")

        # Record version 0.4.0
        snapshot1 = snapshot_manager.create_snapshot(
            version="0.4.0",
            install_dir=install_dir
        )

        version_history.record_installation(
            version="0.4.0",
            installation_type=InstallationType.FRESH_INSTALL,
            install_dir=str(install_dir),
            snapshot_id=snapshot1.snapshot_id
        )

        # Simulate upgrade to 0.5.0
        (install_dir / "test_file.txt").write_text("version 0.5.0")

        snapshot2 = snapshot_manager.create_snapshot(
            version="0.5.0",
            install_dir=install_dir
        )

        version_history.record_installation(
            version="0.5.0",
            installation_type=InstallationType.UPGRADE,
            install_dir=str(install_dir),
            previous_version="0.4.0",
            snapshot_id=snapshot2.snapshot_id
        )

        return {
            "snapshot_manager": snapshot_manager,
            "version_history": version_history,
            "install_dir": install_dir
        }

    def test_can_rollback(self, setup_rollback_test):
        """Test checking if rollback is possible"""
        engine = RollbackEngine(
            snapshot_manager=setup_rollback_test["snapshot_manager"],
            version_history=setup_rollback_test["version_history"],
            install_dir=setup_rollback_test["install_dir"]
        )

        assert engine.can_rollback()

    def test_get_rollback_info(self, setup_rollback_test):
        """Test getting rollback information"""
        engine = RollbackEngine(
            snapshot_manager=setup_rollback_test["snapshot_manager"],
            version_history=setup_rollback_test["version_history"],
            install_dir=setup_rollback_test["install_dir"]
        )

        info = engine.get_rollback_info()
        assert info is not None
        assert info["current_version"] == "0.5.0"
        assert info["target_version"] == "0.4.0"
        assert info["can_rollback"]

    @pytest.mark.asyncio
    async def test_perform_rollback(self, setup_rollback_test):
        """Test performing a rollback"""
        engine = RollbackEngine(
            snapshot_manager=setup_rollback_test["snapshot_manager"],
            version_history=setup_rollback_test["version_history"],
            install_dir=setup_rollback_test["install_dir"]
        )

        # Note: This is a simplified test that won't actually stop/start services
        # Full integration test would require running on actual Windows system

        pytest.skip("Full rollback test requires Windows environment with services")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
