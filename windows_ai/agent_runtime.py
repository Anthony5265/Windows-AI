"""Canonical agent orchestration runtime.

Agents use the shared model router and unified tool router.  The runtime keeps
conversation state lightweight and in-process; durable workspace state remains
owned by ``Workspace``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping
import uuid

from .providers.models import ModelRequest, ModelResponse
from .providers.router import ModelRouter
from .tools.models import ToolCall, ToolResult
from .tools.router import ToolRouter


@dataclass(frozen=True)
class AgentDefinition:
    id: str
    name: str
    instructions: str = ""
    model: str | None = None
    allowed_tools: frozenset[str] = frozenset()
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass
class AgentTurn:
    text: str
    tool_results: list[ToolResult] = field(default_factory=list)
    response: ModelResponse | None = None


class AgentRuntime:
    """Registry and execution engine for application agents."""

    def __init__(self, tools: ToolRouter, models: ModelRouter) -> None:
        self.tools = tools
        self.models = models
        self._agents: dict[str, AgentDefinition] = {}
        self._history: dict[str, list[dict[str, Any]]] = {}

    def register(self, agent: AgentDefinition, *, replace: bool = False) -> AgentDefinition:
        if agent.id in self._agents and not replace:
            raise ValueError(f"Agent already registered: {agent.id}")
        self._agents[agent.id] = agent
        return agent

    def get(self, agent_id: str) -> AgentDefinition | None:
        return self._agents.get(agent_id)

    def list(self) -> list[AgentDefinition]:
        return list(self._agents.values())

    def history(self, agent_id: str) -> list[dict[str, Any]]:
        return list(self._history.get(agent_id, []))

    def clear_history(self, agent_id: str) -> None:
        self._history.pop(agent_id, None)

    async def run_turn(
        self,
        *,
        agent_id: str,
        message: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> ModelResponse:
        agent = self._agents.get(agent_id)
        if agent is None:
            raise KeyError(f"Unknown agent: {agent_id}")

        history = self._history.setdefault(agent_id, [])
        history.append({"role": "user", "content": message})
        request = ModelRequest(
            messages=list(history),
            model=agent.model,
            system=agent.instructions,
            metadata=dict(metadata or {}),
        )
        response = await self.models.invoke(request)
        history.append({"role": "assistant", "content": response.text})
        return response

    async def run(self, agent: AgentDefinition, messages: list[Mapping[str, Any]]) -> AgentTurn:
        request = ModelRequest(messages=list(messages), model=agent.model, system=agent.instructions)
        response = await self.models.invoke(request)
        return AgentTurn(text=response.text, response=response)

    async def execute_tool(
        self,
        agent: AgentDefinition,
        name: str,
        arguments: Mapping[str, Any],
        *,
        actor: str | None = None,
        approved: bool = False,
    ) -> ToolResult:
        call = ToolCall(
            tool_name=name,
            arguments=dict(arguments),
            actor=actor or agent.name,
            request_id=str(uuid.uuid4()),
        )
        if agent.allowed_tools and name not in agent.allowed_tools:
            return ToolResult.fail(call, "Agent is not permitted to use this tool")
        return await self.tools.execute(call, approved=approved)
