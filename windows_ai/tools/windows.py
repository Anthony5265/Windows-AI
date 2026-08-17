"""Windows-native built-in tools with safe read-only defaults."""
from __future__ import annotations

import os
import platform
import subprocess
from pathlib import Path
from typing import Any, Mapping

from .models import ToolDefinition, ToolPermission


def system_info(_: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python": platform.python_version(),
        "hostname": platform.node(),
        "cwd": os.getcwd(),
    }


def list_directory(arguments: Mapping[str, Any]) -> list[dict[str, Any]]:
    path = Path(str(arguments.get("path", "."))).expanduser().resolve()
    if not path.is_dir():
        raise NotADirectoryError(str(path))
    return [
        {"name": item.name, "path": str(item), "type": "directory" if item.is_dir() else "file"}
        for item in sorted(path.iterdir(), key=lambda value: (not value.is_dir(), value.name.lower()))
    ]


def run_powershell(arguments: Mapping[str, Any]) -> dict[str, Any]:
    command = str(arguments.get("command", "")).strip()
    if not command:
        raise ValueError("command is required")
    completed = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
        capture_output=True,
        text=True,
        timeout=float(arguments.get("timeout", 30)),
        check=False,
    )
    return {"returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr}


def definitions() -> list[ToolDefinition]:
    return [
        ToolDefinition(
            name="windows.system_info",
            description="Return basic information about the Windows host.",
            handler=system_info,
            permissions=frozenset({ToolPermission.READ}),
            metadata={"platform": "windows"},
        ),
        ToolDefinition(
            name="windows.list_directory",
            description="List entries in a directory without modifying it.",
            handler=list_directory,
            input_schema={"type": "object", "properties": {"path": {"type": "string"}}},
            permissions=frozenset({ToolPermission.READ}),
            metadata={"platform": "windows"},
        ),
        ToolDefinition(
            name="windows.powershell",
            description="Execute an approved PowerShell command through the Windows-AI permission boundary.",
            handler=run_powershell,
            input_schema={"type": "object", "required": ["command"], "properties": {"command": {"type": "string"}, "timeout": {"type": "number"}}},
            permissions=frozenset({ToolPermission.EXECUTE, ToolPermission.SYSTEM}),
            risk_level="high",
            metadata={"platform": "windows", "requires_approval": True},
        ),
    ]


__all__ = ["definitions"]
