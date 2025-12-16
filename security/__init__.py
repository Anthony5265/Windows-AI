"""
Security Module Compatibility Shim
Re-exports security components from windows_ai.security for test compatibility.
"""

from windows_ai.security import (
    PermissionManager,
    AuditLogger,
    encrypt,
    decrypt,
    ThreatMonitor,
    RollbackManager,
)

__all__ = [
    "PermissionManager",
    "AuditLogger",
    "encrypt",
    "decrypt",
    "ThreatMonitor",
    "RollbackManager",
]
