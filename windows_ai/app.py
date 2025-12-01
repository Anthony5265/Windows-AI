"""
Windows AI - Main Application
Orchestrates all components of the Windows AI platform with zero-configuration setup
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class WindowsAIApp:
    """Main Windows AI Application with Zero-Config Setup"""

    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.components: Dict[str, Any] = {}
        self._running = False
        self.orchestrator = None

    async def initialize(self):
        """Initialize all components with zero-configuration"""
        logger.info("[*] Starting Windows AI...")

        # Step 1: Run auto-setup if first time
        await self._run_auto_setup()

        # Step 2: Load configuration
        await self._load_config()

        # Step 3: Initialize master orchestrator (ALL 2500+ AI capabilities)
        await self._init_orchestrator()

        # Step 4: Initialize legacy components (for backwards compatibility)
        await self._init_plugin_manager()
        await self._init_frameworks()
        await self._init_security()
        await self._init_api_server()

        logger.info("[+] Windows AI initialization complete - Ready to use!")

    async def _run_auto_setup(self):
        """Run automatic setup system"""
        try:
            from windows_ai.core.auto_setup import ensure_setup

            logger.info("[*] Checking system setup...")
            setup_result = await ensure_setup()

            if setup_result:
                logger.info("[+] System setup verified")

        except Exception as e:
            logger.warning(f"Auto-setup encountered an issue: {e}")
            logger.info("Continuing with default configuration...")

    async def _init_orchestrator(self):
        """Initialize the master orchestrator for all AI capabilities"""
        try:
            from windows_ai.core.orchestrator import WindowsAI

            logger.info("[*] Initializing master orchestrator (2500+ AI capabilities)...")

            self.orchestrator = WindowsAI()
            await self.orchestrator.initialize(self.config)

            self.components["orchestrator"] = self.orchestrator

            # Get status
            status = self.orchestrator.status()
            logger.info(f"[+] Orchestrator ready: {status['managers_loaded']} managers loaded")

        except Exception as e:
            logger.error(f"[!] Orchestrator initialization failed: {e}")
            raise

    async def _load_config(self):
        """Load configuration"""
        import yaml

        config_paths = [
            Path.home() / ".windowsai" / "config.yaml",
            Path(__file__).parent / "config" / "default.yaml",
        ]

        for config_path in config_paths:
            if config_path.exists():
                with open(config_path) as f:
                    self.config = yaml.safe_load(f) or {}
                logger.info(f"Loaded config from {config_path}")
                break

        # Apply defaults
        self.config.setdefault("api", {"host": "127.0.0.1", "port": 8765})
        self.config.setdefault("security", {"sandbox_level": "standard", "guardrails": True})

    async def _init_plugin_manager(self):
        """Initialize plugin manager"""
        try:
            from windows_ai.core.plugin_manager import PluginManager
            pm = PluginManager()
            await pm.initialize()
            self.components["plugin_manager"] = pm
            logger.info(f"Plugin manager loaded with {len(pm.plugins)} plugins")
        except Exception as e:
            logger.warning(f"Plugin manager init failed: {e}")

    async def _init_frameworks(self):
        """Initialize AI frameworks"""
        try:
            from windows_ai.frameworks import (
                LangChainManager, LlamaIndexManager, CrewAIManager,
                AutoGenManager, MCPManager, OllamaManager, UnifiedLLMProvider
            )

            # Initialize unified LLM provider
            llm = UnifiedLLMProvider()
            await llm.initialize()
            self.components["llm"] = llm

            # Initialize MCP
            mcp = MCPManager()
            await mcp.initialize()
            self.components["mcp"] = mcp

            # Initialize Ollama for local models
            ollama = OllamaManager()
            await ollama.initialize()
            self.components["ollama"] = ollama

            # Initialize LangChain
            langchain = LangChainManager()
            await langchain.initialize()
            self.components["langchain"] = langchain

            # Initialize LlamaIndex
            llamaindex = LlamaIndexManager()
            await llamaindex.initialize()
            self.components["llamaindex"] = llamaindex

            # Initialize CrewAI
            crewai = CrewAIManager()
            await crewai.initialize()
            self.components["crewai"] = crewai

            # Initialize AutoGen
            autogen = AutoGenManager()
            await autogen.initialize()
            self.components["autogen"] = autogen

            logger.info("AI frameworks initialized")

        except Exception as e:
            logger.warning(f"Framework init failed: {e}")

    async def _init_security(self):
        """Initialize security components"""
        try:
            from windows_ai.security import SandboxManager, GuardrailsManager, PermissionManager

            security_config = self.config.get("security", {})

            # Initialize sandbox
            sandbox = SandboxManager()
            await sandbox.initialize({"level": security_config.get("sandbox_level", "standard")})
            self.components["sandbox"] = sandbox

            # Initialize guardrails
            guardrails = GuardrailsManager()
            level = "standard" if security_config.get("guardrails", True) else "off"
            await guardrails.initialize({"level": level})
            self.components["guardrails"] = guardrails

            # Initialize permissions
            permissions = PermissionManager()
            await permissions.initialize()
            self.components["permissions"] = permissions

            logger.info("Security components initialized")

        except Exception as e:
            logger.warning(f"Security init failed: {e}")

    async def _init_api_server(self):
        """Initialize API server"""
        try:
            from windows_ai.api.server import create_app

            api_config = self.config.get("api", {})
            app = create_app(self.components)
            self.components["api_app"] = app
            self.components["api_config"] = api_config

            logger.info("API server initialized")

        except Exception as e:
            logger.warning(f"API server init failed: {e}")

    async def run(self):
        """Run the application"""
        await self.initialize()

        self._running = True
        logger.info("Windows AI is running")

        # Start API server
        api_config = self.components.get("api_config", {})
        host = api_config.get("host", "127.0.0.1")
        port = api_config.get("port", 8765)

        try:
            import uvicorn
            config = uvicorn.Config(
                self.components.get("api_app"),
                host=host,
                port=port,
                log_level="info"
            )
            server = uvicorn.Server(config)
            await server.serve()
        except Exception as e:
            logger.error(f"Server error: {e}")

    async def shutdown(self):
        """Shutdown the application"""
        logger.info("Shutting down Windows AI...")
        self._running = False

        # Shutdown components
        for name, component in self.components.items():
            if hasattr(component, "shutdown"):
                try:
                    await component.shutdown()
                except Exception as e:
                    logger.error(f"Error shutting down {name}: {e}")

        logger.info("Windows AI shutdown complete")

    def get_component(self, name: str) -> Any:
        """Get a component by name"""
        return self.components.get(name)

    def get_status(self) -> Dict[str, Any]:
        """Get application status"""
        return {
            "running": self._running,
            "components": list(self.components.keys()),
            "config": self.config
        }
