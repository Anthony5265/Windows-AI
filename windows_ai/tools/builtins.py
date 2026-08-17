"""Small, safe built-in capabilities for the unified tool layer."""

from __future__ import annotations

import os
import platform
from pathlib import Path
from typing import Any, Mapping

from .models import ToolDefinition, ToolPermission


def system_info(arguments: Mapping[str, Any]) -> dict[str, Any]:
    """Return non-sensitive host information useful to an agent."""
    return {
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "python": platform.python_version(),
        "cpu_count": os.cpu_count(),
    }


def list_directory(arguments: Mapping[str, Any]) -> list[str]:
    path = Path(str(arguments.get("path", "."))).expanduser()
    if not path.is_dir():
        raise ValueError(f"Not a directory: {path}")
    return [item.name for item in path.iterdir()]


def builtin_tools() -> list[ToolDefinition]:
    return [
        ToolDefinition(
            name="windows.system_info",
            description="Get basic non-sensitive information about the current host.",
            handler=system_info,
            permissions=frozenset({ToolPermission.READ}),
            source="builtin",
        ),
        ToolDefinition(
            name="filesystem.list_directory",
            description="List entries in a directory supplied by the caller.",
            handler=list_directory,
            input_schema={
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
            permissions=frozenset({ToolPermission.READ}),
            source="builtin",
        ),
    ]
