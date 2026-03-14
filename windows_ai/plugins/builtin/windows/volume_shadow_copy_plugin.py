"""
Volume Shadow Copy Plugin for Windows AI
Comprehensive VSS management including snapshots, backup/restore, and shadow copy operations
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class VolumeShadowCopyPlugin(IntegrationPlugin):
    """
    Comprehensive Volume Shadow Copy Service (VSS) management plugin.
    
    Provides 40+ actions for:
    - Shadow copy creation and deletion
    - Snapshot management and scheduling
    - Volume backup and restore
    - VSS writer management
    - Provider configuration
    - Storage allocation and limits
    - Shadow copy mounting and access
    - Backup catalog management
    - System state backup/restore
    """

    def __init__(self):
        metadata = PluginMetadata(
            id="volume-shadow-copy",
            name="Volume Shadow Copy",
            description="Comprehensive VSS management for Windows backup and restore operations",
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["vss", "backup", "restore", "snapshot", "shadow-copy", "windows"]
        )
        super().__init__(metadata)
        self._vss_cache = {}

    async def _run_powershell(self, script: str, as_json: bool = True) -> Dict[str, Any]:
        """Execute PowerShell script and return results."""
        try:
            json_suffix = " | ConvertTo-Json -Depth 10 -Compress" if as_json else ""
            full_script = f"$ErrorActionPreference = 'Stop'; {script}{json_suffix}"
            
            process = await asyncio.create_subprocess_exec(
                "powershell.exe", "-NoProfile", "-NonInteractive", "-Command", full_script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='replace').strip()
                return {"success": False, "error": error_msg}
            
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

    async def _run_vssadmin(self, command: str) -> Dict[str, Any]:
        """Execute vssadmin command."""
        try:
            process = await asyncio.create_subprocess_exec(
                "vssadmin.exe", *command.split(),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            output = stdout.decode('utf-8', errors='replace').strip()
            error = stderr.decode('utf-8', errors='replace').strip()
            
            if process.returncode != 0:
                return {"success": False, "error": error or output}
            
            return {"success": True, "data": output}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _run_wbadmin(self, command: str) -> Dict[str, Any]:
        """Execute wbadmin command for Windows Backup."""
        try:
            process = await asyncio.create_subprocess_exec(
                "wbadmin.exe", *command.split(),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            output = stdout.decode('utf-8', errors='replace').strip()
            error = stderr.decode('utf-8', errors='replace').strip()
            
            if process.returncode != 0:
                return {"success": False, "error": error or output}
            
            return {"success": True, "data": output}
        except Exception as e:
            return {"success": False, "error": str(e)}


    async def connect(self, credentials: Dict[str, str]) -> bool:
        """Connect to the service"""
        return True

    async def disconnect(self) -> bool:
        """Disconnect from the service"""
        return True

    async def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """Execute VSS management actions."""
        actions = {
            # Shadow Copy Operations
            "list_shadow_copies": self._list_shadow_copies,
            "create_shadow_copy": self._create_shadow_copy,
            "delete_shadow_copy": self._delete_shadow_copy,
            "delete_all_shadow_copies": self._delete_all_shadow_copies,
            "get_shadow_copy_details": self._get_shadow_copy_details,
            "resize_shadow_storage": self._resize_shadow_storage,
            "list_shadow_storage": self._list_shadow_storage,
            "get_shadow_copy_by_id": self._get_shadow_copy_by_id,
            
            # VSS Writer Operations
            "list_writers": self._list_writers,
            "get_writer_status": self._get_writer_status,
            "check_writer_health": self._check_writer_health,
            "restart_writer": self._restart_writer,
            
            # VSS Provider Operations
            "list_providers": self._list_providers,
            "get_provider_details": self._get_provider_details,
            
            # Mount and Access Operations
            "mount_shadow_copy": self._mount_shadow_copy,
            "unmount_shadow_copy": self._unmount_shadow_copy,
            "list_mounted_shadow_copies": self._list_mounted_shadow_copies,
            "browse_shadow_copy": self._browse_shadow_copy,
            "restore_file_from_shadow": self._restore_file_from_shadow,
            "restore_folder_from_shadow": self._restore_folder_from_shadow,
            "compare_with_shadow": self._compare_with_shadow,
            
            # Volume Operations
            "get_volume_info": self._get_volume_info,
            "list_volumes": self._list_volumes,
            "enable_shadow_copies": self._enable_shadow_copies,
            "disable_shadow_copies": self._disable_shadow_copies,
            "get_volume_shadow_status": self._get_volume_shadow_status,
            
            # Storage Management
            "get_storage_usage": self._get_storage_usage,
            "set_storage_limit": self._set_storage_limit,
            "get_storage_associations": self._get_storage_associations,
            "add_storage_association": self._add_storage_association,
            "delete_storage_association": self._delete_storage_association,
            
            # Backup Operations (wbadmin)
            "start_backup": self._start_backup,
            "start_system_state_backup": self._start_system_state_backup,
            "list_backups": self._list_backups,
            "get_backup_details": self._get_backup_details,
            "delete_backup": self._delete_backup,
            "start_recovery": self._start_recovery,
            "start_system_state_recovery": self._start_system_state_recovery,
            "get_recovery_items": self._get_recovery_items,
            
            # Scheduling
            "create_shadow_schedule": self._create_shadow_schedule,
            "delete_shadow_schedule": self._delete_shadow_schedule,
            "list_shadow_schedules": self._list_shadow_schedules,
            "modify_shadow_schedule": self._modify_shadow_schedule,
            
            # Diagnostics
            "run_vss_diagnostics": self._run_vss_diagnostics,
            "get_vss_service_status": self._get_vss_service_status,
            "repair_vss": self._repair_vss,
            "get_vss_events": self._get_vss_events,
            "check_vss_prerequisites": self._check_vss_prerequisites,
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

    # Shadow Copy Operations
    async def _list_shadow_copies(self, volume: str = None, **kwargs) -> Dict[str, Any]:
        """List all shadow copies, optionally filtered by volume."""
        if volume:
            script = f'''
            Get-WmiObject Win32_ShadowCopy | Where-Object {{ $_.VolumeName -like "*{volume}*" }} | 
            Select-Object ID, DeviceObject, VolumeName, InstallDate, 
            @{{N='CreationTime';E={{$_.ConvertToDateTime($_.InstallDate)}}}},
            @{{N='SizeMB';E={{[math]::Round($_.Count/1MB,2)}}}}
            '''
        else:
            script = '''
            Get-WmiObject Win32_ShadowCopy | 
            Select-Object ID, DeviceObject, VolumeName, InstallDate,
            @{N='CreationTime';E={$_.ConvertToDateTime($_.InstallDate)}},
            @{N='SizeMB';E={[math]::Round($_.Count/1MB,2)}}
            '''
        return await self._run_powershell(script)

    async def _create_shadow_copy(self, volume: str, **kwargs) -> Dict[str, Any]:
        """Create a new shadow copy for a volume."""
        script = f'''
        $volume = "{volume}"
        if (-not $volume.EndsWith("\\")) {{ $volume += "\\" }}
        $class = [WMICLASS]"root\\cimv2:Win32_ShadowCopy"
        $result = $class.Create($volume, "ClientAccessible")
        if ($result.ReturnValue -eq 0) {{
            $shadowId = $result.ShadowID
            $shadow = Get-WmiObject Win32_ShadowCopy | Where-Object {{ $_.ID -eq $shadowId }}
            @{{
                Success = $true
                ShadowID = $shadowId
                DeviceObject = $shadow.DeviceObject
                CreationTime = $shadow.ConvertToDateTime($shadow.InstallDate)
            }}
        }} else {{
            @{{
                Success = $false
                Error = "Failed to create shadow copy. Return code: $($result.ReturnValue)"
            }}
        }}
        '''
        return await self._run_powershell(script)

    async def _delete_shadow_copy(self, shadow_id: str, **kwargs) -> Dict[str, Any]:
        """Delete a specific shadow copy by ID."""
        script = f'''
        $shadow = Get-WmiObject Win32_ShadowCopy | Where-Object {{ $_.ID -eq "{shadow_id}" }}
        if ($shadow) {{
            $shadow.Delete()
            @{{ Success = $true; Message = "Shadow copy deleted successfully" }}
        }} else {{
            @{{ Success = $false; Error = "Shadow copy not found" }}
        }}
        '''
        return await self._run_powershell(script)

    async def _delete_all_shadow_copies(self, volume: str = None, older_than_days: int = None, **kwargs) -> Dict[str, Any]:
        """Delete all shadow copies, optionally filtered by volume or age."""
        conditions = []
        if volume:
            conditions.append(f'$_.VolumeName -like "*{volume}*"')
        if older_than_days:
            conditions.append(f'$_.ConvertToDateTime($_.InstallDate) -lt (Get-Date).AddDays(-{older_than_days})')
        
        where_clause = " -and ".join(conditions) if conditions else "$true"
        
        script = f'''
        $shadows = Get-WmiObject Win32_ShadowCopy | Where-Object {{ {where_clause} }}
        $count = 0
        foreach ($shadow in $shadows) {{
            $shadow.Delete()
            $count++
        }}
        @{{ Success = $true; DeletedCount = $count }}
        '''
        return await self._run_powershell(script)

    async def _get_shadow_copy_details(self, shadow_id: str, **kwargs) -> Dict[str, Any]:
        """Get detailed information about a specific shadow copy."""
        script = f'''
        $shadow = Get-WmiObject Win32_ShadowCopy | Where-Object {{ $_.ID -eq "{shadow_id}" }}
        if ($shadow) {{
            @{{
                ID = $shadow.ID
                DeviceObject = $shadow.DeviceObject
                VolumeName = $shadow.VolumeName
                OriginatingMachine = $shadow.OriginatingMachine
                ServiceMachine = $shadow.ServiceMachine
                ExposedName = $shadow.ExposedName
                State = $shadow.State
                Persistent = $shadow.Persistent
                ClientAccessible = $shadow.ClientAccessible
                NoAutoRelease = $shadow.NoAutoRelease
                NoWriters = $shadow.NoWriters
                Transportable = $shadow.Transportable
                NotSurfaced = $shadow.NotSurfaced
                HardwareAssisted = $shadow.HardwareAssisted
                Differential = $shadow.Differential
                Plex = $shadow.Plex
                Imported = $shadow.Imported
                ExposedRemotely = $shadow.ExposedRemotely
                ExposedLocally = $shadow.ExposedLocally
                CreationTime = $shadow.ConvertToDateTime($shadow.InstallDate)
                ProviderID = $shadow.ProviderID
            }}
        }} else {{
            @{{ Success = $false; Error = "Shadow copy not found" }}
        }}
        '''
        return await self._run_powershell(script)

    async def _resize_shadow_storage(self, volume: str, for_volume: str, max_size: str, **kwargs) -> Dict[str, Any]:
        """Resize shadow storage for a volume."""
        # max_size can be a number (bytes), percentage, or "UNBOUNDED"
        result = await self._run_vssadmin(f"resize shadowstorage /For={for_volume} /On={volume} /MaxSize={max_size}")
        return result

    async def _list_shadow_storage(self, **kwargs) -> Dict[str, Any]:
        """List shadow copy storage associations."""
        result = await self._run_vssadmin("list shadowstorage")
        return result

    async def _get_shadow_copy_by_id(self, shadow_id: str, **kwargs) -> Dict[str, Any]:
        """Get shadow copy by its ID."""
        script = f'''
        Get-WmiObject Win32_ShadowCopy | Where-Object {{ $_.ID -eq "{shadow_id}" }} |
        Select-Object *
        '''
        return await self._run_powershell(script)

    # VSS Writer Operations
    async def _list_writers(self, **kwargs) -> Dict[str, Any]:
        """List all VSS writers and their status."""
        result = await self._run_vssadmin("list writers")
        return result

    async def _get_writer_status(self, writer_name: str = None, **kwargs) -> Dict[str, Any]:
        """Get status of VSS writers."""
        script = '''
        $writers = @()
        $vssOutput = vssadmin list writers 2>&1
        $currentWriter = $null
        
        foreach ($line in $vssOutput) {
            if ($line -match "Writer name: '(.+)'") {
                if ($currentWriter) { $writers += $currentWriter }
                $currentWriter = @{ Name = $Matches[1] }
            }
            elseif ($line -match "Writer Id: ({.+})") {
                $currentWriter.Id = $Matches[1]
            }
            elseif ($line -match "Writer Instance Id: ({.+})") {
                $currentWriter.InstanceId = $Matches[1]
            }
            elseif ($line -match "State: \\[(.+)\\] (.+)") {
                $currentWriter.StateCode = $Matches[1]
                $currentWriter.State = $Matches[2]
            }
            elseif ($line -match "Last error: (.+)") {
                $currentWriter.LastError = $Matches[1]
            }
        }
        if ($currentWriter) { $writers += $currentWriter }
        '''
        
        if writer_name:
            script += f'\n$writers | Where-Object {{ $_.Name -like "*{writer_name}*" }}'
        else:
            script += '\n$writers'
        
        return await self._run_powershell(script)

    async def _check_writer_health(self, **kwargs) -> Dict[str, Any]:
        """Check health status of all VSS writers."""
        script = '''
        $writers = @()
        $vssOutput = vssadmin list writers 2>&1
        $unhealthyWriters = @()
        $currentWriter = $null
        
        foreach ($line in $vssOutput) {
            if ($line -match "Writer name: '(.+)'") {
                if ($currentWriter) {
                    if ($currentWriter.State -ne "Stable") {
                        $unhealthyWriters += $currentWriter
                    }
                    $writers += $currentWriter
                }
                $currentWriter = @{ Name = $Matches[1] }
            }
            elseif ($line -match "State: \\[(.+)\\] (.+)") {
                $currentWriter.StateCode = $Matches[1]
                $currentWriter.State = $Matches[2]
            }
            elseif ($line -match "Last error: (.+)") {
                $currentWriter.LastError = $Matches[1]
            }
        }
        if ($currentWriter) {
            if ($currentWriter.State -ne "Stable") {
                $unhealthyWriters += $currentWriter
            }
            $writers += $currentWriter
        }
        
        @{
            TotalWriters = $writers.Count
            HealthyWriters = ($writers | Where-Object { $_.State -eq "Stable" }).Count
            UnhealthyWriters = $unhealthyWriters
            AllHealthy = $unhealthyWriters.Count -eq 0
        }
        '''
        return await self._run_powershell(script)

    async def _restart_writer(self, writer_name: str, **kwargs) -> Dict[str, Any]:
        """Attempt to restart a VSS writer by restarting its associated service."""
        script = f'''
        # Map common writer names to services
        $writerServiceMap = @{{
            "System Writer" = "VSS"
            "Registry Writer" = "VSS"
            "COM+ REGDB Writer" = "VSS"
            "WMI Writer" = "Winmgmt"
            "Shadow Copy Optimization Writer" = "VSS"
            "Task Scheduler Writer" = "Schedule"
            "VSS Metadata Store Writer" = "VSS"
            "Performance Counters Writer" = "VSS"
            "SqlServerWriter" = "MSSQLSERVER"
            "SQLWRITER" = "SQLWriter"
            "IIS Config Writer" = "W3SVC"
            "IIS Metabase Writer" = "IISADMIN"
            "DHCP Jet Writer" = "DHCPServer"
            "WINS Jet Writer" = "WINS"
            "DFS Replication service writer" = "DFSR"
            "NTDS" = "NTDS"
            "Hyper-V Writer" = "vmms"
        }}
        
        $writerName = "{writer_name}"
        $serviceName = $null
        
        foreach ($key in $writerServiceMap.Keys) {{
            if ($writerName -like "*$key*") {{
                $serviceName = $writerServiceMap[$key]
                break
            }}
        }}
        
        if ($serviceName) {{
            $service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
            if ($service) {{
                Restart-Service -Name $serviceName -Force
                Start-Sleep -Seconds 2
                $newStatus = (Get-Service -Name $serviceName).Status
                @{{ Success = $true; Service = $serviceName; Status = $newStatus.ToString() }}
            }} else {{
                @{{ Success = $false; Error = "Service '$serviceName' not found" }}
            }}
        }} else {{
            @{{ Success = $false; Error = "No known service mapping for writer '$writerName'" }}
        }}
        '''
        return await self._run_powershell(script)

    # VSS Provider Operations
    async def _list_providers(self, **kwargs) -> Dict[str, Any]:
        """List all VSS providers."""
        result = await self._run_vssadmin("list providers")
        return result

    async def _get_provider_details(self, provider_id: str = None, **kwargs) -> Dict[str, Any]:
        """Get details about VSS providers."""
        script = '''
        Get-WmiObject Win32_ShadowProvider |
        Select-Object ID, Name, Type, Version, VersionID, CLSID
        '''
        if provider_id:
            script = f'''
            Get-WmiObject Win32_ShadowProvider | Where-Object {{ $_.ID -eq "{provider_id}" }} |
            Select-Object ID, Name, Type, Version, VersionID, CLSID
            '''
        return await self._run_powershell(script)

    # Mount and Access Operations
    async def _mount_shadow_copy(self, shadow_id: str, mount_point: str, **kwargs) -> Dict[str, Any]:
        """Mount a shadow copy to a directory."""
        script = f'''
        $shadow = Get-WmiObject Win32_ShadowCopy | Where-Object {{ $_.ID -eq "{shadow_id}" }}
        if ($shadow) {{
            $devicePath = $shadow.DeviceObject + "\\"
            $mountPoint = "{mount_point}"
            
            if (-not (Test-Path $mountPoint)) {{
                New-Item -ItemType Directory -Path $mountPoint -Force | Out-Null
            }}
            
            # Create symbolic link
            cmd /c mklink /d "$mountPoint" "$devicePath" 2>&1
            
            if (Test-Path $mountPoint) {{
                @{{ Success = $true; MountPoint = $mountPoint; DeviceObject = $shadow.DeviceObject }}
            }} else {{
                @{{ Success = $false; Error = "Failed to create mount point" }}
            }}
        }} else {{
            @{{ Success = $false; Error = "Shadow copy not found" }}
        }}
        '''
        return await self._run_powershell(script)

    async def _unmount_shadow_copy(self, mount_point: str, **kwargs) -> Dict[str, Any]:
        """Unmount a shadow copy from a directory."""
        script = f'''
        $mountPoint = "{mount_point}"
        if (Test-Path $mountPoint) {{
            $item = Get-Item $mountPoint -Force
            if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {{
                cmd /c rmdir "$mountPoint" 2>&1
                @{{ Success = $true; Message = "Mount point removed" }}
            }} else {{
                @{{ Success = $false; Error = "Path is not a mount point" }}
            }}
        }} else {{
            @{{ Success = $false; Error = "Mount point not found" }}
        }}
        '''
        return await self._run_powershell(script)

    async def _list_mounted_shadow_copies(self, **kwargs) -> Dict[str, Any]:
        """List all currently mounted shadow copies."""
        script = '''
        $mounts = @()
        Get-ChildItem -Path "C:\\" -Force -ErrorAction SilentlyContinue | 
        Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint } |
        ForEach-Object {
            $target = (Get-Item $_.FullName).Target
            if ($target -like "*VolumeShadowCopy*" -or $target -like "*GLOBALROOT*") {
                $mounts += @{
                    MountPoint = $_.FullName
                    Target = $target
                }
            }
        }
        $mounts
        '''
        return await self._run_powershell(script)

    async def _browse_shadow_copy(self, shadow_id: str, path: str = "\\", **kwargs) -> Dict[str, Any]:
        """Browse contents of a shadow copy."""
        script = f'''
        $shadow = Get-WmiObject Win32_ShadowCopy | Where-Object {{ $_.ID -eq "{shadow_id}" }}
        if ($shadow) {{
            $shadowPath = $shadow.DeviceObject + "{path}"
            if (Test-Path $shadowPath) {{
                Get-ChildItem -Path $shadowPath -Force | Select-Object Name, 
                @{{N='Type';E={{if($_.PSIsContainer){{'Directory'}}else{{'File'}}}}}},
                Length, LastWriteTime, Attributes
            }} else {{
                @{{ Success = $false; Error = "Path not found in shadow copy" }}
            }}
        }} else {{
            @{{ Success = $false; Error = "Shadow copy not found" }}
        }}
        '''
        return await self._run_powershell(script)

    async def _restore_file_from_shadow(self, shadow_id: str, source_path: str, destination_path: str, overwrite: bool = False, **kwargs) -> Dict[str, Any]:
        """Restore a file from a shadow copy."""
        overwrite_flag = "-Force" if overwrite else ""
        script = f'''
        $shadow = Get-WmiObject Win32_ShadowCopy | Where-Object {{ $_.ID -eq "{shadow_id}" }}
        if ($shadow) {{
            $sourcePath = $shadow.DeviceObject + "{source_path}"
            $destPath = "{destination_path}"
            
            if (Test-Path $sourcePath) {{
                $destDir = Split-Path $destPath -Parent
                if (-not (Test-Path $destDir)) {{
                    New-Item -ItemType Directory -Path $destDir -Force | Out-Null
                }}
                Copy-Item -Path $sourcePath -Destination $destPath {overwrite_flag}
                @{{ Success = $true; RestoredTo = $destPath }}
            }} else {{
                @{{ Success = $false; Error = "Source file not found in shadow copy" }}
            }}
        }} else {{
            @{{ Success = $false; Error = "Shadow copy not found" }}
        }}
        '''
        return await self._run_powershell(script)

    async def _restore_folder_from_shadow(self, shadow_id: str, source_path: str, destination_path: str, overwrite: bool = False, **kwargs) -> Dict[str, Any]:
        """Restore a folder from a shadow copy."""
        overwrite_flag = "-Force" if overwrite else ""
        script = f'''
        $shadow = Get-WmiObject Win32_ShadowCopy | Where-Object {{ $_.ID -eq "{shadow_id}" }}
        if ($shadow) {{
            $sourcePath = $shadow.DeviceObject + "{source_path}"
            $destPath = "{destination_path}"
            
            if (Test-Path $sourcePath) {{
                Copy-Item -Path $sourcePath -Destination $destPath -Recurse {overwrite_flag}
                @{{ Success = $true; RestoredTo = $destPath }}
            }} else {{
                @{{ Success = $false; Error = "Source folder not found in shadow copy" }}
            }}
        }} else {{
            @{{ Success = $false; Error = "Shadow copy not found" }}
        }}
        '''
        return await self._run_powershell(script)

    async def _compare_with_shadow(self, shadow_id: str, path: str, **kwargs) -> Dict[str, Any]:
        """Compare current file/folder with shadow copy version."""
        script = f'''
        $shadow = Get-WmiObject Win32_ShadowCopy | Where-Object {{ $_.ID -eq "{shadow_id}" }}
        if ($shadow) {{
            $currentPath = "{path}"
            # Extract relative path from absolute path
            $driveLetter = (Split-Path $currentPath -Qualifier).TrimEnd(":")
            $relativePath = $currentPath.Substring(3)
            $shadowPath = $shadow.DeviceObject + "\\" + $relativePath
            
            if ((Test-Path $currentPath) -and (Test-Path $shadowPath)) {{
                $currentItem = Get-Item $currentPath -Force
                $shadowItem = Get-Item $shadowPath -Force
                
                $comparison = @{{
                    CurrentPath = $currentPath
                    ShadowPath = $shadowPath
                    CurrentSize = $currentItem.Length
                    ShadowSize = $shadowItem.Length
                    CurrentModified = $currentItem.LastWriteTime
                    ShadowModified = $shadowItem.LastWriteTime
                    SizeChanged = $currentItem.Length -ne $shadowItem.Length
                    DateChanged = $currentItem.LastWriteTime -ne $shadowItem.LastWriteTime
                }}
                
                if (-not $currentItem.PSIsContainer) {{
                    $currentHash = (Get-FileHash $currentPath -Algorithm SHA256).Hash
                    $shadowHash = (Get-FileHash $shadowPath -Algorithm SHA256).Hash
                    $comparison.ContentChanged = $currentHash -ne $shadowHash
                    $comparison.CurrentHash = $currentHash
                    $comparison.ShadowHash = $shadowHash
                }}
                
                $comparison
            }} else {{
                @{{ Success = $false; Error = "Path not found in current location or shadow copy" }}
            }}
        }} else {{
            @{{ Success = $false; Error = "Shadow copy not found" }}
        }}
        '''
        return await self._run_powershell(script)

    # Volume Operations
    async def _get_volume_info(self, volume: str, **kwargs) -> Dict[str, Any]:
        """Get detailed information about a volume."""
        script = f'''
        $vol = Get-Volume -DriveLetter "{volume.rstrip(':')}" -ErrorAction SilentlyContinue
        if ($vol) {{
            @{{
                DriveLetter = $vol.DriveLetter
                FileSystemLabel = $vol.FileSystemLabel
                FileSystem = $vol.FileSystem
                DriveType = $vol.DriveType.ToString()
                HealthStatus = $vol.HealthStatus.ToString()
                OperationalStatus = $vol.OperationalStatus.ToString()
                SizeGB = [math]::Round($vol.Size/1GB, 2)
                SizeRemainingGB = [math]::Round($vol.SizeRemaining/1GB, 2)
                UsedGB = [math]::Round(($vol.Size - $vol.SizeRemaining)/1GB, 2)
                PercentUsed = [math]::Round((($vol.Size - $vol.SizeRemaining)/$vol.Size)*100, 2)
            }}
        }} else {{
            @{{ Success = $false; Error = "Volume not found" }}
        }}
        '''
        return await self._run_powershell(script)

    async def _list_volumes(self, **kwargs) -> Dict[str, Any]:
        """List all volumes on the system."""
        script = '''
        Get-Volume | Where-Object { $_.DriveLetter } |
        Select-Object DriveLetter, FileSystemLabel, FileSystem, DriveType,
        @{N='SizeGB';E={[math]::Round($_.Size/1GB,2)}},
        @{N='FreeGB';E={[math]::Round($_.SizeRemaining/1GB,2)}},
        HealthStatus, OperationalStatus
        '''
        return await self._run_powershell(script)

    async def _enable_shadow_copies(self, volume: str, max_size: str = "10%", **kwargs) -> Dict[str, Any]:
        """Enable shadow copies for a volume."""
        script = f'''
        $volume = "{volume}"
        if (-not $volume.EndsWith(":")) {{ $volume += ":" }}
        $volume += "\\"
        
        # Enable shadow copies using vssadmin
        $result = vssadmin add shadowstorage /For=$volume /On=$volume /MaxSize={max_size} 2>&1
        
        if ($LASTEXITCODE -eq 0) {{
            @{{ Success = $true; Message = "Shadow copies enabled for $volume" }}
        }} else {{
            @{{ Success = $false; Error = $result -join " " }}
        }}
        '''
        return await self._run_powershell(script)

    async def _disable_shadow_copies(self, volume: str, delete_existing: bool = False, **kwargs) -> Dict[str, Any]:
        """Disable shadow copies for a volume."""
        script = f'''
        $volume = "{volume}"
        if (-not $volume.EndsWith(":")) {{ $volume += ":" }}
        $volume += "\\"
        
        # Delete storage association
        $result = vssadmin delete shadowstorage /For=$volume /On=$volume /Quiet 2>&1
        
        $deleteExisting = ${str(delete_existing).lower()}
        if ($deleteExisting) {{
            # Delete all shadow copies for this volume
            Get-WmiObject Win32_ShadowCopy | 
            Where-Object {{ $_.VolumeName -like "*$($volume.TrimEnd('\\'))*" }} |
            ForEach-Object {{ $_.Delete() }}
        }}
        
        @{{ Success = $true; Message = "Shadow copies disabled for $volume" }}
        '''
        return await self._run_powershell(script)

    async def _get_volume_shadow_status(self, volume: str, **kwargs) -> Dict[str, Any]:
        """Get shadow copy status for a volume."""
        script = f'''
        $volume = "{volume}"
        if (-not $volume.EndsWith(":")) {{ $volume += ":" }}
        
        $shadows = Get-WmiObject Win32_ShadowCopy | 
        Where-Object {{ $_.VolumeName -like "*$volume*" }}
        
        $storageInfo = vssadmin list shadowstorage /For=$volume\\ 2>&1
        
        @{{
            Volume = $volume
            ShadowCopyCount = $shadows.Count
            OldestShadow = if ($shadows) {{ ($shadows | Sort-Object InstallDate | Select-Object -First 1).ConvertToDateTime(($shadows | Sort-Object InstallDate | Select-Object -First 1).InstallDate) }} else {{ $null }}
            NewestShadow = if ($shadows) {{ ($shadows | Sort-Object InstallDate -Descending | Select-Object -First 1).ConvertToDateTime(($shadows | Sort-Object InstallDate -Descending | Select-Object -First 1).InstallDate) }} else {{ $null }}
            StorageInfo = $storageInfo -join "`n"
        }}
        '''
        return await self._run_powershell(script)

    # Storage Management
    async def _get_storage_usage(self, volume: str = None, **kwargs) -> Dict[str, Any]:
        """Get shadow copy storage usage."""
        if volume:
            result = await self._run_vssadmin(f"list shadowstorage /For={volume}")
        else:
            result = await self._run_vssadmin("list shadowstorage")
        return result

    async def _set_storage_limit(self, volume: str, max_size: str, **kwargs) -> Dict[str, Any]:
        """Set storage limit for shadow copies."""
        # max_size can be bytes, KB, MB, GB, TB, %, or UNBOUNDED
        result = await self._run_vssadmin(f"resize shadowstorage /For={volume} /On={volume} /MaxSize={max_size}")
        return result

    async def _get_storage_associations(self, **kwargs) -> Dict[str, Any]:
        """Get all shadow storage associations."""
        script = '''
        Get-WmiObject Win32_ShadowStorage |
        Select-Object @{N='ForVolume';E={$_.Volume.DeviceID}},
        @{N='OnVolume';E={$_.DiffVolume.DeviceID}},
        @{N='UsedSpaceMB';E={[math]::Round($_.UsedSpace/1MB,2)}},
        @{N='AllocatedSpaceMB';E={[math]::Round($_.AllocatedSpace/1MB,2)}},
        @{N='MaxSpaceMB';E={[math]::Round($_.MaxSpace/1MB,2)}}
        '''
        return await self._run_powershell(script)

    async def _add_storage_association(self, for_volume: str, on_volume: str, max_size: str = "10%", **kwargs) -> Dict[str, Any]:
        """Add a shadow storage association."""
        result = await self._run_vssadmin(f"add shadowstorage /For={for_volume} /On={on_volume} /MaxSize={max_size}")
        return result

    async def _delete_storage_association(self, for_volume: str, on_volume: str, **kwargs) -> Dict[str, Any]:
        """Delete a shadow storage association."""
        result = await self._run_vssadmin(f"delete shadowstorage /For={for_volume} /On={on_volume} /Quiet")
        return result

    # Backup Operations (wbadmin)
    async def _start_backup(self, target: str, include: List[str] = None, all_critical: bool = False, 
                           system_state: bool = False, quiet: bool = True, **kwargs) -> Dict[str, Any]:
        """Start a Windows backup."""
        cmd = f"start backup -backupTarget:{target}"
        
        if include:
            cmd += f" -include:{','.join(include)}"
        if all_critical:
            cmd += " -allCritical"
        if system_state:
            cmd += " -systemState"
        if quiet:
            cmd += " -quiet"
        
        return await self._run_wbadmin(cmd)

    async def _start_system_state_backup(self, target: str, quiet: bool = True, **kwargs) -> Dict[str, Any]:
        """Start a system state backup."""
        cmd = f"start systemstatebackup -backupTarget:{target}"
        if quiet:
            cmd += " -quiet"
        return await self._run_wbadmin(cmd)

    async def _list_backups(self, **kwargs) -> Dict[str, Any]:
        """List all available backups."""
        return await self._run_wbadmin("get versions")

    async def _get_backup_details(self, version: str = None, **kwargs) -> Dict[str, Any]:
        """Get details about a specific backup."""
        if version:
            return await self._run_wbadmin(f"get items -version:{version}")
        return await self._run_wbadmin("get items")

    async def _delete_backup(self, version: str, keep_versions: int = None, delete_oldest: bool = False, quiet: bool = True, **kwargs) -> Dict[str, Any]:
        """Delete a backup."""
        cmd = "delete backup"
        if version:
            cmd += f" -version:{version}"
        if keep_versions:
            cmd += f" -keepVersions:{keep_versions}"
        if delete_oldest:
            cmd += " -deleteOldest"
        if quiet:
            cmd += " -quiet"
        return await self._run_wbadmin(cmd)

    async def _start_recovery(self, version: str, items: List[str], recovery_target: str = None, 
                             recursive: bool = True, quiet: bool = True, **kwargs) -> Dict[str, Any]:
        """Start a recovery operation."""
        cmd = f"start recovery -version:{version} -items:{','.join(items)}"
        if recovery_target:
            cmd += f" -recoveryTarget:{recovery_target}"
        if recursive:
            cmd += " -recursive"
        if quiet:
            cmd += " -quiet"
        return await self._run_wbadmin(cmd)

    async def _start_system_state_recovery(self, version: str, quiet: bool = True, **kwargs) -> Dict[str, Any]:
        """Start a system state recovery."""
        cmd = f"start systemstaterecovery -version:{version}"
        if quiet:
            cmd += " -quiet"
        return await self._run_wbadmin(cmd)

    async def _get_recovery_items(self, version: str, **kwargs) -> Dict[str, Any]:
        """Get items available for recovery from a backup."""
        return await self._run_wbadmin(f"get items -version:{version}")

    # Scheduling
    async def _create_shadow_schedule(self, volume: str, time: str, frequency: str = "Daily", **kwargs) -> Dict[str, Any]:
        """Create a scheduled task for shadow copies."""
        script = f'''
        $taskName = "VSS_ShadowCopy_{volume.rstrip(':')}"
        $volume = "{volume}"
        if (-not $volume.EndsWith(":")) {{ $volume += ":" }}
        
        $action = New-ScheduledTaskAction -Execute "wmic.exe" -Argument "shadowcopy call create Volume='$volume\\'"
        
        $trigger = switch ("{frequency}") {{
            "Daily" {{ New-ScheduledTaskTrigger -Daily -At "{time}" }}
            "Weekly" {{ New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At "{time}" }}
            "Hourly" {{ New-ScheduledTaskTrigger -Once -At "{time}" -RepetitionInterval (New-TimeSpan -Hours 1) }}
            default {{ New-ScheduledTaskTrigger -Daily -At "{time}" }}
        }}
        
        $principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
        $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
        
        Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force
        
        @{{ Success = $true; TaskName = $taskName }}
        '''
        return await self._run_powershell(script)

    async def _delete_shadow_schedule(self, volume: str, **kwargs) -> Dict[str, Any]:
        """Delete a shadow copy scheduled task."""
        script = f'''
        $taskName = "VSS_ShadowCopy_{volume.rstrip(':')}"
        $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
        if ($task) {{
            Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
            @{{ Success = $true; Message = "Schedule deleted" }}
        }} else {{
            @{{ Success = $false; Error = "Schedule not found" }}
        }}
        '''
        return await self._run_powershell(script)

    async def _list_shadow_schedules(self, **kwargs) -> Dict[str, Any]:
        """List all shadow copy schedules."""
        script = '''
        Get-ScheduledTask | Where-Object { $_.TaskName -like "VSS_ShadowCopy*" } |
        Select-Object TaskName, State, 
        @{N='NextRunTime';E={(Get-ScheduledTaskInfo -TaskName $_.TaskName).NextRunTime}},
        @{N='LastRunTime';E={(Get-ScheduledTaskInfo -TaskName $_.TaskName).LastRunTime}},
        @{N='LastResult';E={(Get-ScheduledTaskInfo -TaskName $_.TaskName).LastTaskResult}}
        '''
        return await self._run_powershell(script)

    async def _modify_shadow_schedule(self, volume: str, time: str = None, frequency: str = None, enabled: bool = None, **kwargs) -> Dict[str, Any]:
        """Modify an existing shadow copy schedule."""
        script = f'''
        $taskName = "VSS_ShadowCopy_{volume.rstrip(':')}"
        $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
        
        if ($task) {{
            $changes = @()
        '''
        
        if enabled is not None:
            if enabled:
                script += '''
            Enable-ScheduledTask -TaskName $taskName
            $changes += "Enabled"
        '''
            else:
                script += '''
            Disable-ScheduledTask -TaskName $taskName
            $changes += "Disabled"
        '''
        
        if time:
            script += f'''
            $trigger = New-ScheduledTaskTrigger -Daily -At "{time}"
            Set-ScheduledTask -TaskName $taskName -Trigger $trigger
            $changes += "Time updated to {time}"
        '''
        
        script += '''
            @{ Success = $true; Changes = $changes }
        } else {
            @{ Success = $false; Error = "Schedule not found" }
        }
        '''
        return await self._run_powershell(script)

    # Diagnostics
    async def _run_vss_diagnostics(self, **kwargs) -> Dict[str, Any]:
        """Run comprehensive VSS diagnostics."""
        script = '''
        $diagnostics = @{
            VSSService = (Get-Service VSS).Status.ToString()
            SPPService = (Get-Service "Software Protection" -ErrorAction SilentlyContinue).Status.ToString()
            WriterCount = 0
            UnhealthyWriters = @()
            ProviderCount = 0
            ShadowCopyCount = 0
            Errors = @()
        }
        
        # Check writers
        try {
            $writers = vssadmin list writers 2>&1
            $writerCount = ($writers | Select-String "Writer name:").Count
            $diagnostics.WriterCount = $writerCount
            
            # Find unhealthy writers
            $currentWriter = ""
            foreach ($line in $writers) {
                if ($line -match "Writer name: '(.+)'") {
                    $currentWriter = $Matches[1]
                }
                if ($line -match "State: \\[(.+)\\] (.+)" -and $Matches[2] -ne "Stable") {
                    $diagnostics.UnhealthyWriters += @{
                        Name = $currentWriter
                        State = $Matches[2]
                    }
                }
            }
        } catch {
            $diagnostics.Errors += "Failed to get writer status: $_"
        }
        
        # Check providers
        try {
            $providers = vssadmin list providers 2>&1
            $providerCount = ($providers | Select-String "Provider name:").Count
            $diagnostics.ProviderCount = $providerCount
        } catch {
            $diagnostics.Errors += "Failed to get provider status: $_"
        }
        
        # Check shadow copies
        try {
            $shadows = Get-WmiObject Win32_ShadowCopy
            $diagnostics.ShadowCopyCount = $shadows.Count
        } catch {
            $diagnostics.Errors += "Failed to get shadow copy count: $_"
        }
        
        # Check disk space
        try {
            $systemDrive = $env:SystemDrive
            $volume = Get-Volume -DriveLetter $systemDrive.TrimEnd(":")
            $diagnostics.SystemDriveFreeGB = [math]::Round($volume.SizeRemaining/1GB, 2)
            $diagnostics.SystemDriveFreePercent = [math]::Round(($volume.SizeRemaining/$volume.Size)*100, 2)
        } catch {
            $diagnostics.Errors += "Failed to get disk space: $_"
        }
        
        $diagnostics.OverallHealth = if ($diagnostics.UnhealthyWriters.Count -eq 0 -and $diagnostics.VSSService -eq "Running") { "Healthy" } else { "Issues Detected" }
        
        $diagnostics
        '''
        return await self._run_powershell(script)

    async def _get_vss_service_status(self, **kwargs) -> Dict[str, Any]:
        """Get status of VSS-related services."""
        script = '''
        $services = @("VSS", "SWPRV", "SPP", "wbengine")
        $results = @()
        
        foreach ($svc in $services) {
            $service = Get-Service -Name $svc -ErrorAction SilentlyContinue
            if ($service) {
                $results += @{
                    Name = $service.Name
                    DisplayName = $service.DisplayName
                    Status = $service.Status.ToString()
                    StartType = $service.StartType.ToString()
                }
            }
        }
        
        $results
        '''
        return await self._run_powershell(script)

    async def _repair_vss(self, **kwargs) -> Dict[str, Any]:
        """Attempt to repair VSS by restarting services and re-registering components."""
        script = '''
        $results = @{
            Steps = @()
            Success = $true
        }
        
        # Stop VSS service
        try {
            Stop-Service VSS -Force -ErrorAction Stop
            $results.Steps += "VSS service stopped"
        } catch {
            $results.Steps += "Failed to stop VSS: $_"
        }
        
        # Re-register VSS DLLs
        $dlls = @("ole32.dll", "oleaut32.dll", "vss_ps.dll", "swprv.dll", "vsscm.dll", 
                  "vssui.dll", "msxml.dll", "msxml3.dll", "msxml4.dll", "vbscript.dll")
        
        foreach ($dll in $dlls) {
            try {
                regsvr32.exe /s $dll 2>&1 | Out-Null
                $results.Steps += "Registered $dll"
            } catch {
                $results.Steps += "Failed to register $dll"
            }
        }
        
        # Start VSS service
        try {
            Start-Service VSS -ErrorAction Stop
            $results.Steps += "VSS service started"
        } catch {
            $results.Steps += "Failed to start VSS: $_"
            $results.Success = $false
        }
        
        # Verify
        Start-Sleep -Seconds 2
        $results.FinalStatus = (Get-Service VSS).Status.ToString()
        
        $results
        '''
        return await self._run_powershell(script)

    async def _get_vss_events(self, hours: int = 24, **kwargs) -> Dict[str, Any]:
        """Get VSS-related events from the event log."""
        script = f'''
        $startTime = (Get-Date).AddHours(-{hours})
        
        Get-WinEvent -FilterHashtable @{{
            LogName = 'Application'
            ProviderName = 'VSS'
            StartTime = $startTime
        }} -MaxEvents 50 -ErrorAction SilentlyContinue |
        Select-Object TimeCreated, Id, LevelDisplayName, Message |
        ForEach-Object {{
            @{{
                Time = $_.TimeCreated.ToString("yyyy-MM-dd HH:mm:ss")
                EventId = $_.Id
                Level = $_.LevelDisplayName
                Message = $_.Message.Substring(0, [Math]::Min(500, $_.Message.Length))
            }}
        }}
        '''
        return await self._run_powershell(script)

    async def _check_vss_prerequisites(self, **kwargs) -> Dict[str, Any]:
        """Check all prerequisites for VSS operations."""
        script = '''
        $checks = @{
            Passed = @()
            Failed = @()
            Warnings = @()
        }
        
        # Check if running as admin
        $isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
        if ($isAdmin) {
            $checks.Passed += "Running as Administrator"
        } else {
            $checks.Failed += "Not running as Administrator - VSS operations require elevation"
        }
        
        # Check VSS service
        $vss = Get-Service VSS
        if ($vss.Status -eq "Running") {
            $checks.Passed += "VSS service is running"
        } elseif ($vss.StartType -ne "Disabled") {
            $checks.Warnings += "VSS service is not running but can be started"
        } else {
            $checks.Failed += "VSS service is disabled"
        }
        
        # Check SWPRV service
        $swprv = Get-Service SWPRV -ErrorAction SilentlyContinue
        if ($swprv) {
            if ($swprv.StartType -ne "Disabled") {
                $checks.Passed += "Software Shadow Copy Provider service available"
            } else {
                $checks.Failed += "Software Shadow Copy Provider service is disabled"
            }
        }
        
        # Check disk space on system drive
        $systemDrive = Get-Volume -DriveLetter $env:SystemDrive.TrimEnd(":")
        $freePercent = ($systemDrive.SizeRemaining / $systemDrive.Size) * 100
        if ($freePercent -gt 15) {
            $checks.Passed += "Sufficient disk space on system drive ($([math]::Round($freePercent,1))% free)"
        } elseif ($freePercent -gt 5) {
            $checks.Warnings += "Low disk space on system drive ($([math]::Round($freePercent,1))% free)"
        } else {
            $checks.Failed += "Critical: Very low disk space ($([math]::Round($freePercent,1))% free)"
        }
        
        # Check for VSS writers
        $writerOutput = vssadmin list writers 2>&1
        $writerCount = ($writerOutput | Select-String "Writer name:").Count
        if ($writerCount -gt 0) {
            $checks.Passed += "$writerCount VSS writers registered"
        } else {
            $checks.Failed += "No VSS writers found"
        }
        
        $checks.AllPassed = $checks.Failed.Count -eq 0
        $checks
        '''
        return await self._run_powershell(script)
