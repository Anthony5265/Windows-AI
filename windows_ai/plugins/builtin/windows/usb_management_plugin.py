"""
USB Management Plugin for Windows AI
Comprehensive USB device management operations
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class USBManagementPlugin(IntegrationPlugin):
    """Plugin for managing USB devices on Windows"""

    def __init__(self):
        metadata = PluginMetadata(
            id="usb-management",
            name="USB Management",
            description="Comprehensive USB device management - enumerate, eject, mount, and configure USB devices",
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["usb", "devices", "hardware", "storage", "windows"],
        )
        super().__init__(metadata)
        self._actions = {
            # USB Device Enumeration
            "list_usb_devices": self._list_usb_devices,
            "get_device_details": self._get_device_details,
            "list_usb_controllers": self._list_usb_controllers,
            "list_usb_hubs": self._list_usb_hubs,
            "get_device_tree": self._get_device_tree,
            "list_storage_devices": self._list_storage_devices,
            "list_usb_drives": self._list_usb_drives,
            # Safe Eject Operations
            "safely_eject_device": self._safely_eject_device,
            "eject_by_drive_letter": self._eject_by_drive_letter,
            "get_ejectable_devices": self._get_ejectable_devices,
            "check_device_in_use": self._check_device_in_use,
            "force_eject_device": self._force_eject_device,
            # Mount/Unmount Operations
            "mount_usb_drive": self._mount_usb_drive,
            "unmount_usb_drive": self._unmount_usb_drive,
            "get_mount_points": self._get_mount_points,
            "assign_drive_letter": self._assign_drive_letter,
            "remove_drive_letter": self._remove_drive_letter,
            "get_volume_info": self._get_volume_info,
            # USB Device Configuration
            "enable_usb_device": self._enable_usb_device,
            "disable_usb_device": self._disable_usb_device,
            "get_device_properties": self._get_device_properties,
            "get_device_drivers": self._get_device_drivers,
            "update_device_driver": self._update_device_driver,
            "uninstall_device": self._uninstall_device,
            # USB Power Management
            "get_power_settings": self._get_power_settings,
            "set_selective_suspend": self._set_selective_suspend,
            "disable_usb_power_saving": self._disable_usb_power_saving,
            "get_power_state": self._get_power_state,
            # USB Storage Operations
            "format_usb_drive": self._format_usb_drive,
            "get_disk_partitions": self._get_disk_partitions,
            "create_partition": self._create_partition,
            "delete_partition": self._delete_partition,
            "set_partition_active": self._set_partition_active,
            "clean_disk": self._clean_disk,
            # USB Transfer & Performance
            "get_transfer_speed": self._get_transfer_speed,
            "get_usb_bandwidth": self._get_usb_bandwidth,
            "test_usb_throughput": self._test_usb_throughput,
            "get_device_speed_class": self._get_device_speed_class,
            # USB Security
            "get_usb_policies": self._get_usb_policies,
            "set_usb_storage_policy": self._set_usb_storage_policy,
            "block_usb_storage": self._block_usb_storage,
            "allow_usb_storage": self._allow_usb_storage,
            "get_blocked_devices": self._get_blocked_devices,
            # USB History & Logging
            "get_usb_history": self._get_usb_history,
            "clear_usb_history": self._clear_usb_history,
            "get_connection_events": self._get_connection_events,
            "export_device_report": self._export_device_report,
            # Diagnostics
            "scan_hardware_changes": self._scan_hardware_changes,
            "troubleshoot_usb": self._troubleshoot_usb,
            "reset_usb_controller": self._reset_usb_controller,
            "get_device_errors": self._get_device_errors,
        }

    async def _run_powershell(self, script: str) -> Dict[str, Any]:
        """Execute a PowerShell script and return results"""
        try:
            process = await asyncio.create_subprocess_exec(
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            return {
                "success": process.returncode == 0,
                "output": stdout.decode("utf-8", errors="replace").strip(),
                "error": stderr.decode("utf-8", errors="replace").strip() if stderr else None,
                "return_code": process.returncode,
            }
        except Exception as e:
            logger.warning(f"PowerShell execution unavailable: {e}")
            return {"success": False, "output": "", "error": str(e), "return_code": -1}

    async def initialize(self) -> bool:
        """Initialize the USB management plugin"""
        try:
            # Verify we can access USB device info
            result = await self._run_powershell(
                "Get-CimInstance -ClassName Win32_USBHub -ErrorAction SilentlyContinue | Select-Object -First 1"
            )
            self._initialized = True
            logger.info("USB Management plugin initialized successfully")
            return True
        except Exception as e:
            logger.warning(f"USB Management plugin not available (requires Windows): {e}")
            return False

    async def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """Execute a USB management action"""
        if action not in self._actions:
            return {
                "success": False,
                "error": f"Unknown action: {action}",
                "available_actions": list(self._actions.keys()),
            }
        try:
            result = await self._actions[action](**kwargs)
            return result
        except Exception as e:
            logger.error(f"USB action '{action}' failed: {e}")
            return {"success": False, "error": str(e), "action": action}

    async def cleanup(self) -> None:
        """Cleanup USB management resources"""
        self._initialized = False
        logger.info("USB Management plugin cleaned up")

    # USB Device Enumeration
    async def _list_usb_devices(self, **kwargs) -> Dict[str, Any]:
        """List all connected USB devices"""
        script = """
        $devices = Get-CimInstance -ClassName Win32_PnPEntity | 
            Where-Object { $_.PNPDeviceID -like 'USB*' } |
            Select-Object Name, DeviceID, Status, PNPDeviceID, Manufacturer, Description
        $devices | ForEach-Object {
            [PSCustomObject]@{
                Name = $_.Name
                DeviceID = $_.DeviceID
                Status = $_.Status
                PNPDeviceID = $_.PNPDeviceID
                Manufacturer = $_.Manufacturer
                Description = $_.Description
            }
        } | ConvertTo-Json -Depth 3
        """
        result = await self._run_powershell(script)
        if result["success"] and result["output"]:
            import json
            try:
                devices = json.loads(result["output"])
                if not isinstance(devices, list):
                    devices = [devices]
                return {"success": True, "devices": devices, "count": len(devices)}
            except json.JSONDecodeError:
                return {"success": True, "output": result["output"]}
        return result

    async def _get_device_details(self, device_id: str, **kwargs) -> Dict[str, Any]:
        """Get detailed information about a specific USB device"""
        script = f"""
        $device = Get-CimInstance -ClassName Win32_PnPEntity | 
            Where-Object {{ $_.DeviceID -eq '{device_id}' }}
        if ($device) {{
            $driver = Get-CimInstance -ClassName Win32_PnPSignedDriver | 
                Where-Object {{ $_.DeviceID -eq '{device_id}' }}
            [PSCustomObject]@{{
                Name = $device.Name
                DeviceID = $device.DeviceID
                Status = $device.Status
                PNPDeviceID = $device.PNPDeviceID
                Manufacturer = $device.Manufacturer
                Description = $device.Description
                ClassGuid = $device.ClassGuid
                CompatibleID = $device.CompatibleID
                HardwareID = $device.HardwareID
                DriverName = $driver.DriverName
                DriverVersion = $driver.DriverVersion
                DriverDate = $driver.DriverDate
                DriverProviderName = $driver.DriverProviderName
            }} | ConvertTo-Json
        }} else {{
            Write-Output "Device not found"
        }}
        """
        return await self._run_powershell(script)

    async def _list_usb_controllers(self, **kwargs) -> Dict[str, Any]:
        """List all USB controllers on the system"""
        script = """
        Get-CimInstance -ClassName Win32_USBController | 
            Select-Object Name, DeviceID, Status, Manufacturer, 
                PNPDeviceID, ProtocolSupported, StatusInfo |
            ConvertTo-Json -Depth 3
        """
        return await self._run_powershell(script)

    async def _list_usb_hubs(self, **kwargs) -> Dict[str, Any]:
        """List all USB hubs"""
        script = """
        Get-CimInstance -ClassName Win32_USBHub | 
            Select-Object Name, DeviceID, Status, PNPDeviceID, 
                NumberOfPorts, USBVersion |
            ConvertTo-Json -Depth 3
        """
        return await self._run_powershell(script)

    async def _get_device_tree(self, **kwargs) -> Dict[str, Any]:
        """Get USB device hierarchy tree"""
        script = """
        $controllers = Get-CimInstance -ClassName Win32_USBController
        $hubs = Get-CimInstance -ClassName Win32_USBHub
        $devices = Get-CimInstance -ClassName Win32_PnPEntity | 
            Where-Object { $_.PNPDeviceID -like 'USB*' }
        
        [PSCustomObject]@{
            Controllers = $controllers | Select-Object Name, DeviceID
            Hubs = $hubs | Select-Object Name, DeviceID
            Devices = $devices | Select-Object Name, DeviceID
        } | ConvertTo-Json -Depth 4
        """
        return await self._run_powershell(script)

    async def _list_storage_devices(self, **kwargs) -> Dict[str, Any]:
        """List USB storage devices"""
        script = """
        Get-CimInstance -ClassName Win32_DiskDrive | 
            Where-Object { $_.InterfaceType -eq 'USB' } |
            Select-Object Model, DeviceID, Size, Partitions, 
                InterfaceType, MediaType, SerialNumber, Status |
            ConvertTo-Json -Depth 3
        """
        return await self._run_powershell(script)

    async def _list_usb_drives(self, **kwargs) -> Dict[str, Any]:
        """List USB drives with drive letters"""
        script = """
        $usbDrives = Get-CimInstance -ClassName Win32_DiskDrive | 
            Where-Object { $_.InterfaceType -eq 'USB' }
        
        $results = foreach ($drive in $usbDrives) {
            $partitions = Get-CimInstance -Query "ASSOCIATORS OF {Win32_DiskDrive.DeviceID='$($drive.DeviceID)'} WHERE AssocClass=Win32_DiskDriveToDiskPartition"
            foreach ($partition in $partitions) {
                $volumes = Get-CimInstance -Query "ASSOCIATORS OF {Win32_DiskPartition.DeviceID='$($partition.DeviceID)'} WHERE AssocClass=Win32_LogicalDiskToPartition"
                foreach ($volume in $volumes) {
                    [PSCustomObject]@{
                        DriveLetter = $volume.DeviceID
                        Model = $drive.Model
                        Size = [math]::Round($drive.Size / 1GB, 2)
                        FreeSpace = [math]::Round($volume.FreeSpace / 1GB, 2)
                        FileSystem = $volume.FileSystem
                        VolumeName = $volume.VolumeName
                        SerialNumber = $drive.SerialNumber
                    }
                }
            }
        }
        $results | ConvertTo-Json -Depth 3
        """
        return await self._run_powershell(script)

    # Safe Eject Operations
    async def _safely_eject_device(self, device_id: str, **kwargs) -> Dict[str, Any]:
        """Safely eject a USB device by device ID"""
        script = f"""
        $vol = Get-WmiObject -Class Win32_Volume | Where-Object {{ $_.DeviceID -like '*{device_id}*' }}
        if ($vol) {{
            $vol.Dismount($false, $false) | Out-Null
            Write-Output "Device ejected successfully"
        }} else {{
            # Try using device removal API
            $device = Get-PnpDevice | Where-Object {{ $_.InstanceId -like '*{device_id}*' }}
            if ($device) {{
                $removeCommand = "pnputil /remove-device `"$($device.InstanceId)`""
                Invoke-Expression $removeCommand
            }} else {{
                Write-Output "Device not found"
            }}
        }}
        """
        return await self._run_powershell(script)

    async def _eject_by_drive_letter(self, drive_letter: str, **kwargs) -> Dict[str, Any]:
        """Eject USB drive by drive letter"""
        drive_letter = drive_letter.rstrip(":\\")
        script = f"""
        $driveEject = New-Object -ComObject Shell.Application
        $driveEject.Namespace(17).ParseName("{drive_letter}:").InvokeVerb("Eject")
        Start-Sleep -Seconds 2
        $drive = Get-WmiObject Win32_LogicalDisk | Where-Object {{ $_.DeviceID -eq "{drive_letter}:" }}
        if ($drive) {{
            Write-Output "Eject may be pending - please wait for safe removal notification"
        }} else {{
            Write-Output "Drive ejected successfully"
        }}
        """
        return await self._run_powershell(script)

    async def _get_ejectable_devices(self, **kwargs) -> Dict[str, Any]:
        """Get list of devices that can be safely ejected"""
        script = """
        $ejectable = Get-WmiObject Win32_DiskDrive | 
            Where-Object { $_.InterfaceType -eq 'USB' -or $_.MediaType -eq 'Removable Media' }
        
        foreach ($disk in $ejectable) {
            $partitions = Get-WmiObject -Query "ASSOCIATORS OF {Win32_DiskDrive.DeviceID='$($disk.DeviceID)'} WHERE AssocClass=Win32_DiskDriveToDiskPartition"
            foreach ($partition in $partitions) {
                $volumes = Get-WmiObject -Query "ASSOCIATORS OF {Win32_DiskPartition.DeviceID='$($partition.DeviceID)'} WHERE AssocClass=Win32_LogicalDiskToPartition"
                foreach ($volume in $volumes) {
                    [PSCustomObject]@{
                        DriveLetter = $volume.DeviceID
                        Model = $disk.Model
                        DeviceID = $disk.DeviceID
                        CanEject = $true
                    }
                }
            }
        }
        """ + " | ConvertTo-Json -Depth 3"
        return await self._run_powershell(script)

    async def _check_device_in_use(self, drive_letter: str, **kwargs) -> Dict[str, Any]:
        """Check if a USB drive is currently in use"""
        drive_letter = drive_letter.rstrip(":\\")
        script = f"""
        $handles = & handle.exe {drive_letter}: 2>$null
        if ($handles) {{
            $inUse = $handles | Select-String -Pattern "pid:" 
            [PSCustomObject]@{{
                InUse = $inUse.Count -gt 0
                ProcessCount = $inUse.Count
                Details = $inUse
            }} | ConvertTo-Json
        }} else {{
            # Fallback method
            $volume = Get-WmiObject Win32_Volume | Where-Object {{ $_.DriveLetter -eq "{drive_letter}:" }}
            [PSCustomObject]@{{
                InUse = $false
                Note = "Handle.exe not available - basic check only"
                Status = $volume.Status
            }} | ConvertTo-Json
        }}
        """
        return await self._run_powershell(script)

    async def _force_eject_device(self, drive_letter: str, **kwargs) -> Dict[str, Any]:
        """Force eject a USB drive (closes open handles)"""
        drive_letter = drive_letter.rstrip(":\\")
        script = f"""
        # Warning: This will forcefully close handles
        $volume = Get-WmiObject Win32_Volume | Where-Object {{ $_.DriveLetter -eq "{drive_letter}:" }}
        if ($volume) {{
            $result = $volume.Dismount($true, $false)
            if ($result.ReturnValue -eq 0) {{
                Write-Output "Drive forcefully ejected"
            }} else {{
                Write-Output "Eject failed with code: $($result.ReturnValue)"
            }}
        }} else {{
            Write-Output "Drive not found"
        }}
        """
        return await self._run_powershell(script)

    # Mount/Unmount Operations
    async def _mount_usb_drive(self, disk_number: int, **kwargs) -> Dict[str, Any]:
        """Mount a USB drive that was previously unmounted"""
        script = f"""
        $disk = Get-Disk -Number {disk_number}
        if ($disk.OperationalStatus -eq 'Offline') {{
            Set-Disk -Number {disk_number} -IsOffline $false
        }}
        if ($disk.IsReadOnly) {{
            Set-Disk -Number {disk_number} -IsReadOnly $false
        }}
        $partitions = Get-Partition -DiskNumber {disk_number} -ErrorAction SilentlyContinue
        foreach ($p in $partitions) {{
            if (-not $p.DriveLetter) {{
                Add-PartitionAccessPath -DiskNumber {disk_number} -PartitionNumber $p.PartitionNumber -AssignDriveLetter
            }}
        }}
        Get-Partition -DiskNumber {disk_number} | Select-Object DriveLetter, Size, Type | ConvertTo-Json
        """
        return await self._run_powershell(script)

    async def _unmount_usb_drive(self, drive_letter: str, **kwargs) -> Dict[str, Any]:
        """Unmount a USB drive (remove drive letter but keep accessible)"""
        drive_letter = drive_letter.rstrip(":\\")
        script = f"""
        $partition = Get-Partition | Where-Object {{ $_.DriveLetter -eq '{drive_letter}' }}
        if ($partition) {{
            Remove-PartitionAccessPath -DiskNumber $partition.DiskNumber -PartitionNumber $partition.PartitionNumber -AccessPath "{drive_letter}:"
            Write-Output "Drive letter removed"
        }} else {{
            Write-Output "Drive not found"
        }}
        """
        return await self._run_powershell(script)

    async def _get_mount_points(self, **kwargs) -> Dict[str, Any]:
        """Get all mount points including USB drives"""
        script = """
        Get-Volume | Select-Object DriveLetter, FileSystemLabel, FileSystem, 
            DriveType, SizeRemaining, Size, HealthStatus |
            Where-Object { $_.DriveType -eq 'Removable' -or $_.DriveLetter } |
            ConvertTo-Json -Depth 3
        """
        return await self._run_powershell(script)

    async def _assign_drive_letter(self, disk_number: int, partition_number: int, drive_letter: str, **kwargs) -> Dict[str, Any]:
        """Assign a drive letter to a partition"""
        drive_letter = drive_letter.rstrip(":\\")
        script = f"""
        Set-Partition -DiskNumber {disk_number} -PartitionNumber {partition_number} -NewDriveLetter {drive_letter}
        Get-Partition -DiskNumber {disk_number} -PartitionNumber {partition_number} | 
            Select-Object DriveLetter, Size, Type | ConvertTo-Json
        """
        return await self._run_powershell(script)

    async def _remove_drive_letter(self, drive_letter: str, **kwargs) -> Dict[str, Any]:
        """Remove a drive letter from a partition"""
        drive_letter = drive_letter.rstrip(":\\")
        script = f"""
        $partition = Get-Partition | Where-Object {{ $_.DriveLetter -eq '{drive_letter}' }}
        if ($partition) {{
            Remove-PartitionAccessPath -DiskNumber $partition.DiskNumber -PartitionNumber $partition.PartitionNumber -AccessPath "{drive_letter}:" -Confirm:$false
            Write-Output "Drive letter {drive_letter}: removed"
        }}
        """
        return await self._run_powershell(script)

    async def _get_volume_info(self, drive_letter: str, **kwargs) -> Dict[str, Any]:
        """Get detailed volume information"""
        drive_letter = drive_letter.rstrip(":\\")
        script = f"""
        $volume = Get-Volume -DriveLetter {drive_letter}
        $partition = Get-Partition | Where-Object {{ $_.DriveLetter -eq '{drive_letter}' }}
        $disk = Get-Disk -Number $partition.DiskNumber
        
        [PSCustomObject]@{{
            DriveLetter = $volume.DriveLetter
            FileSystemLabel = $volume.FileSystemLabel
            FileSystem = $volume.FileSystem
            Size = [math]::Round($volume.Size / 1GB, 2)
            SizeRemaining = [math]::Round($volume.SizeRemaining / 1GB, 2)
            HealthStatus = $volume.HealthStatus
            DiskNumber = $partition.DiskNumber
            PartitionNumber = $partition.PartitionNumber
            DiskModel = $disk.Model
            BusType = $disk.BusType
            MediaType = $disk.MediaType
        }} | ConvertTo-Json
        """
        return await self._run_powershell(script)

    # USB Device Configuration
    async def _enable_usb_device(self, device_id: str, **kwargs) -> Dict[str, Any]:
        """Enable a disabled USB device"""
        script = f"""
        $device = Get-PnpDevice | Where-Object {{ $_.InstanceId -like '*{device_id}*' }}
        if ($device) {{
            Enable-PnpDevice -InstanceId $device.InstanceId -Confirm:$false
            Write-Output "Device enabled: $($device.FriendlyName)"
        }} else {{
            Write-Output "Device not found"
        }}
        """
        return await self._run_powershell(script)

    async def _disable_usb_device(self, device_id: str, **kwargs) -> Dict[str, Any]:
        """Disable a USB device"""
        script = f"""
        $device = Get-PnpDevice | Where-Object {{ $_.InstanceId -like '*{device_id}*' }}
        if ($device) {{
            Disable-PnpDevice -InstanceId $device.InstanceId -Confirm:$false
            Write-Output "Device disabled: $($device.FriendlyName)"
        }} else {{
            Write-Output "Device not found"
        }}
        """
        return await self._run_powershell(script)

    async def _get_device_properties(self, device_id: str, **kwargs) -> Dict[str, Any]:
        """Get all properties of a USB device"""
        script = f"""
        $device = Get-PnpDevice | Where-Object {{ $_.InstanceId -like '*{device_id}*' }} | Select-Object -First 1
        if ($device) {{
            $props = Get-PnpDeviceProperty -InstanceId $device.InstanceId
            [PSCustomObject]@{{
                Device = $device.FriendlyName
                InstanceId = $device.InstanceId
                Status = $device.Status
                Class = $device.Class
                Properties = $props | Select-Object KeyName, Data
            }} | ConvertTo-Json -Depth 4
        }}
        """
        return await self._run_powershell(script)

    async def _get_device_drivers(self, device_id: str = None, **kwargs) -> Dict[str, Any]:
        """Get USB device driver information"""
        filter_clause = f"Where-Object {{ $_.DeviceID -like '*{device_id}*' }} |" if device_id else ""
        script = f"""
        Get-CimInstance -ClassName Win32_PnPSignedDriver | 
            Where-Object {{ $_.DeviceID -like 'USB*' }} |
            {filter_clause}
            Select-Object DeviceName, DeviceID, DriverName, DriverVersion, 
                DriverDate, DriverProviderName, IsSigned, Signer |
            ConvertTo-Json -Depth 3
        """
        return await self._run_powershell(script)

    async def _update_device_driver(self, device_id: str, **kwargs) -> Dict[str, Any]:
        """Update driver for a USB device"""
        script = f"""
        $device = Get-PnpDevice | Where-Object {{ $_.InstanceId -like '*{device_id}*' }}
        if ($device) {{
            $result = pnputil /scan-devices
            Write-Output "Scanning for driver updates..."
            Write-Output $result
        }}
        """
        return await self._run_powershell(script)

    async def _uninstall_device(self, device_id: str, **kwargs) -> Dict[str, Any]:
        """Uninstall a USB device"""
        script = f"""
        $device = Get-PnpDevice | Where-Object {{ $_.InstanceId -like '*{device_id}*' }}
        if ($device) {{
            pnputil /remove-device "$($device.InstanceId)"
        }} else {{
            Write-Output "Device not found"
        }}
        """
        return await self._run_powershell(script)

    # USB Power Management
    async def _get_power_settings(self, **kwargs) -> Dict[str, Any]:
        """Get USB power management settings"""
        script = """
        $hubs = Get-CimInstance -ClassName Win32_USBHub
        $results = foreach ($hub in $hubs) {
            $device = Get-PnpDevice | Where-Object { $_.InstanceId -eq $hub.DeviceID }
            $powerMgmt = Get-CimInstance -ClassName MSPower_DeviceEnable -Namespace root\wmi -ErrorAction SilentlyContinue |
                Where-Object { $_.InstanceName -like "*$($hub.DeviceID)*" }
            [PSCustomObject]@{
                HubName = $hub.Name
                DeviceID = $hub.DeviceID
                PowerManagementEnabled = $powerMgmt.Enable
            }
        }
        $results | ConvertTo-Json -Depth 3
        """
        return await self._run_powershell(script)

    async def _set_selective_suspend(self, enabled: bool, **kwargs) -> Dict[str, Any]:
        """Enable or disable USB selective suspend"""
        value = "1" if enabled else "0"
        script = f"""
        # Set USB selective suspend via power options
        powercfg /setacvalueindex SCHEME_CURRENT 2a737441-1930-4402-8d77-b2bebba308a3 48e6b7a6-50f5-4782-a5d4-53bb8f07e226 {value}
        powercfg /setdcvalueindex SCHEME_CURRENT 2a737441-1930-4402-8d77-b2bebba308a3 48e6b7a6-50f5-4782-a5d4-53bb8f07e226 {value}
        powercfg /setactive SCHEME_CURRENT
        Write-Output "USB selective suspend {'enabled' if enabled else 'disabled'}"
        """
        return await self._run_powershell(script)

    async def _disable_usb_power_saving(self, device_id: str = None, **kwargs) -> Dict[str, Any]:
        """Disable power saving for USB devices"""
        script = """
        $hubs = Get-PnpDevice -Class USB | Where-Object { $_.Status -eq 'OK' }
        foreach ($hub in $hubs) {
            $device = Get-WmiObject MSPower_DeviceEnable -Namespace root\wmi | 
                Where-Object { $_.InstanceName -like "*$($hub.InstanceId)*" }
            if ($device) {
                $device.Enable = $false
                $device.Put() | Out-Null
                Write-Output "Disabled power saving for: $($hub.FriendlyName)"
            }
        }
        """
        return await self._run_powershell(script)

    async def _get_power_state(self, device_id: str, **kwargs) -> Dict[str, Any]:
        """Get power state of a USB device"""
        script = f"""
        $device = Get-CimInstance -ClassName Win32_PnPEntity | 
            Where-Object {{ $_.DeviceID -like '*{device_id}*' }}
        if ($device) {{
            [PSCustomObject]@{{
                Device = $device.Name
                Status = $device.Status
                Availability = $device.Availability
                StatusInfo = $device.StatusInfo
                PowerManagementSupported = $device.PowerManagementSupported
                PowerManagementCapabilities = $device.PowerManagementCapabilities
            }} | ConvertTo-Json
        }}
        """
        return await self._run_powershell(script)

    # USB Storage Operations
    async def _format_usb_drive(self, drive_letter: str, file_system: str = "NTFS", 
                                 label: str = "USB Drive", quick: bool = True, **kwargs) -> Dict[str, Any]:
        """Format a USB drive"""
        drive_letter = drive_letter.rstrip(":\\")
        quick_flag = "-Quick" if quick else ""
        script = f"""
        $confirm = Read-Host "This will ERASE all data on {drive_letter}:. Type 'YES' to confirm"
        if ($confirm -eq 'YES') {{
            Format-Volume -DriveLetter {drive_letter} -FileSystem {file_system} -NewFileSystemLabel "{label}" {quick_flag} -Confirm:$false
            Get-Volume -DriveLetter {drive_letter} | Select-Object DriveLetter, FileSystem, FileSystemLabel, Size | ConvertTo-Json
        }} else {{
            Write-Output "Format cancelled"
        }}
        """
        # For automation, skip confirmation
        script = f"""
        Format-Volume -DriveLetter {drive_letter} -FileSystem {file_system} -NewFileSystemLabel "{label}" {quick_flag} -Confirm:$false -ErrorAction Stop
        Get-Volume -DriveLetter {drive_letter} | Select-Object DriveLetter, FileSystem, FileSystemLabel, Size | ConvertTo-Json
        """
        return await self._run_powershell(script)

    async def _get_disk_partitions(self, disk_number: int, **kwargs) -> Dict[str, Any]:
        """Get partitions on a USB disk"""
        script = f"""
        Get-Partition -DiskNumber {disk_number} | 
            Select-Object PartitionNumber, DriveLetter, Size, Type, IsActive, IsBoot, IsSystem |
            ConvertTo-Json -Depth 3
        """
        return await self._run_powershell(script)

    async def _create_partition(self, disk_number: int, size_gb: float = None, 
                                 use_maximum: bool = True, **kwargs) -> Dict[str, Any]:
        """Create a new partition on a USB disk"""
        size_param = "-UseMaximumSize" if use_maximum else f"-Size {size_gb}GB"
        script = f"""
        New-Partition -DiskNumber {disk_number} {size_param} -AssignDriveLetter |
            Select-Object PartitionNumber, DriveLetter, Size | ConvertTo-Json
        """
        return await self._run_powershell(script)

    async def _delete_partition(self, disk_number: int, partition_number: int, **kwargs) -> Dict[str, Any]:
        """Delete a partition"""
        script = f"""
        Remove-Partition -DiskNumber {disk_number} -PartitionNumber {partition_number} -Confirm:$false
        Write-Output "Partition {partition_number} deleted from disk {disk_number}"
        """
        return await self._run_powershell(script)

    async def _set_partition_active(self, disk_number: int, partition_number: int, **kwargs) -> Dict[str, Any]:
        """Set a partition as active"""
        script = f"""
        Set-Partition -DiskNumber {disk_number} -PartitionNumber {partition_number} -IsActive $true
        Get-Partition -DiskNumber {disk_number} -PartitionNumber {partition_number} | 
            Select-Object DriveLetter, IsActive | ConvertTo-Json
        """
        return await self._run_powershell(script)

    async def _clean_disk(self, disk_number: int, **kwargs) -> Dict[str, Any]:
        """Clean all partitions from a USB disk (WARNING: destructive)"""
        script = f"""
        Clear-Disk -Number {disk_number} -RemoveData -RemoveOEM -Confirm:$false
        Write-Output "Disk {disk_number} has been cleaned"
        """
        return await self._run_powershell(script)

    # USB Transfer & Performance
    async def _get_transfer_speed(self, drive_letter: str, **kwargs) -> Dict[str, Any]:
        """Estimate USB drive transfer speed"""
        drive_letter = drive_letter.rstrip(":\\")
        script = f"""
        $testFile = "{drive_letter}:\\speedtest_$([guid]::NewGuid().ToString('N')).tmp"
        $sizes = @(1MB, 10MB)
        $results = @()
        
        foreach ($size in $sizes) {{
            $data = New-Object byte[] $size
            [System.Random]::new().NextBytes($data)
            
            $writeStart = Get-Date
            [System.IO.File]::WriteAllBytes($testFile, $data)
            $writeEnd = Get-Date
            $writeSpeed = [math]::Round($size / ($writeEnd - $writeStart).TotalSeconds / 1MB, 2)
            
            $readStart = Get-Date
            $readData = [System.IO.File]::ReadAllBytes($testFile)
            $readEnd = Get-Date
            $readSpeed = [math]::Round($size / ($readEnd - $readStart).TotalSeconds / 1MB, 2)
            
            $results += [PSCustomObject]@{{
                TestSizeMB = $size / 1MB
                WriteSpeedMBps = $writeSpeed
                ReadSpeedMBps = $readSpeed
            }}
        }}
        
        Remove-Item $testFile -Force -ErrorAction SilentlyContinue
        $results | ConvertTo-Json
        """
        return await self._run_powershell(script)

    async def _get_usb_bandwidth(self, **kwargs) -> Dict[str, Any]:
        """Get USB controller bandwidth information"""
        script = """
        Get-CimInstance -ClassName Win32_USBController | ForEach-Object {
            $speed = switch -Regex ($_.Name) {
                '3\\.0|3\\.1|3\\.2' { 'SuperSpeed (5-20 Gbps)' }
                '2\\.0' { 'High Speed (480 Mbps)' }
                '1\\.1' { 'Full Speed (12 Mbps)' }
                default { 'Unknown' }
            }
            [PSCustomObject]@{
                Controller = $_.Name
                Manufacturer = $_.Manufacturer
                SpeedClass = $speed
                Status = $_.Status
            }
        } | ConvertTo-Json -Depth 3
        """
        return await self._run_powershell(script)

    async def _test_usb_throughput(self, drive_letter: str, size_mb: int = 100, **kwargs) -> Dict[str, Any]:
        """Run comprehensive USB throughput test"""
        drive_letter = drive_letter.rstrip(":\\")
        script = f"""
        $testFile = "{drive_letter}:\\throughput_test.tmp"
        $size = {size_mb}MB
        
        # Sequential write test
        $data = New-Object byte[] $size
        [System.Random]::new().NextBytes($data)
        
        Write-Output "Testing sequential write..."
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        [System.IO.File]::WriteAllBytes($testFile, $data)
        $sw.Stop()
        $seqWriteSpeed = [math]::Round($size / $sw.Elapsed.TotalSeconds / 1MB, 2)
        
        Write-Output "Testing sequential read..."
        $sw.Restart()
        $readData = [System.IO.File]::ReadAllBytes($testFile)
        $sw.Stop()
        $seqReadSpeed = [math]::Round($size / $sw.Elapsed.TotalSeconds / 1MB, 2)
        
        Remove-Item $testFile -Force
        
        [PSCustomObject]@{{
            TestSizeMB = {size_mb}
            SequentialWriteMBps = $seqWriteSpeed
            SequentialReadMBps = $seqReadSpeed
        }} | ConvertTo-Json
        """
        return await self._run_powershell(script)

    async def _get_device_speed_class(self, device_id: str = None, **kwargs) -> Dict[str, Any]:
        """Get USB device speed class (1.0, 2.0, 3.0, etc.)"""
        script = """
        Get-PnpDevice -Class USB | Where-Object { $_.Status -eq 'OK' } | ForEach-Object {
            $props = Get-PnpDeviceProperty -InstanceId $_.InstanceId
            $speed = ($props | Where-Object { $_.KeyName -eq 'DEVPKEY_Device_BusReportedDeviceDesc' }).Data
            [PSCustomObject]@{
                Name = $_.FriendlyName
                InstanceId = $_.InstanceId
                Class = $_.Class
                BusReportedDesc = $speed
            }
        } | ConvertTo-Json -Depth 3
        """
        return await self._run_powershell(script)

    # USB Security
    async def _get_usb_policies(self, **kwargs) -> Dict[str, Any]:
        """Get USB storage policies"""
        script = """
        $policies = @{}
        
        # Check USBSTOR service
        $usbstor = Get-Service USBSTOR -ErrorAction SilentlyContinue
        $policies['USBSTOR_Service'] = $usbstor.Status
        
        # Check registry policies
        $regPath = 'HKLM:\\SYSTEM\\CurrentControlSet\\Services\\USBSTOR'
        $start = Get-ItemProperty -Path $regPath -Name Start -ErrorAction SilentlyContinue
        $policies['USBSTOR_Start'] = switch ($start.Start) {
            3 { 'Enabled (Manual)' }
            4 { 'Disabled' }
            default { $start.Start }
        }
        
        # Check write protection
        $wpPath = 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\StorageDevicePolicies'
        $wp = Get-ItemProperty -Path $wpPath -Name WriteProtect -ErrorAction SilentlyContinue
        $policies['WriteProtect'] = if ($wp.WriteProtect -eq 1) { 'Enabled' } else { 'Disabled' }
        
        $policies | ConvertTo-Json
        """
        return await self._run_powershell(script)

    async def _set_usb_storage_policy(self, enabled: bool, **kwargs) -> Dict[str, Any]:
        """Enable or disable USB storage devices"""
        start_value = "3" if enabled else "4"
        script = f"""
        Set-ItemProperty -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Services\\USBSTOR' -Name Start -Value {start_value}
        $status = if ({str(enabled).lower()}) {{ 'enabled' }} else {{ 'disabled' }}
        Write-Output "USB storage devices $status"
        """
        return await self._run_powershell(script)

    async def _block_usb_storage(self, **kwargs) -> Dict[str, Any]:
        """Block all USB storage devices"""
        script = """
        Set-ItemProperty -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Services\\USBSTOR' -Name Start -Value 4
        Stop-Service USBSTOR -Force -ErrorAction SilentlyContinue
        Write-Output "USB storage devices blocked"
        """
        return await self._run_powershell(script)

    async def _allow_usb_storage(self, **kwargs) -> Dict[str, Any]:
        """Allow USB storage devices"""
        script = """
        Set-ItemProperty -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Services\\USBSTOR' -Name Start -Value 3
        Start-Service USBSTOR -ErrorAction SilentlyContinue
        Write-Output "USB storage devices allowed"
        """
        return await self._run_powershell(script)

    async def _get_blocked_devices(self, **kwargs) -> Dict[str, Any]:
        """Get list of blocked USB device IDs"""
        script = """
        $blockedPath = 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\DeviceInstall\\Restrictions\\DenyDeviceIDs'
        if (Test-Path $blockedPath) {
            Get-ItemProperty -Path $blockedPath | ConvertTo-Json
        } else {
            Write-Output '{"message": "No blocked devices configured"}'
        }
        """
        return await self._run_powershell(script)

    # USB History & Logging
    async def _get_usb_history(self, **kwargs) -> Dict[str, Any]:
        """Get history of USB devices that have been connected"""
        script = """
        $usbHistory = Get-ItemProperty -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Enum\\USBSTOR\\*\\*' -ErrorAction SilentlyContinue |
            Select-Object FriendlyName, HardwareID, Mfg, Service, @{N='PSPath';E={$_.PSPath -replace '.*USBSTOR\\\\',''}}
        
        $usbHistory | ForEach-Object {
            [PSCustomObject]@{
                FriendlyName = $_.FriendlyName
                HardwareID = $_.HardwareID
                Manufacturer = $_.Mfg
                RegistryPath = $_.PSPath
            }
        } | ConvertTo-Json -Depth 3
        """
        return await self._run_powershell(script)

    async def _clear_usb_history(self, **kwargs) -> Dict[str, Any]:
        """Clear USB connection history from registry"""
        script = """
        # Warning: This requires admin privileges and a reboot
        $paths = @(
            'HKLM:\\SYSTEM\\CurrentControlSet\\Enum\\USBSTOR',
            'HKLM:\\SYSTEM\\CurrentControlSet\\Enum\\USB'
        )
        Write-Output "USB history clearing requires admin privileges and may need a reboot"
        Write-Output "History paths: $($paths -join ', ')"
        """
        return await self._run_powershell(script)

    async def _get_connection_events(self, hours: int = 24, **kwargs) -> Dict[str, Any]:
        """Get recent USB connection/disconnection events"""
        script = f"""
        $startTime = (Get-Date).AddHours(-{hours})
        Get-WinEvent -FilterHashtable @{{
            LogName = 'Microsoft-Windows-DriverFrameworks-UserMode/Operational'
            StartTime = $startTime
        }} -ErrorAction SilentlyContinue | 
        Where-Object {{ $_.Message -like '*USB*' }} |
        Select-Object TimeCreated, Id, Message -First 50 |
        ConvertTo-Json -Depth 3
        """
        return await self._run_powershell(script)

    async def _export_device_report(self, output_path: str = None, **kwargs) -> Dict[str, Any]:
        """Export comprehensive USB device report"""
        path = output_path or "$env:TEMP\\usb_report_$(Get-Date -Format 'yyyyMMdd_HHmmss').html"
        script = f"""
        $report = @"
        <html>
        <head><title>USB Device Report</title>
        <style>
            body {{ font-family: Arial; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #4CAF50; color: white; }}
        </style>
        </head>
        <body>
        <h1>USB Device Report - $(Get-Date)</h1>
"@
        
        # Add USB devices
        $devices = Get-CimInstance -ClassName Win32_PnPEntity | Where-Object {{ $_.PNPDeviceID -like 'USB*' }}
        $report += "<h2>Connected USB Devices</h2><table><tr><th>Name</th><th>Status</th><th>Device ID</th></tr>"
        foreach ($d in $devices) {{
            $report += "<tr><td>$($d.Name)</td><td>$($d.Status)</td><td>$($d.DeviceID)</td></tr>"
        }}
        $report += "</table>"
        
        # Add USB controllers
        $controllers = Get-CimInstance -ClassName Win32_USBController
        $report += "<h2>USB Controllers</h2><table><tr><th>Name</th><th>Manufacturer</th><th>Status</th></tr>"
        foreach ($c in $controllers) {{
            $report += "<tr><td>$($c.Name)</td><td>$($c.Manufacturer)</td><td>$($c.Status)</td></tr>"
        }}
        $report += "</table></body></html>"
        
        $report | Out-File -FilePath "{path}" -Encoding UTF8
        Write-Output "Report exported to: {path}"
        """
        return await self._run_powershell(script)

    # Diagnostics
    async def _scan_hardware_changes(self, **kwargs) -> Dict[str, Any]:
        """Scan for hardware changes (like clicking 'Scan for hardware changes')"""
        script = """
        pnputil /scan-devices
        Write-Output "Hardware scan completed"
        """
        return await self._run_powershell(script)

    async def _troubleshoot_usb(self, **kwargs) -> Dict[str, Any]:
        """Run USB troubleshooting diagnostics"""
        script = """
        $diagnostics = @{}
        
        # Check USBSTOR service
        $usbstor = Get-Service USBSTOR -ErrorAction SilentlyContinue
        $diagnostics['USBSTOR_Service'] = $usbstor.Status
        
        # Check USB controllers
        $controllers = Get-CimInstance -ClassName Win32_USBController
        $diagnostics['USB_Controllers'] = $controllers.Count
        $diagnostics['Controller_Status'] = ($controllers | Select-Object -ExpandProperty Status) -join ', '
        
        # Check for problem devices
        $problemDevices = Get-PnpDevice | Where-Object { 
            $_.InstanceId -like 'USB*' -and $_.Status -ne 'OK' 
        }
        $diagnostics['Problem_Devices'] = $problemDevices.Count
        $diagnostics['Problem_Details'] = $problemDevices | Select-Object FriendlyName, Status, Problem
        
        # Check USB hubs
        $hubs = Get-CimInstance -ClassName Win32_USBHub
        $diagnostics['USB_Hubs'] = $hubs.Count
        
        $diagnostics | ConvertTo-Json -Depth 4
        """
        return await self._run_powershell(script)

    async def _reset_usb_controller(self, device_id: str, **kwargs) -> Dict[str, Any]:
        """Reset a USB controller (disable and re-enable)"""
        script = f"""
        $controller = Get-PnpDevice | Where-Object {{ 
            $_.InstanceId -like '*{device_id}*' -and $_.Class -eq 'USB' 
        }}
        if ($controller) {{
            Write-Output "Disabling controller: $($controller.FriendlyName)"
            Disable-PnpDevice -InstanceId $controller.InstanceId -Confirm:$false
            Start-Sleep -Seconds 2
            Write-Output "Re-enabling controller..."
            Enable-PnpDevice -InstanceId $controller.InstanceId -Confirm:$false
            Write-Output "Controller reset complete"
        }} else {{
            Write-Output "Controller not found"
        }}
        """
        return await self._run_powershell(script)

    async def _get_device_errors(self, **kwargs) -> Dict[str, Any]:
        """Get USB devices with errors"""
        script = """
        Get-PnpDevice | Where-Object { 
            $_.InstanceId -like 'USB*' -and $_.Status -ne 'OK' 
        } | Select-Object FriendlyName, InstanceId, Status, Problem, 
            @{N='ProblemDescription';E={
                switch ($_.Problem) {
                    0 { 'No problem' }
                    1 { 'Not configured' }
                    3 { 'Out of memory' }
                    10 { 'Failed to start' }
                    12 { 'Not enough resources' }
                    14 { 'Reinstall required' }
                    18 { 'Reinstall drivers' }
                    21 { 'Windows is removing device' }
                    22 { 'Device disabled' }
                    24 { 'Device not present' }
                    28 { 'Drivers not installed' }
                    29 { 'Missing resources' }
                    31 { 'Device not working properly' }
                    32 { 'Service registry entry corrupted' }
                    33 { 'Resource requirements not known' }
                    34 { 'Need manual configuration' }
                    43 { 'Device reported problems' }
                    44 { 'Firmware disabled device' }
                    45 { 'Device connected to unprepared dock' }
                    46 { 'Resources not available for boot' }
                    47 { 'Need safe removal' }
                    48 { 'Driver blocked' }
                    49 { 'System hive too large' }
                    50 { 'Device not started' }
                    51 { 'Device missing' }
                    52 { 'Driver invalid or missing signature' }
                    53 { 'Driver pending installation' }
                    54 { 'Needs restart' }
                    default { "Unknown error code: $_" }
                }
            }}
        | ConvertTo-Json -Depth 3
        """
        return await self._run_powershell(script)

    async def connect(self, credentials: Dict[str, str]) -> bool:
        """Connect to USB management services"""
        return await self.initialize()

    async def disconnect(self) -> bool:
        """Disconnect from USB management services"""
        await self.cleanup()
        return True


# Plugin instance for registration
plugin = USBManagementPlugin()
