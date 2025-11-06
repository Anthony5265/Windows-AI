from __future__ import annotations

"""Simple persistence for system change snapshots.

The installer records system modifications such as created services or
firewall rules so that they can be undone during uninstallation or rollback.
This module manages the snapshot file and exposes helpers used by both the
PowerShell scripts and the GUI.
"""

from dataclasses import dataclass, field
from pathlib import Path
import json
import subprocess
import logging
import shutil
from typing import Set

# Location of the snapshot record
CONFIG_DIR = Path.home() / ".windows_ai"
SNAPSHOT_FILE = CONFIG_DIR / "snapshot.json"
SNAPSHOT_LOG = CONFIG_DIR / "snapshot.log"

logger = logging.getLogger(__name__)


@dataclass
class Snapshot:
    """Representation of recorded system changes."""

    services: Set[str] = field(default_factory=set)
    firewall_rules: Set[str] = field(default_factory=set)

    # ------------------------------------------------------------------
    def to_dict(self) -> dict[str, list[str]]:
        return {
            "services": sorted(self.services),
            "firewall_rules": sorted(self.firewall_rules),
        }

    @classmethod
    def from_dict(cls, data: dict[str, list[str]]) -> "Snapshot":
        return cls(set(data.get("services", [])), set(data.get("firewall_rules", [])))

    def save(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        SNAPSHOT_FILE.write_text(json.dumps(self.to_dict(), indent=2))

    @classmethod
    def load(cls) -> "Snapshot":
        if SNAPSHOT_FILE.exists():
            try:
                data = json.loads(SNAPSHOT_FILE.read_text())
                return cls.from_dict(data)
            except Exception:
                return cls()
        return cls()

    def clear(self) -> None:
        if SNAPSHOT_FILE.exists():
            SNAPSHOT_FILE.unlink()


# ----------------------------------------------------------------------
# Helper API

def create_snapshot() -> Snapshot:
    """Create a new empty snapshot on disk and return it."""

    snap = Snapshot()
    snap.save()
    return snap


def record_service(name: str) -> None:
    """Record a newly created service."""

    snap = Snapshot.load()
    snap.services.add(name)
    snap.save()


def record_firewall_rule(name: str) -> None:
    """Record a firewall rule that should be removed on restore."""

    snap = Snapshot.load()
    snap.firewall_rules.add(name)
    snap.save()


def restore(snapshot: Snapshot | None = None) -> None:
    """Restore system changes recorded in *snapshot*.

    Each recorded service is removed using ``nssm`` and each firewall rule is
    removed via PowerShell's ``Remove-NetFirewallRule`` cmdlet.  Missing
    commands are ignored and failures do not raise errors so that restore can
    best-effort undo changes during uninstallation.
    """

    snap = snapshot or Snapshot.load()
    SNAPSHOT_LOG.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(SNAPSHOT_LOG, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
    try:
        nssm = shutil.which("nssm")
        pwsh = shutil.which("pwsh")
        if not nssm and snap.services:
            logger.warning("nssm not found; cannot remove services: %s", ", ".join(sorted(snap.services)))
        if not pwsh and snap.firewall_rules:
            logger.warning(
                "pwsh not found; cannot remove firewall rules: %s",
                ", ".join(sorted(snap.firewall_rules)),
            )
        if nssm:
            for service in snap.services:
                result = subprocess.run([nssm, "remove", service, "confirm"], check=False)
                if result.returncode == 0:
                    logger.info("Removed service %s", service)
                else:
                    logger.error("Failed to remove service %s (code %s)", service, result.returncode)
        if pwsh:
            for rule in snap.firewall_rules:
                cmd = f"Remove-NetFirewallRule -DisplayName '{rule}'"
                result = subprocess.run([pwsh, "-NoProfile", "-Command", cmd], check=False)
                if result.returncode == 0:
                    logger.info("Removed firewall rule %s", rule)
                else:
                    logger.error("Failed to remove firewall rule %s (code %s)", rule, result.returncode)
        snap.clear()
        logger.info("Snapshot restore complete")
    finally:
        logger.removeHandler(handler)


def load_snapshot() -> Snapshot:
    """Return the current snapshot without modifying it."""

    return Snapshot.load()


__all__ = [
    "Snapshot",
    "SNAPSHOT_FILE",
    "SNAPSHOT_LOG",
    "create_snapshot",
    "record_service",
    "record_firewall_rule",
    "restore",
    "load_snapshot",
]


if __name__ == "__main__":  # pragma: no cover - CLI helper
    import argparse

    parser = argparse.ArgumentParser(description="Manage Windows AI snapshots")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("create")

    rec = sub.add_parser("record")
    rec.add_argument("kind", choices=["service", "firewall"])
    rec.add_argument("name")

    sub.add_parser("restore")

    ns = parser.parse_args()
    if ns.cmd == "create":
        create_snapshot()
    elif ns.cmd == "record":
        if ns.kind == "service":
            record_service(ns.name)
        else:
            record_firewall_rule(ns.name)
    else:
        restore()
