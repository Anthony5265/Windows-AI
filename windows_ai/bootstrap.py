"""Application bootstrap for the canonical Windows-AI runtime."""
from __future__ import annotations

from .agent_runtime import AgentDefinition
from .canonical_runtime import CanonicalRuntime
from .tools import create_default_registry


def create_runtime(*, workspace: str | None = None, start: bool = True) -> CanonicalRuntime:
    """Create the application runtime with the platform's built-in capabilities."""
    runtime = CanonicalRuntime(core=__import__("windows_ai.runtime", fromlist=["WindowsAIRuntime"]).WindowsAIRuntime(
        tools=create_default_registry()
    ))

    # Register a safe default assistant when the application has no agents yet.
    if not runtime.core.agents.list():
        runtime.core.register_agent(
            AgentDefinition(
                id="default",
                name="Windows AI",
                description="Default Windows-AI assistant with access to registered tools.",
                instructions="Use the available tools when they are appropriate and respect tool permissions.",
                model="default",
            )
        )

    if workspace:
        runtime.open_workspace(workspace)
    if start:
        runtime.start()
    return runtime


__all__ = ["create_runtime"]
