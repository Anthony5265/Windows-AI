from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol


@dataclass(frozen=True)
class ProviderCapabilities:
    streaming: bool = True
    vision: bool = False
    audio: bool = False
    tools: bool = True
    local: bool = False
    offline: bool = False


@dataclass(frozen=True)
class ModelRequest:
    messages: list[Mapping[str, Any]]
    model: str | None = None
    system: str | None = None
    temperature: float | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelResponse:
    text: str
    provider: str
    model: str | None = None
    usage: Mapping[str, Any] = field(default_factory=dict)
    raw: Any = None


class ModelInvoker(Protocol):
    async def invoke(self, request: ModelRequest) -> ModelResponse: ...


@dataclass
class ProviderDefinition:
    name: str
    invoker: ModelInvoker
    capabilities: ProviderCapabilities = field(default_factory=ProviderCapabilities)
    priority: int = 100
    enabled: bool = True
    models: tuple[str, ...] = ()
