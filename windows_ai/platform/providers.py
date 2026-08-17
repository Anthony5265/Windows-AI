from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Protocol


@dataclass(slots=True)
class ModelRequest:
    messages: list[dict[str, Any]]
    model: str | None = None
    provider: str | None = None
    tools: list[dict[str, Any]] = field(default_factory=list)
    temperature: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ModelResponse:
    text: str = ""
    provider: str = ""
    model: str = ""
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    raw: Any = None
    usage: dict[str, Any] = field(default_factory=dict)


class ModelProvider(Protocol):
    name: str
    is_local: bool

    async def complete(self, request: ModelRequest) -> ModelResponse: ...


ProviderFactory = Callable[[], ModelProvider] | ModelProvider


class ProviderRegistry:
    """Provider registry with explicit local-first routing and fallback."""

    def __init__(self) -> None:
        self._providers: dict[str, ModelProvider] = {}

    def register(self, provider: ModelProvider) -> None:
        self._providers[provider.name] = provider

    def unregister(self, name: str) -> None:
        self._providers.pop(name, None)

    def get(self, name: str) -> ModelProvider | None:
        return self._providers.get(name)

    def names(self) -> list[str]:
        return list(self._providers)

    def choose(self, preferred: str | None = None, local_first: bool = True) -> ModelProvider | None:
        if preferred and preferred in self._providers:
            return self._providers[preferred]
        providers = list(self._providers.values())
        if local_first:
            providers.sort(key=lambda p: not bool(getattr(p, "is_local", False)))
        return providers[0] if providers else None

    async def complete(self, request: ModelRequest, *, preferred: str | None = None, local_first: bool = True) -> ModelResponse:
        ordered: list[ModelProvider] = []
        selected = self.choose(preferred, local_first)
        if selected:
            ordered.append(selected)
        for provider in self._providers.values():
            if provider not in ordered:
                ordered.append(provider)
        if not ordered:
            raise RuntimeError("No AI model providers are registered")
        errors: list[str] = []
        for provider in ordered:
            try:
                response = await provider.complete(request)
                if not response.provider:
                    response.provider = provider.name
                return response
            except Exception as exc:
                errors.append(f"{provider.name}: {exc}")
        raise RuntimeError("All AI providers failed: " + "; ".join(errors))
