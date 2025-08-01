"""Build standalone Windows executables using PyInstaller.

This helper script packages either the command line interface or the
Tkinter-based GUI into a single-file executable. It relies on
``pyinstaller`` being installed in the current Python environment.

Usage (from repository root)::

    python scripts/package_windows.py cli
    python scripts/package_windows.py gui

The generated executable will be placed in the ``dist`` directory.
Run this script on a Windows machine to create Windows ``.exe`` files.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build(target: str) -> None:
    """Run PyInstaller for the requested target."""
    if target == "cli":
        entry = ROOT / "installer" / "cli.py"
        name = "windows_ai_cli"
        extra = []
    else:  # gui
        entry = ROOT / "installer" / "gui" / "__main__.py"
        name = "windows_ai_gui"
        extra = ["--noconsole"]

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--name",
        name,
        *extra,
        str(entry),
    ]
    subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Package the Windows AI tools")
    parser.add_argument(
        "target",
        choices=["cli", "gui"],
        help="Which interface to package",
    )
    args = parser.parse_args()

    build(args.target)
    print("\nBuild complete. Check the 'dist' directory for the executable.")


if __name__ == "__main__":
    main()
