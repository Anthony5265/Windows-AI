from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import Iterable

from .models import ModelRequest, ModelResponse, ProviderDefinition


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, ProviderDefinition] = {}
        self._lock = RLock()

    def register(self, provider: ProviderDefinition, *, replace: bool = False) -> None:
        with self._lock:
            if provider.name in self._providers and not replace:
                raise ValueError(f"Provider already registered: {provider.name}")
            self._providers[provider.name] = provider

    def register_many(self, providers: Iterable[ProviderDefinition]) -> None:
        for provider in providers:
            self.register(provider)

    def get(self, name: str) -> ProviderDefinition | None:
        with self._lock:
            return self._providers.get(name)

    def list(self) -> list[ProviderDefinition]:
        with self._lock:
            return sorted((p for p in self._providers.values() if p.enabled), key=lambda p: p.priority)


@dataclass
class ModelRouter:
    registry: ProviderRegistry

    async def invoke(self, request: ModelRequest, *, provider: str | None = None) -> ModelResponse:
        candidates = [self.registry.get(provider)] if provider else self.registry.list()
        candidates = [p for p in candidates if p is not None and p.enabled]
        if request.metadata.get("offline"):
            candidates = [p for p in candidates if p.capabilities.offline or p.capabilities.local]
        if request.metadata.get("vision"):
            candidates = [p for p in candidates if p.capabilities.vision]
        if not candidates:
            raise RuntimeError("No model provider satisfies the request")

        last_error: Exception | None = None
        for candidate in candidates:
            try:
                return await candidate.invoker.invoke(request)
            except Exception as exc:
                last_error = exc
        raise RuntimeError("All eligible model providers failed") from last_error
