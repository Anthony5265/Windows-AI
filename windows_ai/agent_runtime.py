"""Agent orchestration built on Windows-AI's unified tool/action layer."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Mapping
from uuid import uuid4

from .tools import ToolCall, ToolRegistry, ToolResult, ToolRouter

ModelInvoker = Callable[[str, list[dict[str, Any]], list[dict[str, Any]]], Any | Awaitable[Any]]


@dataclass(frozen=True)
class AgentDefinition:
    name: str
    description: str
    system_prompt: str = ""
    allowed_tools: frozenset[str] = frozenset()
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass
class AgentSession:
    agent: AgentDefinition
    session_id: str = field(default_factory=lambda: str(uuid4()))
    messages: list[dict[str, Any]] = field(default_factory=list)


class AgentRuntime:
    """Coordinates agent conversations and tool execution without owning a model provider."""

    def __init__(self, registry: ToolRegistry, router: ToolRouter, model_invoker: ModelInvoker | None = None) -> None:
        self.registry = registry
        self.router = router
        self.model_invoker = model_invoker
        self._agents: dict[str, AgentDefinition] = {}

    def register_agent(self, agent: AgentDefinition, *, replace: bool = False) -> AgentDefinition:
        key = agent.name.strip()
        if not key:
            raise ValueError("Agent name cannot be empty")
        if key in self._agents and not replace:
            raise ValueError(f"Agent already registered: {key}")
        self._agents[key] = agent
        return agent

    def get_agent(self, name: str) -> AgentDefinition | None:
        return self._agents.get(name)

    def list_agents(self) -> list[AgentDefinition]:
        return [self._agents[name] for name in sorted(self._agents)]

    def create_session(self, agent_name: str) -> AgentSession:
        agent = self.get_agent(agent_name)
        if agent is None:
            raise KeyError(f"Unknown agent: {agent_name}")
        session = AgentSession(agent)
        if agent.system_prompt:
            session.messages.append({"role": "system", "content": agent.system_prompt})
        return session

    def tool_schemas(self, agent_name: str) -> list[dict[str, Any]]:
        agent = self.get_agent(agent_name)
        if agent is None:
            raise KeyError(f"Unknown agent: {agent_name}")
        schemas = self.registry.schemas()
        if not agent.allowed_tools:
            return schemas
        return [schema for schema in schemas if schema["name"] in agent.allowed_tools]

    async def execute_tool(self, session: AgentSession, tool_name: str, arguments: Mapping[str, Any] | None = None) -> ToolResult:
        if session.agent.allowed_tools and tool_name not in session.agent.allowed_tools:
            return ToolResult.fail(ToolCall(tool_name, request_id=session.session_id), "Agent is not permitted to use this tool")
        call = ToolCall(tool_name, arguments or {}, actor=session.agent.name, request_id=session.session_id)
        return await self.router.execute(call)

    async def run(self, session: AgentSession, user_message: str) -> Any:
        session.messages.append({"role": "user", "content": user_message})
        if self.model_invoker is None:
            return {"session_id": session.session_id, "message": user_message, "tools": self.tool_schemas(session.agent.name)}
        tools = self.tool_schemas(session.agent.name)
        response = self.model_invoker(session.agent.name, list(session.messages), tools)
        if hasattr(response, "__await__"):
            response = await response
        session.messages.append({"role": "assistant", "content": response})
        return response


__all__ = ["AgentDefinition", "AgentSession", "AgentRuntime"]
