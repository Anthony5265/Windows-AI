"""Lightweight watchdog stub.

Periodically checks for the presence of critical files and emits status logs.
Extend with real health checks (HTTP pings, process supervision) as needed.
"""

from __future__ import annotations

import time
from pathlib import Path

CHECK_INTERVAL_SECONDS = 30
REQUIRED_PATHS = [
    Path("windows_ai/main.py"),
    Path("update-server/server.py"),
    Path("update-server/manifest.json"),
]


def check_once() -> bool:
    missing = [str(path) for path in REQUIRED_PATHS if not path.exists()]
    if missing:
        print(f"[watchdog] missing paths: {', '.join(missing)}")
        return False
    print("[watchdog] all required assets present")
    return True


def main() -> None:
    while True:
        check_once()
        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
