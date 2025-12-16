"""
Snapshot Module Compatibility Shim
Re-exports snapshot utilities from windows_ai.snapshot for test compatibility.
"""

from windows_ai.snapshot import capture, rollback, remove, SNAPSHOT_DIR

__all__ = ["capture", "rollback", "remove", "SNAPSHOT_DIR"]
