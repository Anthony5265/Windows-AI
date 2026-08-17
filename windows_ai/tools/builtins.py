"""Safe, useful native tools exposed through the unified action layer."""
from __future__ import annotations

import os
import platform
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
    }


def list_directory(arguments: Mapping[str, Any]) -> list[dict[str, Any]]:
    path = Path(str(arguments.get("path") or ".")).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"Directory does not exist: {path}")
    if not path.is_dir():
        raise NotADirectoryError(str(path))
    return [
        {"name": item.name, "path": str(item), "type": "directory" if item.is_dir() else "file"}
        for item in sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    ]


def environment(arguments: Mapping[str, Any]) -> dict[str, Any]:
    names = arguments.get("names")
    if names is None:
        return {"count": len(os.environ), "variables": dict(os.environ)}
    return {str(name): os.environ.get(str(name)) for name in names}


def builtin_tools() -> list[ToolDefinition]:
    return [
        ToolDefinition(
            name="windows.system_info",
            description="Return basic host and Python runtime information.",
            handler=system_info,
            permissions=frozenset({ToolPermission.READ}),
            metadata={"category": "windows", "offline": True},
        ),
        ToolDefinition(
            name="filesystem.list_directory",
            description="List entries in a directory.",
            handler=list_directory,
            input_schema={"type": "object", "properties": {"path": {"type": "string"}}, "required": []},
            permissions=frozenset({ToolPermission.READ}),
            metadata={"category": "filesystem", "offline": True},
        ),
        ToolDefinition(
            name="system.environment",
            description="Read environment variables, optionally limited to named variables.",
            handler=environment,
            input_schema={"type": "object", "properties": {"names": {"type": "array", "items": {"type": "string"}}}},
            permissions=frozenset({ToolPermission.READ}),
            metadata={"category": "system", "offline": True, "sensitive": True},
        ),
    ]
