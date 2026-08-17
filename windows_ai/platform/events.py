from __future__ import annotations

import asyncio
import inspect
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable


@dataclass(slots=True)
class PlatformEvent:
    name: str
    payload: dict[str, Any] = field(default_factory=dict)
    source: str = "runtime"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


Subscriber = Callable[[PlatformEvent], Any | Awaitable[Any]]


class EventBus:
    """Small async event bus used to decouple agents, tools, workflows and UI."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Subscriber]] = {}

    def subscribe(self, event_name: str, callback: Subscriber) -> None:
        self._subscribers.setdefault(event_name, []).append(callback)

    def unsubscribe(self, event_name: str, callback: Subscriber) -> None:
        callbacks = self._subscribers.get(event_name, [])
        if callback in callbacks:
            callbacks.remove(callback)

    async def publish(self, event: PlatformEvent) -> list[Any]:
        callbacks = [*self._subscribers.get(event.name, []), *self._subscribers.get("*", [])]
        results: list[Any] = []
        for callback in callbacks:
            result = callback(event)
            if inspect.isawaitable(result):
                result = await result
            results.append(result)
        return results

    async def emit(self, name: str, payload: dict[str, Any] | None = None, source: str = "runtime") -> list[Any]:
        return await self.publish(PlatformEvent(name=name, payload=payload or {}, source=source))
