"""
Compatibility snapshot module for legacy imports (from installer import snapshot).

This module provides a thin wrapper over the modern SnapshotManager in
windows_ai.rollback.snapshot_manager and also preserves a minimal API used by
older code and tests:

- create_snapshot()
- record_service(name)
- record_firewall_rule(name)
- restore()
- CONFIG_DIR, SNAPSHOT_FILE, SNAPSHOT_LOG

The lightweight record/restore helpers manipulate a small JSON file to track
services and firewall rules for restoration. The create/restore functions also
invoke the SnapshotManager to create and restore system-level snapshots when
available.
"""
from __future__ import annotations

from pathlib import Path
import json
import logging
import shutil
import subprocess
from typing import List

try:
    from windows_ai.rollback.snapshot_manager import SnapshotManager
except Exception:  # pragma: no cover - fallback if rollback module is unavailable
    SnapshotManager = None  # type: ignore

logger = logging.getLogger(__name__)

# Default locations (can be monkeypatched in tests)
CONFIG_DIR: Path = Path.home() / ".windows_ai"
SNAPSHOT_FILE: Path = CONFIG_DIR / "snapshot.json"
SNAPSHOT_LOG: Path = CONFIG_DIR / "snapshot.log"


def _ensure_dirs() -> None:
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:  # pragma: no cover - filesystem issues
        logger.warning(f"Failed to create config dir {CONFIG_DIR}: {e}")


def _write_log(message: str) -> None:
    try:
        _ensure_dirs()
        with SNAPSHOT_LOG.open("a", encoding="utf-8") as f:
            f.write(message + "\n")
    except Exception:  # pragma: no cover - best-effort logging
        pass


def _load_snapshot_data() -> dict:
    if SNAPSHOT_FILE.exists():
        try:
            return json.loads(SNAPSHOT_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {"services": [], "firewall_rules": []}
    return {"services": [], "firewall_rules": []}


def _save_snapshot_data(data: dict) -> None:
    _ensure_dirs()
    SNAPSHOT_FILE.write_text(json.dumps(data), encoding="utf-8")


def create_snapshot() -> None:
    """Create a lightweight snapshot record and invoke SnapshotManager if available."""
    # Initialize the lightweight record file
    data = {"services": [], "firewall_rules": []}
    _save_snapshot_data(data)

    # Create a full snapshot via SnapshotManager if available
    try:
        if SnapshotManager is not None:
            mgr = SnapshotManager()
            # Avoid heavy imports for version; default to "dev"
            version = "dev"
            try:
                # Only import version; avoid bringing in full orchestrator
                from windows_ai import __version__ as _ver  # type: ignore

                version = _ver or version
            except Exception:
                pass

            mgr.create_snapshot(version=version, snapshot_type="manual")
    except Exception as e:  # pragma: no cover - best-effort fallback
        logger.warning(f"SnapshotManager.create_snapshot failed: {e}")


def record_service(name: str) -> None:
    data = _load_snapshot_data()
    services: List[str] = list(dict.fromkeys(data.get("services", [])))
    if name not in services:
        services.append(name)
    data["services"] = services
    _save_snapshot_data(data)


def record_firewall_rule(name: str) -> None:
    data = _load_snapshot_data()
    rules: List[str] = list(dict.fromkeys(data.get("firewall_rules", [])))
    if name not in rules:
        rules.append(name)
    data["firewall_rules"] = rules
    _save_snapshot_data(data)


def restore() -> None:
    """Restore services and firewall rules, then attempt SnapshotManager restore.

    Behavior:
    - If nssm is missing, log a warning and skip service removal.
    - If pwsh is missing, log a warning and skip firewall rule removal.
    - Always remove the lightweight SNAPSHOT_FILE at the end.
    - If SnapshotManager is available and snapshots exist, restore the most
      recent snapshot as a best-effort action.
    """
    data = _load_snapshot_data()

    # Remove services via nssm
    nssm = shutil.which("nssm")
    if data.get("services"):
        if not nssm:
            _write_log("nssm not found; cannot remove services")
        else:
            for svc in data["services"]:
                try:
                    subprocess.run([nssm, "remove", svc, "confirm"], check=False)
                except Exception:  # pragma: no cover - best-effort
                    pass

    # Remove firewall rules via PowerShell
    pwsh = shutil.which("pwsh")
    if data.get("firewall_rules"):
        if not pwsh:
            _write_log("pwsh not found; cannot remove firewall rules")
        else:
            try:
                # Build one command that removes all rules
                cmds = "; ".join(
                    [f"Remove-NetFirewallRule -DisplayName '{r}'" for r in data["firewall_rules"]]
                )
                subprocess.run([pwsh, "-Command", cmds], check=False)
            except Exception:  # pragma: no cover - best-effort
                pass

    # Best-effort restore via SnapshotManager (restore most recent)
    try:
        if SnapshotManager is not None:
            mgr = SnapshotManager()
            snapshots = mgr.get_all_snapshots()
            if snapshots:
                # Sort by created_at descending
                snapshots.sort(key=lambda s: s.created_at, reverse=True)
                mgr.restore_from_snapshot(snapshots[0].snapshot_id)
    except Exception as e:  # pragma: no cover - best-effort
        logger.warning(f"SnapshotManager.restore failed: {e}")

    # Cleanup lightweight snapshot file
    try:
        if SNAPSHOT_FILE.exists():
            SNAPSHOT_FILE.unlink()
    except Exception:  # pragma: no cover
        pass
