"""Production agent runtime built around the canonical tool/action layer."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Mapping
from uuid import uuid4

from .tools import ToolCall, ToolRegistry, ToolResult, ToolRouter

ModelInvoker = Callable[[str, list[dict[str, Any]], list[dict[str, Any]]], Any | Awaitable[Any]]


@dataclass(frozen=True)
class AgentDefinition:
    """Declarative identity and policy for an agent."""

    name: str
    description: str = ""
    system_prompt: str = ""
    allowed_tools: frozenset[str] = frozenset()
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass
class AgentSession:
    """Mutable conversation/task state owned by one agent session."""

    session_id: str = field(default_factory=lambda: uuid4().hex)
    messages: list[dict[str, Any]] = field(default_factory=list)
    state: dict[str, Any] = field(default_factory=dict)


class AgentRuntime:
    """Coordinates model turns and tool calls without bypassing ToolRouter."""

    def __init__(self, registry: ToolRegistry, router: ToolRouter, invoker: ModelInvoker | None = None) -> None:
        self.registry = registry
        self.router = router
        self.invoker = invoker
        self.agents: dict[str, AgentDefinition] = {}
        self.sessions: dict[str, AgentSession] = {}

    def register(self, agent: AgentDefinition, *, replace: bool = False) -> AgentDefinition:
        if not agent.name.strip():
            raise ValueError("Agent name cannot be empty")
        if agent.name in self.agents and not replace:
            raise ValueError(f"Agent already registered: {agent.name}")
        self.agents[agent.name] = agent
        return agent

    def session(self) -> AgentSession:
        session = AgentSession()
        self.sessions[session.session_id] = session
        return session

    def available_tools(self, agent_name: str) -> list[dict[str, Any]]:
        agent = self._agent(agent_name)
        schemas = self.registry.schemas()
        if not agent.allowed_tools:
            return schemas
        return [schema for schema in schemas if schema["name"] in agent.allowed_tools]

    async def run_turn(
        self,
        agent_name: str,
        prompt: str,
        *,
        session_id: str | None = None,
        model: str = "default",
    ) -> Any:
        """Run one model turn. Model responses may request tools using the normalized contract."""
        if self.invoker is None:
            raise RuntimeError("No model invoker is configured")
        agent = self._agent(agent_name)
        session = self.sessions.get(session_id) if session_id else self.session()
        if session_id and session is None:
            raise KeyError(f"Unknown session: {session_id}")

        session.messages.append({"role": "user", "content": prompt})
        tools = self.available_tools(agent_name)
        result = self.invoker(model, session.messages, tools)
        if hasattr(result, "__await__"):
            result = await result

        # Providers can return a final message or a normalized tool call.
        if isinstance(result, Mapping) and result.get("tool_name"):
            tool_name = str(result["tool_name"])
            if agent.allowed_tools and tool_name not in agent.allowed_tools:
                return ToolResult.fail(ToolCall(tool_name, request_id=session.session_id), "Agent is not permitted to use this tool")
            call = ToolCall(
                tool_name=tool_name,
                arguments=result.get("arguments", {}),
                actor=agent.name,
                request_id=session.session_id,
            )
            tool_result = await self.router.execute(call)
            session.messages.append({"role": "tool", "name": tool_name, "content": tool_result.output if tool_result.success else tool_result.error})
            return tool_result

        session.messages.append({"role": "assistant", "content": result})
        return result

    def _agent(self, name: str) -> AgentDefinition:
        try:
            return self.agents[name]
        except KeyError as exc:
            raise KeyError(f"Unknown agent: {name}") from exc


__all__ = ["AgentDefinition", "AgentSession", "AgentRuntime"]
