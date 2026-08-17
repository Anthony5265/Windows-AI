from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from windows_ai.tools import ToolRegistry, ToolRouter

from .events import EventBus
from .memory import MemoryStore
from .providers import ModelRequest, ModelResponse, ProviderRegistry


@dataclass(slots=True)
class RuntimeConfig:
    data_dir: Path = Path.home() / ".windows-ai"
    local_first: bool = True
    require_approval_for_high_risk: bool = True


class WindowsAIRuntime:
    """Top-level composition root for the Windows-AI platform."""

    def __init__(self, config: RuntimeConfig | None = None, *, tools: ToolRegistry | None = None) -> None:
        self.config = config or RuntimeConfig()
        self.config.data_dir.mkdir(parents=True, exist_ok=True)
        self.events = EventBus()
        self.providers = ProviderRegistry()
        self.memory = MemoryStore(self.config.data_dir / "memory.db")
        self.tools = tools or ToolRegistry()
        self.router = ToolRouter(self.tools)
        self.started = False

    async def start(self) -> None:
        if self.started:
            return
        self.started = True
        await self.events.emit("runtime.started", {"data_dir": str(self.config.data_dir)})

    async def stop(self) -> None:
        if not self.started:
            return
        self.started = False
        await self.events.emit("runtime.stopped")

    async def chat(self, message: str, *, model: str | None = None, provider: str | None = None, scope: str = "user") -> ModelResponse:
        memories = self.memory.search(message, scope=scope, limit=8)
        context = "\n".join(f"- {m.content}" for m in memories)
        prompt = message if not context else f"Relevant memory:\n{context}\n\nUser request:\n{message}"
        request = ModelRequest(messages=[{"role": "user", "content": prompt}], model=model, provider=provider)
        response = await self.providers.complete(request, preferred=provider, local_first=self.config.local_first)
        self.memory.add(__import__("windows_ai.platform.memory", fromlist=["MemoryRecord"]).MemoryRecord(content=message, scope=scope, kind="conversation"))
        await self.events.emit("chat.completed", {"provider": response.provider, "model": response.model})
        return response

    async def call_tool(self, name: str, arguments: dict[str, Any], **kwargs: Any):
        result = await self.router.execute(name, arguments, **kwargs)
        await self.events.emit("tool.completed", {"tool": name, "success": result.success})
        return result

    def snapshot(self) -> dict[str, Any]:
        return {
            "started": self.started,
            "providers": self.providers.names(),
            "tools": self.tools.list(),
            "memory_path": str(self.memory.path),
        }
