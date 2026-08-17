"""Canonical application facade for the Windows-AI platform.

This facade gives API/GUI/CLI integrations one stable entry point without
replacing the repository's existing subsystems. It is intentionally small:
existing managers can be registered and exposed through a common capability
surface while the platform converges on the architecture in AI_BLUEPRINT.md.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .runtime import WindowsAIRuntime
from .workspace import Workspace, WorkspaceManager


@dataclass
class CanonicalRuntime:
    """Application-level composition root for Windows-AI."""

    core: WindowsAIRuntime = field(default_factory=WindowsAIRuntime)
    workspaces: WorkspaceManager = field(default_factory=WorkspaceManager)
    services: dict[str, Any] = field(default_factory=dict)
    _active_workspace: Workspace | None = field(default=None, init=False)

    def start(self) -> "CanonicalRuntime":
        self.core.start()
        return self

    def stop(self) -> None:
        self.core.stop()

    @property
    def active_workspace(self) -> Workspace | None:
        return self._active_workspace

    def open_workspace(self, root: str) -> Workspace:
        self._active_workspace = self.workspaces.open(root)
        return self._active_workspace

    def register_service(self, name: str, service: Any, *, replace: bool = False) -> None:
        if name in self.services and not replace:
            raise ValueError(f"Service already registered: {name}")
        self.services[name] = service

    def get_service(self, name: str) -> Any | None:
        return self.services.get(name)

    def capabilities(self) -> dict[str, Any]:
        snapshot = self.core.describe()
        snapshot["workspace"] = (
            {"id": self._active_workspace.id, "name": self._active_workspace.name,
             "root": str(self._active_workspace.root)}
            if self._active_workspace else None
        )
        snapshot["services"] = sorted(self.services)
        return snapshot

    async def chat(self, *, agent_id: str, message: str,
                   metadata: Mapping[str, Any] | None = None):
        metadata = dict(metadata or {})
        if self._active_workspace:
            metadata.setdefault("workspace_id", self._active_workspace.id)
            metadata.setdefault("workspace_root", str(self._active_workspace.root))
        return await self.core.chat(agent_id=agent_id, message=message, metadata=metadata)

    async def execute_tool(self, *, tool_name: str,
                           arguments: Mapping[str, Any] | None = None,
                           actor: str = "system", approved: bool = False):
        return await self.core.execute_tool(
            tool_name=tool_name, arguments=arguments, actor=actor, approved=approved
        )
