"""
Windows Subsystem for Linux (WSL) Integration - PRODUCTION

Provides comprehensive WSL management capabilities including:
- Listing and managing distributions
- Running commands in WSL distros
- Import/Export of WSL distributions
- WSL status and configuration management
- Distribution installation and removal
"""
import asyncio
from typing import Dict, Any, List, Optional
from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType
import logging

logger = logging.getLogger(__name__)


class WindowsWSLIntegrationPlugin(IntegrationPlugin):
    """Windows Subsystem for Linux (WSL) integration plugin."""
    
    def __init__(self):
        metadata = PluginMetadata(
            id="windows_wsl_integration",
            name="Windows WSL Integration",
            description="Comprehensive WSL management - distros, commands, import/export, configuration",
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["windows", "wsl", "linux", "virtualization"]
        )
        super().__init__(metadata)
        self.connected = False
        self._wsl_available = False
        self._wsl_version = None

    async def initialize(self) -> bool:
        """Initialize the WSL plugin and check availability."""
        result = await self._run_command(["wsl", "--status"])
        self._wsl_available = result["success"]
        if self._wsl_available:
            version_result = await self._run_command(["wsl", "--version"])
            if version_result["success"]:
                self._wsl_version = version_result["output"]
            logger.info("WSL is available")
        else:
            logger.warning("WSL not available on this system")
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

    async def _run_command(self, cmd: List[str], timeout: int = 60) -> Dict[str, Any]:
        """Execute a WSL command and return results."""
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
        """Execute a WSL operation."""
        if not self.connected:
            return {"success": False, "error": "Not connected"}
        
        if not self._wsl_available and action not in ["status", "install_wsl"]:
            return {"success": False, "error": "WSL not available on this system"}

        actions = {
            "list_distros": self._list_distros,
            "list_running": self._list_running,
            "run_command": self._run_wsl_command,
            "shutdown": self._shutdown_wsl,
            "shutdown_distro": self._shutdown_distro,
            "terminate": self._terminate_distro,
            "set_default": self._set_default_distro,
            "export": self._export_distro,
            "import": self._import_distro,
            "unregister": self._unregister_distro,
            "status": self._get_status,
            "set_version": self._set_distro_version,
            "set_default_version": self._set_default_version,
            "update": self._update_wsl,
            "install_distro": self._install_distro,
            "list_online": self._list_online_distros,
        }

        if action not in actions:
            return {"success": False, "error": f"Unknown action: {action}. Available: {list(actions.keys())}"}

        try:
            return await actions[action](parameters)
        except Exception as e:
            logger.error(f"WSL operation failed: {e}")
            return {"success": False, "error": str(e)}

    async def _list_distros(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List all installed WSL distributions."""
        verbose = params.get("verbose", False)
        cmd = ["wsl", "--list"]
        if verbose:
            cmd.append("--verbose")
        
        result = await self._run_command(cmd)
        if result["success"]:
            distros = self._parse_distro_list(result["output"], verbose)
            return {"success": True, "distros": distros, "count": len(distros)}
        return result

    async def _list_running(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List running WSL distributions."""
        result = await self._run_command(["wsl", "--list", "--running", "--verbose"])
        if result["success"]:
            distros = self._parse_distro_list(result["output"], True)
            return {"success": True, "distros": distros, "count": len(distros)}
        return result

    async def _run_wsl_command(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run a command in a WSL distribution."""
        command = params.get("command")
        if not command:
            return {"success": False, "error": "Command parameter required"}
        
        distro = params.get("distro")
        user = params.get("user")
        working_dir = params.get("working_dir")
        
        cmd = ["wsl"]
        if distro:
            cmd.extend(["--distribution", distro])
        if user:
            cmd.extend(["--user", user])
        if working_dir:
            cmd.extend(["--cd", working_dir])
        cmd.extend(["--exec", "bash", "-c", command])
        
        timeout = params.get("timeout", 60)
        return await self._run_command(cmd, timeout)

    async def _shutdown_wsl(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Shutdown all WSL distributions."""
        return await self._run_command(["wsl", "--shutdown"])

    async def _shutdown_distro(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Terminate a specific distribution."""
        distro = params.get("distro")
        if not distro:
            return {"success": False, "error": "Distro parameter required"}
        return await self._run_command(["wsl", "--terminate", distro])

    async def _terminate_distro(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Terminate a specific distribution (alias for shutdown_distro)."""
        return await self._shutdown_distro(params)

    async def _set_default_distro(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set the default WSL distribution."""
        distro = params.get("distro")
        if not distro:
            return {"success": False, "error": "Distro parameter required"}
        return await self._run_command(["wsl", "--set-default", distro])

    async def _export_distro(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Export a WSL distribution to a tar file."""
        distro = params.get("distro")
        output_path = params.get("output_path")
        if not distro or not output_path:
            return {"success": False, "error": "Distro and output_path parameters required"}
        
        vhd = params.get("vhd", False)
        cmd = ["wsl", "--export", distro, output_path]
        if vhd:
            cmd.append("--vhd")
        
        return await self._run_command(cmd, timeout=3600)

    async def _import_distro(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Import a WSL distribution from a tar file."""
        distro = params.get("distro")
        install_location = params.get("install_location")
        tar_file = params.get("tar_file")
        
        if not all([distro, install_location, tar_file]):
            return {"success": False, "error": "distro, install_location, and tar_file parameters required"}
        
        version = params.get("version", "2")
        vhd = params.get("vhd", False)
        
        cmd = ["wsl", "--import", distro, install_location, tar_file, "--version", str(version)]
        if vhd:
            cmd.append("--vhd")
        
        return await self._run_command(cmd, timeout=3600)

    async def _unregister_distro(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Unregister (delete) a WSL distribution."""
        distro = params.get("distro")
        if not distro:
            return {"success": False, "error": "Distro parameter required"}
        return await self._run_command(["wsl", "--unregister", distro])

    async def _get_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get WSL status information."""
        result = await self._run_command(["wsl", "--status"])
        return {
            "success": True,
            "wsl_available": self._wsl_available,
            "wsl_version": self._wsl_version,
            "status_output": result.get("output", "")
        }

    async def _set_distro_version(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set a distribution to WSL 1 or WSL 2."""
        distro = params.get("distro")
        version = params.get("version", 2)
        if not distro:
            return {"success": False, "error": "Distro parameter required"}
        return await self._run_command(["wsl", "--set-version", distro, str(version)])

    async def _set_default_version(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set the default WSL version for new distributions."""
        version = params.get("version", 2)
        return await self._run_command(["wsl", "--set-default-version", str(version)])

    async def _update_wsl(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update WSL to the latest version."""
        return await self._run_command(["wsl", "--update"], timeout=300)

    async def _install_distro(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Install a WSL distribution from the Microsoft Store."""
        distro = params.get("distro")
        if not distro:
            return {"success": False, "error": "Distro parameter required"}
        return await self._run_command(["wsl", "--install", "--distribution", distro], timeout=600)

    async def _list_online_distros(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List available distributions from the Microsoft Store."""
        result = await self._run_command(["wsl", "--list", "--online"])
        if result["success"]:
            distros = self._parse_online_distros(result["output"])
            return {"success": True, "distros": distros, "count": len(distros)}
        return result

    def _parse_distro_list(self, output: str, verbose: bool = False) -> List[Dict[str, Any]]:
        """Parse WSL distribution list output."""
        distros = []
        lines = output.strip().split('\n')
        
        for line in lines[1:]:
            if not line.strip():
                continue
            
            is_default = line.startswith('*')
            line = line.lstrip('* ')
            
            if verbose:
                parts = line.split()
                if len(parts) >= 3:
                    distros.append({
                        "name": parts[0],
                        "state": parts[1] if len(parts) > 1 else "",
                        "version": parts[2] if len(parts) > 2 else "",
                        "is_default": is_default
                    })
            else:
                distros.append({"name": line.strip(), "is_default": is_default})
        
        return distros

    def _parse_online_distros(self, output: str) -> List[Dict[str, str]]:
        """Parse online distribution list."""
        distros = []
        lines = output.strip().split('\n')
        
        for line in lines[2:]:  # Skip header lines
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 2:
                distros.append({
                    "name": parts[0],
                    "friendly_name": ' '.join(parts[1:])
                })
        return distros

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
                    "enum": ["list_distros", "list_running", "run_command", "shutdown",
                            "shutdown_distro", "terminate", "set_default", "export",
                            "import", "unregister", "status", "set_version",
                            "set_default_version", "update", "install_distro", "list_online"]
                },
                "parameters": {
                    "type": "object",
                    "properties": {
                        "distro": {"type": "string"},
                        "command": {"type": "string"},
                        "user": {"type": "string"},
                        "output_path": {"type": "string"},
                        "version": {"type": "integer"}
                    }
                }
            }
        }


plugin = WindowsWSLIntegrationPlugin()
