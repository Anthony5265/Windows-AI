"""
Windows Winget Integration - PRODUCTION

Provides comprehensive Windows Package Manager (winget) capabilities including:
- Searching for packages
- Installing/uninstalling packages
- Listing installed packages
- Upgrading packages
- Package information retrieval
- Source management
"""
import asyncio
import json
from typing import Dict, Any, Optional, List
from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType
import logging

logger = logging.getLogger(__name__)


class WindowsWingetPlugin(IntegrationPlugin):
    """Windows Package Manager (winget) plugin with comprehensive package management."""
    
    def __init__(self):
        metadata = PluginMetadata(
            id="windows_winget",
            name="Windows Winget Package Manager",
            description="Comprehensive Windows Package Manager (winget) - search, install, upgrade, and manage packages",
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["windows", "winget", "package_manager", "software"]
        )
        super().__init__(metadata)
        self.connected = False
        self._winget_available = False

    async def initialize(self) -> bool:
        """Initialize the winget plugin and check availability."""
        result = await self._run_command(["winget", "--version"])
        self._winget_available = result["success"]
        if self._winget_available:
            logger.info(f"Winget version: {result.get('output', 'unknown')}")
        else:
            logger.warning("Winget not available on this system")
        self._initialized = True
        return True

    async def connect(self, credentials: Dict[str, str]) -> bool:
        """Connect (local access, no credentials needed)."""
        self.connected = True
        return True

    async def disconnect(self) -> bool:
        """Disconnect."""
        self.connected = False
        return True

    async def _run_command(self, cmd: List[str], timeout: int = 120) -> Dict[str, Any]:
        """Execute a winget command and return results."""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            return {
                "success": process.returncode == 0,
                "output": stdout.decode('utf-8', errors='replace').strip(),
                "error": stderr.decode('utf-8', errors='replace').strip() if stderr else None,
                "return_code": process.returncode
            }
        except asyncio.TimeoutError:
            return {"success": False, "error": "Command timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def execute(self, action: str, parameters: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Execute a winget operation."""
        if not self.connected:
            return {"success": False, "error": "Not connected"}
        
        if not self._winget_available:
            return {"success": False, "error": "Winget not available on this system"}

        actions = {
            "search": self._search_packages,
            "install": self._install_package,
            "uninstall": self._uninstall_package,
            "list": self._list_installed,
            "upgrade": self._upgrade_package,
            "upgrade_all": self._upgrade_all,
            "show": self._show_package,
            "list_sources": self._list_sources,
            "add_source": self._add_source,
            "remove_source": self._remove_source,
            "export": self._export_packages,
            "import": self._import_packages,
            "list_upgrades": self._list_upgrades,
        }

        if action not in actions:
            return {"success": False, "error": f"Unknown action: {action}. Available: {list(actions.keys())}"}

        try:
            return await actions[action](parameters)
        except Exception as e:
            logger.error(f"Winget operation failed: {e}")
            return {"success": False, "error": str(e)}

    async def _search_packages(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search for packages."""
        query = params.get("query", "")
        if not query:
            return {"success": False, "error": "Query parameter required"}
        
        source = params.get("source", "")
        exact = params.get("exact", False)
        count = params.get("count", 50)
        
        cmd = ["winget", "search", query, "--accept-source-agreements"]
        if source:
            cmd.extend(["--source", source])
        if exact:
            cmd.append("--exact")
        cmd.extend(["--count", str(count)])
        
        result = await self._run_command(cmd)
        if result["success"]:
            packages = self._parse_package_list(result["output"])
            return {"success": True, "packages": packages, "count": len(packages)}
        return result

    async def _install_package(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Install a package."""
        package_id = params.get("id") or params.get("package_id") or params.get("name")
        if not package_id:
            return {"success": False, "error": "Package ID required"}
        
        version = params.get("version", "")
        source = params.get("source", "")
        silent = params.get("silent", True)
        
        cmd = ["winget", "install", package_id]
        if version:
            cmd.extend(["--version", version])
        if source:
            cmd.extend(["--source", source])
        if silent:
            cmd.append("--silent")
        cmd.extend(["--accept-package-agreements", "--accept-source-agreements"])
        
        result = await self._run_command(cmd, timeout=600)
        return result

    async def _uninstall_package(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Uninstall a package."""
        package_id = params.get("id") or params.get("package_id") or params.get("name")
        if not package_id:
            return {"success": False, "error": "Package ID required"}
        
        cmd = ["winget", "uninstall", package_id]
        if params.get("silent", True):
            cmd.append("--silent")
        
        result = await self._run_command(cmd, timeout=300)
        return result

    async def _list_installed(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List installed packages."""
        cmd = ["winget", "list", "--accept-source-agreements"]
        if params.get("source"):
            cmd.extend(["--source", params["source"]])
        if params.get("query"):
            cmd.append(params["query"])
        
        result = await self._run_command(cmd)
        if result["success"]:
            packages = self._parse_package_list(result["output"])
            return {"success": True, "packages": packages, "count": len(packages)}
        return result

    async def _upgrade_package(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Upgrade a specific package."""
        package_id = params.get("id") or params.get("package_id") or params.get("name")
        if not package_id:
            return {"success": False, "error": "Package ID required"}
        
        cmd = ["winget", "upgrade", package_id, "--accept-source-agreements", "--accept-package-agreements"]
        if params.get("silent", True):
            cmd.append("--silent")
        
        return await self._run_command(cmd, timeout=600)

    async def _upgrade_all(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Upgrade all packages with available updates."""
        cmd = ["winget", "upgrade", "--all", "--accept-source-agreements", "--accept-package-agreements"]
        if params.get("silent", True):
            cmd.append("--silent")
        if params.get("include_unknown", False):
            cmd.append("--include-unknown")
        
        return await self._run_command(cmd, timeout=1800)

    async def _show_package(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Show detailed package information."""
        package_id = params.get("id") or params.get("package_id") or params.get("name")
        if not package_id:
            return {"success": False, "error": "Package ID required"}
        
        cmd = ["winget", "show", package_id, "--accept-source-agreements"]
        result = await self._run_command(cmd)
        
        if result["success"]:
            info = self._parse_package_info(result["output"])
            return {"success": True, "package_info": info}
        return result

    async def _list_sources(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List configured package sources."""
        result = await self._run_command(["winget", "source", "list"])
        if result["success"]:
            sources = self._parse_sources(result["output"])
            return {"success": True, "sources": sources}
        return result

    async def _add_source(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new package source."""
        name = params.get("name")
        url = params.get("url")
        if not name or not url:
            return {"success": False, "error": "Name and URL required"}
        
        cmd = ["winget", "source", "add", "--name", name, "--arg", url, "--type", params.get("type", "Microsoft.Rest")]
        return await self._run_command(cmd)

    async def _remove_source(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove a package source."""
        name = params.get("name")
        if not name:
            return {"success": False, "error": "Source name required"}
        return await self._run_command(["winget", "source", "remove", "--name", name])

    async def _export_packages(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Export list of installed packages to JSON."""
        output_path = params.get("output_path", "packages.json")
        cmd = ["winget", "export", "--output", output_path, "--accept-source-agreements"]
        result = await self._run_command(cmd)
        if result["success"]:
            return {"success": True, "output_path": output_path}
        return result

    async def _import_packages(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Import and install packages from JSON file."""
        input_path = params.get("input_path")
        if not input_path:
            return {"success": False, "error": "Input path required"}
        
        cmd = ["winget", "import", "--import-file", input_path, "--accept-source-agreements", "--accept-package-agreements"]
        if params.get("ignore_unavailable", True):
            cmd.append("--ignore-unavailable")
        return await self._run_command(cmd, timeout=3600)

    async def _list_upgrades(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List packages with available upgrades."""
        cmd = ["winget", "upgrade", "--accept-source-agreements"]
        if params.get("source"):
            cmd.extend(["--source", params["source"]])
        
        result = await self._run_command(cmd)
        if result["success"]:
            packages = self._parse_package_list(result["output"])
            return {"success": True, "packages": packages, "count": len(packages)}
        return result

    def _parse_package_list(self, output: str) -> List[Dict[str, str]]:
        """Parse winget output into list of packages."""
        packages = []
        lines = output.strip().split('\n')
        data_started = False
        
        for line in lines:
            if '---' in line:
                data_started = True
                continue
            if not data_started or not line.strip():
                continue
            
            parts = line.split()
            if len(parts) >= 2:
                packages.append({
                    "name": parts[0] if len(parts) > 0 else "",
                    "id": parts[1] if len(parts) > 1 else "",
                    "version": parts[2] if len(parts) > 2 else "",
                    "available": parts[3] if len(parts) > 3 else "",
                    "source": parts[4] if len(parts) > 4 else ""
                })
        return packages

    def _parse_package_info(self, output: str) -> Dict[str, str]:
        """Parse package show output into dictionary."""
        info = {}
        for line in output.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                info[key.strip()] = value.strip()
        return info

    def _parse_sources(self, output: str) -> List[Dict[str, str]]:
        """Parse source list output."""
        sources = []
        lines = output.strip().split('\n')
        for line in lines[1:]:
            if line.strip():
                parts = line.split()
                if len(parts) >= 2:
                    sources.append({"name": parts[0], "url": parts[1] if len(parts) > 1 else ""})
        return sources

    async def shutdown(self):
        """Shutdown the plugin."""
        self._initialized = False

    def get_schema(self) -> Dict[str, Any]:
        """Get the plugin schema."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["search", "install", "uninstall", "list", "upgrade", 
                            "upgrade_all", "show", "list_sources", "add_source",
                            "remove_source", "export", "import", "list_upgrades"]
                },
                "parameters": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "query": {"type": "string"},
                        "version": {"type": "string"},
                        "source": {"type": "string"},
                        "silent": {"type": "boolean"},
                        "exact": {"type": "boolean"}
                    }
                }
            }
        }


plugin = WindowsWingetPlugin()
