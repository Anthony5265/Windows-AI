"""
Windows AI Update Client

Handles checking for updates, downloading updates, and coordinating installations.
Runs as a background service checking for updates periodically.
"""

import os
import json
import hashlib
import logging
import asyncio
import aiohttp
import aiofiles
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable
from enum import Enum
from dataclasses import dataclass, asdict

from .version_manager import VersionManager, Version


logger = logging.getLogger(__name__)


class UpdateStatus(Enum):
    """Update status states"""
    IDLE = "idle"
    CHECKING = "checking"
    AVAILABLE = "available"
    DOWNLOADING = "downloading"
    DOWNLOADED = "downloaded"
    INSTALLING = "installing"
    INSTALLED = "installed"
    ERROR = "error"
    UP_TO_DATE = "up_to_date"


@dataclass
class UpdateInfo:
    """Information about an available update"""
    version: str
    current_version: str
    release_date: str
    size: int
    download_url: str
    sha256: str
    critical: bool
    requires_restart: bool
    changelog: Dict[str, list]
    release_notes: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_release(cls, release: dict, current_version: str) -> "UpdateInfo":
        """Create from release manifest entry"""
        return cls(
            version=release["version"],
            current_version=current_version,
            release_date=release["releaseDate"],
            size=release["files"]["installer"]["size"],
            download_url=release["files"]["installer"]["url"],
            sha256=release["files"]["installer"]["sha256"],
            critical=release.get("critical", False),
            requires_restart=release.get("requiresRestart", True),
            changelog=release.get("changelog", {}),
            release_notes=release.get("releaseNotes", "")
        )


class UpdateClient:
    """
    Client for checking and downloading Windows AI updates
    """

    def __init__(
        self,
        current_version: str,
        update_server_url: str,
        download_dir: Optional[Path] = None,
        check_interval_hours: int = 6,
        channel: str = "stable",
        auto_download: bool = True
    ):
        """
        Initialize update client

        Args:
            current_version: Current application version
            update_server_url: Update server base URL
            download_dir: Directory for downloaded updates
            check_interval_hours: Hours between update checks
            channel: Release channel (stable, beta, alpha)
            auto_download: Automatically download updates when found
        """
        self.current_version = current_version
        self.update_server_url = update_server_url.rstrip('/')
        self.download_dir = download_dir or Path.home() / "AppData" / "Local" / "WindowsAI" / "updates"
        self.check_interval = timedelta(hours=check_interval_hours)
        self.channel = channel
        self.auto_download = auto_download

        # State
        self.status = UpdateStatus.IDLE
        self.available_update: Optional[UpdateInfo] = None
        self.download_progress: float = 0.0
        self.error_message: Optional[str] = None
        self.last_check: Optional[datetime] = None

        # Callbacks
        self.on_status_change: Optional[Callable[[UpdateStatus], None]] = None
        self.on_update_available: Optional[Callable[[UpdateInfo], None]] = None
        self.on_download_progress: Optional[Callable[[float], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None

        # Ensure download directory exists
        self.download_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"UpdateClient initialized - version={current_version}, channel={channel}")

    def _set_status(self, status: UpdateStatus):
        """Update status and notify callback"""
        self.status = status
        logger.info(f"Update status changed: {status.value}")

        if self.on_status_change:
            try:
                self.on_status_change(status)
            except Exception as e:
                logger.error(f"Error in status change callback: {e}")

    def _set_error(self, message: str):
        """Set error status and message"""
        self.error_message = message
        self._set_status(UpdateStatus.ERROR)
        logger.error(f"Update error: {message}")

        if self.on_error:
            try:
                self.on_error(message)
            except Exception as e:
                logger.error(f"Error in error callback: {e}")

    async def check_for_updates(self) -> Optional[UpdateInfo]:
        """
        Check for available updates

        Returns:
            UpdateInfo if update available, None otherwise
        """
        logger.info("Checking for updates...")
        self._set_status(UpdateStatus.CHECKING)

        try:
            # Fetch manifest
            manifest = await self._fetch_manifest()
            if not manifest:
                self._set_error("Failed to fetch update manifest")
                return None

            # Find latest version in channel
            latest_release = self._find_latest_release(manifest)
            if not latest_release:
                logger.info(f"No releases found in {self.channel} channel")
                self._set_status(UpdateStatus.UP_TO_DATE)
                self.last_check = datetime.now()
                return None

            latest_version = latest_release["version"]

            # Compare versions
            if VersionManager.is_newer(latest_version, self.current_version):
                logger.info(f"Update available: {self.current_version} -> {latest_version}")

                update_info = UpdateInfo.from_release(latest_release, self.current_version)
                self.available_update = update_info
                self._set_status(UpdateStatus.AVAILABLE)

                if self.on_update_available:
                    try:
                        self.on_update_available(update_info)
                    except Exception as e:
                        logger.error(f"Error in update available callback: {e}")

                # Auto-download if enabled
                if self.auto_download:
                    await self.download_update(update_info)

                self.last_check = datetime.now()
                return update_info

            else:
                logger.info(f"No updates available (current: {self.current_version}, latest: {latest_version})")
                self._set_status(UpdateStatus.UP_TO_DATE)
                self.last_check = datetime.now()
                return None

        except Exception as e:
            self._set_error(f"Error checking for updates: {str(e)}")
            logger.exception("Error checking for updates")
            return None

    async def _fetch_manifest(self) -> Optional[dict]:
        """Fetch update manifest from server"""
        manifest_url = f"{self.update_server_url}/manifest.json"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(manifest_url, timeout=30) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Failed to fetch manifest: HTTP {response.status}")
                        return None

        except asyncio.TimeoutError:
            logger.error("Timeout fetching manifest")
            return None
        except Exception as e:
            logger.error(f"Error fetching manifest: {e}")
            return None

    def _find_latest_release(self, manifest: dict) -> Optional[dict]:
        """Find latest release in configured channel"""
        releases = manifest.get("releases", [])

        # Filter by channel
        channel_releases = [
            r for r in releases
            if r.get("channel", "stable") == self.channel
        ]

        if not channel_releases:
            return None

        # Sort by version and get latest
        channel_releases.sort(
            key=lambda r: VersionManager.parse(r["version"]),
            reverse=True
        )

        return channel_releases[0]

    async def download_update(self, update_info: Optional[UpdateInfo] = None) -> Optional[Path]:
        """
        Download update installer

        Args:
            update_info: Update to download (uses available_update if not specified)

        Returns:
            Path to downloaded file, or None on error
        """
        if update_info is None:
            update_info = self.available_update

        if update_info is None:
            self._set_error("No update available to download")
            return None

        logger.info(f"Downloading update {update_info.version}...")
        self._set_status(UpdateStatus.DOWNLOADING)
        self.download_progress = 0.0

        try:
            # Determine download URL
            download_url = update_info.download_url
            if not download_url.startswith('http'):
                download_url = f"{self.update_server_url}{download_url}"

            # Download file
            output_path = self.download_dir / f"WindowsAI-Setup-{update_info.version}.exe"

            downloaded_size = 0
            total_size = update_info.size

            async with aiohttp.ClientSession() as session:
                async with session.get(download_url, timeout=600) as response:
                    if response.status != 200:
                        self._set_error(f"Download failed: HTTP {response.status}")
                        return None

                    # Download with progress tracking
                    async with aiofiles.open(output_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
                            downloaded_size += len(chunk)

                            # Update progress
                            if total_size > 0:
                                progress = (downloaded_size / total_size) * 100
                                self.download_progress = progress

                                if self.on_download_progress:
                                    try:
                                        self.on_download_progress(progress)
                                    except Exception as e:
                                        logger.error(f"Error in progress callback: {e}")

            # Verify checksum
            logger.info("Verifying download integrity...")
            if not await self._verify_checksum(output_path, update_info.sha256):
                self._set_error("Download verification failed - checksum mismatch")
                output_path.unlink(missing_ok=True)
                return None

            logger.info(f"Download complete: {output_path}")
            self._set_status(UpdateStatus.DOWNLOADED)
            return output_path

        except asyncio.TimeoutError:
            self._set_error("Download timeout")
            logger.error("Download timeout")
            return None
        except Exception as e:
            self._set_error(f"Download error: {str(e)}")
            logger.exception("Error downloading update")
            return None

    async def _verify_checksum(self, file_path: Path, expected_sha256: str) -> bool:
        """Verify file checksum"""
        try:
            sha256_hash = hashlib.sha256()

            async with aiofiles.open(file_path, 'rb') as f:
                while chunk := await f.read(8192):
                    sha256_hash.update(chunk)

            actual_sha256 = sha256_hash.hexdigest()

            if actual_sha256.lower() != expected_sha256.lower():
                logger.error(f"Checksum mismatch: expected={expected_sha256}, actual={actual_sha256}")
                return False

            logger.info("Checksum verified successfully")
            return True

        except Exception as e:
            logger.error(f"Error verifying checksum: {e}")
            return False

    async def install_update(self, installer_path: Optional[Path] = None) -> bool:
        """
        Install downloaded update

        Args:
            installer_path: Path to installer (auto-detected if not specified)

        Returns:
            True if installation started successfully
        """
        if installer_path is None and self.available_update:
            installer_path = self.download_dir / f"WindowsAI-Setup-{self.available_update.version}.exe"

        if installer_path is None or not installer_path.exists():
            self._set_error("Installer not found")
            return False

        logger.info(f"Installing update from {installer_path}...")
        self._set_status(UpdateStatus.INSTALLING)

        try:
            # Launch installer
            # Use silent install mode
            import subprocess

            process = await asyncio.create_subprocess_exec(
                str(installer_path),
                "/S",  # Silent install
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Wait for installer to start
            await asyncio.sleep(2)

            logger.info("Installer launched successfully")
            self._set_status(UpdateStatus.INSTALLED)

            # Note: The application will be closed/restarted by the installer
            return True

        except Exception as e:
            self._set_error(f"Installation error: {str(e)}")
            logger.exception("Error installing update")
            return False

    async def run_background_checker(self):
        """
        Run periodic update checks in background

        This is a long-running task that checks for updates at configured intervals.
        Should be run as an asyncio task.
        """
        logger.info("Starting background update checker...")

        while True:
            try:
                # Check if it's time to check for updates
                if self.last_check is None or datetime.now() - self.last_check >= self.check_interval:
                    await self.check_for_updates()

                # Sleep for 1 hour before checking again
                await asyncio.sleep(3600)

            except Exception as e:
                logger.error(f"Error in background update checker: {e}")
                await asyncio.sleep(3600)  # Sleep and retry

    def get_status_info(self) -> dict:
        """
        Get current status information

        Returns:
            Dictionary with current status, update info, progress, etc.
        """
        return {
            "status": self.status.value,
            "current_version": self.current_version,
            "channel": self.channel,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "available_update": self.available_update.to_dict() if self.available_update else None,
            "download_progress": self.download_progress,
            "error_message": self.error_message,
            "auto_download": self.auto_download
        }

    def clear_downloaded_updates(self):
        """Clear all downloaded update files"""
        try:
            for file in self.download_dir.glob("WindowsAI-Setup-*.exe"):
                file.unlink()
                logger.info(f"Deleted {file}")
        except Exception as e:
            logger.error(f"Error clearing downloads: {e}")


# =====================================================================
# Convenience Functions
# =====================================================================

async def check_for_updates_simple(
    current_version: str,
    update_server_url: str,
    channel: str = "stable"
) -> Optional[UpdateInfo]:
    """
    Simple one-shot update check

    Args:
        current_version: Current application version
        update_server_url: Update server URL
        channel: Release channel

    Returns:
        UpdateInfo if update available, None otherwise
    """
    client = UpdateClient(
        current_version=current_version,
        update_server_url=update_server_url,
        channel=channel,
        auto_download=False
    )

    return await client.check_for_updates()


async def download_update_simple(
    update_info: UpdateInfo,
    update_server_url: str,
    download_dir: Optional[Path] = None
) -> Optional[Path]:
    """
    Simple one-shot update download

    Args:
        update_info: Update information
        update_server_url: Update server URL
        download_dir: Download directory

    Returns:
        Path to downloaded file, or None on error
    """
    client = UpdateClient(
        current_version=update_info.current_version,
        update_server_url=update_server_url,
        download_dir=download_dir,
        auto_download=False
    )

    return await client.download_update(update_info)
