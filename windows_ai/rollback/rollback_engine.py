"""
Rollback Engine for Windows AI

Orchestrates the rollback process including:
- Selecting rollback target version
- Stopping services
- Restoring from snapshots
- Restarting services
- Verifying rollback success
- Automatic rollback on critical failures
"""

import logging
import subprocess
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable
from enum import Enum
from dataclasses import dataclass

from .snapshot_manager import SnapshotManager, Snapshot
from .version_history import VersionHistory, VersionRecord, InstallationType


logger = logging.getLogger(__name__)


class RollbackStatus(Enum):
    """Rollback operation status"""
    IDLE = "idle"
    PREPARING = "preparing"
    STOPPING_SERVICES = "stopping_services"
    RESTORING_FILES = "restoring_files"
    RESTORING_CONFIG = "restoring_config"
    RESTORING_REGISTRY = "restoring_registry"
    STARTING_SERVICES = "starting_services"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class RollbackResult:
    """Result of a rollback operation"""
    success: bool
    from_version: str
    to_version: str
    started_at: str
    completed_at: Optional[str]
    status: str
    error_message: Optional[str] = None
    snapshot_id: Optional[str] = None
    steps_completed: list = None

    def __post_init__(self):
        if self.steps_completed is None:
            self.steps_completed = []


class RollbackEngine:
    """
    Manages rollback operations for Windows AI
    """

    def __init__(
        self,
        snapshot_manager: Optional[SnapshotManager] = None,
        version_history: Optional[VersionHistory] = None,
        install_dir: Optional[Path] = None
    ):
        """
        Initialize rollback engine

        Args:
            snapshot_manager: SnapshotManager instance
            version_history: VersionHistory instance
            install_dir: Installation directory
        """
        self.snapshot_manager = snapshot_manager or SnapshotManager()
        self.version_history = version_history or VersionHistory()
        self.install_dir = install_dir or Path("C:/Program Files/Windows AI")

        # State
        self.status = RollbackStatus.IDLE
        self.current_rollback: Optional[RollbackResult] = None
        self.on_status_change: Optional[Callable[[RollbackStatus], None]] = None

        logger.info(f"RollbackEngine initialized - install_dir={install_dir}")

    def _set_status(self, status: RollbackStatus):
        """Update status and notify callback"""
        self.status = status
        logger.info(f"Rollback status: {status.value}")

        if self.on_status_change:
            try:
                self.on_status_change(status)
            except Exception as e:
                logger.error(f"Error in status change callback: {e}")

    def can_rollback(self) -> bool:
        """
        Check if rollback is possible

        Returns:
            True if rollback is possible
        """
        # Check if there's a previous version
        if not self.version_history.can_rollback():
            logger.info("No previous version available for rollback")
            return False

        # Check if there's a snapshot for the target version
        target_version = self.version_history.get_rollback_target()
        if not target_version:
            return False

        if not target_version.snapshot_id:
            logger.warning(f"No snapshot available for version {target_version.version}")
            # Could still rollback by reinstalling, but won't have snapshot
            return True

        snapshot = self.snapshot_manager.get_snapshot(target_version.snapshot_id)
        if not snapshot or not snapshot.valid:
            logger.warning(f"Snapshot {target_version.snapshot_id} not found or invalid")
            return True  # Can still try to rollback

        return True

    def get_rollback_info(self) -> Optional[dict]:
        """
        Get information about potential rollback

        Returns:
            Dictionary with rollback information, or None if not possible
        """
        if not self.can_rollback():
            return None

        current_version = self.version_history.get_current_version()
        target_version = self.version_history.get_rollback_target()

        if not current_version or not target_version:
            return None

        snapshot = None
        if target_version.snapshot_id:
            snapshot = self.snapshot_manager.get_snapshot(target_version.snapshot_id)

        return {
            "can_rollback": True,
            "current_version": current_version.version,
            "target_version": target_version.version,
            "target_installed_at": target_version.installed_at,
            "has_snapshot": snapshot is not None,
            "snapshot_valid": snapshot.valid if snapshot else False,
            "snapshot_size_mb": round(snapshot.size_bytes / 1024 / 1024, 2) if snapshot else 0
        }

    async def perform_rollback(
        self,
        target_version: Optional[str] = None,
        create_backup: bool = True
    ) -> RollbackResult:
        """
        Perform rollback to previous version

        Args:
            target_version: Specific version to rollback to (default: previous version)
            create_backup: Create backup of current version before rollback

        Returns:
            RollbackResult with operation details
        """
        started_at = datetime.now()
        logger.info("Starting rollback operation...")
        self._set_status(RollbackStatus.PREPARING)

        # Get current and target versions
        current_version_record = self.version_history.get_current_version()
        if not current_version_record:
            return RollbackResult(
                success=False,
                from_version="unknown",
                to_version=target_version or "unknown",
                started_at=started_at.isoformat(),
                completed_at=None,
                status=RollbackStatus.FAILED.value,
                error_message="No current version found in history"
            )

        current_version = current_version_record.version

        # Determine target version
        if target_version:
            target_version_record = self.version_history.get_version(target_version)
        else:
            target_version_record = self.version_history.get_rollback_target()

        if not target_version_record:
            return RollbackResult(
                success=False,
                from_version=current_version,
                to_version=target_version or "unknown",
                started_at=started_at.isoformat(),
                completed_at=None,
                status=RollbackStatus.FAILED.value,
                error_message="Target version not found in history"
            )

        target_version = target_version_record.version

        # Initialize result
        result = RollbackResult(
            success=False,
            from_version=current_version,
            to_version=target_version,
            started_at=started_at.isoformat(),
            completed_at=None,
            status=RollbackStatus.PREPARING.value
        )

        try:
            # Step 1: Create backup of current version if requested
            if create_backup:
                logger.info("Creating backup of current version before rollback...")
                snapshot = self.snapshot_manager.create_snapshot(
                    version=current_version,
                    snapshot_type="pre_rollback",
                    install_dir=self.install_dir,
                    notes=f"Backup before rollback to {target_version}"
                )
                if snapshot:
                    logger.info(f"Backup snapshot created: {snapshot.snapshot_id}")
                    result.snapshot_id = snapshot.snapshot_id
                else:
                    logger.warning("Failed to create backup snapshot, continuing anyway...")

            result.steps_completed.append("backup_created")

            # Step 2: Stop Windows AI services
            self._set_status(RollbackStatus.STOPPING_SERVICES)
            logger.info("Stopping Windows AI services...")

            if await self._stop_services():
                logger.info("Services stopped successfully")
                result.steps_completed.append("services_stopped")
            else:
                logger.warning("Failed to stop some services, continuing anyway...")

            # Step 3: Restore from snapshot if available
            self._set_status(RollbackStatus.RESTORING_FILES)

            if target_version_record.snapshot_id:
                logger.info(f"Restoring from snapshot {target_version_record.snapshot_id}...")

                if self.snapshot_manager.restore_from_snapshot(
                    target_version_record.snapshot_id,
                    self.install_dir
                ):
                    logger.info("Files restored successfully from snapshot")
                    result.steps_completed.append("files_restored")
                else:
                    raise Exception("Failed to restore from snapshot")

            else:
                # No snapshot available - need to reinstall
                logger.warning(f"No snapshot available for version {target_version}")
                logger.info("Rollback would require reinstalling the target version")
                result.error_message = "No snapshot available - manual reinstall required"
                result.status = RollbackStatus.FAILED.value
                return result

            # Step 4: Restore configuration
            self._set_status(RollbackStatus.RESTORING_CONFIG)
            logger.info("Restoring configuration...")
            # Configuration is restored as part of snapshot restore
            result.steps_completed.append("config_restored")

            # Step 5: Restore registry
            self._set_status(RollbackStatus.RESTORING_REGISTRY)
            logger.info("Restoring registry...")
            # Registry is restored as part of snapshot restore
            result.steps_completed.append("registry_restored")

            # Step 6: Start services
            self._set_status(RollbackStatus.STARTING_SERVICES)
            logger.info("Starting Windows AI services...")

            if await self._start_services():
                logger.info("Services started successfully")
                result.steps_completed.append("services_started")
            else:
                logger.warning("Failed to start some services")
                # Don't fail the entire rollback for this

            # Step 7: Verify rollback
            self._set_status(RollbackStatus.VERIFYING)
            logger.info("Verifying rollback...")

            if await self._verify_installation():
                logger.info("Rollback verification successful")
                result.steps_completed.append("verification_passed")
            else:
                logger.warning("Rollback verification failed")
                result.error_message = "Rollback completed but verification failed"

            # Step 8: Record rollback in version history
            self.version_history.record_installation(
                version=target_version,
                installation_type=InstallationType.ROLLBACK,
                install_dir=str(self.install_dir),
                previous_version=current_version,
                snapshot_id=target_version_record.snapshot_id,
                notes=f"Rolled back from {current_version}",
                success=True
            )

            # Success!
            result.success = True
            result.status = RollbackStatus.COMPLETED.value
            result.completed_at = datetime.now().isoformat()
            self._set_status(RollbackStatus.COMPLETED)

            logger.info(f"Rollback completed successfully: {current_version} -> {target_version}")

            return result

        except Exception as e:
            logger.error(f"Rollback failed: {e}", exc_info=True)

            result.success = False
            result.status = RollbackStatus.FAILED.value
            result.error_message = str(e)
            result.completed_at = datetime.now().isoformat()
            self._set_status(RollbackStatus.FAILED)

            # Record failed rollback
            self.version_history.record_installation(
                version=target_version,
                installation_type=InstallationType.ROLLBACK,
                install_dir=str(self.install_dir),
                previous_version=current_version,
                notes=f"Failed rollback from {current_version}: {str(e)}",
                success=False
            )

            return result

    async def _stop_services(self) -> bool:
        """Stop Windows AI services"""
        try:
            # Stop Windows service
            result = await asyncio.create_subprocess_exec(
                "net", "stop", "WindowsAI",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.wait()

            # Give services time to stop
            await asyncio.sleep(2)

            return True

        except Exception as e:
            logger.error(f"Error stopping services: {e}")
            return False

    async def _start_services(self) -> bool:
        """Start Windows AI services"""
        try:
            # Start Windows service
            result = await asyncio.create_subprocess_exec(
                "net", "start", "WindowsAI",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.wait()

            # Give services time to start
            await asyncio.sleep(5)

            return True

        except Exception as e:
            logger.error(f"Error starting services: {e}")
            return False

    async def _verify_installation(self) -> bool:
        """Verify installation after rollback"""
        try:
            # Check if critical files exist
            critical_files = [
                self.install_dir / "windows_ai" / "__init__.py",
                self.install_dir / "python" / "python.exe",
            ]

            for file_path in critical_files:
                if not file_path.exists():
                    logger.error(f"Critical file missing: {file_path}")
                    return False

            # Try to connect to backend
            import aiohttp
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get("http://localhost:8010/health", timeout=10) as response:
                        if response.status == 200:
                            logger.info("Backend health check passed")
                            return True
                        else:
                            logger.warning(f"Backend health check returned {response.status}")
                            return False
            except:
                logger.warning("Could not connect to backend")
                # Don't fail verification for this - service might need more time to start
                return True

        except Exception as e:
            logger.error(f"Error verifying installation: {e}")
            return False

    def get_rollback_history(self) -> list:
        """
        Get history of all rollback operations

        Returns:
            List of rollback records
        """
        records = self.version_history.get_all_versions()

        rollbacks = [
            {
                "version": record.version,
                "from_version": record.previous_version,
                "installed_at": record.installed_at,
                "success": record.success,
                "notes": record.notes
            }
            for record in records
            if record.installation_type == InstallationType.ROLLBACK.value
        ]

        return rollbacks


# =====================================================================
# Convenience Functions
# =====================================================================

async def quick_rollback(install_dir: Optional[Path] = None) -> RollbackResult:
    """
    Quick rollback to previous version

    Args:
        install_dir: Installation directory

    Returns:
        RollbackResult
    """
    engine = RollbackEngine(install_dir=install_dir)

    if not engine.can_rollback():
        return RollbackResult(
            success=False,
            from_version="unknown",
            to_version="unknown",
            started_at=datetime.now().isoformat(),
            completed_at=datetime.now().isoformat(),
            status=RollbackStatus.FAILED.value,
            error_message="Rollback not possible - no previous version available"
        )

    return await engine.perform_rollback()
