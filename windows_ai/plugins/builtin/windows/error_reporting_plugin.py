"""
Windows Error Reporting (WER) Integration - PRODUCTION
Manages Windows Error Reporting settings, crash reports, and WER configuration.
"""
import os
import asyncio
import json
from typing import Dict, Any, Optional, List
from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType
import logging

logger = logging.getLogger(__name__)

WER_REG_PATH = r"HKLM:\SOFTWARE\Microsoft\Windows\Windows Error Reporting"
WER_POLICY_PATH = r"HKLM:\SOFTWARE\Policies\Microsoft\Windows\Windows Error Reporting"
WER_STORE_PATH = r"%LOCALAPPDATA%\CrashDumps"


class WindowsErrorReportingPlugin(IntegrationPlugin):
    def __init__(self):
        metadata = PluginMetadata(
            id="windows_error_reporting",
            name="Windows Error Reporting",
            description=(
                "Manage Windows Error Reporting (WER) configuration, view and clear crash reports, "
                "configure reporting behavior, and manage crash dump settings."
            ),
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["windows", "wer", "crash", "error", "debugging", "reporting"],
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
            "get_reports": self._get_reports,
            "clear_reports": self._clear_reports,
            "configure_reporting": self._configure_reporting,
            "get_report_details": self._get_report_details,
            "disable_reporting": self._disable_reporting,
            "enable_reporting": self._enable_reporting,
            "list_crash_logs": self._list_crash_logs,
            "get_wer_config": self._get_wer_config,
            "set_dump_type": self._set_dump_type,
            "get_crash_dumps": self._get_crash_dumps,
            "clear_crash_dumps": self._clear_crash_dumps,
            "get_application_errors": self._get_application_errors,
        }

        handler = actions.get(action)
        if handler is None:
            return {"success": False, "error": f"Unknown action: {action}. Available: {list(actions)}"}
        return await handler(parameters)

    async def _run_ps(self, cmd: str, timeout: int = 30) -> Dict[str, Any]:
        try:
            process = await asyncio.create_subprocess_exec(
                "powershell", "-NoProfile", "-NonInteractive", "-Command", cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            return {
                "success": process.returncode == 0,
                "output": stdout.decode(errors="replace").strip(),
                "error": stderr.decode(errors="replace").strip(),
                "returncode": process.returncode,
            }
        except FileNotFoundError:
            return {"success": False, "error": "PowerShell not available on this system"}
        except asyncio.TimeoutError:
            return {"success": False, "error": "Command timed out"}
        except Exception as e:
            logger.error(f"PowerShell error: {e}")
            return {"success": False, "error": str(e)}

    async def _get_reports(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get list of Windows Error Reports."""
        limit = params.get("limit", 20)
        cmd = fr"""
$reports = @()
$werPath = "$env:LOCALAPPDATA\Microsoft\Windows\WER\ReportQueue"
$archivePath = "$env:LOCALAPPDATA\Microsoft\Windows\WER\ReportArchive"

foreach ($dir in @($werPath, $archivePath)) {{
    if (Test-Path $dir) {{
        Get-ChildItem -Path $dir -Directory -ErrorAction SilentlyContinue |
            Select-Object -First {limit} | ForEach-Object {{
            $reportFile = Join-Path $_.FullName 'Report.wer'
            $info = @{{
                'report_id' = $_.Name
                'path' = $_.FullName
                'created' = $_.CreationTime.ToString('o')
                'modified' = $_.LastWriteTime.ToString('o')
                'type' = if ($dir -like '*Queue*') {{ 'queued' }} else {{ 'archived' }}
                'size_bytes' = (Get-ChildItem $_.FullName -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
            }}
            if (Test-Path $reportFile) {{
                $content = Get-Content $reportFile -Raw -ErrorAction SilentlyContinue
                if ($content -match 'FaultingModule=(.+)') {{ $info['faulting_module'] = $Matches[1].Trim() }}
                if ($content -match 'AppName=(.+)') {{ $info['app_name'] = $Matches[1].Trim() }}
                if ($content -match 'AppVersion=(.+)') {{ $info['app_version'] = $Matches[1].Trim() }}
            }}
            $reports += $info
        }}
    }}
}}
@{{ 'reports' = $reports; 'count' = $reports.Count }} | ConvertTo-Json -Depth 3
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _clear_reports(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Clear Windows Error Reports from the queue and/or archive."""
        target = params.get("target", "both")  # "queue", "archive", or "both"
        cmd = r"""
$cleared = 0
$errors = @()
"""
        if target in ("queue", "both"):
            cmd += r"""
$werQueue = "$env:LOCALAPPDATA\Microsoft\Windows\WER\ReportQueue"
if (Test-Path $werQueue) {
    Get-ChildItem -Path $werQueue -Directory -ErrorAction SilentlyContinue | ForEach-Object {
        try { Remove-Item $_.FullName -Recurse -Force; $cleared++ } catch { $errors += $_.Exception.Message }
    }
}
"""
        if target in ("archive", "both"):
            cmd += r"""
$werArchive = "$env:LOCALAPPDATA\Microsoft\Windows\WER\ReportArchive"
if (Test-Path $werArchive) {
    Get-ChildItem -Path $werArchive -Directory -ErrorAction SilentlyContinue | ForEach-Object {
        try { Remove-Item $_.FullName -Recurse -Force; $cleared++ } catch { $errors += $_.Exception.Message }
    }
}
"""
        cmd += r"@{ 'cleared_count' = $cleared; 'errors' = $errors } | ConvertTo-Json"
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                pass
        return result

    async def _configure_reporting(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Configure Windows Error Reporting settings."""
        cmds = []
        if "consent" in params:
            # 0=Always ask, 1=Always send, 2=Send parameters, 3=Never send
            consent = int(params["consent"])
            cmds.append(
                f"Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\Windows Error Reporting\\Consent' "
                f"-Name 'DefaultConsent' -Value {consent} -Type DWord -Force"
            )
        if "queue_reporting_upload" in params:
            val = 1 if params["queue_reporting_upload"] else 0
            cmds.append(
                f"Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\Windows Error Reporting' "
                f"-Name 'AutoApproveOSDumps' -Value {val} -Type DWord -Force"
            )
        if "max_queue_count" in params:
            val = int(params["max_queue_count"])
            cmds.append(
                f"Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\Windows Error Reporting\\HeapControl' "
                f"-Name 'MaxQueueCount' -Value {val} -Type DWord -Force -ErrorAction SilentlyContinue"
            )
        if not cmds:
            return {"success": False, "error": "No valid configuration parameters provided"}
        cmd = "; ".join(cmds) + "; Write-Output 'Configuration applied'"
        return await self._run_ps(cmd)

    async def _get_report_details(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed information about a specific error report."""
        report_id = params.get("report_id")
        if not report_id:
            return {"success": False, "error": "Parameter 'report_id' is required"}
        safe_id = report_id.replace("'", "''").replace(";", "")
        cmd = fr"""
$found = $false
foreach ($baseDir in @("$env:LOCALAPPDATA\Microsoft\Windows\WER\ReportQueue",
                        "$env:LOCALAPPDATA\Microsoft\Windows\WER\ReportArchive")) {{
    $reportDir = Join-Path $baseDir '{safe_id}'
    if (Test-Path $reportDir) {{
        $found = $true
        $files = Get-ChildItem $reportDir -ErrorAction SilentlyContinue | Select-Object Name, Length, LastWriteTime
        $reportFile = Join-Path $reportDir 'Report.wer'
        $content = if (Test-Path $reportFile) {{ Get-Content $reportFile -Raw }} else {{ '' }}
        @{{
            'report_id' = '{safe_id}'
            'path' = $reportDir
            'files' = @($files | ForEach-Object {{ @{{ 'name'=$_.Name; 'size'=$_.Length; 'modified'=$_.LastWriteTime.ToString('o') }} }})
            'report_content' = $content
        }} | ConvertTo-Json -Depth 3
        break
    }}
}}
if (-not $found) {{ Write-Output '{{"error": "Report not found"}}' }}
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _disable_reporting(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Disable Windows Error Reporting."""
        cmd = r"""
$path = 'HKLM:\SOFTWARE\Microsoft\Windows\Windows Error Reporting'
Set-ItemProperty -Path $path -Name 'Disabled' -Value 1 -Type DWord -Force

$policyPath = 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\Windows Error Reporting'
if (-not (Test-Path $policyPath)) { New-Item -Path $policyPath -Force | Out-Null }
Set-ItemProperty -Path $policyPath -Name 'Disabled' -Value 1 -Type DWord -Force

Set-Service -Name 'WerSvc' -StartupType Disabled -ErrorAction SilentlyContinue
Stop-Service -Name 'WerSvc' -Force -ErrorAction SilentlyContinue
Write-Output 'Windows Error Reporting disabled'
"""
        return await self._run_ps(cmd)

    async def _enable_reporting(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Enable Windows Error Reporting."""
        cmd = r"""
$path = 'HKLM:\SOFTWARE\Microsoft\Windows\Windows Error Reporting'
Set-ItemProperty -Path $path -Name 'Disabled' -Value 0 -Type DWord -Force

$policyPath = 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\Windows Error Reporting'
if (Test-Path $policyPath) {
    Remove-ItemProperty -Path $policyPath -Name 'Disabled' -ErrorAction SilentlyContinue
}

Set-Service -Name 'WerSvc' -StartupType Manual -ErrorAction SilentlyContinue
Start-Service -Name 'WerSvc' -ErrorAction SilentlyContinue
Write-Output 'Windows Error Reporting enabled'
"""
        return await self._run_ps(cmd)

    async def _list_crash_logs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List crash-related events from the Windows Event Log."""
        limit = params.get("limit", 50)
        cmd = f"""
try {{
    $events = Get-WinEvent -FilterHashtable @{{LogName='Application'; Id=1000,1001,1002}} `
        -MaxEvents {limit} -ErrorAction SilentlyContinue |
        Select-Object TimeCreated, Id, LevelDisplayName, Message |
        ForEach-Object {{
            @{{
                'time' = $_.TimeCreated.ToString('o')
                'event_id' = $_.Id
                'level' = $_.LevelDisplayName
                'message_preview' = if ($_.Message) {{ $_.Message.Substring(0, [Math]::Min(200, $_.Message.Length)) }} else {{ '' }}
            }}
        }}
    @{{ 'crash_logs' = @($events); 'count' = @($events).Count }} | ConvertTo-Json -Depth 3
}} catch {{
    @{{ 'error' = $_.Exception.Message; 'crash_logs' = @() }} | ConvertTo-Json
}}
"""
        result = await self._run_ps(cmd, timeout=45)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _get_wer_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get current WER configuration from registry."""
        cmd = r"""
$result = @{}
$path = 'HKLM:\SOFTWARE\Microsoft\Windows\Windows Error Reporting'
if (Test-Path $path) {
    $props = Get-ItemProperty -Path $path -ErrorAction SilentlyContinue
    $result['disabled'] = $props.Disabled -eq 1
    $result['dont_send_additional_data'] = $props.DontSendAdditionalData -eq 1
    $result['log_always'] = $props.LoggingDisabled -ne 1
}
$consentPath = "$path\Consent"
if (Test-Path $consentPath) {
    $consent = (Get-ItemProperty -Path $consentPath -ErrorAction SilentlyContinue).DefaultConsent
    $result['default_consent'] = $consent
    $result['consent_name'] = switch ($consent) {
        0 { 'Always Ask' } 1 { 'Always Send' } 2 { 'Send Parameters' } 3 { 'Never Send' } default { 'Unknown' }
    }
}
$svc = Get-Service WerSvc -ErrorAction SilentlyContinue
$result['service_status'] = if ($svc) { $svc.Status.ToString() } else { 'not_found' }
$result | ConvertTo-Json -Depth 2
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _set_dump_type(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Configure crash dump type (0=None, 1=Mini, 2=Kernel, 3=Complete)."""
        dump_type = params.get("dump_type", 2)
        if dump_type not in (0, 1, 2, 3):
            return {"success": False, "error": "dump_type must be 0 (None), 1 (Mini), 2 (Kernel), or 3 (Complete)"}
        type_names = {0: "None", 1: "MiniDump", 2: "KernelDump", 3: "CompleteDump"}
        cmd = (
            f"Set-ItemProperty -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\CrashControl' "
            f"-Name 'CrashDumpEnabled' -Value {dump_type} -Type DWord -Force; "
            f"Write-Output 'Dump type set to {dump_type} ({type_names[dump_type]})'"
        )
        result = await self._run_ps(cmd)
        result["dump_type"] = dump_type
        result["dump_type_name"] = type_names[dump_type]
        return result

    async def _get_crash_dumps(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List crash dump files."""
        cmd = r"""
$dumps = @()
$paths = @("$env:SystemRoot\Minidump", "$env:LOCALAPPDATA\CrashDumps", $env:SystemRoot)
foreach ($path in $paths) {
    if (Test-Path $path) {
        Get-ChildItem -Path $path -Filter '*.dmp' -ErrorAction SilentlyContinue | ForEach-Object {
            $dumps += @{
                'name' = $_.Name
                'path' = $_.FullName
                'size_mb' = [math]::Round($_.Length / 1MB, 2)
                'created' = $_.CreationTime.ToString('o')
            }
        }
    }
}
@{ 'dumps' = $dumps; 'count' = $dumps.Count } | ConvertTo-Json -Depth 2
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _clear_crash_dumps(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete crash dump files."""
        cmd = r"""
$deleted = 0
$paths = @("$env:SystemRoot\Minidump", "$env:LOCALAPPDATA\CrashDumps")
foreach ($path in $paths) {
    if (Test-Path $path) {
        Get-ChildItem -Path $path -Filter '*.dmp' -ErrorAction SilentlyContinue | ForEach-Object {
            Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue
            $deleted++
        }
    }
}
Write-Output "Deleted $deleted crash dump files"
"""
        return await self._run_ps(cmd)

    async def _get_application_errors(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get application error events from event log."""
        limit = params.get("limit", 30)
        hours = params.get("hours", 24)
        cmd = f"""
try {{
    $since = (Get-Date).AddHours(-{hours})
    $events = Get-WinEvent -FilterHashtable @{{
        LogName = 'Application'
        Level = 2  # Error level
        StartTime = $since
    }} -MaxEvents {limit} -ErrorAction SilentlyContinue | ForEach-Object {{
        @{{
            'time' = $_.TimeCreated.ToString('o')
            'event_id' = $_.Id
            'provider' = $_.ProviderName
            'message' = if ($_.Message) {{ $_.Message.Substring(0, [Math]::Min(300, $_.Message.Length)) }} else {{ '' }}
        }}
    }}
    @{{ 'errors' = @($events); 'count' = @($events).Count; 'hours_back' = {hours} }} | ConvertTo-Json -Depth 3
}} catch {{
    @{{ 'error' = $_.Exception.Message; 'errors' = @() }} | ConvertTo-Json
}}
"""
        result = await self._run_ps(cmd, timeout=45)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def shutdown(self):
        self._initialized = False

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "actions": {
                "get_reports": {"description": "List WER reports", "params": {"limit": "int"}},
                "clear_reports": {"description": "Clear WER reports", "params": {"target": "queue|archive|both"}},
                "configure_reporting": {"description": "Configure WER settings"},
                "get_report_details": {"description": "Get details for a report", "params": {"report_id": "string"}},
                "disable_reporting": {"description": "Disable Windows Error Reporting"},
                "enable_reporting": {"description": "Enable Windows Error Reporting"},
                "list_crash_logs": {"description": "List crash events from event log", "params": {"limit": "int"}},
                "get_wer_config": {"description": "Get current WER configuration"},
                "set_dump_type": {"description": "Set crash dump type (0-3)", "params": {"dump_type": "int"}},
                "get_crash_dumps": {"description": "List crash dump files"},
                "clear_crash_dumps": {"description": "Delete crash dump files"},
                "get_application_errors": {"description": "Get app errors from event log", "params": {"limit": "int", "hours": "int"}},
            },
        }


plugin = WindowsErrorReportingPlugin()
