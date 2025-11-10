"""
Windows AI Rollback System

Provides version rollback capabilities including:
- System state snapshots before updates
- Version history tracking
- One-click rollback to previous versions
- Automatic rollback on critical failures

Components:
- snapshot_manager: Creates and manages system snapshots
- version_history: Tracks installed versions and changes
- rollback_engine: Executes rollback operations
"""

from .snapshot_manager import SnapshotManager, Snapshot
from .version_history import VersionHistory, VersionRecord
from .rollback_engine import RollbackEngine, RollbackStatus

__all__ = [
    "SnapshotManager",
    "Snapshot",
    "VersionHistory",
    "VersionRecord",
    "RollbackEngine",
    "RollbackStatus",
]

__version__ = "1.0.0"
