"""Application bootstrap for the canonical Windows-AI runtime."""
from __future__ import annotations

from pathlib import Path

from .agent_runtime import AgentDefinition
from .canonical_runtime import CanonicalRuntime
from .runtime import WindowsAIRuntime
from .tools import create_default_registry


def create_runtime(*, workspace: str | None = None, start: bool = True) -> CanonicalRuntime:
    """Create the canonical runtime with built-in capabilities."""
    runtime = CanonicalRuntime(
        core=WindowsAIRuntime(tools=create_default_registry())
    )

    # Register the default assistant only when no application agent exists.
    if not runtime.core.agents.list():
        runtime.core.register_agent(
            AgentDefinition(
                id="default",
                name="Windows AI",
                description="Default Windows-AI assistant with access to registered tools.",
                instructions=(
                    "Use available tools when appropriate and always respect tool permissions."
                ),
                model="default",
            )
        )

    if workspace is not None:
        workspace_path = Path(workspace).expanduser().resolve()
        if not workspace_path.exists():
            raise FileNotFoundError(f"Workspace does not exist: {workspace_path}")
        if not workspace_path.is_dir():
            raise NotADirectoryError(f"Workspace is not a directory: {workspace_path}")
        runtime.open_workspace(str(workspace_path))

    if start:
        runtime.start()
    return runtime


__all__ = ["create_runtime"]
