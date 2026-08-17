"""Canonical Windows-AI application runtime.

This module is the integration boundary between the public application and the
new agent/tool/provider architecture. It intentionally keeps orchestration
small and dependency-light so the existing Windows-AI subsystems can migrate
toward it incrementally.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

from .agent_runtime import AgentDefinition, AgentRuntime
from .providers import ModelRequest, ModelResponse, ModelRouter
from .tools import ToolDefinition, ToolRegistry, ToolRouter


@dataclass
class WindowsAIRuntime:
    """Owns the canonical registries used by an application instance."""

    tools: ToolRegistry = field(default_factory=ToolRegistry)
    models: ModelRouter = field(default_factory=ModelRouter)
    agents: AgentRuntime = field(init=False)
    _started: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.tool_router = ToolRouter(self.tools)
        self.agents = AgentRuntime(self.tool_router, self.models)

    def start(self) -> "WindowsAIRuntime":
        self._started = True
        return self

    def stop(self) -> None:
        self._started = False

    @property
    def started(self) -> bool:
        return self._started

    def register_tool(self, tool: ToolDefinition) -> ToolDefinition:
        return self.tools.register(tool)

    def register_agent(self, agent: AgentDefinition) -> AgentDefinition:
        return self.agents.register(agent)

    def register_model(self, provider: Any, model: Any) -> None:
        self.models.register(provider, model)

    async def chat(
        self,
        *,
        agent_id: str,
        message: str,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> ModelResponse:
        """Send one user turn through the canonical agent/model runtime."""
        if not self._started:
            self.start()
        return await self.agents.run_turn(
            agent_id=agent_id,
            message=message,
            metadata=dict(metadata or {}),
        )

    async def execute_tool(
        self,
        *,
        tool_name: str,
        arguments: Mapping[str, Any] | None = None,
        actor: str = "system",
        approved: bool = False,
    ) -> Any:
        """Execute a registered capability through the central tool router."""
        return await self.tool_router.execute(
            tool_name,
            dict(arguments or {}),
            actor=actor,
            approved=approved,
        )

    def describe(self) -> dict[str, Any]:
        """Return a UI/API-friendly snapshot of available capabilities."""
        return {
            "started": self.started,
            "tools": [t.name for t in self.tools.list()],
            "agents": [a.id for a in self.agents.list()],
            "models": [m.id for m in self.models.list_models()],
        }
