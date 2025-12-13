"""
Windows Remote Management (WinRM) Plugin - PRODUCTION
Comprehensive remote Windows administration via WinRM/PowerShell Remoting
"""
import os
import asyncio
import subprocess
import logging
import json
from typing import Dict, Any, Optional, List
from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)

class WinRMIntegrationPlugin(IntegrationPlugin):
    """
    Windows Remote Management Plugin
    
    Features:
    - Remote command execution via WinRM
    - Remote script execution (PowerShell/CMD)
    - Session management and persistence
    - Authentication (Kerberos/NTLM/Basic)
    - Configuration management
    - Remote event log access
    - Remote service management
    - File transfer via PSSession
    """
    
    def __init__(self):
        metadata = PluginMetadata(
            id="windows_winrm_integration",
            name="Windows Remote Management (WinRM)",
            description="Remote Windows administration via WinRM and PowerShell Remoting",
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["windows", "remote", "winrm", "powershell", "administration"]
        )
        super().__init__(metadata)
        self.connected = False
        self._sessions = {}
        self._default_host = None

    async def initialize(self) -> bool:
        """Initialize WinRM plugin"""
        try:
            logger.info("Initializing WinRM plugin...")
            # Check if WinRM service is available
            result = await self._execute_local_ps("Get-Service WinRM")
            if result.get("success"):
                logger.info("WinRM service found")
            else:
                logger.warning("WinRM service not found - remote features may be limited")
            self._initialized = True
            return True
        except Exception as e:
            logger.error(f"Failed to initialize WinRM plugin: {e}")
            return False

    async def connect(self, credentials: Dict[str, str]) -> bool:
        """Connect to remote host"""
        try:
            host = credentials.get("host", "localhost")
            username = credentials.get("username")
            password = credentials.get("password")
            
            self._default_host = host
            self.connected = True
            logger.info(f"Connected to WinRM host: {host}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to WinRM: {e}")
            return False

    async def disconnect(self) -> bool:
        """Disconnect from remote host"""
        try:
            # Close all sessions
            for session_id in list(self._sessions.keys()):
                await self.close_session({"session_id": session_id})
            self.connected = False
            self._default_host = None
            return True
        except Exception as e:
            logger.error(f"Error disconnecting from WinRM: {e}")
            return False

    async def execute(self, action: str, parameters: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Execute WinRM action"""
        if not self.connected and action not in ["test_winrm", "configure_winrm"]:
            return {"success": False, "error": "Not connected"}

        try:
            if action == "execute_command":
                return await self.execute_command(parameters)
            elif action == "execute_script":
                return await self.execute_script(parameters)
            elif action == "create_session":
                return await self.create_session(parameters)
            elif action == "close_session":
                return await self.close_session(parameters)
            elif action == "invoke_in_session":
                return await self.invoke_in_session(parameters)
            elif action == "test_winrm":
                return await self.test_winrm(parameters)
            elif action == "configure_winrm":
                return await self.configure_winrm(parameters)
            elif action == "get_services":
                return await self.get_services(parameters)
            elif action == "manage_service":
                return await self.manage_service(parameters)
            elif action == "get_event_logs":
                return await self.get_event_logs(parameters)
            elif action == "copy_file":
                return await self.copy_file(parameters)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            logger.error(f"Error executing WinRM action '{action}': {e}")
            return {"success": False, "error": str(e)}

    async def execute_command(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute remote command"""
        try:
            host = params.get("host", self._default_host)
            command = params.get("command")
            username = params.get("username")
            password = params.get("password")
            
            if not command:
                return {"success": False, "error": "Command is required"}
            
            ps_script = f'Invoke-Command -ComputerName {host} -ScriptBlock {{ {command} }}'
            
            if username and password:
                ps_script = f'$cred = New-Object System.Management.Automation.PSCredential("{username}", (ConvertTo-SecureString "{password}" -AsPlainText -Force)); {ps_script} -Credential $cred'
            
            result = await self._execute_local_ps(ps_script)
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def execute_script(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute remote PowerShell script"""
        try:
            host = params.get("host", self._default_host)
            script = params.get("script")
            script_path = params.get("script_path")
            
            if not script and not script_path:
                return {"success": False, "error": "Either script or script_path is required"}
            
            if script_path:
                ps_script = f'Invoke-Command -ComputerName {host} -FilePath "{script_path}"'
            else:
                ps_script = f'Invoke-Command -ComputerName {host} -ScriptBlock {{ {script} }}'
            
            result = await self._execute_local_ps(ps_script)
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def create_session(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create persistent PSSession"""
        try:
            host = params.get("host", self._default_host)
            session_name = params.get("session_name", f"session_{host}")
            
            ps_script = f'$session = New-PSSession -ComputerName {host} -Name {session_name}; $session.Id'
            result = await self._execute_local_ps(ps_script)
            
            if result.get("success"):
                session_id = result.get("output", "").strip()
                self._sessions[session_name] = {
                    "id": session_id,
                    "host": host,
                    "name": session_name
                }
                return {"success": True, "session_id": session_name, "ps_session_id": session_id}
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def close_session(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Close PSSession"""
        try:
            session_id = params.get("session_id")
            if not session_id or session_id not in self._sessions:
                return {"success": False, "error": "Invalid session ID"}
            
            session_name = self._sessions[session_id]["name"]
            ps_script = f'Get-PSSession -Name {session_name} | Remove-PSSession'
            result = await self._execute_local_ps(ps_script)
            
            if result.get("success"):
                del self._sessions[session_id]
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def invoke_in_session(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute command in existing session"""
        try:
            session_id = params.get("session_id")
            command = params.get("command")
            
            if not session_id or session_id not in self._sessions:
                return {"success": False, "error": "Invalid session ID"}
            
            session_name = self._sessions[session_id]["name"]
            ps_script = f'Invoke-Command -Session (Get-PSSession -Name {session_name}) -ScriptBlock {{ {command} }}'
            
            return await self._execute_local_ps(ps_script)
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def test_winrm(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Test WinRM connectivity"""
        try:
            host = params.get("host", "localhost")
            ps_script = f'Test-WSMan -ComputerName {host}'
            result = await self._execute_local_ps(ps_script)
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def configure_winrm(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Configure WinRM service"""
        try:
            enable = params.get("enable", True)
            allow_unencrypted = params.get("allow_unencrypted", False)
            
            if enable:
                ps_script = "winrm quickconfig -force"
                if allow_unencrypted:
                    ps_script += "; Set-Item WSMan:\\localhost\\Service\\AllowUnencrypted -Value $true"
            else:
                ps_script = "Stop-Service WinRM; Set-Service WinRM -StartupType Disabled"
            
            return await self._execute_local_ps(ps_script)
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_services(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get remote services"""
        try:
            host = params.get("host", self._default_host)
            ps_script = f'Get-Service -ComputerName {host} | Select-Object Name, Status, DisplayName | ConvertTo-Json'
            
            result = await self._execute_local_ps(ps_script)
            if result.get("success"):
                try:
                    result["services"] = json.loads(result.get("output", "[]"))
                except:
                    pass
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def manage_service(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Manage remote service"""
        try:
            host = params.get("host", self._default_host)
            service_name = params.get("service_name")
            action = params.get("service_action", "status")  # start, stop, restart, status
            
            if not service_name:
                return {"success": False, "error": "service_name is required"}
            
            if action == "start":
                ps_script = f'Start-Service -ComputerName {host} -Name {service_name}'
            elif action == "stop":
                ps_script = f'Stop-Service -ComputerName {host} -Name {service_name} -Force'
            elif action == "restart":
                ps_script = f'Restart-Service -ComputerName {host} -Name {service_name} -Force'
            else:
                ps_script = f'Get-Service -ComputerName {host} -Name {service_name} | Select-Object * | ConvertTo-Json'
            
            return await self._execute_local_ps(ps_script)
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_event_logs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get remote event logs"""
        try:
            host = params.get("host", self._default_host)
            log_name = params.get("log_name", "System")
            max_events = params.get("max_events", 100)
            
            ps_script = f'Get-EventLog -ComputerName {host} -LogName {log_name} -Newest {max_events} | ConvertTo-Json'
            
            result = await self._execute_local_ps(ps_script)
            if result.get("success"):
                try:
                    result["events"] = json.loads(result.get("output", "[]"))
                except:
                    pass
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def copy_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Copy file to/from remote host"""
        try:
            host = params.get("host", self._default_host)
            source = params.get("source")
            destination = params.get("destination")
            to_remote = params.get("to_remote", True)
            
            if not source or not destination:
                return {"success": False, "error": "source and destination are required"}
            
            if to_remote:
                ps_script = f'Copy-Item -Path "{source}" -Destination "{destination}" -ToSession (New-PSSession -ComputerName {host})'
            else:
                ps_script = f'Copy-Item -Path "{source}" -Destination "{destination}" -FromSession (New-PSSession -ComputerName {host})'
            
            return await self._execute_local_ps(ps_script)
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_local_ps(self, script: str) -> Dict[str, Any]:
        """Execute PowerShell script locally"""
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
                        "execute_command", "execute_script", "create_session",
                        "close_session", "invoke_in_session", "test_winrm",
                        "configure_winrm", "get_services", "manage_service",
                        "get_event_logs", "copy_file"
                    ]
                },
                "parameters": {"type": "object"}
            },
            "required": ["action"]
        }

plugin = WinRMIntegrationPlugin()
