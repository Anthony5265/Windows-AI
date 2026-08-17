"""Windows-native capabilities exposed through the canonical tool layer.

All capabilities are deliberately routed through ToolRouter permissions rather
than being called directly by agents.
"""
from __future__ import annotations

import os
import platform
import subprocess
from pathlib import Path
from typing import Any, Mapping

from .models import ToolDefinition, ToolPermission


def _require_windows() -> None:
    if platform.system() != "Windows":
        raise RuntimeError("This capability requires Windows")


def list_processes(_: Mapping[str, Any]) -> list[dict[str, Any]]:
    _require_windows()
    result = subprocess.run(
        ["tasklist", "/FO", "CSV", "/NH"],
        capture_output=True,
        text=True,
        check=True,
        timeout=15,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    rows: list[dict[str, Any]] = []
    for line in result.stdout.splitlines():
        parts = [p.strip('"') for p in line.split('","')]
        if len(parts) >= 2:
            rows.append({"name": parts[0], "pid": parts[1], "memory": parts[4] if len(parts) > 4 else None})
    return rows


def launch_application(arguments: Mapping[str, Any]) -> dict[str, Any]:
    _require_windows()
    target = str(arguments.get("target") or "").strip()
    if not target:
        raise ValueError("target is required")
    # startfile delegates to Windows shell association without constructing a shell command.
    os.startfile(target)  # type: ignore[attr-defined]
    return {"launched": True, "target": target}


def open_path(arguments: Mapping[str, Any]) -> dict[str, Any]:
    _require_windows()
    raw = str(arguments.get("path") or "").strip()
    if not raw:
        raise ValueError("path is required")
    path = Path(raw).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(str(path))
    os.startfile(str(path))  # type: ignore[attr-defined]
    return {"opened": True, "path": str(path)}


def windows_tools() -> list[ToolDefinition]:
    return [
        ToolDefinition(
            name="windows.list_processes",
            description="List running Windows processes.",
            handler=list_processes,
            permissions=frozenset({ToolPermission.READ, ToolPermission.SYSTEM}),
            metadata={"category": "windows", "offline": True},
        ),
        ToolDefinition(
            name="windows.launch_application",
            description="Launch an approved application or Windows-associated target.",
            handler=launch_application,
            input_schema={"type": "object", "properties": {"target": {"type": "string"}}, "required": ["target"]},
            permissions=frozenset({ToolPermission.EXECUTE}),
            risk_level="medium",
            metadata={"category": "windows", "offline": True},
        ),
        ToolDefinition(
            name="windows.open_path",
            description="Open an existing file or directory with its Windows association.",
            handler=open_path,
            input_schema={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
            permissions=frozenset({ToolPermission.READ, ToolPermission.EXECUTE}),
            risk_level="medium",
            metadata={"category": "windows", "offline": True},
        ),
    ]
