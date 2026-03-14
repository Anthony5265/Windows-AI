"""
Windows Remote Management (WinRM) Plugin for Windows AI
Comprehensive PowerShell Remoting and WinRM session management
"""

import asyncio
import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class AuthenticationMethod(Enum):
    """WinRM authentication methods"""
    DEFAULT = "Default"
    BASIC = "Basic"
    NEGOTIATE = "Negotiate"
    KERBEROS = "Kerberos"
    CREDSSP = "CredSSP"
    DIGEST = "Digest"
    CERTIFICATE = "Certificate"


class SessionState(Enum):
    """Remote session states"""
    OPENED = "Opened"
    CLOSED = "Closed"
    DISCONNECTED = "Disconnected"
    BROKEN = "Broken"


@dataclass
class RemoteSession:
    """Represents a WinRM remote session"""
    session_id: str
    computer_name: str
    state: SessionState
    created_at: datetime
    authentication: AuthenticationMethod
    port: int = 5985
    use_ssl: bool = False
    config_name: Optional[str] = None
    application_name: Optional[str] = None
    idle_timeout: int = 7200000  # 2 hours in ms
    open_timeout: int = 180000  # 3 minutes in ms


@dataclass
class TrustedHost:
    """Represents a trusted host entry"""
    host_pattern: str
    added_at: datetime
    is_wildcard: bool = False


@dataclass
class WinRMListener:
    """Represents a WinRM listener configuration"""
    address: str
    transport: str
    port: int
    hostname: Optional[str] = None
    certificate_thumbprint: Optional[str] = None
    enabled: bool = True


@dataclass
class RemoteJob:
    """Represents a remote background job"""
    job_id: str
    name: str
    computer_name: str
    state: str
    command: str
    started_at: datetime
    has_more_data: bool = True


class WindowsWinRMPlugin(IntegrationPlugin):
    """
    Comprehensive Windows Remote Management plugin
    
    Provides:
    - Remote session management (New-PSSession, Enter-PSSession, Remove-PSSession)
    - Invoke-Command for remote execution
    - Trusted hosts management
    - WinRM service configuration
    - Remote background jobs
    - Session configuration management
    - Certificate-based authentication setup
    - Firewall rule management for WinRM
    - Listener configuration
    - Credential management for remoting
    """
    
    def __init__(self):
        metadata = PluginMetadata(
            id="windows-winrm",
            name="Windows Remote Management",
            description="PowerShell Remoting and WinRM session management",
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
        )
        super().__init__(metadata)
        self._sessions: Dict[str, RemoteSession] = {}
        self._jobs: Dict[str, RemoteJob] = {}
        self._trusted_hosts: List[TrustedHost] = []
    

    async def connect(self, credentials: Dict[str, str]) -> bool:
        """Connect to the service"""
        return True

    async def disconnect(self) -> bool:
        """Disconnect from the service"""
        return True

    async def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """Execute WinRM actions"""
        actions = {
            # Session Management
            "create_session": self._create_session,
            "get_session": self._get_session,
            "list_sessions": self._list_sessions,
            "remove_session": self._remove_session,
            "disconnect_session": self._disconnect_session,
            "reconnect_session": self._reconnect_session,
            "enter_session": self._enter_session,
            
            # Remote Execution
            "invoke_command": self._invoke_command,
            "invoke_script": self._invoke_script,
            "invoke_script_file": self._invoke_script_file,
            "copy_item_to_remote": self._copy_item_to_remote,
            "copy_item_from_remote": self._copy_item_from_remote,
            
            # Background Jobs
            "start_job": self._start_job,
            "get_job": self._get_job,
            "list_jobs": self._list_jobs,
            "receive_job": self._receive_job,
            "stop_job": self._stop_job,
            "remove_job": self._remove_job,
            "wait_job": self._wait_job,
            
            # Trusted Hosts
            "get_trusted_hosts": self._get_trusted_hosts,
            "add_trusted_host": self._add_trusted_host,
            "remove_trusted_host": self._remove_trusted_host,
            "clear_trusted_hosts": self._clear_trusted_hosts,
            
            # WinRM Service
            "get_winrm_status": self._get_winrm_status,
            "enable_winrm": self._enable_winrm,
            "disable_winrm": self._disable_winrm,
            "restart_winrm": self._restart_winrm,
            "quickconfig": self._quickconfig,
            
            # Listeners
            "get_listeners": self._get_listeners,
            "create_listener": self._create_listener,
            "remove_listener": self._remove_listener,
            "configure_https_listener": self._configure_https_listener,
            
            # Configuration
            "get_winrm_config": self._get_winrm_config,
            "set_winrm_config": self._set_winrm_config,
            "get_session_configurations": self._get_session_configurations,
            "create_session_configuration": self._create_session_configuration,
            "remove_session_configuration": self._remove_session_configuration,
            
            # Firewall
            "get_winrm_firewall_rules": self._get_winrm_firewall_rules,
            "enable_winrm_firewall_rules": self._enable_winrm_firewall_rules,
            "disable_winrm_firewall_rules": self._disable_winrm_firewall_rules,
            
            # Credentials
            "test_connection": self._test_connection,
            "test_wsman": self._test_wsman,
            
            # Diagnostics
            "get_winrm_diagnostics": self._get_winrm_diagnostics,
            "analyze_connectivity": self._analyze_connectivity,
        }
        
        if action not in actions:
            return {"error": f"Unknown action: {action}", "available_actions": list(actions.keys())}
        
        try:
            return await actions[action](**kwargs)
        except Exception as e:
            logger.error(f"WinRM action '{action}' failed: {e}")
            return {"error": str(e), "action": action}
    
    # ========== Session Management ==========
    
    async def _create_session(
        self,
        computer_name: str,
        credential: Optional[Dict[str, str]] = None,
        authentication: str = "Default",
        port: int = 5985,
        use_ssl: bool = False,
        session_option: Optional[Dict[str, Any]] = None,
        config_name: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a new remote PowerShell session"""
        session_id = str(uuid.uuid4())[:8]
        
        # Build credential parameter
        cred_param = ""
        if credential:
            username = credential.get("username", "")
            password = credential.get("password", "")
            cred_param = f"""
$secPassword = ConvertTo-SecureString '{password}' -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential('{username}', $secPassword)
"""
        
        # Build session options
        option_param = ""
        if session_option:
            options = []
            if "skip_ca_check" in session_option:
                options.append("-SkipCACheck")
            if "skip_cn_check" in session_option:
                options.append("-SkipCNCheck")
            if "skip_revocation_check" in session_option:
                options.append("-SkipRevocationCheck")
            if "idle_timeout" in session_option:
                options.append(f"-IdleTimeout {session_option['idle_timeout']}")
            if "open_timeout" in session_option:
                options.append(f"-OpenTimeout {session_option['open_timeout']}")
            if options:
                option_param = f"$sessionOpt = New-PSSessionOption {' '.join(options)}"
        
        script = f"""
{cred_param}
{option_param}
$params = @{{
    ComputerName = '{computer_name}'
    Port = {port}
    UseSSL = ${str(use_ssl).lower()}
}}
{f"$params['Credential'] = $cred" if credential else ""}
{f"$params['Authentication'] = '{authentication}'" if authentication != "Default" else ""}
{f"$params['ConfigurationName'] = '{config_name}'" if config_name else ""}
{f"$params['SessionOption'] = $sessionOpt" if session_option else ""}

try {{
    $session = New-PSSession @params
    @{{
        success = $true
        session_id = $session.Id
        instance_id = $session.InstanceId.ToString()
        name = $session.Name
        computer_name = $session.ComputerName
        state = $session.State.ToString()
        availability = $session.Availability.ToString()
        config_name = $session.ConfigurationName
    }} | ConvertTo-Json
}} catch {{
    @{{
        success = $false
        error = $_.Exception.Message
        error_type = $_.Exception.GetType().Name
    }} | ConvertTo-Json
}}
"""
        result = await self._run_powershell(script)
        
        try:
            data = json.loads(result)
            if data.get("success"):
                # Track session locally
                auth_method = AuthenticationMethod[authentication.upper()] if authentication != "Default" else AuthenticationMethod.DEFAULT
                session = RemoteSession(
                    session_id=str(data.get("session_id")),
                    computer_name=computer_name,
                    state=SessionState.OPENED,
                    created_at=datetime.now(),
                    authentication=auth_method,
                    port=port,
                    use_ssl=use_ssl,
                    config_name=config_name
                )
                self._sessions[session.session_id] = session
            return data
        except json.JSONDecodeError:
            return {"error": "Failed to parse session result", "raw": result}
    
    async def _get_session(self, session_id: Optional[int] = None, computer_name: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Get information about remote sessions"""
        filter_param = ""
        if session_id is not None:
            filter_param = f"-Id {session_id}"
        elif computer_name:
            filter_param = f"-ComputerName '{computer_name}'"
        
        script = f"""
$sessions = Get-PSSession {filter_param}
$sessions | ForEach-Object {{
    @{{
        id = $_.Id
        instance_id = $_.InstanceId.ToString()
        name = $_.Name
        computer_name = $_.ComputerName
        state = $_.State.ToString()
        availability = $_.Availability.ToString()
        config_name = $_.ConfigurationName
        transport = $_.Transport.ToString()
        idle_timeout = $_.IdleTimeout
    }}
}} | ConvertTo-Json -AsArray
"""
        result = await self._run_powershell(script)
        try:
            return {"sessions": json.loads(result) if result.strip() else []}
        except json.JSONDecodeError:
            return {"sessions": [], "raw": result}
    
    async def _list_sessions(self, **kwargs) -> Dict[str, Any]:
        """List all active remote sessions"""
        return await self._get_session()
    
    async def _remove_session(self, session_id: int, **kwargs) -> Dict[str, Any]:
        """Remove/close a remote session"""
        script = f"""
try {{
    Remove-PSSession -Id {session_id} -ErrorAction Stop
    @{{ success = $true; message = "Session {session_id} removed" }} | ConvertTo-Json
}} catch {{
    @{{ success = $false; error = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        result = await self._run_powershell(script)
        # Remove from local tracking
        if str(session_id) in self._sessions:
            del self._sessions[str(session_id)]
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"success": True, "message": f"Session {session_id} removed"}
    
    async def _disconnect_session(self, session_id: int, **kwargs) -> Dict[str, Any]:
        """Disconnect a remote session (keeps it available for reconnection)"""
        script = f"""
try {{
    $session = Disconnect-PSSession -Id {session_id} -ErrorAction Stop
    @{{
        success = $true
        state = $session.State.ToString()
        message = "Session disconnected"
    }} | ConvertTo-Json
}} catch {{
    @{{ success = $false; error = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to disconnect session", "raw": result}
    
    async def _reconnect_session(self, session_id: int, **kwargs) -> Dict[str, Any]:
        """Reconnect to a disconnected session"""
        script = f"""
try {{
    $session = Connect-PSSession -Id {session_id} -ErrorAction Stop
    @{{
        success = $true
        state = $session.State.ToString()
        availability = $session.Availability.ToString()
        message = "Session reconnected"
    }} | ConvertTo-Json
}} catch {{
    @{{ success = $false; error = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to reconnect session", "raw": result}
    
    async def _enter_session(self, session_id: int, **kwargs) -> Dict[str, Any]:
        """Enter an interactive remote session (returns session info for GUI)"""
        script = f"""
$session = Get-PSSession -Id {session_id}
if ($session) {{
    @{{
        ready = $true
        session_id = $session.Id
        computer_name = $session.ComputerName
        state = $session.State.ToString()
        instructions = "Use Invoke-Command -Session (Get-PSSession -Id {session_id}) -ScriptBlock {{ <commands> }}"
    }} | ConvertTo-Json
}} else {{
    @{{ ready = $false; error = "Session not found" }} | ConvertTo-Json
}}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to prepare session", "raw": result}
    
    # ========== Remote Execution ==========
    
    async def _invoke_command(
        self,
        computer_name: Optional[str] = None,
        session_id: Optional[int] = None,
        script_block: str = "",
        argument_list: Optional[List[Any]] = None,
        credential: Optional[Dict[str, str]] = None,
        as_job: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute a command on remote computer(s)"""
        if not computer_name and session_id is None:
            return {"error": "Either computer_name or session_id must be provided"}
        
        # Build credential parameter
        cred_setup = ""
        cred_param = ""
        if credential:
            username = credential.get("username", "")
            password = credential.get("password", "")
            cred_setup = f"""
$secPassword = ConvertTo-SecureString '{password}' -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential('{username}', $secPassword)
"""
            cred_param = "-Credential $cred"
        
        # Build argument list
        args_param = ""
        if argument_list:
            args_str = ",".join([f"'{a}'" if isinstance(a, str) else str(a) for a in argument_list])
            args_param = f"-ArgumentList @({args_str})"
        
        # Target parameter
        target_param = f"-Session (Get-PSSession -Id {session_id})" if session_id else f"-ComputerName '{computer_name}'"
        
        # Job parameter
        job_param = "-AsJob" if as_job else ""
        
        # Escape script block
        escaped_block = script_block.replace("'", "''")
        
        script = f"""
{cred_setup}
try {{
    $result = Invoke-Command {target_param} {cred_param} {args_param} {job_param} -ScriptBlock {{
        {script_block}
    }} -ErrorAction Stop
    
    if ("{job_param}") {{
        @{{
            success = $true
            is_job = $true
            job_id = $result.Id
            job_name = $result.Name
            job_state = $result.State.ToString()
        }} | ConvertTo-Json
    }} else {{
        @{{
            success = $true
            result = $result
            result_type = if ($result) {{ $result.GetType().Name }} else {{ "null" }}
        }} | ConvertTo-Json -Depth 5
    }}
}} catch {{
    @{{
        success = $false
        error = $_.Exception.Message
        error_type = $_.Exception.GetType().Name
        script_stack_trace = $_.ScriptStackTrace
    }} | ConvertTo-Json
}}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"success": True, "result": result}
    
    async def _invoke_script(
        self,
        computer_name: str,
        script: str,
        credential: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute a multi-line script on remote computer"""
        return await self._invoke_command(
            computer_name=computer_name,
            script_block=script,
            credential=credential,
            **kwargs
        )
    
    async def _invoke_script_file(
        self,
        computer_name: str,
        file_path: str,
        credential: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute a local script file on remote computer"""
        # Build credential parameter
        cred_setup = ""
        cred_param = ""
        if credential:
            username = credential.get("username", "")
            password = credential.get("password", "")
            cred_setup = f"""
$secPassword = ConvertTo-SecureString '{password}' -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential('{username}', $secPassword)
"""
            cred_param = "-Credential $cred"
        
        script = f"""
{cred_setup}
try {{
    $result = Invoke-Command -ComputerName '{computer_name}' {cred_param} -FilePath '{file_path}' -ErrorAction Stop
    @{{
        success = $true
        result = $result
    }} | ConvertTo-Json -Depth 5
}} catch {{
    @{{ success = $false; error = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"success": True, "result": result}
    
    async def _copy_item_to_remote(
        self,
        session_id: int,
        local_path: str,
        remote_path: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Copy files to remote computer via session"""
        script = f"""
try {{
    $session = Get-PSSession -Id {session_id}
    Copy-Item -Path '{local_path}' -Destination '{remote_path}' -ToSession $session -Recurse -Force -ErrorAction Stop
    @{{
        success = $true
        message = "Copied '{local_path}' to '{remote_path}' on remote"
        local_path = '{local_path}'
        remote_path = '{remote_path}'
    }} | ConvertTo-Json
}} catch {{
    @{{ success = $false; error = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to copy item", "raw": result}
    
    async def _copy_item_from_remote(
        self,
        session_id: int,
        remote_path: str,
        local_path: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Copy files from remote computer via session"""
        script = f"""
try {{
    $session = Get-PSSession -Id {session_id}
    Copy-Item -Path '{remote_path}' -Destination '{local_path}' -FromSession $session -Recurse -Force -ErrorAction Stop
    @{{
        success = $true
        message = "Copied '{remote_path}' from remote to '{local_path}'"
        remote_path = '{remote_path}'
        local_path = '{local_path}'
    }} | ConvertTo-Json
}} catch {{
    @{{ success = $false; error = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to copy item", "raw": result}
    
    # ========== Background Jobs ==========
    
    async def _start_job(
        self,
        computer_name: str,
        script_block: str,
        job_name: Optional[str] = None,
        credential: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Start a background job on remote computer"""
        return await self._invoke_command(
            computer_name=computer_name,
            script_block=script_block,
            credential=credential,
            as_job=True,
            **kwargs
        )
    
    async def _get_job(self, job_id: int, **kwargs) -> Dict[str, Any]:
        """Get information about a specific job"""
        script = f"""
$job = Get-Job -Id {job_id} -ErrorAction SilentlyContinue
if ($job) {{
    @{{
        id = $job.Id
        name = $job.Name
        state = $job.State.ToString()
        has_more_data = $job.HasMoreData
        location = $job.Location
        command = $job.Command
        status_message = $job.StatusMessage
        pct_complete = $job.PercentComplete
    }} | ConvertTo-Json
}} else {{
    @{{ error = "Job not found" }} | ConvertTo-Json
}}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to get job info", "raw": result}
    
    async def _list_jobs(self, state: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """List all background jobs"""
        state_filter = f"-State {state}" if state else ""
        script = f"""
Get-Job {state_filter} | ForEach-Object {{
    @{{
        id = $_.Id
        name = $_.Name
        state = $_.State.ToString()
        has_more_data = $_.HasMoreData
        location = $_.Location
        command = $_.Command
    }}
}} | ConvertTo-Json -AsArray
"""
        result = await self._run_powershell(script)
        try:
            return {"jobs": json.loads(result) if result.strip() else []}
        except json.JSONDecodeError:
            return {"jobs": [], "raw": result}
    
    async def _receive_job(self, job_id: int, keep: bool = False, **kwargs) -> Dict[str, Any]:
        """Receive output from a background job"""
        keep_param = "-Keep" if keep else ""
        script = f"""
try {{
    $result = Receive-Job -Id {job_id} {keep_param} -ErrorAction Stop
    @{{
        success = $true
        result = $result
    }} | ConvertTo-Json -Depth 5
}} catch {{
    @{{ success = $false; error = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"success": True, "result": result}
    
    async def _stop_job(self, job_id: int, **kwargs) -> Dict[str, Any]:
        """Stop a running background job"""
        script = f"""
try {{
    Stop-Job -Id {job_id} -ErrorAction Stop
    @{{ success = $true; message = "Job {job_id} stopped" }} | ConvertTo-Json
}} catch {{
    @{{ success = $false; error = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"success": True}
    
    async def _remove_job(self, job_id: int, force: bool = False, **kwargs) -> Dict[str, Any]:
        """Remove a background job"""
        force_param = "-Force" if force else ""
        script = f"""
try {{
    Remove-Job -Id {job_id} {force_param} -ErrorAction Stop
    @{{ success = $true; message = "Job {job_id} removed" }} | ConvertTo-Json
}} catch {{
    @{{ success = $false; error = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"success": True}
    
    async def _wait_job(self, job_id: int, timeout: int = 300, **kwargs) -> Dict[str, Any]:
        """Wait for a background job to complete"""
        script = f"""
try {{
    $job = Wait-Job -Id {job_id} -Timeout {timeout} -ErrorAction Stop
    @{{
        success = $true
        state = $job.State.ToString()
        has_more_data = $job.HasMoreData
        timed_out = $false
    }} | ConvertTo-Json
}} catch {{
    @{{ success = $false; error = $_.Exception.Message; timed_out = $true }} | ConvertTo-Json
}}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to wait for job", "raw": result}
    
    # ========== Trusted Hosts ==========
    
    async def _get_trusted_hosts(self, **kwargs) -> Dict[str, Any]:
        """Get the current trusted hosts list"""
        script = """
$trustedHosts = (Get-Item WSMan:\\localhost\\Client\\TrustedHosts).Value
@{
    trusted_hosts = if ($trustedHosts) { $trustedHosts -split ',' } else { @() }
    raw_value = $trustedHosts
} | ConvertTo-Json
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"trusted_hosts": [], "raw": result}
    
    async def _add_trusted_host(self, host: str, **kwargs) -> Dict[str, Any]:
        """Add a host to the trusted hosts list"""
        script = f"""
try {{
    $current = (Get-Item WSMan:\\localhost\\Client\\TrustedHosts).Value
    if ($current) {{
        $newValue = "$current,{host}"
    }} else {{
        $newValue = "{host}"
    }}
    Set-Item WSMan:\\localhost\\Client\\TrustedHosts -Value $newValue -Force
    @{{
        success = $true
        message = "Added '{host}' to trusted hosts"
        current_hosts = $newValue -split ','
    }} | ConvertTo-Json
}} catch {{
    @{{ success = $false; error = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to add trusted host", "raw": result}
    
    async def _remove_trusted_host(self, host: str, **kwargs) -> Dict[str, Any]:
        """Remove a host from the trusted hosts list"""
        script = f"""
try {{
    $current = (Get-Item WSMan:\\localhost\\Client\\TrustedHosts).Value
    $hosts = $current -split ','
    $newHosts = $hosts | Where-Object {{ $_ -ne '{host}' }}
    $newValue = $newHosts -join ','
    Set-Item WSMan:\\localhost\\Client\\TrustedHosts -Value $newValue -Force
    @{{
        success = $true
        message = "Removed '{host}' from trusted hosts"
        current_hosts = if ($newValue) {{ $newValue -split ',' }} else {{ @() }}
    }} | ConvertTo-Json
}} catch {{
    @{{ success = $false; error = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to remove trusted host", "raw": result}
    
    async def _clear_trusted_hosts(self, **kwargs) -> Dict[str, Any]:
        """Clear all trusted hosts"""
        script = """
try {
    Set-Item WSMan:\\localhost\\Client\\TrustedHosts -Value '' -Force
    @{ success = $true; message = "Cleared all trusted hosts" } | ConvertTo-Json
} catch {
    @{ success = $false; error = $_.Exception.Message } | ConvertTo-Json
}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"success": True}
    
    # ========== WinRM Service ==========
    
    async def _get_winrm_status(self, **kwargs) -> Dict[str, Any]:
        """Get WinRM service status and configuration"""
        script = """
$service = Get-Service WinRM
$config = @{}

try {
    $config['MaxEnvelopeSizekb'] = (Get-Item WSMan:\\localhost\\MaxEnvelopeSizekb).Value
    $config['MaxTimeoutms'] = (Get-Item WSMan:\\localhost\\MaxTimeoutms).Value
    $config['MaxBatchItems'] = (Get-Item WSMan:\\localhost\\MaxBatchItems).Value
    $config['MaxProviderRequests'] = (Get-Item WSMan:\\localhost\\MaxProviderRequests).Value
} catch {}

@{
    service_name = $service.Name
    display_name = $service.DisplayName
    status = $service.Status.ToString()
    start_type = $service.StartType.ToString()
    config = $config
} | ConvertTo-Json
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to get WinRM status", "raw": result}
    
    async def _enable_winrm(self, **kwargs) -> Dict[str, Any]:
        """Enable and start WinRM service"""
        script = """
try {
    Enable-PSRemoting -Force -SkipNetworkProfileCheck
    @{
        success = $true
        message = "WinRM enabled successfully"
        status = (Get-Service WinRM).Status.ToString()
    } | ConvertTo-Json
} catch {
    @{ success = $false; error = $_.Exception.Message } | ConvertTo-Json
}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to enable WinRM", "raw": result}
    
    async def _disable_winrm(self, **kwargs) -> Dict[str, Any]:
        """Disable WinRM service"""
        script = """
try {
    Disable-PSRemoting -Force
    Stop-Service WinRM -Force
    @{
        success = $true
        message = "WinRM disabled"
        status = (Get-Service WinRM).Status.ToString()
    } | ConvertTo-Json
} catch {
    @{ success = $false; error = $_.Exception.Message } | ConvertTo-Json
}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to disable WinRM", "raw": result}
    
    async def _restart_winrm(self, **kwargs) -> Dict[str, Any]:
        """Restart WinRM service"""
        script = """
try {
    Restart-Service WinRM -Force
    Start-Sleep -Seconds 2
    @{
        success = $true
        message = "WinRM restarted"
        status = (Get-Service WinRM).Status.ToString()
    } | ConvertTo-Json
} catch {
    @{ success = $false; error = $_.Exception.Message } | ConvertTo-Json
}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to restart WinRM", "raw": result}
    
    async def _quickconfig(self, skip_network_profile_check: bool = True, **kwargs) -> Dict[str, Any]:
        """Run WinRM quickconfig"""
        skip_param = "-SkipNetworkProfileCheck" if skip_network_profile_check else ""
        script = f"""
try {{
    winrm quickconfig -force
    Enable-PSRemoting -Force {skip_param}
    @{{
        success = $true
        message = "WinRM quick configuration complete"
        status = (Get-Service WinRM).Status.ToString()
    }} | ConvertTo-Json
}} catch {{
    @{{ success = $false; error = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to run quickconfig", "raw": result}
    
    # ========== Listeners ==========
    
    async def _get_listeners(self, **kwargs) -> Dict[str, Any]:
        """Get all WinRM listeners"""
        script = """
$listeners = @()
Get-ChildItem WSMan:\\localhost\\Listener | ForEach-Object {
    $listener = @{
        name = $_.Name
        keys = @{}
    }
    Get-ChildItem $_.PSPath | ForEach-Object {
        $listener.keys[$_.Name] = $_.Value
    }
    $listeners += $listener
}
@{ listeners = $listeners } | ConvertTo-Json -Depth 3
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"listeners": [], "raw": result}
    
    async def _create_listener(
        self,
        transport: str = "HTTP",
        address: str = "*",
        port: int = 5985,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a new WinRM listener"""
        script = f"""
try {{
    New-Item -Path WSMan:\\localhost\\Listener -Transport {transport} -Address {address} -Port {port} -Force
    @{{
        success = $true
        message = "Listener created"
        transport = "{transport}"
        address = "{address}"
        port = {port}
    }} | ConvertTo-Json
}} catch {{
    @{{ success = $false; error = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to create listener", "raw": result}
    
    async def _remove_listener(self, transport: str = "HTTP", address: str = "*", **kwargs) -> Dict[str, Any]:
        """Remove a WinRM listener"""
        script = f"""
try {{
    $path = "WSMan:\\localhost\\Listener\\Listener_*"
    Get-ChildItem $path | Where-Object {{
        $t = (Get-ChildItem $_.PSPath | Where-Object {{ $_.Name -eq 'Transport' }}).Value
        $a = (Get-ChildItem $_.PSPath | Where-Object {{ $_.Name -eq 'Address' }}).Value
        $t -eq '{transport}' -and $a -eq '{address}'
    }} | Remove-Item -Recurse -Force
    @{{ success = $true; message = "Listener removed" }} | ConvertTo-Json
}} catch {{
    @{{ success = $false; error = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to remove listener", "raw": result}
    
    async def _configure_https_listener(
        self,
        certificate_thumbprint: str,
        hostname: Optional[str] = None,
        port: int = 5986,
        **kwargs
    ) -> Dict[str, Any]:
        """Configure HTTPS listener with certificate"""
        hostname_param = f"-Hostname '{hostname}'" if hostname else ""
        script = f"""
try {{
    # Remove existing HTTPS listener if any
    Get-ChildItem WSMan:\\localhost\\Listener | Where-Object {{
        (Get-ChildItem $_.PSPath | Where-Object {{ $_.Name -eq 'Transport' }}).Value -eq 'HTTPS'
    }} | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

    # Create new HTTPS listener
    New-Item -Path WSMan:\\localhost\\Listener -Transport HTTPS -Address * -Port {port} -CertificateThumbprint '{certificate_thumbprint}' {hostname_param} -Force
    
    @{{
        success = $true
        message = "HTTPS listener configured"
        port = {port}
        certificate_thumbprint = '{certificate_thumbprint}'
    }} | ConvertTo-Json
}} catch {{
    @{{ success = $false; error = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to configure HTTPS listener", "raw": result}
    
    # ========== Configuration ==========
    
    async def _get_winrm_config(self, **kwargs) -> Dict[str, Any]:
        """Get WinRM configuration"""
        script = """
$config = @{
    client = @{}
    service = @{}
    winrs = @{}
}

# Client config
Get-ChildItem WSMan:\\localhost\\Client | ForEach-Object {
    $config.client[$_.Name] = $_.Value
}

# Service config
Get-ChildItem WSMan:\\localhost\\Service | ForEach-Object {
    if ($_.PSIsContainer) {
        $config.service[$_.Name] = @{}
        Get-ChildItem $_.PSPath | ForEach-Object {
            $config.service[$_.Parent.Name][$_.Name] = $_.Value
        }
    } else {
        $config.service[$_.Name] = $_.Value
    }
}

# Shell config
Get-ChildItem WSMan:\\localhost\\Shell | ForEach-Object {
    $config.winrs[$_.Name] = $_.Value
}

$config | ConvertTo-Json -Depth 4
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to get config", "raw": result}
    
    async def _set_winrm_config(self, path: str, value: str, **kwargs) -> Dict[str, Any]:
        """Set a WinRM configuration value"""
        script = f"""
try {{
    Set-Item -Path "WSMan:\\localhost\\{path}" -Value '{value}' -Force
    $newValue = (Get-Item "WSMan:\\localhost\\{path}").Value
    @{{
        success = $true
        path = "{path}"
        value = $newValue
    }} | ConvertTo-Json
}} catch {{
    @{{ success = $false; error = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to set config", "raw": result}
    
    async def _get_session_configurations(self, **kwargs) -> Dict[str, Any]:
        """Get registered session configurations"""
        script = """
Get-PSSessionConfiguration | ForEach-Object {
    @{
        name = $_.Name
        permission = $_.Permission
        startup_script = $_.StartupScript
        max_shells = $_.MaxShells
        max_shells_per_user = $_.MaxShellsPerUser
        run_as_user = $_.RunAsUser
        output_buffering_mode = $_.OutputBufferingMode
        psversion = $_.PSVersion
        enabled = $_.Enabled
    }
} | ConvertTo-Json -AsArray
"""
        result = await self._run_powershell(script)
        try:
            return {"configurations": json.loads(result) if result.strip() else []}
        except json.JSONDecodeError:
            return {"configurations": [], "raw": result}
    
    async def _create_session_configuration(
        self,
        name: str,
        startup_script: Optional[str] = None,
        run_as_credential: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a new session configuration"""
        startup_param = f"-StartupScript '{startup_script}'" if startup_script else ""
        
        cred_setup = ""
        cred_param = ""
        if run_as_credential:
            username = run_as_credential.get("username", "")
            password = run_as_credential.get("password", "")
            cred_setup = f"""
$secPassword = ConvertTo-SecureString '{password}' -AsPlainText -Force
$runAsCred = New-Object System.Management.Automation.PSCredential('{username}', $secPassword)
"""
            cred_param = "-RunAsCredential $runAsCred"
        
        script = f"""
{cred_setup}
try {{
    Register-PSSessionConfiguration -Name '{name}' {startup_param} {cred_param} -Force
    @{{
        success = $true
        message = "Session configuration '{name}' created"
        name = '{name}'
    }} | ConvertTo-Json
}} catch {{
    @{{ success = $false; error = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to create session configuration", "raw": result}
    
    async def _remove_session_configuration(self, name: str, **kwargs) -> Dict[str, Any]:
        """Remove a session configuration"""
        script = f"""
try {{
    Unregister-PSSessionConfiguration -Name '{name}' -Force
    @{{ success = $true; message = "Session configuration '{name}' removed" }} | ConvertTo-Json
}} catch {{
    @{{ success = $false; error = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to remove session configuration", "raw": result}
    
    # ========== Firewall ==========
    
    async def _get_winrm_firewall_rules(self, **kwargs) -> Dict[str, Any]:
        """Get WinRM firewall rules"""
        script = """
Get-NetFirewallRule -DisplayName "*WinRM*" -ErrorAction SilentlyContinue | ForEach-Object {
    @{
        name = $_.Name
        display_name = $_.DisplayName
        enabled = $_.Enabled.ToString()
        direction = $_.Direction.ToString()
        action = $_.Action.ToString()
        profile = $_.Profile.ToString()
    }
} | ConvertTo-Json -AsArray
"""
        result = await self._run_powershell(script)
        try:
            return {"rules": json.loads(result) if result.strip() else []}
        except json.JSONDecodeError:
            return {"rules": [], "raw": result}
    
    async def _enable_winrm_firewall_rules(self, **kwargs) -> Dict[str, Any]:
        """Enable WinRM firewall rules"""
        script = """
try {
    Enable-NetFirewallRule -DisplayName "*WinRM*" -ErrorAction SilentlyContinue
    @{ success = $true; message = "WinRM firewall rules enabled" } | ConvertTo-Json
} catch {
    @{ success = $false; error = $_.Exception.Message } | ConvertTo-Json
}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"success": True}
    
    async def _disable_winrm_firewall_rules(self, **kwargs) -> Dict[str, Any]:
        """Disable WinRM firewall rules"""
        script = """
try {
    Disable-NetFirewallRule -DisplayName "*WinRM*" -ErrorAction SilentlyContinue
    @{ success = $true; message = "WinRM firewall rules disabled" } | ConvertTo-Json
} catch {
    @{ success = $false; error = $_.Exception.Message } | ConvertTo-Json
}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"success": True}
    
    # ========== Connection Testing ==========
    
    async def _test_connection(
        self,
        computer_name: str,
        credential: Optional[Dict[str, str]] = None,
        authentication: str = "Default",
        port: int = 5985,
        use_ssl: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Test connection to remote computer"""
        cred_setup = ""
        cred_param = ""
        if credential:
            username = credential.get("username", "")
            password = credential.get("password", "")
            cred_setup = f"""
$secPassword = ConvertTo-SecureString '{password}' -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential('{username}', $secPassword)
"""
            cred_param = "-Credential $cred"
        
        script = f"""
{cred_setup}
$results = @{{
    ping = $false
    wsman = $false
    session = $false
    errors = @()
}}

# Test ping
$results.ping = Test-Connection -ComputerName '{computer_name}' -Count 1 -Quiet

# Test WSMan
try {{
    Test-WSMan -ComputerName '{computer_name}' -ErrorAction Stop | Out-Null
    $results.wsman = $true
}} catch {{
    $results.errors += "WSMan: $($_.Exception.Message)"
}}

# Test session creation
try {{
    $session = New-PSSession -ComputerName '{computer_name}' -Port {port} -UseSSL:${str(use_ssl).lower()} {cred_param} -ErrorAction Stop
    $results.session = $true
    Remove-PSSession $session
}} catch {{
    $results.errors += "Session: $($_.Exception.Message)"
}}

$results | ConvertTo-Json
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to test connection", "raw": result}
    
    async def _test_wsman(self, computer_name: str, **kwargs) -> Dict[str, Any]:
        """Test WSMan connectivity to remote computer"""
        script = f"""
try {{
    $result = Test-WSMan -ComputerName '{computer_name}' -ErrorAction Stop
    @{{
        success = $true
        wsmid = $result.wsmid
        protocol_version = $result.ProtocolVersion
        product_vendor = $result.ProductVendor
        product_version = $result.ProductVersion
    }} | ConvertTo-Json
}} catch {{
    @{{ success = $false; error = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "WSMan test failed", "raw": result}
    
    # ========== Diagnostics ==========
    
    async def _get_winrm_diagnostics(self, **kwargs) -> Dict[str, Any]:
        """Get comprehensive WinRM diagnostics"""
        script = """
$diag = @{
    service = @{}
    listeners = @()
    trusted_hosts = ""
    firewall_rules = @()
    config = @{}
    sessions = @()
}

# Service status
$svc = Get-Service WinRM
$diag.service = @{
    status = $svc.Status.ToString()
    start_type = $svc.StartType.ToString()
}

# Listeners
Get-ChildItem WSMan:\\localhost\\Listener -ErrorAction SilentlyContinue | ForEach-Object {
    $listener = @{}
    Get-ChildItem $_.PSPath | ForEach-Object {
        $listener[$_.Name] = $_.Value
    }
    $diag.listeners += $listener
}

# Trusted hosts
$diag.trusted_hosts = (Get-Item WSMan:\\localhost\\Client\\TrustedHosts -ErrorAction SilentlyContinue).Value

# Firewall rules
Get-NetFirewallRule -DisplayName "*WinRM*" -ErrorAction SilentlyContinue | ForEach-Object {
    $diag.firewall_rules += @{
        name = $_.DisplayName
        enabled = $_.Enabled.ToString()
    }
}

# Current sessions
Get-PSSession -ErrorAction SilentlyContinue | ForEach-Object {
    $diag.sessions += @{
        id = $_.Id
        name = $_.Name
        computer = $_.ComputerName
        state = $_.State.ToString()
    }
}

$diag | ConvertTo-Json -Depth 4
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to get diagnostics", "raw": result}
    
    async def _analyze_connectivity(self, computer_name: str, **kwargs) -> Dict[str, Any]:
        """Analyze connectivity issues to remote computer"""
        script = f"""
$analysis = @{{
    computer = '{computer_name}'
    checks = @()
    recommendations = @()
    overall_status = "unknown"
}}

# DNS resolution
try {{
    $dns = Resolve-DnsName '{computer_name}' -ErrorAction Stop
    $analysis.checks += @{{ name = "DNS Resolution"; passed = $true; details = $dns[0].IPAddress }}
}} catch {{
    $analysis.checks += @{{ name = "DNS Resolution"; passed = $false; details = $_.Exception.Message }}
    $analysis.recommendations += "Check DNS configuration or use IP address"
}}

# Ping test
$ping = Test-Connection -ComputerName '{computer_name}' -Count 1 -Quiet
$analysis.checks += @{{ name = "ICMP Ping"; passed = $ping; details = if ($ping) {{ "Reachable" }} else {{ "Unreachable" }} }}
if (-not $ping) {{
    $analysis.recommendations += "Check network connectivity and firewall rules for ICMP"
}}

# Port 5985 (HTTP)
$http = Test-NetConnection -ComputerName '{computer_name}' -Port 5985 -WarningAction SilentlyContinue
$analysis.checks += @{{ name = "Port 5985 (HTTP)"; passed = $http.TcpTestSucceeded; details = if ($http.TcpTestSucceeded) {{ "Open" }} else {{ "Closed/Filtered" }} }}

# Port 5986 (HTTPS)  
$https = Test-NetConnection -ComputerName '{computer_name}' -Port 5986 -WarningAction SilentlyContinue
$analysis.checks += @{{ name = "Port 5986 (HTTPS)"; passed = $https.TcpTestSucceeded; details = if ($https.TcpTestSucceeded) {{ "Open" }} else {{ "Closed/Filtered" }} }}

# WSMan test
try {{
    Test-WSMan -ComputerName '{computer_name}' -ErrorAction Stop | Out-Null
    $analysis.checks += @{{ name = "WSMan"; passed = $true; details = "Responding" }}
}} catch {{
    $analysis.checks += @{{ name = "WSMan"; passed = $false; details = $_.Exception.Message }}
    $analysis.recommendations += "Ensure WinRM service is running on remote computer"
    $analysis.recommendations += "Check if computer is in trusted hosts list"
}}

# Check trusted hosts
$trustedHosts = (Get-Item WSMan:\\localhost\\Client\\TrustedHosts).Value
$isTrusted = $trustedHosts -match '{computer_name}' -or $trustedHosts -eq '*'
$analysis.checks += @{{ name = "In Trusted Hosts"; passed = $isTrusted; details = if ($isTrusted) {{ "Yes" }} else {{ "No" }} }}
if (-not $isTrusted) {{
    $analysis.recommendations += "Add '{computer_name}' to trusted hosts: Set-Item WSMan:\\localhost\\Client\\TrustedHosts -Value '{computer_name}' -Force"
}}

# Determine overall status
$passedCount = ($analysis.checks | Where-Object {{ $_.passed }}).Count
$totalCount = $analysis.checks.Count
$analysis.overall_status = if ($passedCount -eq $totalCount) {{ "healthy" }} elseif ($passedCount -gt $totalCount/2) {{ "degraded" }} else {{ "unhealthy" }}
$analysis.passed_checks = $passedCount
$analysis.total_checks = $totalCount

$analysis | ConvertTo-Json -Depth 4
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to analyze connectivity", "raw": result}
    
    async def _run_powershell(self, script: str) -> str:
        """Execute PowerShell script and return output"""
        try:
            process = await asyncio.create_subprocess_exec(
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy", "Bypass",
                "-Command", script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if stderr:
                logger.warning(f"PowerShell stderr: {stderr.decode()}")
            
            return stdout.decode().strip()
        except Exception as e:
            logger.error(f"PowerShell execution failed: {e}")
            raise


plugin = WindowsWinRMPlugin()
