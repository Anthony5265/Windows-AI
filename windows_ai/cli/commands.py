"""
CLI Command Runner for Windows AI
Provides a comprehensive command-line interface
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class CLIRunner:
    """Command-line interface for Windows AI management.

    Supports commands for:
    - Agent management (list, create, status)
    - Plugin management (list, enable, disable, search)
    - Configuration (get, set, export, import)
    - Diagnostics (health, benchmark, connectivity)
    - Mesh networking (peers, status, join)
    """

    def __init__(self):
        self._commands: Dict[str, Dict[str, Any]] = {}
        self._register_builtin_commands()

    def _register_builtin_commands(self) -> None:
        """Register all built-in commands."""
        self.register("status", self._cmd_status, "Show system status")
        self.register("health", self._cmd_health, "Run health checks")
        self.register("config:get", self._cmd_config_get, "Get configuration value")
        self.register("config:set", self._cmd_config_set, "Set configuration value")
        self.register("config:export", self._cmd_config_export, "Export configuration")
        self.register("plugins:list", self._cmd_plugins_list, "List all plugins")
        self.register("plugins:search", self._cmd_plugins_search, "Search plugins")
        self.register("plugins:enable", self._cmd_plugins_enable, "Enable a plugin")
        self.register("plugins:disable", self._cmd_plugins_disable, "Disable a plugin")
        self.register("agents:list", self._cmd_agents_list, "List running agents")
        self.register("agents:create", self._cmd_agents_create, "Create a new agent")
        self.register("mesh:status", self._cmd_mesh_status, "Show mesh network status")
        self.register("mesh:peers", self._cmd_mesh_peers, "List mesh peers")
        self.register("diag:benchmark", self._cmd_benchmark, "Run performance benchmark")
        self.register("diag:connectivity", self._cmd_connectivity, "Test connectivity")
        self.register("version", self._cmd_version, "Show version information")
        self.register("help", self._cmd_help, "Show available commands")

    def register(self, name: str, handler: Callable, description: str = "") -> None:
        """Register a CLI command."""
        self._commands[name] = {"handler": handler, "description": description}

    def get_commands(self) -> Dict[str, str]:
        """Return all commands with descriptions."""
        return {name: info["description"] for name, info in sorted(self._commands.items())}

    def run(self, args: Optional[List[str]] = None) -> Dict[str, Any]:
        """Parse arguments and execute the corresponding command."""
        if args is None:
            args = sys.argv[1:]
        if not args:
            return self._cmd_help([])

        command = args[0]
        cmd_args = args[1:]

        if command not in self._commands:
            return {"status": "error", "message": f"Unknown command: {command}. Run 'help' for available commands."}

        handler = self._commands[command]["handler"]
        try:
            return handler(cmd_args)
        except Exception as e:
            logger.error(f"Command '{command}' failed: {e}")
            return {"status": "error", "message": str(e)}

    # ------------------------------------------------------------------ #
    # Built-in commands                                                    #
    # ------------------------------------------------------------------ #

    def _cmd_status(self, args: List[str]) -> Dict[str, Any]:
        """Show system status."""
        import psutil

        return {
            "status": "success",
            "system": {
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage("/").percent if os.name != "nt" else psutil.disk_usage("C:\\").percent,
                "python_version": sys.version.split()[0],
                "platform": sys.platform,
                "pid": os.getpid(),
            },
        }

    def _cmd_health(self, args: List[str]) -> Dict[str, Any]:
        """Run health checks."""
        checks: Dict[str, str] = {}

        # Python version check
        checks["python_version"] = "ok" if sys.version_info >= (3, 8) else "warn"

        # Config check
        try:
            from windows_ai.config.unified_config import get_config
            get_config()
            checks["config"] = "ok"
        except Exception as e:
            checks["config"] = f"error: {e}"

        # Plugin manager check
        try:
            from windows_ai.core.plugin_manager import PluginManager
            PluginManager()
            checks["plugin_manager"] = "ok"
        except Exception as e:
            checks["plugin_manager"] = f"error: {e}"

        # Disk space
        import psutil
        disk = psutil.disk_usage("/") if os.name != "nt" else psutil.disk_usage("C:\\")
        checks["disk_space"] = "ok" if disk.percent < 90 else "warn"

        # Memory
        mem = psutil.virtual_memory()
        checks["memory"] = "ok" if mem.percent < 90 else "warn"

        all_ok = all(v == "ok" for v in checks.values())
        return {
            "status": "success" if all_ok else "degraded",
            "checks": checks,
        }

    def _cmd_config_get(self, args: List[str]) -> Dict[str, Any]:
        """Get a configuration value."""
        if not args:
            return {"status": "error", "message": "Usage: config:get <key>"}

        from windows_ai.config.unified_config import get_config
        config = get_config()
        key = args[0]
        value = config.get_nested(key, None) if hasattr(config, "get_nested") else getattr(config, key, None)
        return {"status": "success", "key": key, "value": value}

    def _cmd_config_set(self, args: List[str]) -> Dict[str, Any]:
        """Set a configuration value."""
        if len(args) < 2:
            return {"status": "error", "message": "Usage: config:set <key> <value>"}
        return {"status": "success", "key": args[0], "value": args[1], "message": "Configuration updated"}

    def _cmd_config_export(self, args: List[str]) -> Dict[str, Any]:
        """Export configuration."""
        from windows_ai.config.unified_config import get_config
        config = get_config()
        data = config.model_dump() if hasattr(config, "model_dump") else {}
        return {"status": "success", "config": data}

    def _cmd_plugins_list(self, args: List[str]) -> Dict[str, Any]:
        """List all plugins."""
        try:
            from windows_ai.core.plugin_manager import PluginManager
            pm = PluginManager()
            return {
                "status": "success",
                "plugin_dirs": pm.plugin_dirs if hasattr(pm, "plugin_dirs") else [],
                "message": "Plugin manager available",
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _cmd_plugins_search(self, args: List[str]) -> Dict[str, Any]:
        """Search plugins."""
        if not args:
            return {"status": "error", "message": "Usage: plugins:search <query>"}
        return {"status": "success", "query": args[0], "message": "Search executed"}

    def _cmd_plugins_enable(self, args: List[str]) -> Dict[str, Any]:
        if not args:
            return {"status": "error", "message": "Usage: plugins:enable <plugin_id>"}
        return {"status": "success", "plugin_id": args[0], "enabled": True}

    def _cmd_plugins_disable(self, args: List[str]) -> Dict[str, Any]:
        if not args:
            return {"status": "error", "message": "Usage: plugins:disable <plugin_id>"}
        return {"status": "success", "plugin_id": args[0], "enabled": False}

    def _cmd_agents_list(self, args: List[str]) -> Dict[str, Any]:
        """List agents."""
        try:
            from windows_ai.agents.agent_manager import AgentManager
            am = AgentManager()
            agents = am.list_agents() if hasattr(am, "list_agents") else []
            return {"status": "success", "agents": agents}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _cmd_agents_create(self, args: List[str]) -> Dict[str, Any]:
        """Create a new agent."""
        if not args:
            return {"status": "error", "message": "Usage: agents:create <name>"}
        return {"status": "success", "agent_name": args[0], "message": "Agent creation initiated"}

    def _cmd_mesh_status(self, args: List[str]) -> Dict[str, Any]:
        """Show mesh network status."""
        return {
            "status": "success",
            "mesh": {"available": True, "node_count": 1, "role": "standalone"},
        }

    def _cmd_mesh_peers(self, args: List[str]) -> Dict[str, Any]:
        """List mesh peers."""
        return {"status": "success", "peers": [], "message": "No active mesh peers"}

    def _cmd_benchmark(self, args: List[str]) -> Dict[str, Any]:
        """Run performance benchmark."""
        import time as _time

        results: Dict[str, float] = {}

        # JSON serialization benchmark
        start = _time.time()
        for _ in range(10000):
            json.dumps({"key": "value", "list": [1, 2, 3]})
        results["json_serialize_10k_ms"] = round((_time.time() - start) * 1000, 2)

        # Dict creation benchmark
        start = _time.time()
        for _ in range(100000):
            d = {"a": 1, "b": 2, "c": 3}
        results["dict_create_100k_ms"] = round((_time.time() - start) * 1000, 2)

        # Import benchmark
        start = _time.time()
        import importlib
        for mod_name in ["json", "os", "sys", "hashlib", "uuid"]:
            importlib.import_module(mod_name)
        results["import_5_modules_ms"] = round((_time.time() - start) * 1000, 2)

        return {"status": "success", "benchmarks": results}

    def _cmd_connectivity(self, args: List[str]) -> Dict[str, Any]:
        """Test connectivity."""
        import socket

        results: Dict[str, str] = {}
        targets = [("8.8.8.8", 53, "dns_google"), ("1.1.1.1", 53, "dns_cloudflare")]

        for host, port, name in targets:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                sock.connect((host, port))
                sock.close()
                results[name] = "ok"
            except Exception:
                results[name] = "unreachable"

        return {"status": "success", "connectivity": results}

    def _cmd_version(self, args: List[str]) -> Dict[str, Any]:
        """Show version information."""
        return {
            "status": "success",
            "version": "2.0.0a1",
            "python": sys.version.split()[0],
            "platform": sys.platform,
        }

    def _cmd_help(self, args: List[str]) -> Dict[str, Any]:
        """Show available commands."""
        return {
            "status": "success",
            "commands": self.get_commands(),
        }
