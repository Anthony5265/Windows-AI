"""
PowerShell Execution Plugin for Windows AI
Comprehensive PowerShell script execution with security, remoting, and module management
"""

import asyncio
import logging
import os
import tempfile
from typing import Any, Dict, List, Optional
from datetime import datetime

from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class PowerShellExecutionPlugin(IntegrationPlugin):
    """
    Comprehensive PowerShell execution plugin for Windows AI.
    
    Provides 45+ actions for:
    - Script execution with various execution policies
    - Remote PowerShell sessions
    - Module management
    - Runspace and job management
    - Script signing and security
    - Profile management
    - History and transcription
    - Pipeline operations
    - Variable and environment management
    - Credential handling
    """

    def __init__(self):
        metadata = PluginMetadata(
            id="powershell-execution",
            name="PowerShell Execution",
            description="Comprehensive PowerShell script execution and management",
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["powershell", "scripting", "automation", "windows", "remote"]
        )
        super().__init__(metadata)
        self._sessions = {}
        self._jobs = {}

    async def _run_powershell(self, script: str, as_json: bool = True, timeout: int = 300,
                              execution_policy: str = None, no_profile: bool = True) -> Dict[str, Any]:
        """Execute PowerShell script and return results."""
        try:
            json_suffix = " | ConvertTo-Json -Depth 10 -Compress" if as_json else ""
            full_script = f"$ErrorActionPreference = 'Stop'; {script}{json_suffix}"
            
            args = ["powershell.exe"]
            if no_profile:
                args.append("-NoProfile")
            args.extend(["-NonInteractive"])
            if execution_policy:
                args.extend(["-ExecutionPolicy", execution_policy])
            args.extend(["-Command", full_script])
            
            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                process.kill()
                return {"success": False, "error": f"Script execution timed out after {timeout} seconds"}
            
            if process.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='replace').strip()
                return {"success": False, "error": error_msg, "returncode": process.returncode}
            
            output = stdout.decode('utf-8', errors='replace').strip()
            if as_json and output:
                import json
                try:
                    return {"success": True, "data": json.loads(output)}
                except json.JSONDecodeError:
                    return {"success": True, "data": output}
            return {"success": True, "data": output if output else None}
        except Exception as e:
            logger.error(f"PowerShell execution failed: {e}")
            return {"success": False, "error": str(e)}


    async def connect(self, credentials: Dict[str, str]) -> bool:
        """Connect to the service"""
        return True

    async def disconnect(self) -> bool:
        """Disconnect from the service"""
        return True

    async def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """Execute PowerShell management actions."""
        actions = {
            # Script Execution
            "execute_script": self._execute_script,
            "execute_script_file": self._execute_script_file,
            "execute_command": self._execute_command,
            "execute_scriptblock": self._execute_scriptblock,
            "execute_with_arguments": self._execute_with_arguments,
            "execute_as_job": self._execute_as_job,
            "execute_parallel": self._execute_parallel,
            
            # Remote Execution
            "invoke_remote": self._invoke_remote,
            "create_remote_session": self._create_remote_session,
            "close_remote_session": self._close_remote_session,
            "list_remote_sessions": self._list_remote_sessions,
            "enter_remote_session": self._enter_remote_session,
            "copy_to_remote": self._copy_to_remote,
            "copy_from_remote": self._copy_from_remote,
            
            # Module Management
            "list_modules": self._list_modules,
            "get_module_info": self._get_module_info,
            "import_module": self._import_module,
            "remove_module": self._remove_module,
            "install_module": self._install_module,
            "update_module": self._update_module,
            "uninstall_module": self._uninstall_module,
            "find_module": self._find_module,
            "get_module_commands": self._get_module_commands,
            
            # Job Management
            "get_jobs": self._get_jobs,
            "get_job_result": self._get_job_result,
            "stop_job": self._stop_job,
            "remove_job": self._remove_job,
            "wait_job": self._wait_job,
            
            # Security and Signing
            "get_execution_policy": self._get_execution_policy,
            "set_execution_policy": self._set_execution_policy,
            "sign_script": self._sign_script,
            "verify_script_signature": self._verify_script_signature,
            "get_authenticode_signature": self._get_authenticode_signature,
            "list_certificates": self._list_certificates,
            
            # Profile Management
            "get_profile_paths": self._get_profile_paths,
            "test_profile_exists": self._test_profile_exists,
            "get_profile_content": self._get_profile_content,
            "add_to_profile": self._add_to_profile,
            
            # History and Transcription
            "get_history": self._get_history,
            "clear_history": self._clear_history,
            "start_transcript": self._start_transcript,
            "stop_transcript": self._stop_transcript,
            
            # Variables and Environment
            "get_variable": self._get_variable,
            "set_variable": self._set_variable,
            "remove_variable": self._remove_variable,
            "list_variables": self._list_variables,
            "get_environment_variable": self._get_environment_variable,
            "set_environment_variable": self._set_environment_variable,
            
            # Command Discovery
            "get_command": self._get_command,
            "get_command_syntax": self._get_command_syntax,
            "get_alias": self._get_alias,
            "list_aliases": self._list_aliases,
            
            # Pipeline and Output
            "format_output": self._format_output,
            "export_to_csv": self._export_to_csv,
            "export_to_xml": self._export_to_xml,
            "export_to_json": self._export_to_json,
            
            # Diagnostics
            "get_powershell_version": self._get_powershell_version,
            "get_host_info": self._get_host_info,
            "test_script_syntax": self._test_script_syntax,
            "measure_command": self._measure_command,
        }
        
        if action not in actions:
            return {
                "success": False,
                "error": f"Unknown action: {action}",
                "available_actions": list(actions.keys())
            }
        
        try:
            return await actions[action](**kwargs)
        except Exception as e:
            logger.error(f"Action {action} failed: {e}")
            return {"success": False, "error": str(e)}

    # Script Execution
    async def _execute_script(self, script: str, timeout: int = 300, 
                              execution_policy: str = None, **kwargs) -> Dict[str, Any]:
        """Execute a PowerShell script string."""
        return await self._run_powershell(script, timeout=timeout, execution_policy=execution_policy)

    async def _execute_script_file(self, file_path: str, arguments: Dict[str, Any] = None,
                                   timeout: int = 300, **kwargs) -> Dict[str, Any]:
        """Execute a PowerShell script file."""
        args_str = ""
        if arguments:
            args_str = " ".join([f"-{k} '{v}'" for k, v in arguments.items()])
        
        script = f'& "{file_path}" {args_str}'
        return await self._run_powershell(script, timeout=timeout, as_json=False)

    async def _execute_command(self, command: str, timeout: int = 60, **kwargs) -> Dict[str, Any]:
        """Execute a single PowerShell command."""
        return await self._run_powershell(command, timeout=timeout)

    async def _execute_scriptblock(self, scriptblock: str, arguments: List[Any] = None, **kwargs) -> Dict[str, Any]:
        """Execute a PowerShell scriptblock."""
        if arguments:
            args_str = ", ".join([f"'{a}'" if isinstance(a, str) else str(a) for a in arguments])
            script = f'& {{ {scriptblock} }} {args_str}'
        else:
            script = f'& {{ {scriptblock} }}'
        return await self._run_powershell(script)

    async def _execute_with_arguments(self, script: str, parameters: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Execute script with named parameters."""
        param_definitions = []
        param_values = []
        
        for name, value in parameters.items():
            param_definitions.append(f"${name}")
            if isinstance(value, str):
                param_values.append(f'${name} = "{value}"')
            elif isinstance(value, bool):
                param_values.append(f"${name} = ${str(value).lower()}")
            elif isinstance(value, list):
                items = ", ".join([f'"{v}"' if isinstance(v, str) else str(v) for v in value])
                param_values.append(f"${name} = @({items})")
            else:
                param_values.append(f"${name} = {value}")
        
        full_script = "\n".join(param_values) + "\n" + script
        return await self._run_powershell(full_script)

    async def _execute_as_job(self, script: str, job_name: str = None, **kwargs) -> Dict[str, Any]:
        """Execute script as a background job."""
        name_param = f' -Name "{job_name}"' if job_name else ""
        ps_script = f'''
        $job = Start-Job{name_param} -ScriptBlock {{ {script} }}
        @{{
            JobId = $job.Id
            Name = $job.Name
            State = $job.State.ToString()
            HasMoreData = $job.HasMoreData
            Location = $job.Location
            Command = $job.Command
        }}
        '''
        return await self._run_powershell(ps_script)

    async def _execute_parallel(self, scripts: List[str], throttle_limit: int = 5, **kwargs) -> Dict[str, Any]:
        """Execute multiple scripts in parallel using jobs."""
        scripts_array = "\n".join([f'"{s.replace(chr(34), chr(96)+chr(34))}"' for s in scripts])
        ps_script = f'''
        $scripts = @(
            {scripts_array}
        )
        
        $jobs = @()
        foreach ($script in $scripts) {{
            $jobs += Start-Job -ScriptBlock ([scriptblock]::Create($script))
            
            # Throttle
            while (($jobs | Where-Object {{ $_.State -eq "Running" }}).Count -ge {throttle_limit}) {{
                Start-Sleep -Milliseconds 100
            }}
        }}
        
        $results = $jobs | Wait-Job | Receive-Job
        $jobs | Remove-Job
        
        @{{
            Results = $results
            CompletedCount = $jobs.Count
        }}
        '''
        return await self._run_powershell(ps_script, timeout=600)

    # Remote Execution
    async def _invoke_remote(self, computer: str, script: str, credential: str = None, **kwargs) -> Dict[str, Any]:
        """Invoke a script on a remote computer."""
        cred_param = ""
        if credential:
            cred_param = f'-Credential (Get-Credential -UserName "{credential}" -Message "Enter password")'
        
        ps_script = f'''
        Invoke-Command -ComputerName "{computer}" {cred_param} -ScriptBlock {{ {script} }}
        '''
        return await self._run_powershell(ps_script, as_json=False)

    async def _create_remote_session(self, computer: str, session_name: str = None, 
                                      credential: str = None, **kwargs) -> Dict[str, Any]:
        """Create a persistent remote PowerShell session."""
        name_param = f'-Name "{session_name}"' if session_name else ""
        cred_param = ""
        if credential:
            cred_param = f'-Credential (Get-Credential -UserName "{credential}" -Message "Enter password")'
        
        ps_script = f'''
        $session = New-PSSession -ComputerName "{computer}" {name_param} {cred_param}
        @{{
            Id = $session.Id
            Name = $session.Name
            ComputerName = $session.ComputerName
            State = $session.State.ToString()
            Availability = $session.Availability.ToString()
            ConfigurationName = $session.ConfigurationName
        }}
        '''
        return await self._run_powershell(ps_script)

    async def _close_remote_session(self, session_id: int = None, session_name: str = None, **kwargs) -> Dict[str, Any]:
        """Close a remote PowerShell session."""
        if session_id:
            filter_clause = f'-Id {session_id}'
        elif session_name:
            filter_clause = f'-Name "{session_name}"'
        else:
            return {"success": False, "error": "Must specify session_id or session_name"}
        
        ps_script = f'''
        $session = Get-PSSession {filter_clause}
        if ($session) {{
            Remove-PSSession $session
            @{{ Success = $true; Message = "Session closed" }}
        }} else {{
            @{{ Success = $false; Error = "Session not found" }}
        }}
        '''
        return await self._run_powershell(ps_script)

    async def _list_remote_sessions(self, **kwargs) -> Dict[str, Any]:
        """List all active remote PowerShell sessions."""
        ps_script = '''
        Get-PSSession | Select-Object Id, Name, ComputerName, 
        @{N='State';E={$_.State.ToString()}},
        @{N='Availability';E={$_.Availability.ToString()}},
        ConfigurationName, InstanceId
        '''
        return await self._run_powershell(ps_script)

    async def _enter_remote_session(self, session_id: int, **kwargs) -> Dict[str, Any]:
        """Enter an interactive remote session (returns session info)."""
        ps_script = f'''
        $session = Get-PSSession -Id {session_id}
        if ($session) {{
            @{{
                Message = "Use 'Enter-PSSession -Id {session_id}' to enter interactive mode"
                SessionInfo = @{{
                    Id = $session.Id
                    Name = $session.Name
                    ComputerName = $session.ComputerName
                    State = $session.State.ToString()
                }}
            }}
        }} else {{
            @{{ Success = $false; Error = "Session not found" }}
        }}
        '''
        return await self._run_powershell(ps_script)

    async def _copy_to_remote(self, session_id: int, local_path: str, remote_path: str, **kwargs) -> Dict[str, Any]:
        """Copy a file to a remote computer using a session."""
        ps_script = f'''
        $session = Get-PSSession -Id {session_id}
        if ($session) {{
            Copy-Item -Path "{local_path}" -Destination "{remote_path}" -ToSession $session
            @{{ Success = $true; Message = "File copied to remote" }}
        }} else {{
            @{{ Success = $false; Error = "Session not found" }}
        }}
        '''
        return await self._run_powershell(ps_script)

    async def _copy_from_remote(self, session_id: int, remote_path: str, local_path: str, **kwargs) -> Dict[str, Any]:
        """Copy a file from a remote computer using a session."""
        ps_script = f'''
        $session = Get-PSSession -Id {session_id}
        if ($session) {{
            Copy-Item -Path "{remote_path}" -Destination "{local_path}" -FromSession $session
            @{{ Success = $true; Message = "File copied from remote" }}
        }} else {{
            @{{ Success = $false; Error = "Session not found" }}
        }}
        '''
        return await self._run_powershell(ps_script)

    # Module Management
    async def _list_modules(self, list_available: bool = False, **kwargs) -> Dict[str, Any]:
        """List PowerShell modules."""
        if list_available:
            ps_script = '''
            Get-Module -ListAvailable | Select-Object Name, Version, ModuleType, Path |
            Group-Object Name | ForEach-Object { $_.Group | Sort-Object Version -Descending | Select-Object -First 1 }
            '''
        else:
            ps_script = '''
            Get-Module | Select-Object Name, Version, ModuleType, 
            @{N='ExportedCommands';E={$_.ExportedCommands.Count}},
            @{N='ExportedFunctions';E={$_.ExportedFunctions.Count}},
            @{N='ExportedCmdlets';E={$_.ExportedCmdlets.Count}}
            '''
        return await self._run_powershell(ps_script)

    async def _get_module_info(self, module_name: str, **kwargs) -> Dict[str, Any]:
        """Get detailed information about a module."""
        ps_script = f'''
        $mod = Get-Module -Name "{module_name}" -ListAvailable | Select-Object -First 1
        if ($mod) {{
            @{{
                Name = $mod.Name
                Version = $mod.Version.ToString()
                ModuleType = $mod.ModuleType.ToString()
                Description = $mod.Description
                Author = $mod.Author
                CompanyName = $mod.CompanyName
                Copyright = $mod.Copyright
                PowerShellVersion = $mod.PowerShellVersion.ToString()
                CLRVersion = if($mod.CLRVersion){{$mod.CLRVersion.ToString()}}else{{$null}}
                Path = $mod.Path
                ModuleBase = $mod.ModuleBase
                ExportedFunctions = @($mod.ExportedFunctions.Keys)
                ExportedCmdlets = @($mod.ExportedCmdlets.Keys)
                ExportedAliases = @($mod.ExportedAliases.Keys)
                ExportedVariables = @($mod.ExportedVariables.Keys)
                RequiredModules = @($mod.RequiredModules | ForEach-Object {{ $_.Name }})
                NestedModules = @($mod.NestedModules | ForEach-Object {{ $_.Name }})
            }}
        }} else {{
            @{{ Success = $false; Error = "Module not found" }}
        }}
        '''
        return await self._run_powershell(ps_script)

    async def _import_module(self, module_name: str, version: str = None, 
                             prefix: str = None, **kwargs) -> Dict[str, Any]:
        """Import a PowerShell module."""
        params = [f'-Name "{module_name}"']
        if version:
            params.append(f'-RequiredVersion "{version}"')
        if prefix:
            params.append(f'-Prefix "{prefix}"')
        
        ps_script = f'''
        Import-Module {" ".join(params)} -PassThru | 
        Select-Object Name, Version, @{{N='CommandCount';E={{$_.ExportedCommands.Count}}}}
        '''
        return await self._run_powershell(ps_script)

    async def _remove_module(self, module_name: str, **kwargs) -> Dict[str, Any]:
        """Remove a loaded PowerShell module."""
        ps_script = f'''
        Remove-Module -Name "{module_name}" -Force -ErrorAction Stop
        @{{ Success = $true; Message = "Module removed" }}
        '''
        return await self._run_powershell(ps_script)

    async def _install_module(self, module_name: str, version: str = None,
                              scope: str = "CurrentUser", force: bool = False, **kwargs) -> Dict[str, Any]:
        """Install a PowerShell module from PSGallery."""
        params = [f'-Name "{module_name}"', f'-Scope {scope}']
        if version:
            params.append(f'-RequiredVersion "{version}"')
        if force:
            params.append('-Force')
        params.append('-AllowClobber')
        
        ps_script = f'''
        Install-Module {" ".join(params)}
        @{{ Success = $true; Message = "Module '{module_name}' installed" }}
        '''
        return await self._run_powershell(ps_script, timeout=600)

    async def _update_module(self, module_name: str, **kwargs) -> Dict[str, Any]:
        """Update a PowerShell module."""
        ps_script = f'''
        Update-Module -Name "{module_name}" -Force
        $mod = Get-Module -Name "{module_name}" -ListAvailable | Select-Object -First 1
        @{{ Success = $true; Version = $mod.Version.ToString() }}
        '''
        return await self._run_powershell(ps_script, timeout=600)

    async def _uninstall_module(self, module_name: str, all_versions: bool = False, **kwargs) -> Dict[str, Any]:
        """Uninstall a PowerShell module."""
        all_flag = "-AllVersions" if all_versions else ""
        ps_script = f'''
        Uninstall-Module -Name "{module_name}" {all_flag} -Force
        @{{ Success = $true; Message = "Module uninstalled" }}
        '''
        return await self._run_powershell(ps_script)

    async def _find_module(self, search_string: str, tag: str = None, **kwargs) -> Dict[str, Any]:
        """Find modules in PSGallery."""
        params = [f'-Name "*{search_string}*"']
        if tag:
            params.append(f'-Tag "{tag}"')
        
        ps_script = f'''
        Find-Module {" ".join(params)} | Select-Object -First 20 Name, Version, Author, Description,
        @{{N='Downloads';E={{$_.AdditionalMetadata.downloadCount}}}},
        @{{N='Published';E={{$_.AdditionalMetadata.published}}}}
        '''
        return await self._run_powershell(ps_script, timeout=60)

    async def _get_module_commands(self, module_name: str, command_type: str = None, **kwargs) -> Dict[str, Any]:
        """Get commands exported by a module."""
        type_filter = f'-CommandType {command_type}' if command_type else ""
        ps_script = f'''
        Get-Command -Module "{module_name}" {type_filter} | 
        Select-Object Name, CommandType, 
        @{{N='Parameters';E={{$_.Parameters.Keys -join ", "}}}},
        @{{N='ParameterSets';E={{$_.ParameterSets.Name -join ", "}}}}
        '''
        return await self._run_powershell(ps_script)

    # Job Management
    async def _get_jobs(self, state: str = None, **kwargs) -> Dict[str, Any]:
        """Get PowerShell background jobs."""
        filter_clause = f'| Where-Object {{ $_.State -eq "{state}" }}' if state else ""
        ps_script = f'''
        Get-Job {filter_clause} | Select-Object Id, Name, 
        @{{N='State';E={{$_.State.ToString()}}}},
        HasMoreData, Location, Command,
        @{{N='StartTime';E={{$_.PSBeginTime}}}},
        @{{N='EndTime';E={{$_.PSEndTime}}}}
        '''
        return await self._run_powershell(ps_script)

    async def _get_job_result(self, job_id: int, keep: bool = False, **kwargs) -> Dict[str, Any]:
        """Get the result of a background job."""
        keep_flag = "-Keep" if keep else ""
        ps_script = f'''
        $job = Get-Job -Id {job_id}
        if ($job) {{
            $result = Receive-Job -Id {job_id} {keep_flag}
            @{{
                JobId = $job.Id
                State = $job.State.ToString()
                HasMoreData = $job.HasMoreData
                Result = $result
            }}
        }} else {{
            @{{ Success = $false; Error = "Job not found" }}
        }}
        '''
        return await self._run_powershell(ps_script)

    async def _stop_job(self, job_id: int, **kwargs) -> Dict[str, Any]:
        """Stop a running background job."""
        ps_script = f'''
        Stop-Job -Id {job_id}
        $job = Get-Job -Id {job_id}
        @{{ Success = $true; State = $job.State.ToString() }}
        '''
        return await self._run_powershell(ps_script)

    async def _remove_job(self, job_id: int, force: bool = False, **kwargs) -> Dict[str, Any]:
        """Remove a background job."""
        force_flag = "-Force" if force else ""
        ps_script = f'''
        Remove-Job -Id {job_id} {force_flag}
        @{{ Success = $true; Message = "Job removed" }}
        '''
        return await self._run_powershell(ps_script)

    async def _wait_job(self, job_id: int, timeout: int = 300, **kwargs) -> Dict[str, Any]:
        """Wait for a job to complete."""
        ps_script = f'''
        $job = Wait-Job -Id {job_id} -Timeout {timeout}
        if ($job) {{
            @{{
                JobId = $job.Id
                State = $job.State.ToString()
                HasMoreData = $job.HasMoreData
                Completed = $job.State -eq "Completed"
            }}
        }} else {{
            @{{ Success = $false; Error = "Job timed out or not found" }}
        }}
        '''
        return await self._run_powershell(ps_script, timeout=timeout + 30)

    # Security and Signing
    async def _get_execution_policy(self, scope: str = None, **kwargs) -> Dict[str, Any]:
        """Get the current execution policy."""
        if scope:
            ps_script = f'Get-ExecutionPolicy -Scope {scope}'
        else:
            ps_script = '''
            Get-ExecutionPolicy -List | ForEach-Object {
                @{
                    Scope = $_.Scope.ToString()
                    ExecutionPolicy = $_.ExecutionPolicy.ToString()
                }
            }
            '''
        return await self._run_powershell(ps_script)

    async def _set_execution_policy(self, policy: str, scope: str = "CurrentUser", **kwargs) -> Dict[str, Any]:
        """Set the execution policy."""
        ps_script = f'''
        Set-ExecutionPolicy -ExecutionPolicy {policy} -Scope {scope} -Force
        @{{ Success = $true; Policy = "{policy}"; Scope = "{scope}" }}
        '''
        return await self._run_powershell(ps_script)

    async def _sign_script(self, script_path: str, certificate_thumbprint: str, **kwargs) -> Dict[str, Any]:
        """Sign a PowerShell script with a certificate."""
        ps_script = f'''
        $cert = Get-ChildItem -Path Cert:\\CurrentUser\\My -CodeSigningCert | 
                Where-Object {{ $_.Thumbprint -eq "{certificate_thumbprint}" }}
        if ($cert) {{
            $sig = Set-AuthenticodeSignature -FilePath "{script_path}" -Certificate $cert
            @{{
                Path = $sig.Path
                Status = $sig.Status.ToString()
                StatusMessage = $sig.StatusMessage
                SignerCertificate = $sig.SignerCertificate.Subject
            }}
        }} else {{
            @{{ Success = $false; Error = "Certificate not found" }}
        }}
        '''
        return await self._run_powershell(ps_script)

    async def _verify_script_signature(self, script_path: str, **kwargs) -> Dict[str, Any]:
        """Verify the signature of a PowerShell script."""
        ps_script = f'''
        $sig = Get-AuthenticodeSignature -FilePath "{script_path}"
        @{{
            Path = $sig.Path
            Status = $sig.Status.ToString()
            StatusMessage = $sig.StatusMessage
            IsValid = $sig.Status -eq "Valid"
            SignerCertificate = if($sig.SignerCertificate) {{
                @{{
                    Subject = $sig.SignerCertificate.Subject
                    Issuer = $sig.SignerCertificate.Issuer
                    Thumbprint = $sig.SignerCertificate.Thumbprint
                    NotBefore = $sig.SignerCertificate.NotBefore
                    NotAfter = $sig.SignerCertificate.NotAfter
                }}
            }} else {{ $null }}
        }}
        '''
        return await self._run_powershell(ps_script)

    async def _get_authenticode_signature(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Get Authenticode signature details for a file."""
        ps_script = f'''
        $sig = Get-AuthenticodeSignature -FilePath "{file_path}"
        @{{
            Path = $sig.Path
            SignatureType = $sig.SignatureType.ToString()
            Status = $sig.Status.ToString()
            StatusMessage = $sig.StatusMessage
            IsOSBinary = $sig.IsOSBinary
        }}
        '''
        return await self._run_powershell(ps_script)

    async def _list_certificates(self, store: str = "CurrentUser", purpose: str = None, **kwargs) -> Dict[str, Any]:
        """List certificates available for code signing."""
        filter_clause = "-CodeSigningCert" if purpose == "codesigning" else ""
        ps_script = f'''
        Get-ChildItem -Path Cert:\\{store}\\My {filter_clause} |
        Select-Object Subject, Issuer, Thumbprint, NotBefore, NotAfter,
        @{{N='HasPrivateKey';E={{$_.HasPrivateKey}}}},
        @{{N='EnhancedKeyUsage';E={{$_.EnhancedKeyUsageList.FriendlyName -join ", "}}}}
        '''
        return await self._run_powershell(ps_script)

    # Profile Management
    async def _get_profile_paths(self, **kwargs) -> Dict[str, Any]:
        """Get all PowerShell profile paths."""
        ps_script = '''
        @{
            AllUsersAllHosts = $PROFILE.AllUsersAllHosts
            AllUsersCurrentHost = $PROFILE.AllUsersCurrentHost
            CurrentUserAllHosts = $PROFILE.CurrentUserAllHosts
            CurrentUserCurrentHost = $PROFILE.CurrentUserCurrentHost
            CurrentProfile = $PROFILE
        }
        '''
        return await self._run_powershell(ps_script)

    async def _test_profile_exists(self, **kwargs) -> Dict[str, Any]:
        """Test which profiles exist."""
        ps_script = '''
        @{
            AllUsersAllHosts = Test-Path $PROFILE.AllUsersAllHosts
            AllUsersCurrentHost = Test-Path $PROFILE.AllUsersCurrentHost
            CurrentUserAllHosts = Test-Path $PROFILE.CurrentUserAllHosts
            CurrentUserCurrentHost = Test-Path $PROFILE.CurrentUserCurrentHost
        }
        '''
        return await self._run_powershell(ps_script)

    async def _get_profile_content(self, profile_type: str = "CurrentUserCurrentHost", **kwargs) -> Dict[str, Any]:
        """Get the content of a PowerShell profile."""
        ps_script = f'''
        $profilePath = $PROFILE.{profile_type}
        if (Test-Path $profilePath) {{
            @{{
                Path = $profilePath
                Content = Get-Content $profilePath -Raw
                Lines = (Get-Content $profilePath).Count
            }}
        }} else {{
            @{{ Success = $false; Error = "Profile does not exist"; Path = $profilePath }}
        }}
        '''
        return await self._run_powershell(ps_script)

    async def _add_to_profile(self, content: str, profile_type: str = "CurrentUserCurrentHost", **kwargs) -> Dict[str, Any]:
        """Add content to a PowerShell profile."""
        # Escape special characters
        escaped_content = content.replace("'", "''")
        ps_script = f'''
        $profilePath = $PROFILE.{profile_type}
        $parentDir = Split-Path $profilePath -Parent
        if (-not (Test-Path $parentDir)) {{
            New-Item -ItemType Directory -Path $parentDir -Force | Out-Null
        }}
        
        Add-Content -Path $profilePath -Value '{escaped_content}'
        @{{ Success = $true; Path = $profilePath }}
        '''
        return await self._run_powershell(ps_script)

    # History and Transcription
    async def _get_history(self, count: int = 50, **kwargs) -> Dict[str, Any]:
        """Get PowerShell command history."""
        ps_script = f'''
        Get-History -Count {count} | Select-Object Id, CommandLine, 
        @{{N='StartTime';E={{$_.StartExecutionTime}}}},
        @{{N='EndTime';E={{$_.EndExecutionTime}}}},
        @{{N='Duration';E={{$_.EndExecutionTime - $_.StartExecutionTime}}}},
        @{{N='Status';E={{$_.ExecutionStatus.ToString()}}}}
        '''
        return await self._run_powershell(ps_script)

    async def _clear_history(self, **kwargs) -> Dict[str, Any]:
        """Clear PowerShell command history."""
        ps_script = '''
        Clear-History
        @{ Success = $true; Message = "History cleared" }
        '''
        return await self._run_powershell(ps_script)

    async def _start_transcript(self, path: str = None, append: bool = False, **kwargs) -> Dict[str, Any]:
        """Start a PowerShell transcript."""
        params = []
        if path:
            params.append(f'-Path "{path}"')
        if append:
            params.append("-Append")
        
        ps_script = f'''
        $transcript = Start-Transcript {" ".join(params)}
        @{{ Success = $true; Message = $transcript }}
        '''
        return await self._run_powershell(ps_script, as_json=False)

    async def _stop_transcript(self, **kwargs) -> Dict[str, Any]:
        """Stop the current PowerShell transcript."""
        ps_script = '''
        $result = Stop-Transcript
        @{ Success = $true; Message = $result }
        '''
        return await self._run_powershell(ps_script, as_json=False)

    # Variables and Environment
    async def _get_variable(self, name: str, **kwargs) -> Dict[str, Any]:
        """Get a PowerShell variable value."""
        ps_script = f'''
        $var = Get-Variable -Name "{name}" -ErrorAction SilentlyContinue
        if ($var) {{
            @{{
                Name = $var.Name
                Value = $var.Value
                Description = $var.Description
                Options = $var.Options.ToString()
            }}
        }} else {{
            @{{ Success = $false; Error = "Variable not found" }}
        }}
        '''
        return await self._run_powershell(ps_script)

    async def _set_variable(self, name: str, value: Any, description: str = None, **kwargs) -> Dict[str, Any]:
        """Set a PowerShell variable."""
        desc_param = f'-Description "{description}"' if description else ""
        if isinstance(value, str):
            value_str = f'"{value}"'
        elif isinstance(value, bool):
            value_str = f"${str(value).lower()}"
        else:
            value_str = str(value)
        
        ps_script = f'''
        Set-Variable -Name "{name}" -Value {value_str} {desc_param} -Scope Global
        @{{ Success = $true; Name = "{name}" }}
        '''
        return await self._run_powershell(ps_script)

    async def _remove_variable(self, name: str, **kwargs) -> Dict[str, Any]:
        """Remove a PowerShell variable."""
        ps_script = f'''
        Remove-Variable -Name "{name}" -Scope Global -Force -ErrorAction Stop
        @{{ Success = $true; Message = "Variable removed" }}
        '''
        return await self._run_powershell(ps_script)

    async def _list_variables(self, scope: str = None, **kwargs) -> Dict[str, Any]:
        """List PowerShell variables."""
        scope_param = f'-Scope {scope}' if scope else ""
        ps_script = f'''
        Get-Variable {scope_param} | Select-Object Name, 
        @{{N='Value';E={{if($_.Value -is [string] -or $_.Value -is [int] -or $_.Value -is [bool]){{$_.Value}}else{{$_.Value.GetType().Name}}}}}},
        @{{N='Options';E={{$_.Options.ToString()}}}}
        '''
        return await self._run_powershell(ps_script)

    async def _get_environment_variable(self, name: str, target: str = "Process", **kwargs) -> Dict[str, Any]:
        """Get an environment variable."""
        ps_script = f'''
        $value = [Environment]::GetEnvironmentVariable("{name}", "{target}")
        @{{
            Name = "{name}"
            Value = $value
            Target = "{target}"
            Exists = $null -ne $value
        }}
        '''
        return await self._run_powershell(ps_script)

    async def _set_environment_variable(self, name: str, value: str, target: str = "Process", **kwargs) -> Dict[str, Any]:
        """Set an environment variable."""
        ps_script = f'''
        [Environment]::SetEnvironmentVariable("{name}", "{value}", "{target}")
        @{{ Success = $true; Name = "{name}"; Target = "{target}" }}
        '''
        return await self._run_powershell(ps_script)

    # Command Discovery
    async def _get_command(self, command_name: str, **kwargs) -> Dict[str, Any]:
        """Get information about a PowerShell command."""
        ps_script = f'''
        $cmd = Get-Command -Name "{command_name}" -ErrorAction SilentlyContinue
        if ($cmd) {{
            @{{
                Name = $cmd.Name
                CommandType = $cmd.CommandType.ToString()
                ModuleName = $cmd.ModuleName
                Source = $cmd.Source
                Version = if($cmd.Version){{$cmd.Version.ToString()}}else{{$null}}
                Definition = if($cmd.CommandType -eq "Alias"){{$cmd.Definition}}else{{$null}}
                Parameters = @($cmd.Parameters.Keys)
            }}
        }} else {{
            @{{ Success = $false; Error = "Command not found" }}
        }}
        '''
        return await self._run_powershell(ps_script)

    async def _get_command_syntax(self, command_name: str, **kwargs) -> Dict[str, Any]:
        """Get the syntax of a PowerShell command."""
        ps_script = f'''
        $syntax = Get-Command -Name "{command_name}" -Syntax
        @{{
            Command = "{command_name}"
            Syntax = $syntax
        }}
        '''
        return await self._run_powershell(ps_script)

    async def _get_alias(self, alias_name: str, **kwargs) -> Dict[str, Any]:
        """Get information about a PowerShell alias."""
        ps_script = f'''
        $alias = Get-Alias -Name "{alias_name}" -ErrorAction SilentlyContinue
        if ($alias) {{
            @{{
                Name = $alias.Name
                Definition = $alias.Definition
                Description = $alias.Description
                Options = $alias.Options.ToString()
                ReferencedCommand = $alias.ReferencedCommand.Name
            }}
        }} else {{
            @{{ Success = $false; Error = "Alias not found" }}
        }}
        '''
        return await self._run_powershell(ps_script)

    async def _list_aliases(self, definition: str = None, **kwargs) -> Dict[str, Any]:
        """List PowerShell aliases."""
        filter_clause = f'| Where-Object {{ $_.Definition -like "*{definition}*" }}' if definition else ""
        ps_script = f'''
        Get-Alias {filter_clause} | Select-Object Name, Definition, Description,
        @{{N='Options';E={{$_.Options.ToString()}}}}
        '''
        return await self._run_powershell(ps_script)

    # Pipeline and Output
    async def _format_output(self, script: str, format_type: str = "Table", **kwargs) -> Dict[str, Any]:
        """Format PowerShell output."""
        format_cmd = {
            "Table": "Format-Table -AutoSize",
            "List": "Format-List",
            "Wide": "Format-Wide",
            "Custom": "Format-Custom"
        }.get(format_type, "Format-Table -AutoSize")
        
        ps_script = f'{script} | {format_cmd} | Out-String'
        return await self._run_powershell(ps_script, as_json=False)

    async def _export_to_csv(self, script: str, path: str, **kwargs) -> Dict[str, Any]:
        """Export PowerShell output to CSV."""
        ps_script = f'''
        {script} | Export-Csv -Path "{path}" -NoTypeInformation
        @{{ Success = $true; Path = "{path}" }}
        '''
        return await self._run_powershell(ps_script)

    async def _export_to_xml(self, script: str, path: str, **kwargs) -> Dict[str, Any]:
        """Export PowerShell output to XML."""
        ps_script = f'''
        {script} | Export-Clixml -Path "{path}"
        @{{ Success = $true; Path = "{path}" }}
        '''
        return await self._run_powershell(ps_script)

    async def _export_to_json(self, script: str, path: str, depth: int = 10, **kwargs) -> Dict[str, Any]:
        """Export PowerShell output to JSON."""
        ps_script = f'''
        {script} | ConvertTo-Json -Depth {depth} | Out-File -FilePath "{path}"
        @{{ Success = $true; Path = "{path}" }}
        '''
        return await self._run_powershell(ps_script)

    # Diagnostics
    async def _get_powershell_version(self, **kwargs) -> Dict[str, Any]:
        """Get PowerShell version information."""
        ps_script = '''
        @{
            PSVersion = $PSVersionTable.PSVersion.ToString()
            PSEdition = $PSVersionTable.PSEdition
            GitCommitId = $PSVersionTable.GitCommitId
            OS = $PSVersionTable.OS
            Platform = $PSVersionTable.Platform
            PSCompatibleVersions = @($PSVersionTable.PSCompatibleVersions | ForEach-Object { $_.ToString() })
            PSRemotingProtocolVersion = $PSVersionTable.PSRemotingProtocolVersion.ToString()
            SerializationVersion = $PSVersionTable.SerializationVersion.ToString()
            WSManStackVersion = $PSVersionTable.WSManStackVersion.ToString()
        }
        '''
        return await self._run_powershell(ps_script)

    async def _get_host_info(self, **kwargs) -> Dict[str, Any]:
        """Get PowerShell host information."""
        ps_script = '''
        @{
            Name = $Host.Name
            Version = $Host.Version.ToString()
            InstanceId = $Host.InstanceId.ToString()
            CurrentCulture = $Host.CurrentCulture.Name
            CurrentUICulture = $Host.CurrentUICulture.Name
            PrivateData = $Host.PrivateData
        }
        '''
        return await self._run_powershell(ps_script)

    async def _test_script_syntax(self, script: str, **kwargs) -> Dict[str, Any]:
        """Test PowerShell script syntax without executing."""
        # Write script to temp file for parsing
        escaped_script = script.replace("'", "''")
        ps_script = f'''
        $errors = @()
        $tokens = @()
        $ast = [System.Management.Automation.Language.Parser]::ParseInput(
            '{escaped_script}',
            [ref]$tokens,
            [ref]$errors
        )
        
        @{{
            IsValid = $errors.Count -eq 0
            Errors = @($errors | ForEach-Object {{
                @{{
                    Message = $_.Message
                    Extent = $_.Extent.Text
                    Line = $_.Extent.StartLineNumber
                    Column = $_.Extent.StartColumnNumber
                }}
            }})
            TokenCount = $tokens.Count
        }}
        '''
        return await self._run_powershell(ps_script)

    async def _measure_command(self, command: str, iterations: int = 1, **kwargs) -> Dict[str, Any]:
        """Measure command execution time."""
        ps_script = f'''
        $results = 1..{iterations} | ForEach-Object {{
            Measure-Command {{ {command} }}
        }}
        
        @{{
            Iterations = {iterations}
            TotalMilliseconds = ($results | Measure-Object -Property TotalMilliseconds -Sum).Sum
            AverageMilliseconds = ($results | Measure-Object -Property TotalMilliseconds -Average).Average
            MinMilliseconds = ($results | Measure-Object -Property TotalMilliseconds -Minimum).Minimum
            MaxMilliseconds = ($results | Measure-Object -Property TotalMilliseconds -Maximum).Maximum
        }}
        '''
        return await self._run_powershell(ps_script, timeout=iterations * 60 + 60)
