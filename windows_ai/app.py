"""Windows AI application lifecycle facade.

The canonical runtime owns agent/model/tool execution.  This module keeps the
legacy application facade for callers that still import ``WindowsAIApp`` while
avoiding a second orchestrator lifecycle.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class WindowsAIApp:
    """Compatibility application facade backed by the canonical runtime."""

    def __init__(self, *, workspace: Optional[str] = None) -> None:
        self.config: Dict[str, Any] = {}
        self.components: Dict[str, Any] = {}
        self._running = False
        self.runtime = None
        self.orchestrator = None  # Compatibility attribute; no legacy orchestrator is created.
        self.workspace = workspace

    async def initialize(self) -> None:
        """Initialize the canonical runtime and optional integration services."""
        if self._running:
            return

        from windows_ai.bootstrap import create_runtime

        self.runtime = create_runtime(workspace=self.workspace)
        await self.runtime.start()
        self.components["runtime"] = self.runtime
        self.config = dict(self.runtime.config)

        # Keep optional integrations available without making them competing
        # execution runtimes. Failures are isolated so the core runtime stays usable.
        await self._init_plugin_manager()
        await self._init_frameworks()
        await self._register_plugin_models_with_llm()
        await self._init_security()
        await self._init_api_server()
        self._running = True
        logger.info("Windows AI initialization complete")

    async def _init_plugin_manager(self) -> None:
        try:
            from windows_ai.core.plugin_manager import PluginManager
            manager = PluginManager()
            await manager.initialize()
            self.components["plugin_manager"] = manager
        except Exception as exc:
            logger.warning("Plugin manager initialization skipped: %s", exc)

    async def _init_frameworks(self) -> None:
        try:
            from windows_ai.frameworks import (
                AutoGenManager,
                CrewAIManager,
                LangChainManager,
                LlamaIndexManager,
                MCPManager,
                OllamaManager,
                UnifiedLLMProvider,
            )

            services = {
                "llm": UnifiedLLMProvider(),
                "mcp": MCPManager(),
                "ollama": OllamaManager(),
                "langchain": LangChainManager(),
                "llamaindex": LlamaIndexManager(),
                "crewai": CrewAIManager(),
                "autogen": AutoGenManager(),
            }
            for name, service in services.items():
                await service.initialize()
                self.components[name] = service
        except Exception as exc:
            logger.warning("Framework integrations initialization skipped: %s", exc)

    async def _register_plugin_models_with_llm(self) -> None:
        pm = self.components.get("plugin_manager")
        llm = self.components.get("llm")
        if not pm or not llm:
            return

        try:
            from windows_ai.frameworks.unified_llm import LLMConfig, LLMProvider
        except ImportError:
            return

        for plugin_id, plugin in pm.plugins.items():
            try:
                for model in plugin.get_supported_models() or []:
                    model_id = model.get("id")
                    if not model_id:
                        continue
                    provider_name = model.get("provider")
                    provider = None
                    if provider_name:
                        try:
                            provider = LLMProvider[str(provider_name).upper()]
                        except (KeyError, ValueError):
                            logger.warning("Unknown provider %r from plugin %s", provider_name, plugin_id)
                            continue
                    config = LLMConfig(
                        provider=provider,
                        model=model.get("model") or model_id,
                        display_name=model.get("name") or model_id,
                        category=model.get("type", "cloud"),
                        preview=bool(model.get("preview", False)),
                        badge=model.get("badge"),
                    )
                    llm.register_config(model_id, config)
            except Exception as exc:
                logger.warning("Failed to register models for plugin %s: %s", plugin_id, exc)

    async def _init_security(self) -> None:
        try:
            from windows_ai.security import GuardrailsManager, PermissionManager, SandboxManager

            security = self.config.get("security", {})
            sandbox = SandboxManager()
            await sandbox.initialize({"level": security.get("sandbox_level", "standard")})
            self.components["sandbox"] = sandbox

            guardrails = GuardrailsManager()
            await guardrails.initialize({"level": "standard" if security.get("guardrails", True) else "off"})
            self.components["guardrails"] = guardrails

            permissions = PermissionManager()
            await permissions.initialize()
            self.components["permissions"] = permissions
        except Exception as exc:
            logger.warning("Security integrations initialization skipped: %s", exc)

    async def _init_api_server(self) -> None:
        try:
            from windows_ai.api.server import create_app
            api_config = self.config.get("api", {})
            self.components["api_app"] = create_app(self.components)
            self.components["api_config"] = api_config
        except Exception as exc:
            logger.warning("API integration initialization skipped: %s", exc)

    async def run(self) -> None:
        """Initialize the application and serve its API when configured."""
        await self.initialize()
        api_app = self.components.get("api_app")
        if api_app is None:
            logger.info("Windows AI is running without an API server")
            return

        self._running = True
        api_config = self.components.get("api_config", {})
        try:
            import uvicorn
            server = uvicorn.Server(uvicorn.Config(
                api_app,
                host=api_config.get("host", "127.0.0.1"),
                port=int(api_config.get("port", 8765)),
                log_level="info",
            ))
            await server.serve()
        finally:
            self._running = False

    async def shutdown(self) -> None:
        """Stop the canonical runtime and integration services exactly once."""
        if not self.components and not self.runtime:
            self._running = False
            return

        for name, component in reversed(list(self.components.items())):
            if component is self.runtime or name == "api_app":
                continue
            shutdown = getattr(component, "shutdown", None)
            if shutdown is not None:
                try:
                    result = shutdown()
                    if hasattr(result, "__await__"):
                        await result
                except Exception as exc:
                    logger.error("Error shutting down %s: %s", name, exc)

        if self.runtime is not None:
            await self.runtime.stop()
        self.components.clear()
        self.runtime = None
        self._running = False

    def get_component(self, name: str) -> Any:
        return self.components.get(name)

    def get_status(self) -> Dict[str, Any]:
        """Return application status without exposing mutable configuration state."""
        return {
            "running": self._running,
            "components": list(self.components),
            "runtime": self.runtime.status() if self.runtime else None,
            "config": dict(self.config),
        }
