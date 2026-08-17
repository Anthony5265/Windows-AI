"""Persistent workspace context and boundaries for agents."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import json
import uuid


@dataclass
class Workspace:
    id: str
    name: str
    root: Path
    instructions: str = ""
    memory: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def config_path(self) -> Path:
        return self.root / ".windows-ai" / "workspace.json"

    def save(self) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "id": self.id,
            "name": self.name,
            "root": str(self.root),
            "instructions": self.instructions,
            "memory": self.memory,
            "metadata": self.metadata,
        }
        self.config_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, root: str | Path) -> "Workspace":
        path = Path(root).expanduser().resolve()
        config = path / ".windows-ai" / "workspace.json"
        if not config.exists():
            return cls(id=str(uuid.uuid4()), name=path.name or "Workspace", root=path)
        payload = json.loads(config.read_text(encoding="utf-8"))
        return cls(
            id=str(payload.get("id") or uuid.uuid4()),
            name=str(payload.get("name") or path.name or "Workspace"),
            root=path,
            instructions=str(payload.get("instructions") or ""),
            memory=dict(payload.get("memory") or {}),
            metadata=dict(payload.get("metadata") or {}),
        )


class WorkspaceManager:
    def open(self, root: str | Path) -> Workspace:
        workspace = Workspace.load(root)
        workspace.root.mkdir(parents=True, exist_ok=True)
        return workspace

    def create(self, root: str | Path, name: str | None = None) -> Workspace:
        path = Path(root).expanduser().resolve()
        workspace = Workspace(id=str(uuid.uuid4()), name=name or path.name or "Workspace", root=path)
        workspace.save()
        return workspace
