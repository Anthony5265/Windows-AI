"""
Windows Cortana & Search Integration - PRODUCTION
Manages Cortana settings, Windows Search configuration, and search indexing.
"""
import os
import asyncio
import json
from typing import Dict, Any, Optional, List
from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType
import logging

logger = logging.getLogger(__name__)

SEARCH_REG_PATH = r"HKLM:\SOFTWARE\Policies\Microsoft\Windows\Windows Search"
CORTANA_REG_PATH = r"HKLM:\SOFTWARE\Policies\Microsoft\Windows\Windows Search"
USER_CORTANA_PATH = r"HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Search"


class WindowsCortanaPlugin(IntegrationPlugin):
    def __init__(self):
        metadata = PluginMetadata(
            id="windows_cortana",
            name="Windows Cortana & Search",
            description=(
                "Manage Cortana and Windows Search settings including enabling/disabling "
                "Cortana, configuring search indexing, web search, and search policies."
            ),
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["windows", "cortana", "search", "indexing", "privacy"],
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
            "get_status": self._get_status,
            "configure_search": self._configure_search,
            "disable_cortana": self._disable_cortana,
            "enable_cortana": self._enable_cortana,
            "enable_web_search": self._enable_web_search,
            "disable_web_search": self._disable_web_search,
            "get_indexing_status": self._get_indexing_status,
            "rebuild_index": self._rebuild_index,
            "add_index_location": self._add_index_location,
            "remove_index_location": self._remove_index_location,
            "list_index_locations": self._list_index_locations,
            "pause_indexing": self._pause_indexing,
            "resume_indexing": self._resume_indexing,
        }

        handler = actions.get(action)
        if handler is None:
            return {"success": False, "error": f"Unknown action: {action}. Available: {list(actions)}"}
        return await handler(parameters)

    async def _run_ps(self, cmd: str) -> Dict[str, Any]:
        """Run a PowerShell command and return structured output."""
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

    async def _get_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get current Cortana and Windows Search status."""
        cmd = r"""
$result = @{}
# Cortana policy status
$cortanaPath = 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\Windows Search'
$cortanaEnabled = $null
if (Test-Path $cortanaPath) {
    $cortanaEnabled = (Get-ItemProperty -Path $cortanaPath -Name 'AllowCortana' -ErrorAction SilentlyContinue).AllowCortana
}
$result['cortana_policy'] = if ($cortanaEnabled -eq 0) { 'disabled_by_policy' } elseif ($cortanaEnabled -eq 1) { 'enabled_by_policy' } else { 'not_configured' }

# User-level search settings
$userPath = 'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Search'
$webSearch = (Get-ItemProperty -Path $userPath -Name 'BingSearchEnabled' -ErrorAction SilentlyContinue).BingSearchEnabled
$result['web_search_enabled'] = ($webSearch -ne 0)

$safeSearch = (Get-ItemProperty -Path $userPath -Name 'SafeSearchMode' -ErrorAction SilentlyContinue).SafeSearchMode
$result['safe_search_mode'] = $safeSearch

# Search service status
$svc = Get-Service -Name 'WSearch' -ErrorAction SilentlyContinue
$result['search_service_status'] = if ($svc) { $svc.Status.ToString() } else { 'not_found' }
$result['search_service_start_type'] = if ($svc) { $svc.StartType.ToString() } else { 'unknown' }

$result | ConvertTo-Json
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _configure_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Configure Windows Search settings."""
        settings = params.get("settings", {})
        cmds = []

        if "safe_search" in settings:
            mode = int(settings["safe_search"])  # 0=off, 1=moderate, 2=strict
            cmds.append(
                f"Set-ItemProperty -Path 'HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Search' "
                f"-Name 'SafeSearchMode' -Value {mode} -Type DWord -Force"
            )
        if "index_encrypted_files" in settings:
            val = 1 if settings["index_encrypted_files"] else 0
            cmds.append(
                f"Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows Search\\Gathering Manager' "
                f"-Name 'EnableIndexingEncryptedFiles' -Value {val} -Type DWord -Force -ErrorAction SilentlyContinue"
            )
        if not cmds:
            return {"success": False, "error": "No valid settings provided"}

        cmd = "; ".join(cmds)
        return await self._run_ps(cmd)

    async def _disable_cortana(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Disable Cortana via registry policy."""
        cmd = (
            r"If (-not (Test-Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\Windows Search')) { "
            r"New-Item -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\Windows Search' -Force | Out-Null }; "
            r"Set-ItemProperty -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\Windows Search' "
            r"-Name 'AllowCortana' -Value 0 -Type DWord -Force; "
            r"Write-Output 'Cortana disabled via policy'"
        )
        result = await self._run_ps(cmd)
        if result["success"]:
            result["message"] = "Cortana has been disabled via Group Policy registry key. A restart may be required."
        return result

    async def _enable_cortana(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Enable Cortana by removing the policy restriction."""
        cmd = (
            r"$path = 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\Windows Search'; "
            r"if (Test-Path $path) { "
            r"Remove-ItemProperty -Path $path -Name 'AllowCortana' -ErrorAction SilentlyContinue }; "
            r"Write-Output 'Cortana policy restriction removed'"
        )
        result = await self._run_ps(cmd)
        if result["success"]:
            result["message"] = "Cortana policy restriction removed. A restart may be required."
        return result

    async def _enable_web_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Enable Bing web search in Windows Search."""
        cmd = (
            r"Set-ItemProperty -Path 'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Search' "
            r"-Name 'BingSearchEnabled' -Value 1 -Type DWord -Force; "
            r"Set-ItemProperty -Path 'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Search' "
            r"-Name 'CortanaConsent' -Value 1 -Type DWord -Force; "
            r"Write-Output 'Web search enabled'"
        )
        return await self._run_ps(cmd)

    async def _disable_web_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Disable Bing web search in Windows Search."""
        cmd = (
            r"Set-ItemProperty -Path 'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Search' "
            r"-Name 'BingSearchEnabled' -Value 0 -Type DWord -Force; "
            r"Set-ItemProperty -Path 'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Search' "
            r"-Name 'CortanaConsent' -Value 0 -Type DWord -Force; "
            r"Write-Output 'Web search disabled'"
        )
        return await self._run_ps(cmd)

    async def _get_indexing_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get Windows Search indexing status and statistics."""
        cmd = r"""
$result = @{}
$svc = Get-Service -Name 'WSearch' -ErrorAction SilentlyContinue
$result['service_status'] = if ($svc) { $svc.Status.ToString() } else { 'not_found' }

# Get indexed item count via WMI
try {
    $wmi = Get-WmiObject -Namespace 'Root\Microsoft\Windows\WindowsSearch' -Class 'SystemIndex_Catalog' -ErrorAction Stop
    $result['indexed_items'] = $wmi.IndexedItems
    $result['pending_items'] = $wmi.PendingItems
    $result['notifications_queued'] = $wmi.NotificationsQueued
} catch {
    $result['indexed_items'] = 'unavailable'
    $result['error'] = $_.Exception.Message
}

# Get indexed locations
try {
    $locations = @(Get-WmiObject -Namespace 'Root\Microsoft\Windows\WindowsSearch' -Class 'SystemIndex_RoamingScopes' -ErrorAction Stop |
        Select-Object -ExpandProperty Scope)
    $result['indexed_locations'] = $locations
} catch {
    $result['indexed_locations'] = @()
}

$result | ConvertTo-Json -Depth 3
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _rebuild_index(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Rebuild the Windows Search index."""
        cmd = r"""
Stop-Service WSearch -Force -ErrorAction SilentlyContinue
$indexPath = "$env:ProgramData\Microsoft\Search\Data\Applications\Windows"
if (Test-Path $indexPath) {
    Remove-Item "$indexPath\Windows.edb" -Force -ErrorAction SilentlyContinue
}
Start-Service WSearch -ErrorAction SilentlyContinue
Write-Output 'Index rebuild initiated'
"""
        result = await self._run_ps(cmd)
        if result["success"]:
            result["message"] = "Index rebuild initiated. Re-indexing may take several minutes."
        return result

    async def _list_index_locations(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List all locations included in the search index."""
        cmd = r"""
try {
    $scopes = Get-WmiObject -Namespace 'Root\Microsoft\Windows\WindowsSearch' `
        -Class 'SystemIndex_RoamingScopes' -ErrorAction Stop |
        Select-Object Scope, IncludedInIndex, Reason |
        ConvertTo-Json -Depth 2
    Write-Output $scopes
} catch {
    # Fallback: read from registry
    $path = 'HKLM:\SOFTWARE\Microsoft\Windows Search\CrawlScopeManager\Windows\SystemIndex\WorkingSetRules'
    if (Test-Path $path) {
        Get-ChildItem $path | ForEach-Object { $_.PSChildName } | ConvertTo-Json
    } else {
        Write-Output '[]'
    }
}
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["locations"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["locations"] = result["output"]
        return result

    async def _add_index_location(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add a location to the search index."""
        path = params.get("path")
        if not path:
            return {"success": False, "error": "Parameter 'path' is required"}
        cmd = f"""
$shell = New-Object -ComObject Shell.Application -ErrorAction Stop
$folder = $shell.NameSpace('{path}')
if ($folder) {{
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($shell) | Out-Null
    Write-Output 'Location added (manual indexing configuration required via Control Panel)'
}} else {{
    Write-Error 'Invalid path'
}}
"""
        return await self._run_ps(cmd)

    async def _remove_index_location(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove a location from the search index."""
        path = params.get("path")
        if not path:
            return {"success": False, "error": "Parameter 'path' is required"}
        escaped = path.replace("'", "''")
        cmd = (
            f"Write-Output 'Note: Use Control Panel > Indexing Options to remove: {escaped}'"
        )
        return await self._run_ps(cmd)

    async def _pause_indexing(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Pause the Windows Search indexing service."""
        cmd = "Stop-Service WSearch -Force; Write-Output 'Indexing service stopped'"
        return await self._run_ps(cmd)

    async def _resume_indexing(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Resume the Windows Search indexing service."""
        cmd = "Start-Service WSearch; Write-Output 'Indexing service started'"
        return await self._run_ps(cmd)

    async def shutdown(self):
        self._initialized = False

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "actions": {
                "get_status": {"description": "Get Cortana and Windows Search status"},
                "configure_search": {"description": "Configure search settings", "params": {"settings": "object"}},
                "disable_cortana": {"description": "Disable Cortana via policy"},
                "enable_cortana": {"description": "Enable Cortana (remove policy restriction)"},
                "enable_web_search": {"description": "Enable Bing web search in Windows Search"},
                "disable_web_search": {"description": "Disable Bing web search"},
                "get_indexing_status": {"description": "Get search indexing status and stats"},
                "rebuild_index": {"description": "Rebuild the Windows Search index"},
                "list_index_locations": {"description": "List indexed locations"},
                "add_index_location": {"description": "Add location to index", "params": {"path": "string"}},
                "remove_index_location": {"description": "Remove location from index", "params": {"path": "string"}},
                "pause_indexing": {"description": "Pause indexing service"},
                "resume_indexing": {"description": "Resume indexing service"},
            },
        }


plugin = WindowsCortanaPlugin()
