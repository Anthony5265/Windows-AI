"""
PowerShell Bridge Plugin - Execute PowerShell scripts and manage sessions
"""

import asyncio
import subprocess
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata

logger = logging.getLogger(__name__)


class PowerShellBridgePlugin(IntegrationPlugin):
    """Plugin for executing PowerShell commands and managing PowerShell sessions"""

    def __init__(self):
        metadata = PluginMetadata(
            id="windows.powershell-bridge",
            name="PowerShell Bridge",
            description="Execute PowerShell scripts and commands with advanced session management",
            version="2.0.0",
            author="Windows AI Team",
            category="windows",
            tags=["powershell", "scripting", "automation", "windows"],
            requires_admin=False,
            platforms=["windows"]
        )
        super().__init__(metadata)
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._execution_policy = None
        self._default_timeout = 300

    async def initialize(self) -> bool:
        """Initialize PowerShell bridge"""
        try:
            # Check PowerShell availability
            result = await self._run_powershell("$PSVersionTable | ConvertTo-Json")
            if result.get("success"):
                version_info = json.loads(result.get("output", "{}"))
                logger.info(f"PowerShell Bridge initialized - Version: {version_info.get('PSVersion', {})}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize PowerShell Bridge: {e}")
            return False

    async def _run_powershell(self, script: str, timeout: int = None, as_admin: bool = False,
                               execution_policy: str = None, working_dir: str = None,
                               env_vars: Dict[str, str] = None, input_data: str = None) -> Dict[str, Any]:
        """Execute a PowerShell script with options"""
        try:
            timeout = timeout or self._default_timeout
            
            # Build PowerShell command
            cmd = ["powershell.exe", "-NoProfile", "-NonInteractive"]
            
            if execution_policy:
                cmd.extend(["-ExecutionPolicy", execution_policy])
            
            cmd.extend(["-Command", script])
            
            # Prepare environment
            env = None
            if env_vars:
                import os
                env = os.environ.copy()
                env.update(env_vars)
            
            # Execute
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE if input_data else None,
                cwd=working_dir,
                env=env
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=input_data.encode() if input_data else None),
                timeout=timeout
            )
            
            return {
                "success": process.returncode == 0,
                "output": stdout.decode("utf-8", errors="replace").strip(),
                "error": stderr.decode("utf-8", errors="replace").strip() if stderr else None,
                "exit_code": process.returncode
            }
        except asyncio.TimeoutError:
            return {"success": False, "error": f"Command timed out after {timeout} seconds"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def execute(self, action: str = "run_command", params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute PowerShell bridge actions"""
        params = params or {}
        
        actions = {
            # Core execution
            "run_command": self._run_command,
            "run_script": self._run_script,
            "run_script_file": self._run_script_file,
            "invoke_expression": self._invoke_expression,
            
            # Session management
            "create_session": self._create_session,
            "get_session": self._get_session,
            "close_session": self._close_session,
            "list_sessions": self._list_sessions,
            "invoke_in_session": self._invoke_in_session,
            
            # Remote execution
            "invoke_remote": self._invoke_remote,
            "enter_pssession": self._enter_pssession,
            "exit_pssession": self._exit_pssession,
            
            # Module management
            "list_modules": self._list_modules,
            "get_module": self._get_module,
            "import_module": self._import_module,
            "remove_module": self._remove_module,
            "find_module": self._find_module,
            "install_module": self._install_module,
            
            # Command discovery
            "get_command": self._get_command,
            "get_help": self._get_help,
            "get_alias": self._get_alias,
            
            # Variables and environment
            "get_variable": self._get_variable,
            "set_variable": self._set_variable,
            "get_env_variable": self._get_env_variable,
            "set_env_variable": self._set_env_variable,
            
            # Execution policy
            "get_execution_policy": self._get_execution_policy,
            "set_execution_policy": self._set_execution_policy,
            
            # Profile management
            "get_profile": self._get_profile,
            "test_profile": self._test_profile,
            
            # History
            "get_history": self._get_history,
            "clear_history": self._clear_history,
            
            # Error handling
            "get_error": self._get_error,
            "clear_error": self._clear_error,
            
            # Version info
            "get_version": self._get_version,
            "get_host": self._get_host
        }
        
        if action not in actions:
            return {"success": False, "error": f"Unknown action: {action}. Available: {list(actions.keys())}"}
        
        try:
            return await actions[action](params)
        except Exception as e:
            logger.error(f"PowerShell bridge action '{action}' failed: {e}")
            return {"success": False, "error": str(e)}

    async def _run_command(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run a PowerShell command"""
        command = params.get("command")
        if not command:
            return {"success": False, "error": "Command is required"}
        
        return await self._run_powershell(
            command,
            timeout=params.get("timeout"),
            execution_policy=params.get("execution_policy"),
            working_dir=params.get("working_dir"),
            env_vars=params.get("env_vars")
        )

    async def _run_script(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run a multi-line PowerShell script"""
        script = params.get("script")
        if not script:
            return {"success": False, "error": "Script content is required"}
        
        # Handle script parameters
        script_params = params.get("parameters", {})
        if script_params:
            param_block = "param(" + ", ".join([f"${k}" for k in script_params.keys()]) + ")\n"
            script = param_block + script
            # Add parameter values
            param_values = "; ".join([f"${k} = '{v}'" for k, v in script_params.items()])
            script = param_values + "\n" + script
        
        return await self._run_powershell(
            script,
            timeout=params.get("timeout", 600),
            execution_policy=params.get("execution_policy"),
            working_dir=params.get("working_dir")
        )

    async def _run_script_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a PowerShell script file"""
        file_path = params.get("file_path")
        if not file_path:
            return {"success": False, "error": "File path is required"}
        
        args = params.get("arguments", "")
        script = f"& '{file_path}' {args}"
        
        return await self._run_powershell(
            script,
            timeout=params.get("timeout", 600),
            execution_policy=params.get("execution_policy", "Bypass"),
            working_dir=params.get("working_dir")
        )

    async def _invoke_expression(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke an expression"""
        expression = params.get("expression")
        if not expression:
            return {"success": False, "error": "Expression is required"}
        
        script = f"Invoke-Expression '{expression.replace(chr(39), chr(39)+chr(39))}' | ConvertTo-Json -Depth 10"
        return await self._run_powershell(script)

    async def _create_session(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a named PowerShell session"""
        name = params.get("name", f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        self._sessions[name] = {
            "name": name,
            "created": datetime.now().isoformat(),
            "variables": {},
            "history": []
        }
        
        return {"success": True, "session": name, "message": f"Session '{name}' created"}

    async def _get_session(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get session info"""
        name = params.get("name")
        if not name:
            return {"success": False, "error": "Session name is required"}
        
        session = self._sessions.get(name)
        if not session:
            return {"success": False, "error": f"Session '{name}' not found"}
        
        return {"success": True, "session": session}

    async def _close_session(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Close a session"""
        name = params.get("name")
        if name and name in self._sessions:
            del self._sessions[name]
            return {"success": True, "message": f"Session '{name}' closed"}
        return {"success": False, "error": f"Session '{name}' not found"}

    async def _list_sessions(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List all sessions"""
        return {"success": True, "sessions": list(self._sessions.keys()), "count": len(self._sessions)}

    async def _invoke_in_session(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute command in a session context"""
        name = params.get("session")
        command = params.get("command")
        
        if not name or not command:
            return {"success": False, "error": "Session name and command are required"}
        
        session = self._sessions.get(name)
        if not session:
            return {"success": False, "error": f"Session '{name}' not found"}
        
        # Build script with session variables
        var_setup = "\n".join([f"${k} = {json.dumps(v)}" for k, v in session["variables"].items()])
        script = f"{var_setup}\n{command}"
        
        result = await self._run_powershell(script)
        
        # Store in history
        session["history"].append({
            "command": command,
            "timestamp": datetime.now().isoformat(),
            "success": result.get("success")
        })
        
        return result

    async def _invoke_remote(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute command on remote computer"""
        computer = params.get("computer")
        command = params.get("command")
        
        if not computer or not command:
            return {"success": False, "error": "Computer name and command are required"}
        
        credential = ""
        if params.get("username"):
            credential = f"-Credential (New-Object PSCredential('{params['username']}', (ConvertTo-SecureString '{params.get('password', '')}' -AsPlainText -Force)))"
        
        script = f"Invoke-Command -ComputerName '{computer}' {credential} -ScriptBlock {{ {command} }} | ConvertTo-Json -Depth 10"
        return await self._run_powershell(script)

    async def _enter_pssession(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create interactive remote session (returns session object)"""
        computer = params.get("computer")
        if not computer:
            return {"success": False, "error": "Computer name is required"}
        
        script = f"New-PSSession -ComputerName '{computer}' | Select-Object Id, Name, ComputerName, State | ConvertTo-Json"
        return await self._run_powershell(script)

    async def _exit_pssession(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove remote session"""
        session_id = params.get("session_id")
        if not session_id:
            return {"success": False, "error": "Session ID is required"}
        
        script = f"Remove-PSSession -Id {session_id}"
        return await self._run_powershell(script)

    async def _list_modules(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List PowerShell modules"""
        list_available = params.get("list_available", False)
        name_filter = params.get("name", "*")
        
        cmd = "Get-Module" if not list_available else "Get-Module -ListAvailable"
        script = f"{cmd} -Name '{name_filter}' | Select-Object Name, Version, ModuleType, Path | ConvertTo-Json"
        return await self._run_powershell(script)

    async def _get_module(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed module info"""
        name = params.get("name")
        if not name:
            return {"success": False, "error": "Module name is required"}
        
        script = f"Get-Module -Name '{name}' -ListAvailable | Select-Object * | ConvertTo-Json -Depth 5"
        return await self._run_powershell(script)

    async def _import_module(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Import a PowerShell module"""
        name = params.get("name")
        if not name:
            return {"success": False, "error": "Module name is required"}
        
        force = "-Force" if params.get("force") else ""
        script = f"Import-Module '{name}' {force} -PassThru | Select-Object Name, Version | ConvertTo-Json"
        return await self._run_powershell(script)

    async def _remove_module(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove a PowerShell module"""
        name = params.get("name")
        if not name:
            return {"success": False, "error": "Module name is required"}
        
        script = f"Remove-Module '{name}' -Force; @{{success=$true}} | ConvertTo-Json"
        return await self._run_powershell(script)

    async def _find_module(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Find modules in PSGallery"""
        name = params.get("name", "*")
        script = f"Find-Module -Name '{name}' | Select-Object Name, Version, Author, Description | ConvertTo-Json"
        return await self._run_powershell(script, timeout=60)

    async def _install_module(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Install a module from PSGallery"""
        name = params.get("name")
        if not name:
            return {"success": False, "error": "Module name is required"}
        
        scope = params.get("scope", "CurrentUser")
        force = "-Force" if params.get("force") else ""
        
        script = f"Install-Module '{name}' -Scope {scope} {force} -AllowClobber; @{{success=$true; module='{name}'}} | ConvertTo-Json"
        return await self._run_powershell(script, timeout=300)

    async def _get_command(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get command info"""
        name = params.get("name", "*")
        cmd_type = params.get("type", "")  # Cmdlet, Function, Alias, etc.
        
        type_filter = f"-CommandType {cmd_type}" if cmd_type else ""
        script = f"Get-Command '{name}' {type_filter} -ErrorAction SilentlyContinue | Select-Object Name, CommandType, ModuleName, Version | ConvertTo-Json"
        return await self._run_powershell(script)

    async def _get_help(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get help for a command"""
        name = params.get("name")
        if not name:
            return {"success": False, "error": "Command name is required"}
        
        detailed = "-Detailed" if params.get("detailed") else ""
        examples = "-Examples" if params.get("examples") else ""
        
        script = f"Get-Help '{name}' {detailed} {examples} | Out-String"
        return await self._run_powershell(script)

    async def _get_alias(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get alias definitions"""
        name = params.get("name", "*")
        script = f"Get-Alias -Name '{name}' -ErrorAction SilentlyContinue | Select-Object Name, Definition | ConvertTo-Json"
        return await self._run_powershell(script)

    async def _get_variable(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get PowerShell variable"""
        name = params.get("name")
        if not name:
            return {"success": False, "error": "Variable name is required"}
        
        script = f"Get-Variable -Name '{name}' -ErrorAction SilentlyContinue | Select-Object Name, Value | ConvertTo-Json"
        return await self._run_powershell(script)

    async def _set_variable(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set PowerShell variable (session-scoped)"""
        name = params.get("name")
        value = params.get("value")
        
        if not name:
            return {"success": False, "error": "Variable name is required"}
        
        script = f"Set-Variable -Name '{name}' -Value {json.dumps(value)} -PassThru | Select-Object Name, Value | ConvertTo-Json"
        return await self._run_powershell(script)

    async def _get_env_variable(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get environment variable"""
        name = params.get("name")
        if name:
            script = f"[Environment]::GetEnvironmentVariable('{name}') | ConvertTo-Json"
        else:
            script = "Get-ChildItem Env: | Select-Object Name, Value | ConvertTo-Json"
        return await self._run_powershell(script)

    async def _set_env_variable(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set environment variable"""
        name = params.get("name")
        value = params.get("value")
        target = params.get("target", "Process")  # Process, User, Machine
        
        if not name:
            return {"success": False, "error": "Variable name is required"}
        
        script = f"[Environment]::SetEnvironmentVariable('{name}', '{value}', '{target}'); @{{success=$true}} | ConvertTo-Json"
        return await self._run_powershell(script)

    async def _get_execution_policy(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get execution policy"""
        scope = params.get("scope", "")
        scope_param = f"-Scope {scope}" if scope else "-List"
        script = f"Get-ExecutionPolicy {scope_param} | ConvertTo-Json"
        return await self._run_powershell(script)

    async def _set_execution_policy(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set execution policy"""
        policy = params.get("policy")
        scope = params.get("scope", "CurrentUser")
        
        if not policy:
            return {"success": False, "error": "Policy is required (Restricted, AllSigned, RemoteSigned, Unrestricted, Bypass)"}
        
        script = f"Set-ExecutionPolicy -ExecutionPolicy {policy} -Scope {scope} -Force; Get-ExecutionPolicy -Scope {scope}"
        return await self._run_powershell(script)

    async def _get_profile(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get PowerShell profile paths"""
        script = """
        @{
            CurrentUserCurrentHost = $PROFILE.CurrentUserCurrentHost
            CurrentUserAllHosts = $PROFILE.CurrentUserAllHosts
            AllUsersCurrentHost = $PROFILE.AllUsersCurrentHost
            AllUsersAllHosts = $PROFILE.AllUsersAllHosts
        } | ConvertTo-Json
        """
        return await self._run_powershell(script)

    async def _test_profile(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Test if profile exists"""
        script = """
        @{
            CurrentUserCurrentHost = Test-Path $PROFILE.CurrentUserCurrentHost
            CurrentUserAllHosts = Test-Path $PROFILE.CurrentUserAllHosts
            AllUsersCurrentHost = Test-Path $PROFILE.AllUsersCurrentHost
            AllUsersAllHosts = Test-Path $PROFILE.AllUsersAllHosts
        } | ConvertTo-Json
        """
        return await self._run_powershell(script)

    async def _get_history(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get command history"""
        count = params.get("count", 50)
        script = f"Get-History -Count {count} | Select-Object Id, CommandLine, StartExecutionTime, EndExecutionTime | ConvertTo-Json"
        return await self._run_powershell(script)

    async def _clear_history(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Clear command history"""
        script = "Clear-History; @{success=$true; message='History cleared'} | ConvertTo-Json"
        return await self._run_powershell(script)

    async def _get_error(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get recent errors"""
        count = params.get("count", 10)
        script = f"$Error[0..{count-1}] | ForEach-Object {{ @{{Message=$_.Exception.Message; Type=$_.Exception.GetType().Name; Script=$_.InvocationInfo.ScriptName; Line=$_.InvocationInfo.ScriptLineNumber}} }} | ConvertTo-Json"
        return await self._run_powershell(script)

    async def _clear_error(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Clear error variable"""
        script = "$Error.Clear(); @{success=$true; message='Errors cleared'} | ConvertTo-Json"
        return await self._run_powershell(script)

    async def _get_version(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get PowerShell version info"""
        script = "$PSVersionTable | ConvertTo-Json"
        return await self._run_powershell(script)

    async def _get_host(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get host information"""
        script = "$Host | Select-Object Name, Version, CurrentCulture, CurrentUICulture | ConvertTo-Json"
        return await self._run_powershell(script)

    async def cleanup(self) -> None:
        """Cleanup plugin resources"""
        self._sessions.clear()
        logger.info("PowerShell Bridge plugin cleaned up")
