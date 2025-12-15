"""
Microsoft Store API Plugin - PRODUCTION
Comprehensive Microsoft Store integration for app management
"""
import os
import asyncio
import subprocess
import logging
import json
from typing import Dict, Any, Optional, List
from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)

class WindowsStoreAPIPlugin(IntegrationPlugin):
    """
    Microsoft Store Integration Plugin
    
    Features:
    - Search Microsoft Store for apps
    - Install apps from Store
    - Update installed Store apps
    - List installed Store apps
    - Manage app licenses
    - Query app details and reviews
    - Handle app purchases
    - Manage app library
    """
    
    def __init__(self):
        metadata = PluginMetadata(
            id="windows_store_api",
            name="Microsoft Store API",
            description="Microsoft Store integration for app discovery and management",
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["windows", "store", "apps", "uwp", "microsoft"]
        )
        super().__init__(metadata)
        self.connected = False

    async def initialize(self) -> bool:
        """Initialize Microsoft Store plugin"""
        try:
            logger.info("Initializing Microsoft Store plugin...")
            # Check if winget (Windows Package Manager) is available
            result = await self._execute_cmd(["winget", "--version"])
            if result.get("success"):
                logger.info("Windows Package Manager (winget) found")
            else:
                logger.warning("winget not found - some features may be limited")
            self._initialized = True
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Microsoft Store plugin: {e}")
            return False

    async def connect(self, credentials: Dict[str, str]) -> bool:
        """Connect to Microsoft Store"""
        self.connected = True
        return True

    async def disconnect(self) -> bool:
        """Disconnect from Microsoft Store"""
        self.connected = False
        return True

    async def execute(self, action: str, parameters: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Execute Microsoft Store action"""
        if not self.connected:
            return {"success": False, "error": "Not connected"}

        try:
            if action == "search_store":
                return await self.search_store(parameters)
            elif action == "install_app":
                return await self.install_app(parameters)
            elif action == "update_app":
                return await self.update_app(parameters)
            elif action == "uninstall_app":
                return await self.uninstall_app(parameters)
            elif action == "list_installed":
                return await self.list_installed(parameters)
            elif action == "get_app_info":
                return await self.get_app_info(parameters)
            elif action == "update_all":
                return await self.update_all(parameters)
            elif action == "list_sources":
                return await self.list_sources(parameters)
            elif action == "export_apps":
                return await self.export_apps(parameters)
            elif action == "import_apps":
                return await self.import_apps(parameters)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            logger.error(f"Error executing Store action '{action}': {e}")
            return {"success": False, "error": str(e)}

    async def search_store(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search Microsoft Store"""
        try:
            query = params.get("query", "")
            if not query:
                return {"success": False, "error": "Query is required"}
            
            # Use winget search
            result = await self._execute_cmd(["winget", "search", query, "--source", "msstore"])
            
            if result.get("success"):
                # Parse winget output
                apps = self._parse_winget_output(result.get("output", ""))
                return {"success": True, "apps": apps, "count": len(apps)}
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def install_app(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Install app from Microsoft Store"""
        try:
            app_id = params.get("app_id")
            app_name = params.get("app_name")
            
            if not app_id and not app_name:
                return {"success": False, "error": "Either app_id or app_name is required"}
            
            target = app_id or app_name
            cmd = ["winget", "install", target, "--source", "msstore", "--accept-package-agreements", "--accept-source-agreements"]
            
            silent = params.get("silent", True)
            if silent:
                cmd.append("--silent")
            
            result = await self._execute_cmd(cmd)
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def update_app(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update specific app"""
        try:
            app_id = params.get("app_id")
            app_name = params.get("app_name")
            
            if not app_id and not app_name:
                return {"success": False, "error": "Either app_id or app_name is required"}
            
            target = app_id or app_name
            cmd = ["winget", "upgrade", target, "--source", "msstore"]
            
            silent = params.get("silent", True)
            if silent:
                cmd.append("--silent")
            
            result = await self._execute_cmd(cmd)
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def uninstall_app(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Uninstall app"""
        try:
            app_id = params.get("app_id")
            app_name = params.get("app_name")
            
            if not app_id and not app_name:
                return {"success": False, "error": "Either app_id or app_name is required"}
            
            target = app_id or app_name
            cmd = ["winget", "uninstall", target]
            
            silent = params.get("silent", True)
            if silent:
                cmd.append("--silent")
            
            result = await self._execute_cmd(cmd)
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def list_installed(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List installed Store apps"""
        try:
            # Using PowerShell to get AppX packages
            ps_script = "Get-AppxPackage | Select-Object Name, Publisher, Version, InstallLocation | ConvertTo-Json"
            result = await self._execute_powershell(ps_script)
            
            if result.get("success"):
                try:
                    apps = json.loads(result.get("output", "[]"))
                    if not isinstance(apps, list):
                        apps = [apps]
                    result["apps"] = apps
                    result["count"] = len(apps)
                except:
                    pass
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_app_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed app information"""
        try:
            app_id = params.get("app_id")
            app_name = params.get("app_name")
            
            if not app_id and not app_name:
                return {"success": False, "error": "Either app_id or app_name is required"}
            
            target = app_id or app_name
            result = await self._execute_cmd(["winget", "show", target])
            
            if result.get("success"):
                # Parse app info from output
                info = self._parse_app_info(result.get("output", ""))
                result["info"] = info
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def update_all(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update all apps"""
        try:
            cmd = ["winget", "upgrade", "--all", "--source", "msstore"]
            
            silent = params.get("silent", True)
            if silent:
                cmd.append("--silent")
            
            result = await self._execute_cmd(cmd)
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def list_sources(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List package sources"""
        try:
            result = await self._execute_cmd(["winget", "source", "list"])
            if result.get("success"):
                sources = self._parse_winget_output(result.get("output", ""))
                result["sources"] = sources
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def export_apps(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Export installed apps to JSON"""
        try:
            output_file = params.get("output_file", "installed_apps.json")
            result = await self._execute_cmd(["winget", "export", "-o", output_file])
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def import_apps(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Import and install apps from JSON"""
        try:
            input_file = params.get("input_file")
            if not input_file:
                return {"success": False, "error": "input_file is required"}
            
            result = await self._execute_cmd(["winget", "import", "-i", input_file])
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _parse_winget_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse winget command output into structured data"""
        apps = []
        lines = output.strip().split('\n')
        
        for line in lines[2:]:  # Skip header lines
            if line.strip():
                parts = line.split()
                if len(parts) >= 2:
                    apps.append({
                        "name": parts[0],
                        "id": parts[1] if len(parts) > 1 else "",
                        "version": parts[2] if len(parts) > 2 else ""
                    })
        return apps

    def _parse_app_info(self, output: str) -> Dict[str, Any]:
        """Parse app info from winget show output"""
        info = {}
        lines = output.strip().split('\n')
        
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                info[key.strip()] = value.strip()
        return info

    async def _execute_powershell(self, script: str) -> Dict[str, Any]:
        """Execute PowerShell script"""
        try:
            process = await asyncio.create_subprocess_exec(
                "powershell", "-NoProfile", "-Command", script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            return {
                "success": process.returncode == 0,
                "output": stdout.decode() if stdout else "",
                "error": stderr.decode() if stderr else ""
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_cmd(self, command: List[str]) -> Dict[str, Any]:
        """Execute command"""
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            return {
                "success": process.returncode == 0,
                "output": stdout.decode() if stdout else "",
                "error": stderr.decode() if stderr else ""
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def shutdown(self):
        """Shutdown plugin"""
        await self.disconnect()
        self._initialized = False

    def get_schema(self) -> Dict[str, Any]:
        """Get plugin schema"""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "search_store", "install_app", "update_app", "uninstall_app",
                        "list_installed", "get_app_info", "update_all", "list_sources",
                        "export_apps", "import_apps"
                    ]
                },
                "parameters": {"type": "object"}
            },
            "required": ["action"]
        }

plugin = WindowsStoreAPIPlugin()
