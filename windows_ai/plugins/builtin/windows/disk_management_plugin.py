"""
Windows Disk Management Plugin - PRODUCTION

Provides comprehensive disk and storage management including:
- Physical disk operations
- Partition management
- Volume management
- Disk initialization
- Storage spaces
"""
import asyncio
import json
from typing import Dict, Any, List, Optional
from windows_ai.plugins.base import Plugin, PluginMetadata, PluginType
import logging

logger = logging.getLogger(__name__)


class WindowsDiskManagementPlugin(Plugin):
    """Windows disk management plugin with comprehensive storage support."""
    
    def __init__(self):
        metadata = PluginMetadata(
            id="windows_disk_management",
            name="Windows Disk Management",
            description="Disk, partition, and volume management for Windows",
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["windows", "disk", "storage", "partition", "volume", "ssd", "hdd"]
        )
        super().__init__(metadata)

    async def initialize(self) -> bool:
        """Initialize plugin."""
        self._initialized = True
        return True

    async def _run_powershell(self, command: str, timeout: int = 60) -> Dict[str, Any]:
        """Execute a PowerShell command."""
        try:
            process = await asyncio.create_subprocess_exec(
                "powershell", "-NoProfile", "-Command", command,
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

    async def execute(self, action: str = "status", parameters: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """Execute a disk management operation."""
        if parameters is None:
            parameters = kwargs

        actions = {
            # Disk operations
            "status": self._get_status,
            "list_disks": self._list_disks,
            "get_disk": self._get_disk,
            "initialize_disk": self._initialize_disk,
            "clear_disk": self._clear_disk,
            "set_disk_online": self._set_disk_online,
            "set_disk_offline": self._set_disk_offline,
            "set_disk_readonly": self._set_disk_readonly,
            "set_disk_readwrite": self._set_disk_readwrite,
            # Physical disk info
            "get_physical_disks": self._get_physical_disks,
            "get_disk_health": self._get_disk_health,
            "get_smart_data": self._get_smart_data,
            # Partition operations
            "list_partitions": self._list_partitions,
            "get_partition": self._get_partition,
            "create_partition": self._create_partition,
            "remove_partition": self._remove_partition,
            "resize_partition": self._resize_partition,
            "set_partition_active": self._set_partition_active,
            # Volume operations
            "list_volumes": self._list_volumes,
            "get_volume": self._get_volume,
            "format_volume": self._format_volume,
            "set_volume_label": self._set_volume_label,
            "optimize_volume": self._optimize_volume,
            "repair_volume": self._repair_volume,
            # Drive letters
            "get_drive_letters": self._get_drive_letters,
            "set_drive_letter": self._set_drive_letter,
            "remove_drive_letter": self._remove_drive_letter,
            # Storage info
            "get_storage_pools": self._get_storage_pools,
            "get_storage_spaces": self._get_storage_spaces,
            "get_storage_jobs": self._get_storage_jobs,
            # TRIM/Optimize
            "enable_trim": self._enable_trim,
            "disable_trim": self._disable_trim,
            "run_trim": self._run_trim,
            # File system
            "check_filesystem": self._check_filesystem,
            "get_filesystem_stats": self._get_filesystem_stats,
            # VHD operations
            "mount_vhd": self._mount_vhd,
            "dismount_vhd": self._dismount_vhd,
            "create_vhd": self._create_vhd,
            "get_vhd_info": self._get_vhd_info,
        }

        if action not in actions:
            return {"success": False, "error": f"Unknown action: {action}. Available: {list(actions.keys())}"}

        try:
            return await actions[action](parameters)
        except Exception as e:
            logger.error(f"Disk operation failed: {e}")
            return {"success": False, "error": str(e)}

    # Disk operations
    async def _get_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get disk status overview."""
        cmd = "Get-Disk | Select-Object Number,FriendlyName,Size,PartitionStyle,OperationalStatus,HealthStatus | ConvertTo-Json"
        result = await self._run_powershell(cmd)
        if result["success"]:
            try:
                disks = json.loads(result["output"]) if result["output"] else []
                if isinstance(disks, dict):
                    disks = [disks]
                for disk in disks:
                    if "Size" in disk and disk["Size"]:
                        disk["SizeGB"] = round(disk["Size"] / (1024**3), 2)
                return {"success": True, "disks": disks, "count": len(disks)}
            except json.JSONDecodeError:
                return result
        return result

    async def _list_disks(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List all disks with details."""
        cmd = """Get-Disk | Select-Object Number,FriendlyName,SerialNumber,Size,AllocatedSize,PartitionStyle,
            OperationalStatus,HealthStatus,BusType,MediaType,Model,IsBoot,IsSystem,IsOffline,IsReadOnly | ConvertTo-Json"""
        result = await self._run_powershell(cmd)
        if result["success"]:
            try:
                disks = json.loads(result["output"]) if result["output"] else []
                if isinstance(disks, dict):
                    disks = [disks]
                for disk in disks:
                    if "Size" in disk and disk["Size"]:
                        disk["SizeGB"] = round(disk["Size"] / (1024**3), 2)
                    if "AllocatedSize" in disk and disk["AllocatedSize"]:
                        disk["AllocatedSizeGB"] = round(disk["AllocatedSize"] / (1024**3), 2)
                return {"success": True, "disks": disks, "count": len(disks)}
            except json.JSONDecodeError:
                return result
        return result

    async def _get_disk(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get details for specific disk."""
        number = params.get("number") or params.get("disk")
        if number is None:
            return {"success": False, "error": "disk number required"}
        
        cmd = f"Get-Disk -Number {number} | Select-Object * | ConvertTo-Json -Depth 2"
        result = await self._run_powershell(cmd)
        if result["success"]:
            try:
                disk = json.loads(result["output"]) if result["output"] else None
                return {"success": True, "disk": disk}
            except json.JSONDecodeError:
                return result
        return result

    async def _initialize_disk(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize a disk."""
        number = params.get("number") or params.get("disk")
        partition_style = params.get("partition_style", "GPT")
        
        if number is None:
            return {"success": False, "error": "disk number required"}
        
        if partition_style not in ["GPT", "MBR"]:
            return {"success": False, "error": "partition_style must be GPT or MBR"}
        
        cmd = f"Initialize-Disk -Number {number} -PartitionStyle {partition_style} -PassThru | ConvertTo-Json"
        result = await self._run_powershell(cmd)
        if result["success"]:
            return {"success": True, "message": f"Disk {number} initialized as {partition_style}"}
        return result

    async def _clear_disk(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Clear all data from disk (DANGEROUS)."""
        number = params.get("number") or params.get("disk")
        confirm = params.get("confirm", False)
        
        if number is None:
            return {"success": False, "error": "disk number required"}
        if not confirm:
            return {"success": False, "error": "set confirm=True to clear disk (DESTRUCTIVE)"}
        
        cmd = f"Clear-Disk -Number {number} -RemoveData -RemoveOEM -Confirm:$false"
        result = await self._run_powershell(cmd)
        if result["success"]:
            return {"success": True, "message": f"Disk {number} cleared"}
        return result

    async def _set_disk_online(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set disk online."""
        number = params.get("number") or params.get("disk")
        if number is None:
            return {"success": False, "error": "disk number required"}
        
        cmd = f"Set-Disk -Number {number} -IsOffline $false"
        result = await self._run_powershell(cmd)
        if result["success"]:
            return {"success": True, "message": f"Disk {number} set online"}
        return result

    async def _set_disk_offline(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set disk offline."""
        number = params.get("number") or params.get("disk")
        if number is None:
            return {"success": False, "error": "disk number required"}
        
        cmd = f"Set-Disk -Number {number} -IsOffline $true"
        result = await self._run_powershell(cmd)
        if result["success"]:
            return {"success": True, "message": f"Disk {number} set offline"}
        return result

    async def _set_disk_readonly(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set disk read-only."""
        number = params.get("number") or params.get("disk")
        if number is None:
            return {"success": False, "error": "disk number required"}
        
        cmd = f"Set-Disk -Number {number} -IsReadOnly $true"
        result = await self._run_powershell(cmd)
        if result["success"]:
            return {"success": True, "message": f"Disk {number} set read-only"}
        return result

    async def _set_disk_readwrite(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set disk read-write."""
        number = params.get("number") or params.get("disk")
        if number is None:
            return {"success": False, "error": "disk number required"}
        
        cmd = f"Set-Disk -Number {number} -IsReadOnly $false"
        result = await self._run_powershell(cmd)
        if result["success"]:
            return {"success": True, "message": f"Disk {number} set read-write"}
        return result

    # Physical disk info
    async def _get_physical_disks(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get physical disk information."""
        cmd = """Get-PhysicalDisk | Select-Object DeviceId,FriendlyName,SerialNumber,MediaType,BusType,
            Size,AllocatedSize,HealthStatus,OperationalStatus,SpindleSpeed,FirmwareVersion | ConvertTo-Json"""
        result = await self._run_powershell(cmd)
        if result["success"]:
            try:
                disks = json.loads(result["output"]) if result["output"] else []
                if isinstance(disks, dict):
                    disks = [disks]
                for disk in disks:
                    if "Size" in disk and disk["Size"]:
                        disk["SizeGB"] = round(disk["Size"] / (1024**3), 2)
                return {"success": True, "physical_disks": disks, "count": len(disks)}
            except json.JSONDecodeError:
                return result
        return result

    async def _get_disk_health(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get disk health status."""
        cmd = """Get-PhysicalDisk | Select-Object FriendlyName,HealthStatus,OperationalStatus,
            @{N='Temperature';E={$_.StorageReliabilityCounter.Temperature}},
            @{N='ReadErrors';E={$_.StorageReliabilityCounter.ReadErrorsTotal}},
            @{N='WriteErrors';E={$_.StorageReliabilityCounter.WriteErrorsTotal}} | ConvertTo-Json"""
        result = await self._run_powershell(cmd)
        if result["success"]:
            try:
                health = json.loads(result["output"]) if result["output"] else []
                if isinstance(health, dict):
                    health = [health]
                return {"success": True, "health": health}
            except json.JSONDecodeError:
                return result
        return result

    async def _get_smart_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get SMART data for disks."""
        cmd = """Get-PhysicalDisk | Get-StorageReliabilityCounter | Select-Object DeviceId,
            Temperature,ReadErrorsTotal,WriteErrorsTotal,ReadLatencyMax,WriteLatencyMax,
            PowerOnHours,StartStopCycleCount | ConvertTo-Json"""
        result = await self._run_powershell(cmd)
        if result["success"]:
            try:
                smart = json.loads(result["output"]) if result["output"] else []
                if isinstance(smart, dict):
                    smart = [smart]
                return {"success": True, "smart_data": smart}
            except json.JSONDecodeError:
                return result
        return result

    # Partition operations
    async def _list_partitions(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List all partitions."""
        disk_number = params.get("disk")
        cmd = "Get-Partition"
        if disk_number is not None:
            cmd += f" -DiskNumber {disk_number}"
        cmd += " | Select-Object DiskNumber,PartitionNumber,DriveLetter,Size,Type,IsActive,IsBoot,IsSystem,GptType | ConvertTo-Json"
        result = await self._run_powershell(cmd)
        if result["success"]:
            try:
                partitions = json.loads(result["output"]) if result["output"] else []
                if isinstance(partitions, dict):
                    partitions = [partitions]
                for p in partitions:
                    if "Size" in p and p["Size"]:
                        p["SizeGB"] = round(p["Size"] / (1024**3), 2)
                return {"success": True, "partitions": partitions, "count": len(partitions)}
            except json.JSONDecodeError:
                return result
        return result

    async def _get_partition(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get specific partition details."""
        disk = params.get("disk")
        partition = params.get("partition")
        drive = params.get("drive_letter")
        
        if drive:
            cmd = f"Get-Partition -DriveLetter '{drive}' | Select-Object * | ConvertTo-Json -Depth 2"
        elif disk is not None and partition is not None:
            cmd = f"Get-Partition -DiskNumber {disk} -PartitionNumber {partition} | Select-Object * | ConvertTo-Json -Depth 2"
        else:
            return {"success": False, "error": "drive_letter or disk+partition number required"}
        
        result = await self._run_powershell(cmd)
        if result["success"]:
            try:
                part = json.loads(result["output"]) if result["output"] else None
                return {"success": True, "partition": part}
            except json.JSONDecodeError:
                return result
        return result

    async def _create_partition(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new partition."""
        disk = params.get("disk")
        size = params.get("size")  # in bytes, or "max" for max
        drive_letter = params.get("drive_letter")
        gpt_type = params.get("gpt_type")  # e.g., "{ebd0a0a2-b9e5-4433-87c0-68b6b72699c7}" for basic data
        
        if disk is None:
            return {"success": False, "error": "disk number required"}
        
        cmd = f"New-Partition -DiskNumber {disk}"
        if size == "max" or size is None:
            cmd += " -UseMaximumSize"
        else:
            cmd += f" -Size {size}"
        
        if drive_letter:
            cmd += f" -DriveLetter '{drive_letter}'"
        else:
            cmd += " -AssignDriveLetter"
        
        if gpt_type:
            cmd += f" -GptType '{gpt_type}'"
        
        cmd += " | ConvertTo-Json"
        result = await self._run_powershell(cmd)
        if result["success"]:
            return {"success": True, "message": "Partition created", "output": result["output"]}
        return result

    async def _remove_partition(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove a partition (DANGEROUS)."""
        disk = params.get("disk")
        partition = params.get("partition")
        drive = params.get("drive_letter")
        confirm = params.get("confirm", False)
        
        if not confirm:
            return {"success": False, "error": "set confirm=True to remove partition (DESTRUCTIVE)"}
        
        if drive:
            cmd = f"Remove-Partition -DriveLetter '{drive}' -Confirm:$false"
        elif disk is not None and partition is not None:
            cmd = f"Remove-Partition -DiskNumber {disk} -PartitionNumber {partition} -Confirm:$false"
        else:
            return {"success": False, "error": "drive_letter or disk+partition number required"}
        
        result = await self._run_powershell(cmd)
        if result["success"]:
            return {"success": True, "message": "Partition removed"}
        return result

    async def _resize_partition(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Resize a partition."""
        disk = params.get("disk")
        partition = params.get("partition")
        drive = params.get("drive_letter")
        size = params.get("size")
        
        if size is None:
            return {"success": False, "error": "size required (in bytes)"}
        
        if drive:
            cmd = f"Resize-Partition -DriveLetter '{drive}' -Size {size}"
        elif disk is not None and partition is not None:
            cmd = f"Resize-Partition -DiskNumber {disk} -PartitionNumber {partition} -Size {size}"
        else:
            return {"success": False, "error": "drive_letter or disk+partition number required"}
        
        result = await self._run_powershell(cmd)
        if result["success"]:
            return {"success": True, "message": "Partition resized"}
        return result

    async def _set_partition_active(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set partition as active."""
        disk = params.get("disk")
        partition = params.get("partition")
        
        if disk is None or partition is None:
            return {"success": False, "error": "disk and partition number required"}
        
        cmd = f"Set-Partition -DiskNumber {disk} -PartitionNumber {partition} -IsActive $true"
        result = await self._run_powershell(cmd)
        if result["success"]:
            return {"success": True, "message": f"Partition {partition} on disk {disk} set active"}
        return result

    # Volume operations
    async def _list_volumes(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List all volumes."""
        cmd = """Get-Volume | Select-Object DriveLetter,FileSystemLabel,FileSystem,DriveType,
            HealthStatus,OperationalStatus,Size,SizeRemaining | ConvertTo-Json"""
        result = await self._run_powershell(cmd)
        if result["success"]:
            try:
                volumes = json.loads(result["output"]) if result["output"] else []
                if isinstance(volumes, dict):
                    volumes = [volumes]
                for v in volumes:
                    if "Size" in v and v["Size"]:
                        v["SizeGB"] = round(v["Size"] / (1024**3), 2)
                    if "SizeRemaining" in v and v["SizeRemaining"]:
                        v["SizeRemainingGB"] = round(v["SizeRemaining"] / (1024**3), 2)
                return {"success": True, "volumes": volumes, "count": len(volumes)}
            except json.JSONDecodeError:
                return result
        return result

    async def _get_volume(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get volume details."""
        drive = params.get("drive_letter") or params.get("drive")
        if not drive:
            return {"success": False, "error": "drive_letter required"}
        
        drive = drive.rstrip(':')
        cmd = f"Get-Volume -DriveLetter '{drive}' | Select-Object * | ConvertTo-Json -Depth 2"
        result = await self._run_powershell(cmd)
        if result["success"]:
            try:
                volume = json.loads(result["output"]) if result["output"] else None
                return {"success": True, "volume": volume}
            except json.JSONDecodeError:
                return result
        return result

    async def _format_volume(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Format a volume (DANGEROUS)."""
        drive = params.get("drive_letter") or params.get("drive")
        filesystem = params.get("filesystem", "NTFS")
        label = params.get("label", "")
        confirm = params.get("confirm", False)
        quick = params.get("quick", True)
        
        if not drive:
            return {"success": False, "error": "drive_letter required"}
        if not confirm:
            return {"success": False, "error": "set confirm=True to format volume (DESTRUCTIVE)"}
        
        drive = drive.rstrip(':')
        cmd = f"Format-Volume -DriveLetter '{drive}' -FileSystem {filesystem}"
        if label:
            cmd += f" -NewFileSystemLabel '{label}'"
        if quick:
            cmd += " -Full:$false"
        cmd += " -Confirm:$false | ConvertTo-Json"
        
        result = await self._run_powershell(cmd, timeout=300)
        if result["success"]:
            return {"success": True, "message": f"Volume {drive}: formatted as {filesystem}"}
        return result

    async def _set_volume_label(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set volume label."""
        drive = params.get("drive_letter") or params.get("drive")
        label = params.get("label")
        
        if not drive or label is None:
            return {"success": False, "error": "drive_letter and label required"}
        
        drive = drive.rstrip(':')
        cmd = f"Set-Volume -DriveLetter '{drive}' -NewFileSystemLabel '{label}'"
        result = await self._run_powershell(cmd)
        if result["success"]:
            return {"success": True, "message": f"Volume {drive}: label set to '{label}'"}
        return result

    async def _optimize_volume(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize/defragment volume."""
        drive = params.get("drive_letter") or params.get("drive")
        retrim = params.get("retrim", False)
        defrag = params.get("defrag", True)
        
        if not drive:
            return {"success": False, "error": "drive_letter required"}
        
        drive = drive.rstrip(':')
        cmd = f"Optimize-Volume -DriveLetter '{drive}'"
        if retrim:
            cmd += " -ReTrim"
        if defrag:
            cmd += " -Defrag"
        cmd += " -Verbose"
        
        result = await self._run_powershell(cmd, timeout=600)
        if result["success"]:
            return {"success": True, "message": f"Volume {drive}: optimized", "output": result["output"]}
        return result

    async def _repair_volume(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Repair volume."""
        drive = params.get("drive_letter") or params.get("drive")
        scan_only = params.get("scan_only", True)
        
        if not drive:
            return {"success": False, "error": "drive_letter required"}
        
        drive = drive.rstrip(':')
        cmd = f"Repair-Volume -DriveLetter '{drive}'"
        if scan_only:
            cmd += " -Scan"
        else:
            cmd += " -SpotFix"
        
        result = await self._run_powershell(cmd, timeout=600)
        return result

    # Drive letters
    async def _get_drive_letters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get used and available drive letters."""
        cmd = """$used = (Get-Volume | Where-Object DriveLetter).DriveLetter
            $all = 65..90 | ForEach-Object {[char]$_}
            $available = $all | Where-Object {$_ -notin $used}
            [PSCustomObject]@{Used=$used;Available=$available} | ConvertTo-Json"""
        result = await self._run_powershell(cmd)
        if result["success"]:
            try:
                letters = json.loads(result["output"]) if result["output"] else {}
                return {"success": True, "drive_letters": letters}
            except json.JSONDecodeError:
                return result
        return result

    async def _set_drive_letter(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Change partition drive letter."""
        disk = params.get("disk")
        partition = params.get("partition")
        old_letter = params.get("old_letter")
        new_letter = params.get("new_letter")
        
        if not new_letter:
            return {"success": False, "error": "new_letter required"}
        
        new_letter = new_letter.rstrip(':')
        
        if old_letter:
            old_letter = old_letter.rstrip(':')
            cmd = f"Get-Partition -DriveLetter '{old_letter}' | Set-Partition -NewDriveLetter '{new_letter}'"
        elif disk is not None and partition is not None:
            cmd = f"Set-Partition -DiskNumber {disk} -PartitionNumber {partition} -NewDriveLetter '{new_letter}'"
        else:
            return {"success": False, "error": "old_letter or disk+partition required"}
        
        result = await self._run_powershell(cmd)
        if result["success"]:
            return {"success": True, "message": f"Drive letter changed to {new_letter}:"}
        return result

    async def _remove_drive_letter(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove drive letter from partition."""
        letter = params.get("drive_letter") or params.get("letter")
        if not letter:
            return {"success": False, "error": "drive_letter required"}
        
        letter = letter.rstrip(':')
        cmd = f"Remove-PartitionAccessPath -DriveLetter '{letter}' -AccessPath '{letter}:\\'"
        result = await self._run_powershell(cmd)
        if result["success"]:
            return {"success": True, "message": f"Drive letter {letter}: removed"}
        return result

    # Storage pools/spaces
    async def _get_storage_pools(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get storage pools."""
        cmd = "Get-StoragePool | Select-Object FriendlyName,OperationalStatus,HealthStatus,Size,AllocatedSize,IsPrimordial | ConvertTo-Json"
        result = await self._run_powershell(cmd)
        if result["success"]:
            try:
                pools = json.loads(result["output"]) if result["output"] else []
                if isinstance(pools, dict):
                    pools = [pools]
                return {"success": True, "storage_pools": pools}
            except json.JSONDecodeError:
                return result
        return result

    async def _get_storage_spaces(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get storage spaces (virtual disks)."""
        cmd = "Get-VirtualDisk | Select-Object FriendlyName,OperationalStatus,HealthStatus,Size,ResiliencySettingName,NumberOfColumns | ConvertTo-Json"
        result = await self._run_powershell(cmd)
        if result["success"]:
            try:
                spaces = json.loads(result["output"]) if result["output"] else []
                if isinstance(spaces, dict):
                    spaces = [spaces]
                return {"success": True, "storage_spaces": spaces}
            except json.JSONDecodeError:
                return result
        return result

    async def _get_storage_jobs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get running storage jobs."""
        cmd = "Get-StorageJob | Select-Object Name,JobState,PercentComplete,ElapsedTime | ConvertTo-Json"
        result = await self._run_powershell(cmd)
        if result["success"]:
            try:
                jobs = json.loads(result["output"]) if result["output"] else []
                if isinstance(jobs, dict):
                    jobs = [jobs]
                return {"success": True, "storage_jobs": jobs}
            except json.JSONDecodeError:
                return result
        return result

    # TRIM operations
    async def _enable_trim(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Enable TRIM for SSDs."""
        cmd = "fsutil behavior set DisableDeleteNotify 0"
        result = await self._run_powershell(cmd)
        if result["success"]:
            return {"success": True, "message": "TRIM enabled"}
        return result

    async def _disable_trim(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Disable TRIM for SSDs."""
        cmd = "fsutil behavior set DisableDeleteNotify 1"
        result = await self._run_powershell(cmd)
        if result["success"]:
            return {"success": True, "message": "TRIM disabled"}
        return result

    async def _run_trim(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run TRIM on SSD volume."""
        drive = params.get("drive_letter") or params.get("drive")
        if not drive:
            return {"success": False, "error": "drive_letter required"}
        
        drive = drive.rstrip(':')
        cmd = f"Optimize-Volume -DriveLetter '{drive}' -ReTrim -Verbose"
        result = await self._run_powershell(cmd, timeout=300)
        return result

    # Filesystem
    async def _check_filesystem(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Check filesystem integrity."""
        drive = params.get("drive_letter") or params.get("drive")
        if not drive:
            return {"success": False, "error": "drive_letter required"}
        
        drive = drive.rstrip(':')
        cmd = f"chkdsk {drive}: /scan"
        result = await self._run_powershell(cmd, timeout=600)
        return {"success": True, "output": result["output"]}

    async def _get_filesystem_stats(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get filesystem statistics."""
        drive = params.get("drive_letter") or params.get("drive")
        if not drive:
            return {"success": False, "error": "drive_letter required"}
        
        drive = drive.rstrip(':')
        cmd = f"fsutil volume diskfree {drive}:"
        result = await self._run_powershell(cmd)
        return result

    # VHD operations
    async def _mount_vhd(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Mount a VHD/VHDX file."""
        path = params.get("path")
        readonly = params.get("readonly", False)
        
        if not path:
            return {"success": False, "error": "path required"}
        
        cmd = f"Mount-VHD -Path '{path}'"
        if readonly:
            cmd += " -ReadOnly"
        cmd += " -PassThru | ConvertTo-Json"
        
        result = await self._run_powershell(cmd)
        if result["success"]:
            return {"success": True, "message": f"VHD mounted: {path}"}
        return result

    async def _dismount_vhd(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Dismount a VHD/VHDX file."""
        path = params.get("path")
        
        if not path:
            return {"success": False, "error": "path required"}
        
        cmd = f"Dismount-VHD -Path '{path}'"
        result = await self._run_powershell(cmd)
        if result["success"]:
            return {"success": True, "message": f"VHD dismounted: {path}"}
        return result

    async def _create_vhd(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new VHD/VHDX file."""
        path = params.get("path")
        size = params.get("size")  # e.g., 10GB
        dynamic = params.get("dynamic", True)
        
        if not path or not size:
            return {"success": False, "error": "path and size required"}
        
        cmd = f"New-VHD -Path '{path}' -SizeBytes {size}"
        if dynamic:
            cmd += " -Dynamic"
        else:
            cmd += " -Fixed"
        cmd += " | ConvertTo-Json"
        
        result = await self._run_powershell(cmd, timeout=300)
        if result["success"]:
            return {"success": True, "message": f"VHD created: {path}"}
        return result

    async def _get_vhd_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get VHD/VHDX information."""
        path = params.get("path")
        
        if not path:
            return {"success": False, "error": "path required"}
        
        cmd = f"Get-VHD -Path '{path}' | Select-Object * | ConvertTo-Json"
        result = await self._run_powershell(cmd)
        if result["success"]:
            try:
                vhd = json.loads(result["output"]) if result["output"] else None
                return {"success": True, "vhd": vhd}
            except json.JSONDecodeError:
                return result
        return result

    def get_schema(self) -> Dict[str, Any]:
        """Return the plugin schema."""
        return {
            "type": "object",
            "actions": {
                "status": "Get disk overview",
                "list_disks": "List all disks",
                "get_disk": "Get disk details",
                "initialize_disk": "Initialize disk (GPT/MBR)",
                "list_partitions": "List partitions",
                "create_partition": "Create partition",
                "list_volumes": "List volumes",
                "format_volume": "Format volume",
                "get_physical_disks": "Get physical disk info",
                "get_disk_health": "Get disk health",
                "get_smart_data": "Get SMART data",
                "optimize_volume": "Defragment/optimize",
                "repair_volume": "Check/repair volume",
                "mount_vhd": "Mount VHD file",
                "dismount_vhd": "Dismount VHD",
                "create_vhd": "Create VHD file"
            }
        }


plugin = WindowsDiskManagementPlugin()
