"""
Windows Service Control Integration - PRODUCTION

Provides comprehensive Windows Service management capabilities including:
- Starting/stopping/restarting services
- Service status monitoring
- Service configuration changes
- Service dependency management
- Creating and deleting services
"""
import asyncio
import json
from typing import Dict, Any, Optional, List
from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType
import logging

logger = logging.getLogger(__name__)


class WindowsServiceControlPlugin(IntegrationPlugin):
    """Windows Service Control plugin with comprehensive service management."""
    
    def __init__(self):
        metadata = PluginMetadata(
            id="windows_service_control",
            name="Windows Service Control",
            description="Comprehensive Windows Service management - start, stop, restart, configure services",
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["windows", "service", "system", "administration"]
        )
        super().__init__(metadata)
        self.connected = False

    async def initialize(self) -> bool:
        """Initialize the service control plugin."""
        self._initialized = True
        return True

    async def connect(self, credentials: Dict[str, str]) -> bool:
        """Connect (local access)."""
        self.connected = True
        return True

    async def disconnect(self) -> bool:
        """Disconnect."""
        self.connected = False
        return True

    async def _run_powershell(self, command: str) -> Dict[str, Any]:
        """Execute a PowerShell command and return results."""
        try:
            process = await asyncio.create_subprocess_exec(
                "powershell", "-NoProfile", "-NonInteractive", "-Command", command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            return {
                "success": process.returncode == 0,
                "output": stdout.decode('utf-8', errors='replace').strip(),
                "error": stderr.decode('utf-8', errors='replace').strip() if stderr else None,
                "return_code": process.returncode
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def execute(self, action: str, parameters: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Execute a service control operation."""
        if not self.connected:
            return {"success": False, "error": "Not connected"}

        actions = {
            "list_services": self._list_services,
            "get_service": self._get_service,
            "start_service": self._start_service,
            "stop_service": self._stop_service,
            "restart_service": self._restart_service,
            "pause_service": self._pause_service,
            "resume_service": self._resume_service,
            "set_startup_type": self._set_startup_type,
            "get_dependencies": self._get_dependencies,
            "get_dependent_services": self._get_dependent_services,
            "create_service": self._create_service,
            "delete_service": self._delete_service,
            "set_service_account": self._set_service_account,
            "get_service_recovery": self._get_service_recovery,
            "set_service_recovery": self._set_service_recovery,
        }

        if action not in actions:
            return {"success": False, "error": f"Unknown action: {action}. Available: {list(actions.keys())}"}

        try:
            return await actions[action](parameters)
        except Exception as e:
            logger.error(f"Service control operation failed: {e}")
            return {"success": False, "error": str(e)}

    async def _list_services(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List all services or filter by status/type."""
        status_filter = params.get("status", "")  # Running, Stopped, Paused, etc.
        type_filter = params.get("type", "")  # Win32OwnProcess, Win32ShareProcess, etc.
        name_pattern = params.get("name_pattern", "*")
        
        where_clause = ""
        if status_filter:
            where_clause = f"| Where-Object {{ $_.Status -eq '{status_filter}' }}"
        
        cmd = f"""
        Get-Service -Name '{name_pattern}' {where_clause} | 
        Select-Object Name, DisplayName, Status, StartType, ServiceType |
        ConvertTo-Json -Depth 2
        """
        
        result = await self._run_powershell(cmd)
        if result["success"] and result["output"]:
            try:
                services = json.loads(result["output"]) if result["output"] else []
                if isinstance(services, dict):
                    services = [services]
                return {"success": True, "services": services, "count": len(services)}
            except json.JSONDecodeError:
                return {"success": True, "services": [], "raw_output": result["output"]}
        return {"success": True, "services": []}

    async def _get_service(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed information about a specific service."""
        service_name = params.get("service_name", "")
        
        if not service_name:
            return {"success": False, "error": "service_name is required"}
        
        cmd = f"""
        $svc = Get-Service -Name '{service_name}' -ErrorAction SilentlyContinue
        if ($svc) {{
            $wmi = Get-WmiObject Win32_Service -Filter "Name='{service_name}'"
            @{{
                Name = $svc.Name
                DisplayName = $svc.DisplayName
                Status = $svc.Status.ToString()
                StartType = $svc.StartType.ToString()
                ServiceType = $svc.ServiceType.ToString()
                CanStop = $svc.CanStop
                CanPauseAndContinue = $svc.CanPauseAndContinue
                Description = $wmi.Description
                PathName = $wmi.PathName
                ProcessId = $wmi.ProcessId
                StartName = $wmi.StartName
            }} | ConvertTo-Json
        }} else {{
            @{{ error = "Service not found" }} | ConvertTo-Json
        }}
        """
        
        result = await self._run_powershell(cmd)
        if result["success"] and result["output"]:
            try:
                svc_info = json.loads(result["output"])
                if "error" in svc_info:
                    return {"success": False, "error": svc_info["error"]}
                return {"success": True, "service": svc_info}
            except json.JSONDecodeError:
                return {"success": False, "error": "Failed to parse service info"}
        return result

    async def _start_service(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Start a service."""
        service_name = params.get("service_name", "")
        wait = params.get("wait", True)
        
        if not service_name:
            return {"success": False, "error": "service_name is required"}
        
        cmd = f"Start-Service -Name '{service_name}' -PassThru | Select-Object Name, Status | ConvertTo-Json"
        result = await self._run_powershell(cmd)
        
        if result["success"]:
            return {"success": True, "message": f"Service '{service_name}' started"}
        return result

    async def _stop_service(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Stop a service."""
        service_name = params.get("service_name", "")
        force = params.get("force", False)
        
        if not service_name:
            return {"success": False, "error": "service_name is required"}
        
        force_flag = "-Force" if force else ""
        cmd = f"Stop-Service -Name '{service_name}' {force_flag} -PassThru | Select-Object Name, Status | ConvertTo-Json"
        result = await self._run_powershell(cmd)
        
        if result["success"]:
            return {"success": True, "message": f"Service '{service_name}' stopped"}
        return result

    async def _restart_service(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Restart a service."""
        service_name = params.get("service_name", "")
        force = params.get("force", False)
        
        if not service_name:
            return {"success": False, "error": "service_name is required"}
        
        force_flag = "-Force" if force else ""
        cmd = f"Restart-Service -Name '{service_name}' {force_flag} -PassThru | Select-Object Name, Status | ConvertTo-Json"
        result = await self._run_powershell(cmd)
        
        if result["success"]:
            return {"success": True, "message": f"Service '{service_name}' restarted"}
        return result

    async def _pause_service(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Pause a service."""
        service_name = params.get("service_name", "")
        
        if not service_name:
            return {"success": False, "error": "service_name is required"}
        
        cmd = f"Suspend-Service -Name '{service_name}' -PassThru | Select-Object Name, Status | ConvertTo-Json"
        result = await self._run_powershell(cmd)
        
        if result["success"]:
            return {"success": True, "message": f"Service '{service_name}' paused"}
        return result

    async def _resume_service(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Resume a paused service."""
        service_name = params.get("service_name", "")
        
        if not service_name:
            return {"success": False, "error": "service_name is required"}
        
        cmd = f"Resume-Service -Name '{service_name}' -PassThru | Select-Object Name, Status | ConvertTo-Json"
        result = await self._run_powershell(cmd)
        
        if result["success"]:
            return {"success": True, "message": f"Service '{service_name}' resumed"}
        return result

    async def _set_startup_type(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set the startup type of a service."""
        service_name = params.get("service_name", "")
        startup_type = params.get("startup_type", "")  # Automatic, Manual, Disabled, Boot, System
        
        if not service_name or not startup_type:
            return {"success": False, "error": "service_name and startup_type are required"}
        
        valid_types = ["Automatic", "Manual", "Disabled", "Boot", "System", "AutomaticDelayedStart"]
        if startup_type not in valid_types:
            return {"success": False, "error": f"startup_type must be one of: {valid_types}"}
        
        cmd = f"Set-Service -Name '{service_name}' -StartupType '{startup_type}'"
        result = await self._run_powershell(cmd)
        
        if result["success"]:
            return {"success": True, "message": f"Service '{service_name}' startup type set to '{startup_type}'"}
        return result

    async def _get_dependencies(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get services that this service depends on."""
        service_name = params.get("service_name", "")
        
        if not service_name:
            return {"success": False, "error": "service_name is required"}
        
        cmd = f"""
        $svc = Get-Service -Name '{service_name}'
        $svc.ServicesDependedOn | Select-Object Name, DisplayName, Status | ConvertTo-Json
        """
        
        result = await self._run_powershell(cmd)
        if result["success"] and result["output"]:
            try:
                deps = json.loads(result["output"]) if result["output"] else []
                if isinstance(deps, dict):
                    deps = [deps]
                return {"success": True, "dependencies": deps}
            except json.JSONDecodeError:
                return {"success": True, "dependencies": []}
        return {"success": True, "dependencies": []}

    async def _get_dependent_services(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get services that depend on this service."""
        service_name = params.get("service_name", "")
        
        if not service_name:
            return {"success": False, "error": "service_name is required"}
        
        cmd = f"""
        $svc = Get-Service -Name '{service_name}'
        $svc.DependentServices | Select-Object Name, DisplayName, Status | ConvertTo-Json
        """
        
        result = await self._run_powershell(cmd)
        if result["success"] and result["output"]:
            try:
                deps = json.loads(result["output"]) if result["output"] else []
                if isinstance(deps, dict):
                    deps = [deps]
                return {"success": True, "dependent_services": deps}
            except json.JSONDecodeError:
                return {"success": True, "dependent_services": []}
        return {"success": True, "dependent_services": []}

    async def _create_service(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new Windows service."""
        service_name = params.get("service_name", "")
        display_name = params.get("display_name", "")
        binary_path = params.get("binary_path", "")
        startup_type = params.get("startup_type", "Manual")
        description = params.get("description", "")
        
        if not service_name or not binary_path:
            return {"success": False, "error": "service_name and binary_path are required"}
        
        display_name = display_name or service_name
        
        cmd = f"""
        New-Service -Name '{service_name}' -DisplayName '{display_name}' -BinaryPathName '{binary_path}' -StartupType '{startup_type}' -Description '{description}'
        @{{ success = $true; service_name = '{service_name}' }} | ConvertTo-Json
        """
        
        result = await self._run_powershell(cmd)
        if result["success"]:
            return {"success": True, "message": f"Service '{service_name}' created successfully"}
        return result

    async def _delete_service(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a Windows service."""
        service_name = params.get("service_name", "")
        
        if not service_name:
            return {"success": False, "error": "service_name is required"}
        
        # First stop the service if running
        await self._stop_service({"service_name": service_name, "force": True})
        
        # Use sc.exe to delete (more reliable than Remove-Service which requires newer PowerShell)
        cmd = f"sc.exe delete '{service_name}'"
        result = await self._run_powershell(cmd)
        
        if result["success"] or "SUCCESS" in result.get("output", ""):
            return {"success": True, "message": f"Service '{service_name}' deleted successfully"}
        return result

    async def _set_service_account(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set the account under which a service runs."""
        service_name = params.get("service_name", "")
        account = params.get("account", "")  # LocalSystem, NT AUTHORITY\LocalService, etc.
        password = params.get("password", "")  # Empty for built-in accounts
        
        if not service_name or not account:
            return {"success": False, "error": "service_name and account are required"}
        
        if password:
            cmd = f"sc.exe config '{service_name}' obj= '{account}' password= '{password}'"
        else:
            cmd = f"sc.exe config '{service_name}' obj= '{account}'"
        
        result = await self._run_powershell(cmd)
        if result["success"] or "SUCCESS" in result.get("output", ""):
            return {"success": True, "message": f"Service account updated to '{account}'"}
        return result

    async def _get_service_recovery(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get service recovery options."""
        service_name = params.get("service_name", "")
        
        if not service_name:
            return {"success": False, "error": "service_name is required"}
        
        cmd = f"sc.exe qfailure '{service_name}'"
        result = await self._run_powershell(cmd)
        
        if result["success"]:
            return {"success": True, "recovery_info": result["output"]}
        return result

    async def _set_service_recovery(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set service recovery options."""
        service_name = params.get("service_name", "")
        first_failure = params.get("first_failure", "restart")  # restart, run, reboot, none
        second_failure = params.get("second_failure", "restart")
        subsequent_failure = params.get("subsequent_failure", "restart")
        reset_period = params.get("reset_period", 86400)  # seconds
        restart_delay = params.get("restart_delay", 60000)  # milliseconds
        
        if not service_name:
            return {"success": False, "error": "service_name is required"}
        
        actions = f"actions= {first_failure}/{restart_delay}/{second_failure}/{restart_delay}/{subsequent_failure}/{restart_delay}"
        cmd = f"sc.exe failure '{service_name}' reset= {reset_period} {actions}"
        
        result = await self._run_powershell(cmd)
        if result["success"] or "SUCCESS" in result.get("output", ""):
            return {"success": True, "message": "Service recovery options updated"}
        return result

    async def shutdown(self):
        """Shutdown the plugin."""
        self._initialized = False

    def get_schema(self) -> Dict[str, Any]:
        """Return the plugin schema."""
        return {
            "type": "object",
            "actions": {
                "list_services": {"params": {"status": "string (optional)", "name_pattern": "string (optional)"}},
                "get_service": {"params": {"service_name": "string"}},
                "start_service": {"params": {"service_name": "string"}},
                "stop_service": {"params": {"service_name": "string", "force": "bool (optional)"}},
                "restart_service": {"params": {"service_name": "string", "force": "bool (optional)"}},
                "pause_service": {"params": {"service_name": "string"}},
                "resume_service": {"params": {"service_name": "string"}},
                "set_startup_type": {"params": {"service_name": "string", "startup_type": "Automatic|Manual|Disabled"}},
                "get_dependencies": {"params": {"service_name": "string"}},
                "get_dependent_services": {"params": {"service_name": "string"}},
                "create_service": {"params": {"service_name": "string", "binary_path": "string", "display_name": "string (optional)"}},
                "delete_service": {"params": {"service_name": "string"}},
                "set_service_account": {"params": {"service_name": "string", "account": "string", "password": "string (optional)"}},
                "get_service_recovery": {"params": {"service_name": "string"}},
                "set_service_recovery": {"params": {"service_name": "string", "first_failure": "restart|run|reboot|none"}}
            }
        }


plugin = WindowsServiceControlPlugin()
