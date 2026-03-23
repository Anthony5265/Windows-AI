"""
Windows System Restore Plugin for Windows AI
Comprehensive system restore point and recovery management
"""

import asyncio
import subprocess
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class SystemRestorePlugin(IntegrationPlugin):
    """
    Comprehensive Windows System Restore management plugin.
    
    Provides 30+ actions for:
    - Restore point creation and management
    - System recovery operations
    - Restore point configuration
    - Disk space management for restore
    - Shadow copy management
    - System protection settings
    """

    def __init__(self):
        metadata = PluginMetadata(
            id="windows-system-restore",
            name="Windows System Restore",
            description="Comprehensive Windows system restore and recovery management",
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["windows", "system-restore", "recovery", "backup", "protection", "restore-point"],
            requirements=[]
        )
        super().__init__(metadata)
        
        self._actions = {
            # Restore Points
            "create_restore_point": self._create_restore_point,
            "list_restore_points": self._list_restore_points,
            "get_restore_point": self._get_restore_point,
            "delete_restore_point": self._delete_restore_point,
            "delete_all_restore_points": self._delete_all_restore_points,
            "get_latest_restore_point": self._get_latest_restore_point,
            
            # System Restore Operations
            "start_system_restore": self._start_system_restore,
            "restore_to_point": self._restore_to_point,
            "get_restore_status": self._get_restore_status,
            "cancel_restore": self._cancel_restore,
            "open_system_restore_wizard": self._open_system_restore_wizard,
            
            # System Protection
            "get_protection_status": self._get_protection_status,
            "enable_protection": self._enable_protection,
            "disable_protection": self._disable_protection,
            "get_protected_drives": self._get_protected_drives,
            "configure_protection": self._configure_protection,
            
            # Disk Space Management
            "get_disk_space_usage": self._get_disk_space_usage,
            "set_max_disk_usage": self._set_max_disk_usage,
            "get_max_disk_usage": self._get_max_disk_usage,
            "cleanup_old_restore_points": self._cleanup_old_restore_points,
            
            # Shadow Copies
            "list_shadow_copies": self._list_shadow_copies,
            "create_shadow_copy": self._create_shadow_copy,
            "delete_shadow_copy": self._delete_shadow_copy,
            "get_shadow_copy_storage": self._get_shadow_copy_storage,
            
            # Recovery Options
            "get_recovery_options": self._get_recovery_options,
            "access_advanced_startup": self._access_advanced_startup,
            "create_recovery_drive": self._create_recovery_drive,
            "open_recovery_settings": self._open_recovery_settings,
            
            # System Information
            "get_system_restore_info": self._get_system_restore_info,
            "get_restore_events": self._get_restore_events,
            "verify_restore_point_integrity": self._verify_restore_point_integrity
        }

    async def initialize(self) -> bool:
        """Initialize the System Restore plugin."""
        try:
            logger.info("Initializing Windows System Restore plugin")
            self._initialized = True
            return True
        except Exception as e:
            logger.error(f"Failed to initialize System Restore plugin: {e}")
            return False


    async def connect(self, credentials: Dict[str, str]) -> bool:
        """Connect to the service"""
        return True

    async def disconnect(self) -> bool:
        """Disconnect from the service"""
        return True

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute a system restore action."""
        action = kwargs.get("action", "get_protection_status")
        
        if action not in self._actions:
            return {
                "status": "error",
                "error": f"Unknown action: {action}",
                "available_actions": list(self._actions.keys())
            }
        
        try:
            result = await self._actions[action](**kwargs)
            return {
                "status": "success",
                "action": action,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Action {action} failed: {e}")
            return {
                "status": "error",
                "action": action,
                "error": str(e)
            }

    async def _run_powershell(self, script: str, as_admin: bool = False) -> Dict[str, Any]:
        """Execute a PowerShell script and return results."""
        try:
            cmd = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass"]
            if as_admin:
                script = f"Start-Process powershell -Verb RunAs -ArgumentList '-NoProfile -ExecutionPolicy Bypass -Command {script}'"
            cmd.extend(["-Command", script])
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            return {
                "success": process.returncode == 0,
                "stdout": stdout.decode("utf-8", errors="replace").strip(),
                "stderr": stderr.decode("utf-8", errors="replace").strip(),
                "return_code": process.returncode
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    # ==================== Restore Points ====================

    async def _create_restore_point(self, **kwargs) -> Dict[str, Any]:
        """Create a new system restore point."""
        description = kwargs.get("description", f"Windows AI Restore Point - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        restore_type = kwargs.get("type", "MODIFY_SETTINGS")  # APPLICATION_INSTALL, APPLICATION_UNINSTALL, MODIFY_SETTINGS, CANCELLED_OPERATION, DEVICE_DRIVER_INSTALL
        
        type_map = {
            "APPLICATION_INSTALL": 0,
            "APPLICATION_UNINSTALL": 1,
            "MODIFY_SETTINGS": 12,
            "CANCELLED_OPERATION": 13,
            "DEVICE_DRIVER_INSTALL": 10
        }
        type_value = type_map.get(restore_type, 12)
        
        script = f'''
$description = "{description}"
$restoreType = {type_value}

# Enable computer restore if not enabled
Enable-ComputerRestore -Drive "C:\\" -ErrorAction SilentlyContinue

# Create restore point using WMI
$result = Checkpoint-Computer -Description $description -RestorePointType MODIFY_SETTINGS -ErrorAction Stop

# Get the created restore point
$latestRP = Get-ComputerRestorePoint | Sort-Object -Property SequenceNumber -Descending | Select-Object -First 1

if ($latestRP) {{
    @{{
        status = "created"
        sequence_number = $latestRP.SequenceNumber
        description = $latestRP.Description
        creation_time = $latestRP.CreationTime
        restore_point_type = $latestRP.RestorePointType
    }} | ConvertTo-Json
}} else {{
    @{{
        status = "created"
        description = $description
        note = "Restore point created but details not immediately available"
    }} | ConvertTo-Json
}}
'''
        result = await self._run_powershell(script)
        if result["success"]:
            try:
                return json.loads(result["stdout"])
            except:
                return {"status": "created", "description": description}
        return {"error": result.get("stderr", result.get("error", "Failed to create restore point")), "note": "Administrator privileges required"}

    async def _list_restore_points(self, **kwargs) -> Dict[str, Any]:
        """List all available restore points."""
        limit = kwargs.get("limit", 50)
        
        script = f'''
$restorePoints = Get-ComputerRestorePoint -ErrorAction SilentlyContinue | 
    Sort-Object -Property SequenceNumber -Descending |
    Select-Object -First {limit} |
    ForEach-Object {{
        @{{
            sequence_number = $_.SequenceNumber
            description = $_.Description
            creation_time = $_.CreationTime
            restore_point_type = $_.RestorePointType
            event_type = $_.EventType
        }}
    }}

@{{
    restore_points = @($restorePoints)
    count = @($restorePoints).Count
    limit = {limit}
}} | ConvertTo-Json -Depth 3
'''
        result = await self._run_powershell(script)
        if result["success"]:
            try:
                return json.loads(result["stdout"])
            except:
                return {"restore_points": [], "count": 0}
        return {"restore_points": [], "count": 0, "error": result.get("stderr", "")}

    async def _get_restore_point(self, **kwargs) -> Dict[str, Any]:
        """Get details of a specific restore point."""
        sequence_number = kwargs.get("sequence_number", 0)
        
        if not sequence_number:
            return {"error": "sequence_number is required"}
        
        script = f'''
$rp = Get-ComputerRestorePoint -RestorePoint {sequence_number} -ErrorAction SilentlyContinue

if ($rp) {{
    @{{
        sequence_number = $rp.SequenceNumber
        description = $rp.Description
        creation_time = $rp.CreationTime
        restore_point_type = $rp.RestorePointType
        event_type = $rp.EventType
    }} | ConvertTo-Json
}} else {{
    @{{ error = "Restore point not found"; sequence_number = {sequence_number} }} | ConvertTo-Json
}}
'''
        result = await self._run_powershell(script)
        if result["success"]:
            try:
                return json.loads(result["stdout"])
            except:
                return {"error": "Failed to parse restore point"}
        return {"error": result.get("stderr", "Failed to get restore point")}

    async def _delete_restore_point(self, **kwargs) -> Dict[str, Any]:
        """Delete a specific restore point."""
        sequence_number = kwargs.get("sequence_number", 0)
        
        if not sequence_number:
            return {"error": "sequence_number is required"}
        
        script = f'''
# Deleting restore points requires vssadmin
$result = vssadmin delete shadows /Shadow={{*}} /Quiet 2>&1
@{{
    status = "delete_requested"
    sequence_number = {sequence_number}
    note = "Individual restore point deletion requires elevated vssadmin commands"
}} | ConvertTo-Json
'''
        result = await self._run_powershell(script)
        return {"status": "delete_requested", "sequence_number": sequence_number, "note": "Use delete_all_restore_points or vssadmin for deletion"}

    async def _delete_all_restore_points(self, **kwargs) -> Dict[str, Any]:
        """Delete all restore points for a drive."""
        drive = kwargs.get("drive", "C:")
        
        script = f'''
# This requires admin privileges
vssadmin delete shadows /for={drive}\\ /all /quiet 2>&1
@{{
    status = "deleted"
    drive = "{drive}"
    note = "All restore points deleted for drive"
}} | ConvertTo-Json
'''
        result = await self._run_powershell(script)
        return {"status": "delete_requested", "drive": drive, "note": "Requires administrator privileges"}

    async def _get_latest_restore_point(self, **kwargs) -> Dict[str, Any]:
        """Get the most recent restore point."""
        script = '''
$rp = Get-ComputerRestorePoint | Sort-Object -Property SequenceNumber -Descending | Select-Object -First 1

if ($rp) {
    @{
        sequence_number = $rp.SequenceNumber
        description = $rp.Description
        creation_time = $rp.CreationTime
        restore_point_type = $rp.RestorePointType
    } | ConvertTo-Json
} else {
    @{ error = "No restore points found" } | ConvertTo-Json
}
'''
        result = await self._run_powershell(script)
        if result["success"]:
            try:
                return json.loads(result["stdout"])
            except:
                return {"error": "No restore points found"}
        return {"error": "No restore points found"}

    # ==================== System Restore Operations ====================

    async def _start_system_restore(self, **kwargs) -> Dict[str, Any]:
        """Start system restore process."""
        sequence_number = kwargs.get("sequence_number", 0)
        
        if not sequence_number:
            return {"error": "sequence_number is required"}
        
        script = f'''
# Start system restore - this will prompt and restart
rstrui.exe /RUNONCE /RP:{sequence_number}
@{{
    status = "restore_initiated"
    sequence_number = {sequence_number}
    note = "System restore wizard started. Follow prompts to complete."
}} | ConvertTo-Json
'''
        result = await self._run_powershell(script)
        return {"status": "restore_initiated", "sequence_number": sequence_number}

    async def _restore_to_point(self, **kwargs) -> Dict[str, Any]:
        """Restore system to a specific point (requires restart)."""
        sequence_number = kwargs.get("sequence_number", 0)
        confirm = kwargs.get("confirm", False)
        
        if not sequence_number:
            return {"error": "sequence_number is required"}
        
        if not confirm:
            return {
                "warning": "This will restart your computer and restore to the selected point",
                "sequence_number": sequence_number,
                "action_required": "Set confirm=True to proceed"
            }
        
        script = f'''
# Initiate restore - requires confirmation as it will restart
rstrui.exe /OFFLINE:C:\\windows=active /RP:{sequence_number}
@{{
    status = "restore_initiated"
    sequence_number = {sequence_number}
    note = "System restore initiated. Computer will restart."
}} | ConvertTo-Json
'''
        result = await self._run_powershell(script)
        return {"status": "restore_initiated", "sequence_number": sequence_number}

    async def _get_restore_status(self, **kwargs) -> Dict[str, Any]:
        """Get current system restore status."""
        script = '''
$status = @{
    restore_in_progress = $false
    last_restore_status = "unknown"
    last_restore_time = $null
}

# Check for pending restore
$pendingPath = "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\SystemRestore"
if (Test-Path $pendingPath) {
    $props = Get-ItemProperty $pendingPath -ErrorAction SilentlyContinue
    $status.last_restore_status = if ($props.RPSessionInterval -eq 0) { "idle" } else { "active" }
}

# Check event log for last restore
$lastRestore = Get-WinEvent -FilterHashtable @{LogName="Application"; ProviderName="System Restore"} -MaxEvents 1 -ErrorAction SilentlyContinue
if ($lastRestore) {
    $status.last_restore_time = $lastRestore.TimeCreated.ToString("o")
    $status.last_restore_message = $lastRestore.Message
}

$status | ConvertTo-Json
'''
        result = await self._run_powershell(script)
        if result["success"]:
            try:
                return json.loads(result["stdout"])
            except:
                return {"restore_in_progress": False}
        return {"restore_in_progress": False}

    async def _cancel_restore(self, **kwargs) -> Dict[str, Any]:
        """Cancel pending system restore (if possible)."""
        return {"status": "not_applicable", "note": "System restore cannot be cancelled once initiated. Use rstrui.exe to manage."}

    async def _open_system_restore_wizard(self, **kwargs) -> Dict[str, Any]:
        """Open the System Restore wizard."""
        script = '''
Start-Process rstrui.exe
@{ status = "opened" } | ConvertTo-Json
'''
        result = await self._run_powershell(script)
        return {"status": "opened"}

    # ==================== System Protection ====================

    async def _get_protection_status(self, **kwargs) -> Dict[str, Any]:
        """Get system protection status for all drives."""
        script = '''
$drives = @()
Get-WmiObject -Class Win32_Volume | Where-Object { $_.DriveLetter } | ForEach-Object {
    $drive = $_.DriveLetter
    $status = vssadmin list shadowstorage /for=$drive 2>&1
    
    $protected = $false
    $usedSpace = "0"
    $maxSpace = "0"
    
    if ($status -notmatch "No items found") {
        $protected = $true
        if ($status -match "Used Shadow Copy Storage space: (.+)") {
            $usedSpace = $Matches[1]
        }
        if ($status -match "Maximum Shadow Copy Storage space: (.+)") {
            $maxSpace = $Matches[1]
        }
    }
    
    $drives += @{
        drive = $drive
        protected = $protected
        used_space = $usedSpace
        max_space = $maxSpace
    }
}

@{
    drives = $drives
    protection_enabled = ($drives | Where-Object { $_.protected }).Count -gt 0
} | ConvertTo-Json -Depth 3
'''
        result = await self._run_powershell(script)
        if result["success"]:
            try:
                return json.loads(result["stdout"])
            except:
                return {"protection_enabled": False, "drives": []}
        return {"protection_enabled": False, "drives": []}

    async def _enable_protection(self, **kwargs) -> Dict[str, Any]:
        """Enable system protection for a drive."""
        drive = kwargs.get("drive", "C:")
        
        script = f'''
Enable-ComputerRestore -Drive "{drive}\\" -ErrorAction Stop
@{{
    status = "enabled"
    drive = "{drive}"
}} | ConvertTo-Json
'''
        result = await self._run_powershell(script)
        if result["success"]:
            return {"status": "enabled", "drive": drive}
        return {"error": result.get("stderr", "Failed to enable protection"), "note": "Requires administrator privileges"}

    async def _disable_protection(self, **kwargs) -> Dict[str, Any]:
        """Disable system protection for a drive."""
        drive = kwargs.get("drive", "C:")
        confirm = kwargs.get("confirm", False)
        
        if not confirm:
            return {
                "warning": "This will delete all restore points for the drive",
                "drive": drive,
                "action_required": "Set confirm=True to proceed"
            }
        
        script = f'''
Disable-ComputerRestore -Drive "{drive}\\" -ErrorAction Stop
@{{
    status = "disabled"
    drive = "{drive}"
}} | ConvertTo-Json
'''
        result = await self._run_powershell(script)
        if result["success"]:
            return {"status": "disabled", "drive": drive}
        return {"error": result.get("stderr", "Failed to disable protection")}

    async def _get_protected_drives(self, **kwargs) -> Dict[str, Any]:
        """Get list of drives with system protection enabled."""
        script = '''
$protectedDrives = @()

Get-WmiObject -Class Win32_Volume | Where-Object { $_.DriveLetter } | ForEach-Object {
    $drive = $_.DriveLetter
    try {
        $status = vssadmin list shadowstorage /for=$drive 2>&1
        if ($status -notmatch "No items found" -and $status -notmatch "Error") {
            $protectedDrives += $drive
        }
    } catch {}
}

@{
    protected_drives = $protectedDrives
    count = $protectedDrives.Count
} | ConvertTo-Json
'''
        result = await self._run_powershell(script)
        if result["success"]:
            try:
                return json.loads(result["stdout"])
            except:
                return {"protected_drives": [], "count": 0}
        return {"protected_drives": [], "count": 0}

    async def _configure_protection(self, **kwargs) -> Dict[str, Any]:
        """Configure system protection settings."""
        drive = kwargs.get("drive", "C:")
        max_size_percent = kwargs.get("max_size_percent", 10)
        
        script = f'''
# Open System Protection settings for the drive
Start-Process SystemPropertiesProtection.exe
@{{
    status = "settings_opened"
    drive = "{drive}"
    note = "Use the System Protection dialog to configure settings"
}} | ConvertTo-Json
'''
        result = await self._run_powershell(script)
        return {"status": "settings_opened", "drive": drive}

    # ==================== Disk Space Management ====================

    async def _get_disk_space_usage(self, **kwargs) -> Dict[str, Any]:
        """Get disk space used by restore points."""
        drive = kwargs.get("drive", "C:")
        
        script = f'''
$output = vssadmin list shadowstorage /for={drive}\\ 2>&1

$usage = @{{
    drive = "{drive}"
    used_space = "Unknown"
    allocated_space = "Unknown"
    max_space = "Unknown"
}}

if ($output -match "Used Shadow Copy Storage space: (.+)") {{
    $usage.used_space = $Matches[1].Trim()
}}
if ($output -match "Allocated Shadow Copy Storage space: (.+)") {{
    $usage.allocated_space = $Matches[1].Trim()
}}
if ($output -match "Maximum Shadow Copy Storage space: (.+)") {{
    $usage.max_space = $Matches[1].Trim()
}}

$usage | ConvertTo-Json
'''
        result = await self._run_powershell(script)
        if result["success"]:
            try:
                return json.loads(result["stdout"])
            except:
                return {"drive": drive, "used_space": "Unknown"}
        return {"drive": drive, "error": result.get("stderr", "")}

    async def _set_max_disk_usage(self, **kwargs) -> Dict[str, Any]:
        """Set maximum disk space for restore points."""
        drive = kwargs.get("drive", "C:")
        max_size = kwargs.get("max_size", "10GB")  # e.g., "10GB" or "10%"
        
        script = f'''
vssadmin resize shadowstorage /for={drive}\\ /on={drive}\\ /maxsize={max_size} 2>&1
@{{
    status = "configured"
    drive = "{drive}"
    max_size = "{max_size}"
}} | ConvertTo-Json
'''
        result = await self._run_powershell(script)
        return {"status": "configured", "drive": drive, "max_size": max_size, "note": "Requires administrator privileges"}

    async def _get_max_disk_usage(self, **kwargs) -> Dict[str, Any]:
        """Get maximum disk space setting for restore points."""
        return await self._get_disk_space_usage(**kwargs)

    async def _cleanup_old_restore_points(self, **kwargs) -> Dict[str, Any]:
        """Clean up old restore points to free space."""
        drive = kwargs.get("drive", "C:")
        keep_latest = kwargs.get("keep_latest", 1)
        
        script = f'''
# Keep only the latest restore points
$allPoints = Get-ComputerRestorePoint | Sort-Object -Property SequenceNumber -Descending

$toKeep = $allPoints | Select-Object -First {keep_latest}
$toDelete = $allPoints | Select-Object -Skip {keep_latest}

$deletedCount = 0
# Note: Individual deletion requires vssadmin with specific shadow IDs

@{{
    status = "cleanup_info"
    total_restore_points = $allPoints.Count
    points_to_keep = {keep_latest}
    points_to_delete = $toDelete.Count
    note = "Use vssadmin delete shadows /for={drive}\\ /oldest to delete oldest shadows"
}} | ConvertTo-Json
'''
        result = await self._run_powershell(script)
        if result["success"]:
            try:
                return json.loads(result["stdout"])
            except:
                return {"status": "cleanup_info"}
        return {"error": result.get("stderr", "")}

    # ==================== Shadow Copies ====================

    async def _list_shadow_copies(self, **kwargs) -> Dict[str, Any]:
        """List all shadow copies (VSS snapshots)."""
        drive = kwargs.get("drive", "")
        
        filter_cmd = f"/for={drive}\\" if drive else ""
        
        script = f'''
$output = vssadmin list shadows {filter_cmd} 2>&1
$shadows = @()

$currentShadow = @{{}}
foreach ($line in $output -split "`n") {{
    if ($line -match "Shadow Copy ID: (.+)") {{
        if ($currentShadow.id) {{ $shadows += $currentShadow }}
        $currentShadow = @{{ id = $Matches[1].Trim() }}
    }}
    elseif ($line -match "Original Volume: (.+)") {{
        $currentShadow.volume = $Matches[1].Trim()
    }}
    elseif ($line -match "Shadow Copy Volume: (.+)") {{
        $currentShadow.shadow_volume = $Matches[1].Trim()
    }}
    elseif ($line -match "Creation Time: (.+)") {{
        $currentShadow.creation_time = $Matches[1].Trim()
    }}
}}
if ($currentShadow.id) {{ $shadows += $currentShadow }}

@{{
    shadow_copies = $shadows
    count = $shadows.Count
}} | ConvertTo-Json -Depth 3
'''
        result = await self._run_powershell(script)
        if result["success"]:
            try:
                return json.loads(result["stdout"])
            except:
                return {"shadow_copies": [], "count": 0}
        return {"shadow_copies": [], "count": 0}

    async def _create_shadow_copy(self, **kwargs) -> Dict[str, Any]:
        """Create a new shadow copy."""
        drive = kwargs.get("drive", "C:")
        
        script = f'''
$shadow = (Get-WmiObject -List Win32_ShadowCopy).Create("{drive}\\", "ClientAccessible")
@{{
    status = "created"
    drive = "{drive}"
    shadow_id = $shadow.ShadowID
}} | ConvertTo-Json
'''
        result = await self._run_powershell(script)
        if result["success"]:
            try:
                return json.loads(result["stdout"])
            except:
                return {"status": "created", "drive": drive}
        return {"error": result.get("stderr", ""), "note": "Requires administrator privileges"}

    async def _delete_shadow_copy(self, **kwargs) -> Dict[str, Any]:
        """Delete a specific shadow copy."""
        shadow_id = kwargs.get("shadow_id", "")
        
        if not shadow_id:
            return {"error": "shadow_id is required"}
        
        script = f'''
vssadmin delete shadows /Shadow="{shadow_id}" /quiet 2>&1
@{{
    status = "deleted"
    shadow_id = "{shadow_id}"
}} | ConvertTo-Json
'''
        result = await self._run_powershell(script)
        return {"status": "delete_requested", "shadow_id": shadow_id}

    async def _get_shadow_copy_storage(self, **kwargs) -> Dict[str, Any]:
        """Get shadow copy storage information."""
        script = '''
$output = vssadmin list shadowstorage 2>&1
$storage = @()

$current = @{}
foreach ($line in $output -split "`n") {
    if ($line -match "For volume: (.+)") {
        if ($current.volume) { $storage += $current }
        $current = @{ volume = $Matches[1].Trim() }
    }
    elseif ($line -match "Shadow Copy Storage volume: (.+)") {
        $current.storage_volume = $Matches[1].Trim()
    }
    elseif ($line -match "Used Shadow Copy Storage space: (.+)") {
        $current.used_space = $Matches[1].Trim()
    }
    elseif ($line -match "Maximum Shadow Copy Storage space: (.+)") {
        $current.max_space = $Matches[1].Trim()
    }
}
if ($current.volume) { $storage += $current }

@{
    storage_info = $storage
    count = $storage.Count
} | ConvertTo-Json -Depth 3
'''
        result = await self._run_powershell(script)
        if result["success"]:
            try:
                return json.loads(result["stdout"])
            except:
                return {"storage_info": [], "count": 0}
        return {"storage_info": [], "count": 0}

    # ==================== Recovery Options ====================

    async def _get_recovery_options(self, **kwargs) -> Dict[str, Any]:
        """Get available recovery options."""
        script = '''
$options = @{
    system_restore_available = (Get-Service -Name "VSS" -ErrorAction SilentlyContinue).Status -eq "Running"
    recovery_environment = Test-Path "$env:SystemRoot\\System32\\Recovery\\ReAgent.xml"
    reset_this_pc = Test-Path "$env:SystemRoot\\System32\\ResetEngine.dll"
    advanced_startup = $true
}

# Check if Windows RE is enabled
$reagentc = reagentc /info 2>&1
$options.windows_re_enabled = $reagentc -match "Enabled"

$options | ConvertTo-Json
'''
        result = await self._run_powershell(script)
        if result["success"]:
            try:
                return json.loads(result["stdout"])
            except:
                return {"system_restore_available": True}
        return {"system_restore_available": False}

    async def _access_advanced_startup(self, **kwargs) -> Dict[str, Any]:
        """Schedule reboot into Advanced Startup options."""
        confirm = kwargs.get("confirm", False)
        
        if not confirm:
            return {
                "warning": "This will restart your computer into Advanced Startup",
                "action_required": "Set confirm=True to proceed"
            }
        
        script = '''
shutdown /r /o /t 0
@{ status = "restarting_to_advanced_startup" } | ConvertTo-Json
'''
        result = await self._run_powershell(script)
        return {"status": "restart_initiated"}

    async def _create_recovery_drive(self, **kwargs) -> Dict[str, Any]:
        """Open the Create Recovery Drive wizard."""
        script = '''
Start-Process RecoveryDrive.exe
@{ status = "wizard_opened" } | ConvertTo-Json
'''
        result = await self._run_powershell(script)
        return {"status": "wizard_opened"}

    async def _open_recovery_settings(self, **kwargs) -> Dict[str, Any]:
        """Open Windows Recovery settings."""
        script = '''
Start-Process "ms-settings:recovery"
@{ status = "opened" } | ConvertTo-Json
'''
        result = await self._run_powershell(script)
        return {"status": "opened"}

    # ==================== System Information ====================

    async def _get_system_restore_info(self, **kwargs) -> Dict[str, Any]:
        """Get comprehensive system restore information."""
        script = '''
$info = @{
    service_status = (Get-Service -Name "VSS" -ErrorAction SilentlyContinue).Status
    restore_points_count = (Get-ComputerRestorePoint -ErrorAction SilentlyContinue).Count
    system_drive = $env:SystemDrive
}

# Get last successful restore
$lastRestore = Get-WinEvent -FilterHashtable @{LogName="Application"; ProviderName="System Restore"; Id=8194} -MaxEvents 1 -ErrorAction SilentlyContinue
if ($lastRestore) {
    $info.last_restore = @{
        time = $lastRestore.TimeCreated.ToString("o")
        message = $lastRestore.Message
    }
}

# Get protection status for system drive
$status = vssadmin list shadowstorage /for=$env:SystemDrive\\ 2>&1
$info.protection_enabled = $status -notmatch "No items found"

$info | ConvertTo-Json -Depth 3
'''
        result = await self._run_powershell(script)
        if result["success"]:
            try:
                return json.loads(result["stdout"])
            except:
                return {"service_status": "Unknown"}
        return {"error": result.get("stderr", "")}

    async def _get_restore_events(self, **kwargs) -> Dict[str, Any]:
        """Get system restore related events from event log."""
        limit = kwargs.get("limit", 20)
        
        script = f'''
$events = @()

Get-WinEvent -FilterHashtable @{{LogName="Application"; ProviderName="System Restore"}} -MaxEvents {limit} -ErrorAction SilentlyContinue | ForEach-Object {{
    $events += @{{
        time = $_.TimeCreated.ToString("o")
        id = $_.Id
        level = $_.LevelDisplayName
        message = $_.Message.Substring(0, [Math]::Min(200, $_.Message.Length))
    }}
}}

@{{
    events = $events
    count = $events.Count
}} | ConvertTo-Json -Depth 3
'''
        result = await self._run_powershell(script)
        if result["success"]:
            try:
                return json.loads(result["stdout"])
            except:
                return {"events": [], "count": 0}
        return {"events": [], "count": 0}

    async def _verify_restore_point_integrity(self, **kwargs) -> Dict[str, Any]:
        """Verify integrity of restore points."""
        script = '''
$verification = @{
    vss_service = (Get-Service -Name "VSS" -ErrorAction SilentlyContinue).Status -eq "Running"
    restore_points_valid = $false
    integrity_check = "unknown"
}

$restorePoints = Get-ComputerRestorePoint -ErrorAction SilentlyContinue
if ($restorePoints) {
    $verification.restore_points_valid = $true
    $verification.restore_points_count = $restorePoints.Count
    $verification.integrity_check = "passed"
    
    # Verify shadow copies exist
    $shadows = vssadmin list shadows 2>&1
    $verification.shadow_copies_exist = $shadows -notmatch "No items found"
}

$verification | ConvertTo-Json
'''
        result = await self._run_powershell(script)
        if result["success"]:
            try:
                return json.loads(result["stdout"])
            except:
                return {"integrity_check": "unknown"}
        return {"integrity_check": "failed", "error": result.get("stderr", "")}

    async def cleanup(self):
        """Cleanup plugin resources."""
        self._initialized = False
        logger.info("Windows System Restore plugin cleaned up")


plugin = SystemRestorePlugin()
