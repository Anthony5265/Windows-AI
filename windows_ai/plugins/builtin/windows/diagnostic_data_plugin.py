"""
Windows Diagnostic Data & Telemetry Integration - PRODUCTION
Manages Windows diagnostic data levels, feedback frequency, activity history, and telemetry settings.
"""
import os
import asyncio
import json
from typing import Dict, Any, Optional, List
from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType
import logging

logger = logging.getLogger(__name__)

DIAG_REG_PATH = r"HKLM:\SOFTWARE\Policies\Microsoft\Windows\DataCollection"
TELEMETRY_REG_PATH = r"HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\DataCollection"
FEEDBACK_REG_PATH = r"HKCU:\SOFTWARE\Microsoft\Siuf\Rules"
ACTIVITY_REG_PATH = r"HKLM:\SOFTWARE\Policies\Microsoft\Windows\System"


class WindowsDiagnosticDataPlugin(IntegrationPlugin):
    DIAGNOSTIC_LEVELS = {
        0: "Security (Enterprise/EDU only)",
        1: "Basic",
        2: "Enhanced",
        3: "Full",
    }
    FEEDBACK_FREQUENCIES = {
        0: "Automatically",
        1: "Always",
        2: "Once a day",
        3: "Once a week",
        100: "Never",
    }

    def __init__(self):
        metadata = PluginMetadata(
            id="windows_diagnostic_data",
            name="Windows Diagnostic Data & Telemetry",
            description=(
                "Manage Windows telemetry and diagnostic data settings, feedback frequency, "
                "activity history, and privacy-related data collection controls."
            ),
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["windows", "privacy", "telemetry", "diagnostics", "data"],
        )
        super().__init__(metadata)
        self.connected = False

    async def initialize(self) -> bool:
        self._initialized = True
        return True

    async def connect(self, credentials: Dict[str, str]) -> bool:
        self.connected = True
        return True

    async def disconnect(self) -> bool:
        self.connected = False
        return True

    async def execute(self, action: str, parameters: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        if not self.connected:
            return {"success": False, "error": "Not connected"}

        actions = {
            "get_diagnostic_level": self._get_diagnostic_level,
            "set_diagnostic_level": self._set_diagnostic_level,
            "get_feedback_frequency": self._get_feedback_frequency,
            "set_feedback_frequency": self._set_feedback_frequency,
            "get_activity_history": self._get_activity_history,
            "clear_activity_history": self._clear_activity_history,
            "disable_activity_history": self._disable_activity_history,
            "enable_activity_history": self._enable_activity_history,
            "export_diagnostics": self._export_diagnostics,
            "get_telemetry_endpoints": self._get_telemetry_endpoints,
            "disable_telemetry": self._disable_telemetry,
        }

        handler = actions.get(action)
        if handler is None:
            return {"success": False, "error": f"Unknown action: {action}. Available: {list(actions)}"}
        return await handler(parameters)

    async def _run_ps(self, cmd: str) -> Dict[str, Any]:
        try:
            process = await asyncio.create_subprocess_exec(
                "powershell", "-NoProfile", "-NonInteractive", "-Command", cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)
            return {
                "success": process.returncode == 0,
                "output": stdout.decode(errors="replace").strip(),
                "error": stderr.decode(errors="replace").strip(),
                "returncode": process.returncode,
            }
        except FileNotFoundError:
            return {"success": False, "error": "PowerShell not available on this system"}
        except asyncio.TimeoutError:
            return {"success": False, "error": "PowerShell command timed out"}
        except Exception as e:
            logger.error(f"PowerShell execution error: {e}")
            return {"success": False, "error": str(e)}

    async def _get_diagnostic_level(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get current Windows diagnostic data collection level."""
        cmd = r"""
$result = @{}
# Check policy path first
$policyPath = 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\DataCollection'
$dataPath = 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\DataCollection'

$policyLevel = (Get-ItemProperty -Path $policyPath -Name 'AllowTelemetry' -ErrorAction SilentlyContinue).AllowTelemetry
$dataLevel = (Get-ItemProperty -Path $dataPath -Name 'AllowTelemetry' -ErrorAction SilentlyContinue).AllowTelemetry

$levels = @{0='Security (Enterprise only)'; 1='Basic'; 2='Enhanced'; 3='Full'}

$result['policy_level'] = $policyLevel
$result['policy_level_name'] = if ($policyLevel -ne $null) { $levels[$policyLevel] } else { 'not_configured' }
$result['data_level'] = $dataLevel
$result['data_level_name'] = if ($dataLevel -ne $null) { $levels[$dataLevel] } else { 'not_configured' }
$result['effective_level'] = if ($policyLevel -ne $null) { $policyLevel } else { $dataLevel }

# Check connected user experiences service
$svc = Get-Service -Name 'DiagTrack' -ErrorAction SilentlyContinue
$result['diagtrack_service'] = if ($svc) { $svc.Status.ToString() } else { 'not_found' }

$result | ConvertTo-Json
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _set_diagnostic_level(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set the Windows diagnostic data collection level (0-3)."""
        level = params.get("level")
        if level is None or not isinstance(level, int) or level not in range(4):
            return {
                "success": False,
                "error": "Parameter 'level' must be 0 (Security), 1 (Basic), 2 (Enhanced), or 3 (Full)",
            }
        level_names = {0: "Security", 1: "Basic", 2: "Enhanced", 3: "Full"}
        cmd = f"""
$policyPath = 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection'
if (-not (Test-Path $policyPath)) {{ New-Item -Path $policyPath -Force | Out-Null }}
Set-ItemProperty -Path $policyPath -Name 'AllowTelemetry' -Value {level} -Type DWord -Force

$dataPath = 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\DataCollection'
if (-not (Test-Path $dataPath)) {{ New-Item -Path $dataPath -Force | Out-Null }}
Set-ItemProperty -Path $dataPath -Name 'AllowTelemetry' -Value {level} -Type DWord -Force

Write-Output 'Diagnostic level set to {level} ({level_names[level]})'
"""
        result = await self._run_ps(cmd)
        result["level"] = level
        result["level_name"] = level_names[level]
        return result

    async def _get_feedback_frequency(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get Windows feedback notification frequency."""
        cmd = r"""
$result = @{}
$fbPath = 'HKCU:\SOFTWARE\Microsoft\Siuf\Rules'
if (Test-Path $fbPath) {
    $freq = (Get-ItemProperty -Path $fbPath -ErrorAction SilentlyContinue).NumberOfSIUFInPeriod
    $period = (Get-ItemProperty -Path $fbPath -ErrorAction SilentlyContinue).PeriodInNanoSeconds
    $result['feedback_count_in_period'] = $freq
    $result['period_nanoseconds'] = $period
} else {
    $result['feedback_count_in_period'] = $null
    $result['period_nanoseconds'] = $null
}
$policyPath = 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\DataCollection'
$policyFreq = (Get-ItemProperty -Path $policyPath -Name 'DoNotShowFeedbackNotifications' -ErrorAction SilentlyContinue).DoNotShowFeedbackNotifications
$result['policy_feedback_disabled'] = ($policyFreq -eq 1)
$result | ConvertTo-Json
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _set_feedback_frequency(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set or disable feedback notifications."""
        disable = params.get("disable", False)
        if disable:
            cmd = (
                r"$p = 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\DataCollection'; "
                r"if (-not (Test-Path $p)) { New-Item -Path $p -Force | Out-Null }; "
                r"Set-ItemProperty -Path $p -Name 'DoNotShowFeedbackNotifications' -Value 1 -Type DWord -Force; "
                r"Write-Output 'Feedback notifications disabled'"
            )
        else:
            cmd = (
                r"$p = 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\DataCollection'; "
                r"Remove-ItemProperty -Path $p -Name 'DoNotShowFeedbackNotifications' -ErrorAction SilentlyContinue; "
                r"Write-Output 'Feedback notifications re-enabled'"
            )
        return await self._run_ps(cmd)

    async def _get_activity_history(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get activity history settings and status."""
        cmd = r"""
$result = @{}
$path = 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\System'
$storeEnabled = (Get-ItemProperty -Path $path -Name 'EnableActivityFeed' -ErrorAction SilentlyContinue).EnableActivityFeed
$uploadEnabled = (Get-ItemProperty -Path $path -Name 'PublishUserActivities' -ErrorAction SilentlyContinue).PublishUserActivities
$result['activity_feed_enabled'] = ($storeEnabled -ne 0)
$result['upload_activities_enabled'] = ($uploadEnabled -ne 0)
$result['policy_store'] = $storeEnabled
$result['policy_upload'] = $uploadEnabled
$result | ConvertTo-Json
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _clear_activity_history(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Clear the Windows activity history."""
        cmd = r"""
# Clear activity history via Settings URI or direct DB
$dbPath = "$env:LOCALAPPDATA\ConnectedDevicesPlatform"
if (Test-Path $dbPath) {
    Get-ChildItem -Path $dbPath -Filter 'ActivitiesCache.db' -Recurse -ErrorAction SilentlyContinue |
        ForEach-Object { Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue }
    Write-Output 'Activity history cache cleared'
} else {
    Write-Output 'Activity history database not found'
}
"""
        result = await self._run_ps(cmd)
        if result["success"]:
            result["message"] = "Activity history cleared. Some entries may persist until next logon."
        return result

    async def _disable_activity_history(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Disable Windows activity history collection and upload."""
        cmd = r"""
$path = 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\System'
if (-not (Test-Path $path)) { New-Item -Path $path -Force | Out-Null }
Set-ItemProperty -Path $path -Name 'EnableActivityFeed' -Value 0 -Type DWord -Force
Set-ItemProperty -Path $path -Name 'PublishUserActivities' -Value 0 -Type DWord -Force
Set-ItemProperty -Path $path -Name 'UploadUserActivities' -Value 0 -Type DWord -Force
Write-Output 'Activity history disabled'
"""
        return await self._run_ps(cmd)

    async def _enable_activity_history(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Enable Windows activity history."""
        cmd = r"""
$path = 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\System'
if (-not (Test-Path $path)) { New-Item -Path $path -Force | Out-Null }
Set-ItemProperty -Path $path -Name 'EnableActivityFeed' -Value 1 -Type DWord -Force
Set-ItemProperty -Path $path -Name 'PublishUserActivities' -Value 1 -Type DWord -Force
Write-Output 'Activity history enabled'
"""
        return await self._run_ps(cmd)

    async def _export_diagnostics(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Export diagnostic information to a file or return as structured data."""
        output_path = params.get("output_path", "")
        cmd = r"""
$result = @{
    'os_version' = (Get-WmiObject Win32_OperatingSystem).Caption
    'build' = (Get-WmiObject Win32_OperatingSystem).BuildNumber
    'computer_name' = $env:COMPUTERNAME
    'last_boot' = (Get-WmiObject Win32_OperatingSystem).LastBootUpTime
    'telemetry_level' = (Get-ItemProperty 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\DataCollection' -Name 'AllowTelemetry' -ErrorAction SilentlyContinue).AllowTelemetry
    'diagtrack_status' = (Get-Service DiagTrack -ErrorAction SilentlyContinue).Status.ToString()
    'error_reporting' = (Get-Service WerSvc -ErrorAction SilentlyContinue).Status.ToString()
    'event_log_size' = (Get-WinEvent -ListLog Application -ErrorAction SilentlyContinue).MaximumSizeInBytes
}
$result | ConvertTo-Json -Depth 2
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                data = json.loads(result["output"])
                result["data"] = data
                if output_path:
                    with open(output_path, "w") as f:
                        json.dump(data, f, indent=2)
                    result["exported_to"] = output_path
            except (json.JSONDecodeError, OSError) as e:
                result["data"] = {"raw": result["output"]}
                result["export_error"] = str(e)
        return result

    async def _get_telemetry_endpoints(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get list of known Windows telemetry endpoints."""
        known_endpoints = [
            "vortex.data.microsoft.com",
            "settings-win.data.microsoft.com",
            "telemetry.microsoft.com",
            "watson.microsoft.com",
            "watson.telemetry.microsoft.com",
            "oca.telemetry.microsoft.com",
            "sqm.telemetry.microsoft.com",
        ]
        return {"success": True, "endpoints": known_endpoints, "count": len(known_endpoints)}

    async def _disable_telemetry(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Disable telemetry services and set minimum diagnostic level."""
        cmd = r"""
# Set diagnostic level to minimum
$policyPath = 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\DataCollection'
if (-not (Test-Path $policyPath)) { New-Item -Path $policyPath -Force | Out-Null }
Set-ItemProperty -Path $policyPath -Name 'AllowTelemetry' -Value 0 -Type DWord -Force

# Disable DiagTrack service
Set-Service -Name 'DiagTrack' -StartupType Disabled -ErrorAction SilentlyContinue
Stop-Service -Name 'DiagTrack' -Force -ErrorAction SilentlyContinue

# Disable dmwappushservice
Set-Service -Name 'dmwappushservice' -StartupType Disabled -ErrorAction SilentlyContinue
Stop-Service -Name 'dmwappushservice' -Force -ErrorAction SilentlyContinue

# Disable feedback notifications
Set-ItemProperty -Path $policyPath -Name 'DoNotShowFeedbackNotifications' -Value 1 -Type DWord -Force

Write-Output 'Telemetry disabled'
"""
        result = await self._run_ps(cmd)
        if result["success"]:
            result["message"] = "Telemetry services disabled and diagnostic level set to minimum."
        return result

    async def shutdown(self):
        self._initialized = False

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "actions": {
                "get_diagnostic_level": {"description": "Get current telemetry/diagnostic level"},
                "set_diagnostic_level": {"description": "Set diagnostic level", "params": {"level": "int (0-3)"}},
                "get_feedback_frequency": {"description": "Get feedback notification frequency"},
                "set_feedback_frequency": {"description": "Set feedback frequency", "params": {"disable": "bool"}},
                "get_activity_history": {"description": "Get activity history settings"},
                "clear_activity_history": {"description": "Clear activity history cache"},
                "disable_activity_history": {"description": "Disable activity history collection"},
                "enable_activity_history": {"description": "Enable activity history"},
                "export_diagnostics": {"description": "Export diagnostic info", "params": {"output_path": "string"}},
                "get_telemetry_endpoints": {"description": "List known telemetry endpoints"},
                "disable_telemetry": {"description": "Disable telemetry services and set minimum level"},
            },
        }


plugin = WindowsDiagnosticDataPlugin()
