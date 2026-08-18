"""Canonical Windows-AI application runtime."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .agent_runtime import AgentDefinition, AgentRuntime
from .providers.models import ModelResponse, ProviderDefinition
from .providers.router import ModelRouter, ProviderRegistry
from .tools import ToolDefinition, ToolRegistry, ToolRouter


@dataclass
class WindowsAIRuntime:
    """Single integration boundary for the Windows-AI application."""

    tools: ToolRegistry = field(default_factory=ToolRegistry)
    providers: ProviderRegistry = field(default_factory=ProviderRegistry)
    agents: AgentRuntime = field(init=False)
    _started: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.tool_router = ToolRouter(self.tools)
        self.model_router = ModelRouter(self.providers)
        self.agents = AgentRuntime(self.tool_router, self.model_router)

    @property
    def models(self) -> ModelRouter:
        """Compatibility alias for the canonical model router."""
        return self.model_router

    def start(self) -> "WindowsAIRuntime":
        """Start the runtime; repeated calls are intentionally idempotent."""
        self._started = True
        return self

    def stop(self) -> None:
        """Stop the runtime and prevent new application operations."""
        self._started = False

    @property
    def started(self) -> bool:
        return self._started

    def _ensure_started(self) -> None:
        if not self._started:
            raise RuntimeError("Windows-AI runtime is not started")

    def register_tool(self, tool: ToolDefinition, *, replace: bool = False) -> ToolDefinition:
        return self.tools.register(tool, replace=replace)

    def register_agent(self, agent: AgentDefinition, *, replace: bool = False) -> AgentDefinition:
        return self.agents.register(agent, replace=replace)

    def register_provider(self, provider: ProviderDefinition, *, replace: bool = False) -> None:
        self.providers.register(provider, replace=replace)

    async def chat(
        self,
        *,
        agent_id: str,
        message: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> ModelResponse:
        self._ensure_started()
        return await self.agents.run_turn(
            agent_id=agent_id,
            message=message,
            metadata=metadata,
        )

    async def execute_tool(
        self,
        *,
        tool_name: str,
        arguments: Mapping[str, Any] | None = None,
        actor: str = "system",
        approved: bool = False,
    ) -> Any:
        self._ensure_started()
        return await self.tool_router.execute(
            tool_name,
            dict(arguments or {}),
            actor=actor,
            approved=approved,
        )

    def describe(self) -> dict[str, Any]:
        return {
            "started": self.started,
            "tools": [tool.name for tool in self.tools.list()],
            "agents": [agent.id for agent in self.agents.list()],
            "providers": [provider.name for provider in self.providers.list()],
            "models": [model for provider in self.providers.list() for model in provider.models],
        }
