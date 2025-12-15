"""
BITS Transfer Plugin for Windows AI
Background Intelligent Transfer Service management and file transfers
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata

logger = logging.getLogger(__name__)


class BitsTransferPlugin(IntegrationPlugin):
    """
    Comprehensive BITS (Background Intelligent Transfer Service) plugin.
    
    Provides 30+ actions for:
    - BITS job management
    - Download/upload operations
    - Bandwidth throttling
    - Job priorities and scheduling
    - Transfer monitoring
    - Error handling and retries
    """

    def __init__(self):
        metadata = PluginMetadata(
            id="bits-transfer",
            name="BITS Transfer",
            description="Background Intelligent Transfer Service management and file transfers",
            version="2.0.0",
            author="Windows AI Team",
            tags=["bits", "transfer", "download", "upload", "windows"]
        )
        super().__init__(metadata)

    async def _run_powershell(self, script: str, as_json: bool = True, timeout: int = 60) -> Dict[str, Any]:
        """Execute PowerShell script and return results."""
        try:
            json_suffix = " | ConvertTo-Json -Depth 10 -Compress" if as_json else ""
            full_script = f"Import-Module BitsTransfer; $ErrorActionPreference = 'Stop'; {script}{json_suffix}"
            
            process = await asyncio.create_subprocess_exec(
                "powershell.exe", "-NoProfile", "-NonInteractive", "-Command", full_script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                process.kill()
                return {"success": False, "error": f"Command timed out after {timeout} seconds"}
            
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

    async def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """Execute BITS transfer actions."""
        actions = {
            # Job Management
            "list_jobs": self._list_jobs,
            "get_job": self._get_job,
            "create_download_job": self._create_download_job,
            "create_upload_job": self._create_upload_job,
            "remove_job": self._remove_job,
            "complete_job": self._complete_job,
            "suspend_job": self._suspend_job,
            "resume_job": self._resume_job,
            
            # File Operations
            "add_file": self._add_file,
            "add_files": self._add_files,
            "get_files": self._get_files,
            "remove_file": self._remove_file,
            
            # Job Configuration
            "set_priority": self._set_priority,
            "set_description": self._set_description,
            "set_credentials": self._set_credentials,
            "set_proxy": self._set_proxy,
            "set_retry_delay": self._set_retry_delay,
            "set_retry_timeout": self._set_retry_timeout,
            "set_minimum_retry_delay": self._set_minimum_retry_delay,
            "set_no_progress_timeout": self._set_no_progress_timeout,
            
            # Transfer Control
            "start_transfer": self._start_transfer,
            "sync_download": self._sync_download,
            "sync_upload": self._sync_upload,
            "async_download": self._async_download,
            
            # Monitoring
            "get_progress": self._get_progress,
            "get_error_info": self._get_error_info,
            "get_transfer_stats": self._get_transfer_stats,
            
            # Bulk Operations
            "clear_all_jobs": self._clear_all_jobs,
            "cancel_all_jobs": self._cancel_all_jobs,
            "get_service_status": self._get_service_status,
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

    # Job Management
    async def _list_jobs(self, all_users: bool = False, **kwargs) -> Dict[str, Any]:
        """List all BITS jobs."""
        all_param = "-AllUsers" if all_users else ""
        script = f'''
        Get-BitsTransfer {all_param} | Select-Object JobId, DisplayName, 
        @{{N='TransferType';E={{$_.TransferType.ToString()}}}},
        @{{N='JobState';E={{$_.JobState.ToString()}}}},
        @{{N='Priority';E={{$_.Priority.ToString()}}}},
        BytesTotal, BytesTransferred,
        @{{N='PercentComplete';E={{if($_.BytesTotal -gt 0){{[math]::Round(($_.BytesTransferred/$_.BytesTotal)*100, 2)}}else{{0}}}}}},
        FilesTotal, FilesTransferred,
        CreationTime, ModificationTime,
        @{{N='Owner';E={{$_.OwnerAccount}}}}
        '''
        return await self._run_powershell(script)

    async def _get_job(self, job_id: str = None, job_name: str = None, **kwargs) -> Dict[str, Any]:
        """Get detailed information about a BITS job."""
        if job_id:
            filter_param = f'-JobId "{job_id}"'
        elif job_name:
            filter_param = f'-Name "{job_name}"'
        else:
            return {"success": False, "error": "Either job_id or job_name required"}
        
        script = f'''
        $job = Get-BitsTransfer {filter_param}
        @{{
            JobId = $job.JobId.ToString()
            DisplayName = $job.DisplayName
            Description = $job.Description
            TransferType = $job.TransferType.ToString()
            JobState = $job.JobState.ToString()
            Priority = $job.Priority.ToString()
            BytesTotal = $job.BytesTotal
            BytesTransferred = $job.BytesTransferred
            PercentComplete = if($job.BytesTotal -gt 0){{[math]::Round(($job.BytesTransferred/$job.BytesTotal)*100, 2)}}else{{0}}
            FilesTotal = $job.FilesTotal
            FilesTransferred = $job.FilesTransferred
            CreationTime = $job.CreationTime
            ModificationTime = $job.ModificationTime
            Owner = $job.OwnerAccount
            ErrorCount = $job.ErrorCount
            TransientErrorCount = $job.TransientErrorCount
            ProxyUsage = $job.ProxyUsage.ToString()
            RetryDelay = $job.RetryDelay
            RetryTimeout = $job.RetryTimeout
            MinimumRetryDelay = $job.MinimumRetryDelay
            NoProgressTimeout = $job.NoProgressTimeout
        }}
        '''
        return await self._run_powershell(script)

    async def _create_download_job(self, job_name: str, source_url: str, destination: str,
                                    priority: str = "Normal", description: str = None,
                                    **kwargs) -> Dict[str, Any]:
        """Create a new download job."""
        desc_param = f'-Description "{description}"' if description else ""
        script = f'''
        $job = Start-BitsTransfer -Source "{source_url}" -Destination "{destination}" `
            -DisplayName "{job_name}" -Priority {priority} {desc_param} -Asynchronous
        @{{
            Success = $true
            JobId = $job.JobId.ToString()
            DisplayName = $job.DisplayName
            JobState = $job.JobState.ToString()
        }}
        '''
        return await self._run_powershell(script)

    async def _create_upload_job(self, job_name: str, source: str, destination_url: str,
                                  priority: str = "Normal", description: str = None,
                                  **kwargs) -> Dict[str, Any]:
        """Create a new upload job."""
        desc_param = f'-Description "{description}"' if description else ""
        script = f'''
        $job = Start-BitsTransfer -Source "{source}" -Destination "{destination_url}" `
            -DisplayName "{job_name}" -Priority {priority} {desc_param} -TransferType Upload -Asynchronous
        @{{
            Success = $true
            JobId = $job.JobId.ToString()
            DisplayName = $job.DisplayName
            JobState = $job.JobState.ToString()
        }}
        '''
        return await self._run_powershell(script)

    async def _remove_job(self, job_id: str = None, job_name: str = None, **kwargs) -> Dict[str, Any]:
        """Remove a BITS job."""
        if job_id:
            filter_param = f'-JobId "{job_id}"'
        elif job_name:
            filter_param = f'-Name "{job_name}"'
        else:
            return {"success": False, "error": "Either job_id or job_name required"}
        
        script = f'''
        Get-BitsTransfer {filter_param} | Remove-BitsTransfer
        @{{ Success = $true; Message = "Job removed" }}
        '''
        return await self._run_powershell(script)

    async def _complete_job(self, job_id: str = None, job_name: str = None, **kwargs) -> Dict[str, Any]:
        """Complete a BITS job (finalize transferred files)."""
        if job_id:
            filter_param = f'-JobId "{job_id}"'
        elif job_name:
            filter_param = f'-Name "{job_name}"'
        else:
            return {"success": False, "error": "Either job_id or job_name required"}
        
        script = f'''
        Get-BitsTransfer {filter_param} | Complete-BitsTransfer
        @{{ Success = $true; Message = "Job completed" }}
        '''
        return await self._run_powershell(script)

    async def _suspend_job(self, job_id: str = None, job_name: str = None, **kwargs) -> Dict[str, Any]:
        """Suspend a BITS job."""
        if job_id:
            filter_param = f'-JobId "{job_id}"'
        elif job_name:
            filter_param = f'-Name "{job_name}"'
        else:
            return {"success": False, "error": "Either job_id or job_name required"}
        
        script = f'''
        $job = Get-BitsTransfer {filter_param} | Suspend-BitsTransfer -PassThru
        @{{ Success = $true; JobState = $job.JobState.ToString() }}
        '''
        return await self._run_powershell(script)

    async def _resume_job(self, job_id: str = None, job_name: str = None, 
                          asynchronous: bool = True, **kwargs) -> Dict[str, Any]:
        """Resume a suspended BITS job."""
        if job_id:
            filter_param = f'-JobId "{job_id}"'
        elif job_name:
            filter_param = f'-Name "{job_name}"'
        else:
            return {"success": False, "error": "Either job_id or job_name required"}
        
        async_param = "-Asynchronous" if asynchronous else ""
        script = f'''
        $job = Get-BitsTransfer {filter_param} | Resume-BitsTransfer {async_param} -PassThru
        @{{ Success = $true; JobState = $job.JobState.ToString() }}
        '''
        return await self._run_powershell(script)

    # File Operations
    async def _add_file(self, job_name: str, source: str, destination: str, **kwargs) -> Dict[str, Any]:
        """Add a file to an existing BITS job."""
        script = f'''
        $job = Get-BitsTransfer -Name "{job_name}"
        Add-BitsFile -BitsJob $job -Source "{source}" -Destination "{destination}"
        @{{ Success = $true; Source = "{source}"; Destination = "{destination}" }}
        '''
        return await self._run_powershell(script)

    async def _add_files(self, job_name: str, files: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Add multiple files to an existing BITS job."""
        file_entries = "\\n".join([f'"{f["source"]}","{f["destination"]}"' for f in files])
        script = f'''
        $job = Get-BitsTransfer -Name "{job_name}"
        $files = @"
{file_entries}
"@ | ConvertFrom-Csv -Header Source, Destination
        foreach ($file in $files) {{
            Add-BitsFile -BitsJob $job -Source $file.Source -Destination $file.Destination
        }}
        @{{ Success = $true; FilesAdded = {len(files)} }}
        '''
        return await self._run_powershell(script)

    async def _get_files(self, job_id: str = None, job_name: str = None, **kwargs) -> Dict[str, Any]:
        """Get files in a BITS job."""
        if job_id:
            filter_param = f'-JobId "{job_id}"'
        elif job_name:
            filter_param = f'-Name "{job_name}"'
        else:
            return {"success": False, "error": "Either job_id or job_name required"}
        
        script = f'''
        $job = Get-BitsTransfer {filter_param}
        $job.FileList | Select-Object RemoteName, LocalName, BytesTotal, BytesTransferred,
        @{{N='PercentComplete';E={{if($_.BytesTotal -gt 0){{[math]::Round(($_.BytesTransferred/$_.BytesTotal)*100, 2)}}else{{0}}}}}},
        @{{N='IsTransferComplete';E={{$_.IsTransferComplete}}}}
        '''
        return await self._run_powershell(script)

    async def _remove_file(self, job_name: str, source: str, **kwargs) -> Dict[str, Any]:
        """Remove a file from a BITS job (not widely supported)."""
        return {"success": False, "error": "BITS does not support removing individual files. Remove and recreate the job."}

    # Job Configuration
    async def _set_priority(self, job_name: str, priority: str, **kwargs) -> Dict[str, Any]:
        """Set job priority (Foreground, High, Normal, Low)."""
        script = f'''
        $job = Get-BitsTransfer -Name "{job_name}"
        Set-BitsTransfer -BitsJob $job -Priority {priority}
        @{{ Success = $true; Priority = "{priority}" }}
        '''
        return await self._run_powershell(script)

    async def _set_description(self, job_name: str, description: str, **kwargs) -> Dict[str, Any]:
        """Set job description."""
        script = f'''
        $job = Get-BitsTransfer -Name "{job_name}"
        Set-BitsTransfer -BitsJob $job -Description "{description}"
        @{{ Success = $true; Description = "{description}" }}
        '''
        return await self._run_powershell(script)

    async def _set_credentials(self, job_name: str, username: str, password: str,
                                mechanism: str = "Basic", usage: str = "Server", **kwargs) -> Dict[str, Any]:
        """Set credentials for a BITS job."""
        script = f'''
        $job = Get-BitsTransfer -Name "{job_name}"
        $cred = New-Object System.Management.Automation.PSCredential("{username}", (ConvertTo-SecureString "{password}" -AsPlainText -Force))
        Set-BitsTransfer -BitsJob $job -Credential $cred -Authentication {mechanism}
        @{{ Success = $true; Username = "{username}" }}
        '''
        return await self._run_powershell(script)

    async def _set_proxy(self, job_name: str, proxy_server: str = None, 
                         proxy_usage: str = "SystemDefault", **kwargs) -> Dict[str, Any]:
        """Set proxy configuration for a BITS job."""
        proxy_param = f'-ProxyList "{proxy_server}"' if proxy_server else ""
        script = f'''
        $job = Get-BitsTransfer -Name "{job_name}"
        Set-BitsTransfer -BitsJob $job -ProxyUsage {proxy_usage} {proxy_param}
        @{{ Success = $true; ProxyUsage = "{proxy_usage}" }}
        '''
        return await self._run_powershell(script)

    async def _set_retry_delay(self, job_name: str, seconds: int, **kwargs) -> Dict[str, Any]:
        """Set retry delay in seconds."""
        script = f'''
        $job = Get-BitsTransfer -Name "{job_name}"
        Set-BitsTransfer -BitsJob $job -RetryInterval {seconds}
        @{{ Success = $true; RetryDelay = {seconds} }}
        '''
        return await self._run_powershell(script)

    async def _set_retry_timeout(self, job_name: str, seconds: int, **kwargs) -> Dict[str, Any]:
        """Set retry timeout in seconds."""
        script = f'''
        $job = Get-BitsTransfer -Name "{job_name}"
        Set-BitsTransfer -BitsJob $job -RetryTimeout {seconds}
        @{{ Success = $true; RetryTimeout = {seconds} }}
        '''
        return await self._run_powershell(script)

    async def _set_minimum_retry_delay(self, job_name: str, seconds: int, **kwargs) -> Dict[str, Any]:
        """Set minimum retry delay."""
        script = f'''
        $job = Get-BitsTransfer -Name "{job_name}"
        $job.MinimumRetryDelay = {seconds}
        @{{ Success = $true; MinimumRetryDelay = {seconds} }}
        '''
        return await self._run_powershell(script)

    async def _set_no_progress_timeout(self, job_name: str, seconds: int, **kwargs) -> Dict[str, Any]:
        """Set no-progress timeout in seconds."""
        script = f'''
        $job = Get-BitsTransfer -Name "{job_name}"
        $job.NoProgressTimeout = {seconds}
        @{{ Success = $true; NoProgressTimeout = {seconds} }}
        '''
        return await self._run_powershell(script)

    # Transfer Control
    async def _start_transfer(self, source: str, destination: str, 
                               transfer_type: str = "Download",
                               priority: str = "Foreground",
                               display_name: str = None, **kwargs) -> Dict[str, Any]:
        """Start a synchronous transfer."""
        name_param = f'-DisplayName "{display_name}"' if display_name else ""
        script = f'''
        $job = Start-BitsTransfer -Source "{source}" -Destination "{destination}" `
            -TransferType {transfer_type} -Priority {priority} {name_param}
        @{{
            Success = $true
            Source = "{source}"
            Destination = "{destination}"
            Message = "Transfer completed"
        }}
        '''
        return await self._run_powershell(script, timeout=300)

    async def _sync_download(self, url: str, destination: str, 
                              display_name: str = None, **kwargs) -> Dict[str, Any]:
        """Perform a synchronous download."""
        name_param = f'-DisplayName "{display_name}"' if display_name else ""
        script = f'''
        Start-BitsTransfer -Source "{url}" -Destination "{destination}" {name_param}
        if (Test-Path "{destination}") {{
            $file = Get-Item "{destination}"
            @{{
                Success = $true
                Destination = "{destination}"
                SizeBytes = $file.Length
                Message = "Download completed"
            }}
        }} else {{
            @{{ Success = $false; Error = "File not found after download" }}
        }}
        '''
        return await self._run_powershell(script, timeout=600)

    async def _sync_upload(self, source: str, destination_url: str,
                            display_name: str = None, **kwargs) -> Dict[str, Any]:
        """Perform a synchronous upload."""
        name_param = f'-DisplayName "{display_name}"' if display_name else ""
        script = f'''
        Start-BitsTransfer -Source "{source}" -Destination "{destination_url}" `
            -TransferType Upload {name_param}
        @{{
            Success = $true
            Source = "{source}"
            Destination = "{destination_url}"
            Message = "Upload completed"
        }}
        '''
        return await self._run_powershell(script, timeout=600)

    async def _async_download(self, url: str, destination: str,
                               display_name: str = "WindowsAI Download",
                               priority: str = "Normal", **kwargs) -> Dict[str, Any]:
        """Start an asynchronous download."""
        script = f'''
        $job = Start-BitsTransfer -Source "{url}" -Destination "{destination}" `
            -DisplayName "{display_name}" -Priority {priority} -Asynchronous
        @{{
            Success = $true
            JobId = $job.JobId.ToString()
            DisplayName = $job.DisplayName
            JobState = $job.JobState.ToString()
            Source = "{url}"
            Destination = "{destination}"
        }}
        '''
        return await self._run_powershell(script)

    # Monitoring
    async def _get_progress(self, job_id: str = None, job_name: str = None, **kwargs) -> Dict[str, Any]:
        """Get transfer progress for a job."""
        if job_id:
            filter_param = f'-JobId "{job_id}"'
        elif job_name:
            filter_param = f'-Name "{job_name}"'
        else:
            return {"success": False, "error": "Either job_id or job_name required"}
        
        script = f'''
        $job = Get-BitsTransfer {filter_param}
        @{{
            JobId = $job.JobId.ToString()
            DisplayName = $job.DisplayName
            JobState = $job.JobState.ToString()
            BytesTotal = $job.BytesTotal
            BytesTransferred = $job.BytesTransferred
            PercentComplete = if($job.BytesTotal -gt 0){{[math]::Round(($job.BytesTransferred/$job.BytesTotal)*100, 2)}}else{{0}}
            FilesTotal = $job.FilesTotal
            FilesTransferred = $job.FilesTransferred
            TransferRate = if($job.BytesTotal -gt 0 -and $job.ModificationTime){{
                $elapsed = (Get-Date) - $job.CreationTime
                if($elapsed.TotalSeconds -gt 0){{[math]::Round($job.BytesTransferred/$elapsed.TotalSeconds, 0)}}else{{0}}
            }}else{{0}}
        }}
        '''
        return await self._run_powershell(script)

    async def _get_error_info(self, job_id: str = None, job_name: str = None, **kwargs) -> Dict[str, Any]:
        """Get error information for a failed job."""
        if job_id:
            filter_param = f'-JobId "{job_id}"'
        elif job_name:
            filter_param = f'-Name "{job_name}"'
        else:
            return {"success": False, "error": "Either job_id or job_name required"}
        
        script = f'''
        $job = Get-BitsTransfer {filter_param}
        $error = $job.Error
        @{{
            JobId = $job.JobId.ToString()
            JobState = $job.JobState.ToString()
            ErrorCount = $job.ErrorCount
            TransientErrorCount = $job.TransientErrorCount
            ErrorContext = if($error){{$error.ErrorContext.ToString()}}else{{$null}}
            ErrorDescription = if($error){{$error.ErrorDescription}}else{{$null}}
            ErrorContextDescription = if($error){{$error.ErrorContextDescription}}else{{$null}}
        }}
        '''
        return await self._run_powershell(script)

    async def _get_transfer_stats(self, **kwargs) -> Dict[str, Any]:
        """Get overall BITS transfer statistics."""
        script = '''
        $jobs = Get-BitsTransfer -AllUsers -ErrorAction SilentlyContinue
        $stats = @{
            TotalJobs = $jobs.Count
            ByState = @{}
            ByType = @{}
            TotalBytesTransferred = 0
            TotalBytesRemaining = 0
            ActiveDownloads = 0
            ActiveUploads = 0
        }
        
        foreach ($job in $jobs) {
            $state = $job.JobState.ToString()
            $type = $job.TransferType.ToString()
            
            if (-not $stats.ByState.ContainsKey($state)) { $stats.ByState[$state] = 0 }
            $stats.ByState[$state]++
            
            if (-not $stats.ByType.ContainsKey($type)) { $stats.ByType[$type] = 0 }
            $stats.ByType[$type]++
            
            $stats.TotalBytesTransferred += $job.BytesTransferred
            $stats.TotalBytesRemaining += ($job.BytesTotal - $job.BytesTransferred)
            
            if ($job.JobState -eq "Transferring") {
                if ($type -eq "Download") { $stats.ActiveDownloads++ }
                else { $stats.ActiveUploads++ }
            }
        }
        
        $stats
        '''
        return await self._run_powershell(script)

    # Bulk Operations
    async def _clear_all_jobs(self, completed_only: bool = True, **kwargs) -> Dict[str, Any]:
        """Clear/remove BITS jobs."""
        if completed_only:
            filter_clause = '| Where-Object { $_.JobState -eq "Transferred" -or $_.JobState -eq "Error" -or $_.JobState -eq "Cancelled" }'
        else:
            filter_clause = ""
        
        script = f'''
        $jobs = Get-BitsTransfer {filter_clause}
        $count = $jobs.Count
        $jobs | Remove-BitsTransfer
        @{{ Success = $true; JobsRemoved = $count }}
        '''
        return await self._run_powershell(script)

    async def _cancel_all_jobs(self, **kwargs) -> Dict[str, Any]:
        """Cancel all active BITS jobs."""
        script = '''
        $jobs = Get-BitsTransfer | Where-Object { $_.JobState -eq "Transferring" -or $_.JobState -eq "Suspended" -or $_.JobState -eq "Connecting" }
        $count = $jobs.Count
        $jobs | Remove-BitsTransfer
        @{ Success = $true; JobsCancelled = $count }
        '''
        return await self._run_powershell(script)

    async def _get_service_status(self, **kwargs) -> Dict[str, Any]:
        """Get BITS service status."""
        script = '''
        $service = Get-Service -Name BITS
        $config = Get-WmiObject Win32_Service -Filter "Name='BITS'"
        @{
            ServiceName = $service.Name
            DisplayName = $service.DisplayName
            Status = $service.Status.ToString()
            StartType = $config.StartMode
            ProcessId = $config.ProcessId
            Description = $config.Description
            PathName = $config.PathName
        }
        '''
        return await self._run_powershell(script)
