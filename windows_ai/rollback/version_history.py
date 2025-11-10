"""
Version History Tracking for Windows AI

Maintains a history of all installed versions, including:
- Installation timestamps
- File locations
- Registry keys
- Configuration backups
- Rollback metadata
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum


logger = logging.getLogger(__name__)


class InstallationType(Enum):
    """Type of installation"""
    FRESH_INSTALL = "fresh_install"
    UPGRADE = "upgrade"
    DOWNGRADE = "downgrade"
    REINSTALL = "reinstall"
    ROLLBACK = "rollback"


@dataclass
class VersionRecord:
    """Record of an installed version"""
    version: str
    installed_at: str  # ISO 8601 timestamp
    installation_type: str
    install_dir: str
    previous_version: Optional[str] = None
    installer_path: Optional[str] = None
    snapshot_id: Optional[str] = None
    files_count: int = 0
    registry_keys: List[str] = None
    notes: str = ""
    success: bool = True

    def __post_init__(self):
        if self.registry_keys is None:
            self.registry_keys = []

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "VersionRecord":
        """Create from dictionary"""
        return cls(**data)

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "VersionRecord":
        """Create from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)


class VersionHistory:
    """
    Manages version history for Windows AI installations
    """

    def __init__(self, history_file: Optional[Path] = None):
        """
        Initialize version history

        Args:
            history_file: Path to history JSON file (default: %APPDATA%/WindowsAI/version_history.json)
        """
        if history_file is None:
            appdata = Path.home() / "AppData" / "Local" / "WindowsAI"
            appdata.mkdir(parents=True, exist_ok=True)
            history_file = appdata / "version_history.json"

        self.history_file = history_file
        self.records: List[VersionRecord] = []

        # Load existing history
        self._load_history()

        logger.info(f"VersionHistory initialized - file={history_file}, records={len(self.records)}")

    def _load_history(self):
        """Load history from file"""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r') as f:
                    data = json.load(f)

                self.records = [
                    VersionRecord.from_dict(record)
                    for record in data.get("records", [])
                ]

                logger.info(f"Loaded {len(self.records)} version records")
            else:
                logger.info("No existing history file found, starting fresh")
                self.records = []

        except Exception as e:
            logger.error(f"Error loading version history: {e}")
            self.records = []

    def _save_history(self):
        """Save history to file"""
        try:
            data = {
                "version": "1.0",
                "last_updated": datetime.now().isoformat(),
                "records": [record.to_dict() for record in self.records]
            }

            # Write to file
            with open(self.history_file, 'w') as f:
                json.dump(data, f, indent=2)

            logger.info(f"Saved version history ({len(self.records)} records)")

        except Exception as e:
            logger.error(f"Error saving version history: {e}")
            raise

    def add_record(self, record: VersionRecord):
        """
        Add a version record to history

        Args:
            record: VersionRecord to add
        """
        self.records.append(record)
        self._save_history()
        logger.info(f"Added version record: {record.version} ({record.installation_type})")

    def record_installation(
        self,
        version: str,
        installation_type: InstallationType,
        install_dir: str,
        previous_version: Optional[str] = None,
        installer_path: Optional[str] = None,
        snapshot_id: Optional[str] = None,
        files_count: int = 0,
        registry_keys: Optional[List[str]] = None,
        notes: str = "",
        success: bool = True
    ) -> VersionRecord:
        """
        Record a new installation

        Args:
            version: Version being installed
            installation_type: Type of installation
            install_dir: Installation directory
            previous_version: Previous version (for upgrades)
            installer_path: Path to installer
            snapshot_id: Associated snapshot ID
            files_count: Number of files installed
            registry_keys: Registry keys created/modified
            notes: Additional notes
            success: Whether installation was successful

        Returns:
            Created VersionRecord
        """
        record = VersionRecord(
            version=version,
            installed_at=datetime.now().isoformat(),
            installation_type=installation_type.value,
            install_dir=install_dir,
            previous_version=previous_version,
            installer_path=installer_path,
            snapshot_id=snapshot_id,
            files_count=files_count,
            registry_keys=registry_keys or [],
            notes=notes,
            success=success
        )

        self.add_record(record)
        return record

    def get_current_version(self) -> Optional[VersionRecord]:
        """
        Get the current (most recent successful) version

        Returns:
            Most recent successful VersionRecord, or None
        """
        successful_records = [r for r in self.records if r.success]

        if not successful_records:
            return None

        # Return most recent
        successful_records.sort(key=lambda r: r.installed_at, reverse=True)
        return successful_records[0]

    def get_version(self, version: str) -> Optional[VersionRecord]:
        """
        Get record for specific version

        Args:
            version: Version to find

        Returns:
            VersionRecord for that version, or None
        """
        for record in reversed(self.records):
            if record.version == version and record.success:
                return record

        return None

    def get_previous_version(self, current_version: Optional[str] = None) -> Optional[VersionRecord]:
        """
        Get previous version before specified version

        Args:
            current_version: Version to go back from (default: current version)

        Returns:
            Previous VersionRecord, or None
        """
        if current_version is None:
            current = self.get_current_version()
            if current is None:
                return None
            current_version = current.version

        # Find index of current version
        current_idx = None
        for i, record in enumerate(reversed(self.records)):
            if record.version == current_version and record.success:
                current_idx = len(self.records) - 1 - i
                break

        if current_idx is None:
            return None

        # Find previous successful version
        for i in range(current_idx - 1, -1, -1):
            if self.records[i].success:
                return self.records[i]

        return None

    def get_all_versions(self) -> List[VersionRecord]:
        """
        Get all version records

        Returns:
            List of all VersionRecords
        """
        return self.records.copy()

    def get_successful_versions(self) -> List[VersionRecord]:
        """
        Get all successful version records

        Returns:
            List of successful VersionRecords
        """
        return [r for r in self.records if r.success]

    def get_version_history_summary(self) -> List[Dict[str, Any]]:
        """
        Get summary of version history

        Returns:
            List of version summaries
        """
        summaries = []

        for record in reversed(self.records):
            summaries.append({
                "version": record.version,
                "installed_at": record.installed_at,
                "installation_type": record.installation_type,
                "previous_version": record.previous_version,
                "success": record.success,
                "has_snapshot": record.snapshot_id is not None
            })

        return summaries

    def can_rollback(self) -> bool:
        """
        Check if rollback is possible

        Returns:
            True if there is a previous version to rollback to
        """
        return self.get_previous_version() is not None

    def get_rollback_target(self) -> Optional[VersionRecord]:
        """
        Get the version that would be rolled back to

        Returns:
            VersionRecord to rollback to, or None
        """
        return self.get_previous_version()

    def clear_history(self):
        """Clear all version history"""
        self.records = []
        self._save_history()
        logger.info("Version history cleared")

    def export_history(self, export_path: Path):
        """
        Export version history to file

        Args:
            export_path: Path to export to
        """
        try:
            data = {
                "version": "1.0",
                "exported_at": datetime.now().isoformat(),
                "total_records": len(self.records),
                "records": [record.to_dict() for record in self.records]
            }

            with open(export_path, 'w') as f:
                json.dump(data, f, indent=2)

            logger.info(f"Exported version history to {export_path}")

        except Exception as e:
            logger.error(f"Error exporting version history: {e}")
            raise

    def import_history(self, import_path: Path, merge: bool = False):
        """
        Import version history from file

        Args:
            import_path: Path to import from
            merge: If True, merge with existing history; if False, replace
        """
        try:
            with open(import_path, 'r') as f:
                data = json.load(f)

            imported_records = [
                VersionRecord.from_dict(record)
                for record in data.get("records", [])
            ]

            if merge:
                # Merge with existing records
                self.records.extend(imported_records)
                # Sort by installed_at
                self.records.sort(key=lambda r: r.installed_at)
            else:
                # Replace existing records
                self.records = imported_records

            self._save_history()
            logger.info(f"Imported {len(imported_records)} version records (merge={merge})")

        except Exception as e:
            logger.error(f"Error importing version history: {e}")
            raise

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about version history

        Returns:
            Dictionary with statistics
        """
        total_records = len(self.records)
        successful_records = len([r for r in self.records if r.success])
        failed_records = total_records - successful_records

        # Count by installation type
        by_type = {}
        for record in self.records:
            by_type[record.installation_type] = by_type.get(record.installation_type, 0) + 1

        # Get unique versions
        unique_versions = set(r.version for r in self.records if r.success)

        # Get date range
        if self.records:
            dates = sorted(r.installed_at for r in self.records)
            first_install = dates[0]
            last_install = dates[-1]
        else:
            first_install = None
            last_install = None

        return {
            "total_records": total_records,
            "successful_installations": successful_records,
            "failed_installations": failed_records,
            "unique_versions": len(unique_versions),
            "versions": sorted(unique_versions, reverse=True),
            "installation_types": by_type,
            "first_install": first_install,
            "last_install": last_install,
            "can_rollback": self.can_rollback(),
            "current_version": self.get_current_version().version if self.get_current_version() else None
        }
