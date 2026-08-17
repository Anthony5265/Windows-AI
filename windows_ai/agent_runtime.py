"""Agent execution runtime using the canonical tool and model layers."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping
import uuid

from .providers.models import ModelRequest, ModelResponse, ModelInvoker
from .tools.models import ToolCall, ToolResult
from .tools.router import ToolRouter


@dataclass
class AgentDefinition:
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
    def __init__(self, model: ModelInvoker, tools: ToolRouter) -> None:
        self.model = model
        self.tools = tools

    async def run(self, agent: AgentDefinition, messages: list[Mapping[str, Any]]) -> AgentTurn:
        request = ModelRequest(messages=list(messages), model=agent.model, system=agent.instructions)
        response = await self.model.invoke(request)
        return AgentTurn(text=response.text, response=response)

    async def execute_tool(self, agent: AgentDefinition, name: str, arguments: Mapping[str, Any], *, actor: str | None = None) -> ToolResult:
        if agent.allowed_tools and name not in agent.allowed_tools:
            call = ToolCall(tool_name=name, arguments=arguments, actor=actor or agent.name, request_id=str(uuid.uuid4()))
            return ToolResult.fail(call, "Agent is not permitted to use this tool")
        call = ToolCall(tool_name=name, arguments=arguments, actor=actor or agent.name, request_id=str(uuid.uuid4()))
        return await self.tools.execute(call)
