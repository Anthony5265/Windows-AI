"""
Windows Update Plugin
Comprehensive Windows Update management capabilities
"""

import asyncio
import subprocess
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType


logger = logging.getLogger(__name__)


class WindowsUpdatePlugin(IntegrationPlugin):
    """
    Windows Update management plugin providing comprehensive update capabilities.
    
    Features:
    - Check for available updates
    - Download and install updates
    - View update history
    - Configure Windows Update settings
    - Manage update scheduling
    - Hide/unhide specific updates
    - Pause and resume updates
    - Restart management
    """
    
    def __init__(self):
        metadata = PluginMetadata(
            id="windows-update",
            name="Windows Update Plugin",
            description="Comprehensive Windows Update management",
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["windows", "update", "security", "patches", "system"],
            requirements=[]
        )
        super().__init__(metadata)
        
        self._actions = {
            # Update discovery
            "check_updates": self._check_updates,
            "list_available_updates": self._list_available_updates,
            "get_update_count": self._get_update_count,
            "search_updates": self._search_updates,
            
            # Update installation
            "download_updates": self._download_updates,
            "install_updates": self._install_updates,
            "install_specific_update": self._install_specific_update,
            "install_all_updates": self._install_all_updates,
            
            # Update history
            "get_update_history": self._get_update_history,
            "get_recent_updates": self._get_recent_updates,
            "get_failed_updates": self._get_failed_updates,
            "get_installed_updates": self._get_installed_updates,
            "uninstall_update": self._uninstall_update,
            
            # Update management
            "hide_update": self._hide_update,
            "unhide_update": self._unhide_update,
            "get_hidden_updates": self._get_hidden_updates,
            
            # Settings and configuration
            "get_update_settings": self._get_update_settings,
            "set_active_hours": self._set_active_hours,
            "get_active_hours": self._get_active_hours,
            "pause_updates": self._pause_updates,
            "resume_updates": self._resume_updates,
            "get_pause_status": self._get_pause_status,
            
            # Windows Update service
            "get_service_status": self._get_service_status,
            "start_service": self._start_service,
            "stop_service": self._stop_service,
            "restart_service": self._restart_service,
            
            # Restart management
            "get_restart_required": self._get_restart_required,
            "schedule_restart": self._schedule_restart,
            "cancel_scheduled_restart": self._cancel_scheduled_restart,
            "get_scheduled_restart": self._get_scheduled_restart,
            
            # Delivery Optimization
            "get_delivery_optimization": self._get_delivery_optimization,
            "set_delivery_optimization": self._set_delivery_optimization,
            "get_do_statistics": self._get_do_statistics,
            
            # WSUS configuration
            "get_wsus_settings": self._get_wsus_settings,
            "set_wsus_server": self._set_wsus_server,
            "clear_wsus_settings": self._clear_wsus_settings,
            
            # Diagnostics
            "run_troubleshooter": self._run_troubleshooter,
            "get_update_errors": self._get_update_errors,
            "clear_update_cache": self._clear_update_cache,
            "get_update_log": self._get_update_log,
        }
    
    async def initialize(self) -> bool:
        """Initialize the Windows Update plugin."""
        try:
            logger.info("Initializing Windows Update plugin")
            self._initialized = True
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Windows Update plugin: {e}")
            return False
    

    async def connect(self, credentials: Dict[str, str]) -> bool:
        """Connect to the service"""
        return True

    async def disconnect(self) -> bool:
        """Disconnect from the service"""
        return True

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute a Windows Update action."""
        action = kwargs.get("action", "check_updates")
        
        if action not in self._actions:
            return {
                "status": "error",
                "error": f"Unknown action: {action}",
                "available_actions": list(self._actions.keys())
            }
        
        try:
            result = await self._actions[action](**kwargs)
            return {"status": "success", "result": result}
        except Exception as e:
            logger.error(f"Windows Update action '{action}' failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _run_powershell(self, script: str) -> Dict[str, Any]:
        """Execute a PowerShell script and return results."""
        try:
            process = await asyncio.create_subprocess_exec(
                "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                "-Command", script,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            return {
                "success": process.returncode == 0,
                "output": stdout.decode("utf-8", errors="ignore").strip(),
                "error": stderr.decode("utf-8", errors="ignore").strip() if stderr else None,
                "return_code": process.returncode
            }
        except Exception as e:
            return {"success": False, "error": str(e), "output": ""}
    
    # Update Discovery Actions
    async def _check_updates(self, **kwargs) -> Dict[str, Any]:
        """Check for available Windows updates."""
        script = '''
        $UpdateSession = New-Object -ComObject Microsoft.Update.Session
        $UpdateSearcher = $UpdateSession.CreateUpdateSearcher()
        try {
            $SearchResult = $UpdateSearcher.Search("IsInstalled=0")
            $updates = @()
            foreach ($Update in $SearchResult.Updates) {
                $updates += @{
                    Title = $Update.Title
                    Description = $Update.Description
                    KB = ($Update.KBArticleIDs -join ", ")
                    Size = [math]::Round($Update.MaxDownloadSize / 1MB, 2)
                    IsMandatory = $Update.IsMandatory
                    IsDownloaded = $Update.IsDownloaded
                    Categories = @($Update.Categories | ForEach-Object { $_.Name })
                }
            }
            @{
                TotalUpdates = $SearchResult.Updates.Count
                Updates = $updates
            } | ConvertTo-Json -Depth 5
        } catch {
            @{ Error = $_.Exception.Message } | ConvertTo-Json
        }
        '''
        result = await self._run_powershell(script)
        if result["success"] and result["output"]:
            try:
                return json.loads(result["output"])
            except:
                return {"raw_output": result["output"]}
        return {"error": result.get("error", "Failed to check updates")}
    
    async def _list_available_updates(self, **kwargs) -> Dict[str, Any]:
        """List all available updates with details."""
        return await self._check_updates(**kwargs)
    
    async def _get_update_count(self, **kwargs) -> Dict[str, Any]:
        """Get count of available updates."""
        script = '''
        $UpdateSession = New-Object -ComObject Microsoft.Update.Session
        $UpdateSearcher = $UpdateSession.CreateUpdateSearcher()
        $SearchResult = $UpdateSearcher.Search("IsInstalled=0")
        @{
            TotalCount = $SearchResult.Updates.Count
            ImportantCount = ($SearchResult.Updates | Where-Object { $_.IsMandatory }).Count
            OptionalCount = ($SearchResult.Updates | Where-Object { -not $_.IsMandatory }).Count
        } | ConvertTo-Json
        '''
        result = await self._run_powershell(script)
        if result["success"] and result["output"]:
            try:
                return json.loads(result["output"])
            except:
                return {"raw_output": result["output"]}
        return {"error": result.get("error", "Failed to get update count")}
    
    async def _search_updates(self, **kwargs) -> Dict[str, Any]:
        """Search for specific updates by criteria."""
        criteria = kwargs.get("criteria", "IsInstalled=0")
        script = f'''
        $UpdateSession = New-Object -ComObject Microsoft.Update.Session
        $UpdateSearcher = $UpdateSession.CreateUpdateSearcher()
        $SearchResult = $UpdateSearcher.Search("{criteria}")
        $updates = @()
        foreach ($Update in $SearchResult.Updates) {{
            $updates += @{{
                Title = $Update.Title
                KB = ($Update.KBArticleIDs -join ", ")
                IsInstalled = $Update.IsInstalled
                IsDownloaded = $Update.IsDownloaded
                IsMandatory = $Update.IsMandatory
            }}
        }}
        $updates | ConvertTo-Json -Depth 3
        '''
        result = await self._run_powershell(script)
        if result["success"] and result["output"]:
            try:
                return json.loads(result["output"])
            except:
                return {"raw_output": result["output"]}
        return {"error": result.get("error", "Failed to search updates")}
    
    # Update Installation Actions
    async def _download_updates(self, **kwargs) -> Dict[str, Any]:
        """Download available updates without installing."""
        script = '''
        $UpdateSession = New-Object -ComObject Microsoft.Update.Session
        $UpdateSearcher = $UpdateSession.CreateUpdateSearcher()
        $SearchResult = $UpdateSearcher.Search("IsInstalled=0 and IsDownloaded=0")
        
        if ($SearchResult.Updates.Count -eq 0) {
            @{ Message = "No updates to download"; Count = 0 } | ConvertTo-Json
        } else {
            $UpdatesToDownload = New-Object -ComObject Microsoft.Update.UpdateColl
            foreach ($Update in $SearchResult.Updates) {
                $UpdatesToDownload.Add($Update) | Out-Null
            }
            $Downloader = $UpdateSession.CreateUpdateDownloader()
            $Downloader.Updates = $UpdatesToDownload
            $DownloadResult = $Downloader.Download()
            @{
                ResultCode = $DownloadResult.ResultCode
                Downloaded = $SearchResult.Updates.Count
                Message = switch ($DownloadResult.ResultCode) {
                    2 { "Download completed successfully" }
                    3 { "Download completed with errors" }
                    4 { "Download failed" }
                    5 { "Download aborted" }
                    default { "Unknown result" }
                }
            } | ConvertTo-Json
        }
        '''
        result = await self._run_powershell(script)
        if result["success"] and result["output"]:
            try:
                return json.loads(result["output"])
            except:
                return {"raw_output": result["output"]}
        return {"error": result.get("error", "Failed to download updates")}
    
    async def _install_updates(self, **kwargs) -> Dict[str, Any]:
        """Install downloaded updates."""
        accept_eula = kwargs.get("accept_eula", True)
        script = f'''
        $UpdateSession = New-Object -ComObject Microsoft.Update.Session
        $UpdateSearcher = $UpdateSession.CreateUpdateSearcher()
        $SearchResult = $UpdateSearcher.Search("IsInstalled=0 and IsDownloaded=1")
        
        if ($SearchResult.Updates.Count -eq 0) {{
            @{{ Message = "No downloaded updates to install"; Count = 0 }} | ConvertTo-Json
        }} else {{
            $UpdatesToInstall = New-Object -ComObject Microsoft.Update.UpdateColl
            foreach ($Update in $SearchResult.Updates) {{
                if ($Update.EulaAccepted -eq $false) {{
                    if ({str(accept_eula).lower()}) {{
                        $Update.AcceptEula()
                    }}
                }}
                $UpdatesToInstall.Add($Update) | Out-Null
            }}
            $Installer = $UpdateSession.CreateUpdateInstaller()
            $Installer.Updates = $UpdatesToInstall
            $InstallResult = $Installer.Install()
            @{{
                ResultCode = $InstallResult.ResultCode
                Installed = $SearchResult.Updates.Count
                RebootRequired = $InstallResult.RebootRequired
                Message = switch ($InstallResult.ResultCode) {{
                    2 {{ "Installation completed successfully" }}
                    3 {{ "Installation completed with errors" }}
                    4 {{ "Installation failed" }}
                    5 {{ "Installation aborted" }}
                    default {{ "Unknown result" }}
                }}
            }} | ConvertTo-Json
        }}
        '''
        result = await self._run_powershell(script)
        if result["success"] and result["output"]:
            try:
                return json.loads(result["output"])
            except:
                return {"raw_output": result["output"]}
        return {"error": result.get("error", "Failed to install updates")}
    
    async def _install_specific_update(self, **kwargs) -> Dict[str, Any]:
        """Install a specific update by KB number."""
        kb_number = kwargs.get("kb_number", "")
        if not kb_number:
            return {"error": "KB number is required"}
        
        script = f'''
        $UpdateSession = New-Object -ComObject Microsoft.Update.Session
        $UpdateSearcher = $UpdateSession.CreateUpdateSearcher()
        $SearchResult = $UpdateSearcher.Search("IsInstalled=0")
        
        $TargetUpdate = $SearchResult.Updates | Where-Object {{ 
            $_.KBArticleIDs -contains "{kb_number.replace('KB', '')}"
        }}
        
        if (-not $TargetUpdate) {{
            @{{ Error = "Update KB{kb_number.replace('KB', '')} not found" }} | ConvertTo-Json
        }} else {{
            $UpdatesToInstall = New-Object -ComObject Microsoft.Update.UpdateColl
            if ($TargetUpdate.EulaAccepted -eq $false) {{
                $TargetUpdate.AcceptEula()
            }}
            $UpdatesToInstall.Add($TargetUpdate) | Out-Null
            
            # Download if needed
            if (-not $TargetUpdate.IsDownloaded) {{
                $Downloader = $UpdateSession.CreateUpdateDownloader()
                $Downloader.Updates = $UpdatesToInstall
                $Downloader.Download()
            }}
            
            $Installer = $UpdateSession.CreateUpdateInstaller()
            $Installer.Updates = $UpdatesToInstall
            $InstallResult = $Installer.Install()
            @{{
                Update = $TargetUpdate.Title
                ResultCode = $InstallResult.ResultCode
                RebootRequired = $InstallResult.RebootRequired
                Success = $InstallResult.ResultCode -eq 2
            }} | ConvertTo-Json
        }}
        '''
        result = await self._run_powershell(script)
        if result["success"] and result["output"]:
            try:
                return json.loads(result["output"])
            except:
                return {"raw_output": result["output"]}
        return {"error": result.get("error", "Failed to install update")}
    
    async def _install_all_updates(self, **kwargs) -> Dict[str, Any]:
        """Download and install all available updates."""
        await self._download_updates(**kwargs)
        return await self._install_updates(**kwargs)
    
    # Update History Actions
    async def _get_update_history(self, **kwargs) -> Dict[str, Any]:
        """Get Windows Update history."""
        count = kwargs.get("count", 50)
        script = f'''
        $UpdateSession = New-Object -ComObject Microsoft.Update.Session
        $UpdateSearcher = $UpdateSession.CreateUpdateSearcher()
        $HistoryCount = $UpdateSearcher.GetTotalHistoryCount()
        $History = $UpdateSearcher.QueryHistory(0, [Math]::Min({count}, $HistoryCount))
        
        $updates = @()
        foreach ($entry in $History) {{
            $updates += @{{
                Title = $entry.Title
                Date = $entry.Date.ToString("yyyy-MM-dd HH:mm:ss")
                Operation = switch ($entry.Operation) {{
                    1 {{ "Installation" }}
                    2 {{ "Uninstallation" }}
                    default {{ "Unknown" }}
                }}
                ResultCode = switch ($entry.ResultCode) {{
                    0 {{ "Not Started" }}
                    1 {{ "In Progress" }}
                    2 {{ "Succeeded" }}
                    3 {{ "Succeeded with Errors" }}
                    4 {{ "Failed" }}
                    5 {{ "Aborted" }}
                    default {{ "Unknown" }}
                }}
                SupportUrl = $entry.SupportUrl
            }}
        }}
        @{{
            TotalHistory = $HistoryCount
            ReturnedCount = $History.Count
            Updates = $updates
        }} | ConvertTo-Json -Depth 3
        '''
        result = await self._run_powershell(script)
        if result["success"] and result["output"]:
            try:
                return json.loads(result["output"])
            except:
                return {"raw_output": result["output"]}
        return {"error": result.get("error", "Failed to get update history")}
    
    async def _get_recent_updates(self, **kwargs) -> Dict[str, Any]:
        """Get recently installed updates."""
        days = kwargs.get("days", 7)
        script = f'''
        Get-HotFix | Where-Object {{ $_.InstalledOn -gt (Get-Date).AddDays(-{days}) }} |
        Select-Object HotFixID, Description, InstalledOn, InstalledBy |
        ConvertTo-Json -Depth 2
        '''
        result = await self._run_powershell(script)
        if result["success"] and result["output"]:
            try:
                return json.loads(result["output"])
            except:
                return {"raw_output": result["output"]}
        return {"error": result.get("error", "Failed to get recent updates")}
    
    async def _get_failed_updates(self, **kwargs) -> Dict[str, Any]:
        """Get failed update attempts."""
        script = '''
        $UpdateSession = New-Object -ComObject Microsoft.Update.Session
        $UpdateSearcher = $UpdateSession.CreateUpdateSearcher()
        $HistoryCount = $UpdateSearcher.GetTotalHistoryCount()
        $History = $UpdateSearcher.QueryHistory(0, $HistoryCount)
        
        $failed = $History | Where-Object { $_.ResultCode -eq 4 } | Select-Object -First 20
        $updates = @()
        foreach ($entry in $failed) {
            $updates += @{
                Title = $entry.Title
                Date = $entry.Date.ToString("yyyy-MM-dd HH:mm:ss")
                HResult = $entry.HResult
            }
        }
        $updates | ConvertTo-Json -Depth 2
        '''
        result = await self._run_powershell(script)
        if result["success"] and result["output"]:
            try:
                return json.loads(result["output"])
            except:
                return {"raw_output": result["output"]}
        return {"error": result.get("error", "Failed to get failed updates")}
    
    async def _get_installed_updates(self, **kwargs) -> Dict[str, Any]:
        """Get list of installed updates (hotfixes)."""
        script = '''
        Get-HotFix | Select-Object HotFixID, Description, InstalledOn, InstalledBy |
        Sort-Object InstalledOn -Descending | ConvertTo-Json -Depth 2
        '''
        result = await self._run_powershell(script)
        if result["success"] and result["output"]:
            try:
                return json.loads(result["output"])
            except:
                return {"raw_output": result["output"]}
        return {"error": result.get("error", "Failed to get installed updates")}
    
    async def _uninstall_update(self, **kwargs) -> Dict[str, Any]:
        """Uninstall a specific update by KB number."""
        kb_number = kwargs.get("kb_number", "")
        if not kb_number:
            return {"error": "KB number is required"}
        
        kb_clean = kb_number.replace("KB", "")
        script = f'''
        $update = Get-HotFix -Id "KB{kb_clean}" -ErrorAction SilentlyContinue
        if ($update) {{
            wusa.exe /uninstall /kb:{kb_clean} /quiet /norestart
            @{{ Success = $true; Message = "Uninstall initiated for KB{kb_clean}" }} | ConvertTo-Json
        }} else {{
            @{{ Success = $false; Error = "Update KB{kb_clean} not found" }} | ConvertTo-Json
        }}
        '''
        result = await self._run_powershell(script)
        if result["success"] and result["output"]:
            try:
                return json.loads(result["output"])
            except:
                return {"raw_output": result["output"]}
        return {"error": result.get("error", "Failed to uninstall update")}
    
    # Update Management Actions
    async def _hide_update(self, **kwargs) -> Dict[str, Any]:
        """Hide a specific update to prevent installation."""
        kb_number = kwargs.get("kb_number", "")
        if not kb_number:
            return {"error": "KB number is required"}
        
        script = f'''
        $UpdateSession = New-Object -ComObject Microsoft.Update.Session
        $UpdateSearcher = $UpdateSession.CreateUpdateSearcher()
        $SearchResult = $UpdateSearcher.Search("IsInstalled=0")
        
        $kb = "{kb_number.replace('KB', '')}"
        $update = $SearchResult.Updates | Where-Object {{ $_.KBArticleIDs -contains $kb }}
        
        if ($update) {{
            $update.IsHidden = $true
            @{{ Success = $true; Message = "Update KB$kb hidden"; Title = $update.Title }} | ConvertTo-Json
        }} else {{
            @{{ Success = $false; Error = "Update KB$kb not found" }} | ConvertTo-Json
        }}
        '''
        result = await self._run_powershell(script)
        if result["success"] and result["output"]:
            try:
                return json.loads(result["output"])
            except:
                return {"raw_output": result["output"]}
        return {"error": result.get("error", "Failed to hide update")}
    
    async def _unhide_update(self, **kwargs) -> Dict[str, Any]:
        """Unhide a previously hidden update."""
        kb_number = kwargs.get("kb_number", "")
        if not kb_number:
            return {"error": "KB number is required"}
        
        script = f'''
        $UpdateSession = New-Object -ComObject Microsoft.Update.Session
        $UpdateSearcher = $UpdateSession.CreateUpdateSearcher()
        $SearchResult = $UpdateSearcher.Search("IsHidden=1")
        
        $kb = "{kb_number.replace('KB', '')}"
        $update = $SearchResult.Updates | Where-Object {{ $_.KBArticleIDs -contains $kb }}
        
        if ($update) {{
            $update.IsHidden = $false
            @{{ Success = $true; Message = "Update KB$kb unhidden"; Title = $update.Title }} | ConvertTo-Json
        }} else {{
            @{{ Success = $false; Error = "Hidden update KB$kb not found" }} | ConvertTo-Json
        }}
        '''
        result = await self._run_powershell(script)
        if result["success"] and result["output"]:
            try:
                return json.loads(result["output"])
            except:
                return {"raw_output": result["output"]}
        return {"error": result.get("error", "Failed to unhide update")}
    
    async def _get_hidden_updates(self, **kwargs) -> Dict[str, Any]:
        """Get list of hidden updates."""
        script = '''
        $UpdateSession = New-Object -ComObject Microsoft.Update.Session
        $UpdateSearcher = $UpdateSession.CreateUpdateSearcher()
        $SearchResult = $UpdateSearcher.Search("IsHidden=1")
        
        $updates = @()
        foreach ($Update in $SearchResult.Updates) {
            $updates += @{
                Title = $Update.Title
                KB = ($Update.KBArticleIDs -join ", ")
                Description = $Update.Description
            }
        }
        @{ Count = $SearchResult.Updates.Count; Updates = $updates } | ConvertTo-Json -Depth 3
        '''
        result = await self._run_powershell(script)
        if result["success"] and result["output"]:
            try:
                return json.loads(result["output"])
            except:
                return {"raw_output": result["output"]}
        return {"error": result.get("error", "Failed to get hidden updates")}
    
    # Settings Actions
    async def _get_update_settings(self, **kwargs) -> Dict[str, Any]:
        """Get Windows Update settings."""
        script = '''
        $AU = (New-Object -ComObject Microsoft.Update.AutoUpdate).Settings
        $settings = @{
            NotificationLevel = switch ($AU.NotificationLevel) {
                0 { "Not configured" }
                1 { "Disabled" }
                2 { "Notify before download" }
                3 { "Notify before install" }
                4 { "Scheduled install" }
                default { "Unknown" }
            }
            ScheduledInstallDay = $AU.ScheduledInstallationDay
            ScheduledInstallTime = $AU.ScheduledInstallationTime
            IncludeRecommendedUpdates = $AU.IncludeRecommendedUpdates
        }
        
        # Add registry-based settings
        $WUKey = "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate"
        $AUKey = "$WUKey\\AU"
        
        if (Test-Path $AUKey) {
            $settings.NoAutoUpdate = (Get-ItemProperty -Path $AUKey -Name "NoAutoUpdate" -ErrorAction SilentlyContinue).NoAutoUpdate
            $settings.AUOptions = (Get-ItemProperty -Path $AUKey -Name "AUOptions" -ErrorAction SilentlyContinue).AUOptions
        }
        
        $settings | ConvertTo-Json -Depth 2
        '''
        result = await self._run_powershell(script)
        if result["success"] and result["output"]:
            try:
                return json.loads(result["output"])
            except:
                return {"raw_output": result["output"]}
        return {"error": result.get("error", "Failed to get update settings")}
    
    async def _set_active_hours(self, **kwargs) -> Dict[str, Any]:
        """Set active hours to prevent restarts during work time."""
        start_hour = kwargs.get("start_hour", 8)
        end_hour = kwargs.get("end_hour", 17)
        
        script = f'''
        $key = "HKLM:\\SOFTWARE\\Microsoft\\WindowsUpdate\\UX\\Settings"
        Set-ItemProperty -Path $key -Name "ActiveHoursStart" -Value {start_hour} -Type DWord
        Set-ItemProperty -Path $key -Name "ActiveHoursEnd" -Value {end_hour} -Type DWord
        @{{ Success = $true; ActiveHoursStart = {start_hour}; ActiveHoursEnd = {end_hour} }} | ConvertTo-Json
        '''
        result = await self._run_powershell(script)
        if result["success"] and result["output"]:
            try:
                return json.loads(result["output"])
            except:
                return {"raw_output": result["output"]}
        return {"error": result.get("error", "Failed to set active hours")}
    
    async def _get_active_hours(self, **kwargs) -> Dict[str, Any]:
        """Get currently configured active hours."""
        script = '''
        $key = "HKLM:\\SOFTWARE\\Microsoft\\WindowsUpdate\\UX\\Settings"
        $start = (Get-ItemProperty -Path $key -Name "ActiveHoursStart" -ErrorAction SilentlyContinue).ActiveHoursStart
        $end = (Get-ItemProperty -Path $key -Name "ActiveHoursEnd" -ErrorAction SilentlyContinue).ActiveHoursEnd
        @{ ActiveHoursStart = $start; ActiveHoursEnd = $end } | ConvertTo-Json
        '''
        result = await self._run_powershell(script)
        if result["success"] and result["output"]:
            try:
                return json.loads(result["output"])
            except:
                return {"raw_output": result["output"]}
        return {"error": result.get("error", "Failed to get active hours")}
    
    async def _pause_updates(self, **kwargs) -> Dict[str, Any]:
        """Pause Windows Updates for specified days."""
        days = kwargs.get("days", 7)
        script = f'''
        $key = "HKLM:\\SOFTWARE\\Microsoft\\WindowsUpdate\\UX\\Settings"
        $pauseDate = (Get-Date).AddDays({days}).ToString("yyyy-MM-ddTHH:mm:ssZ")
        Set-ItemProperty -Path $key -Name "PauseUpdatesExpiryTime" -Value $pauseDate
        Set-ItemProperty -Path $key -Name "PauseFeatureUpdatesStartTime" -Value (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
        Set-ItemProperty -Path $key -Name "PauseQualityUpdatesStartTime" -Value (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
        Set-ItemProperty -Path $key -Name "PauseFeatureUpdatesEndTime" -Value $pauseDate
        Set-ItemProperty -Path $key -Name "PauseQualityUpdatesEndTime" -Value $pauseDate
        @{{ Success = $true; PausedUntil = $pauseDate; Days = {days} }} | ConvertTo-Json
        '''
        result = await self._run_powershell(script)
        if result["success"] and result["output"]:
            try:
                return json.loads(result["output"])
            except:
                return {"raw_output": result["output"]}
        return {"error": result.get("error", "Failed to pause updates")}
    
    async def _resume_updates(self, **kwargs) -> Dict[str, Any]:
        """Resume paused Windows Updates."""
        script = '''
        $key = "HKLM:\\SOFTWARE\\Microsoft\\WindowsUpdate\\UX\\Settings"
        Remove-ItemProperty -Path $key -Name "PauseUpdatesExpiryTime" -ErrorAction SilentlyContinue
        Remove-ItemProperty -Path $key -Name "PauseFeatureUpdatesStartTime" -ErrorAction SilentlyContinue
        Remove-ItemProperty -Path $key -Name "PauseQualityUpdatesStartTime" -ErrorAction SilentlyContinue
        Remove-ItemProperty -Path $key -Name "PauseFeatureUpdatesEndTime" -ErrorAction SilentlyContinue
        Remove-ItemProperty -Path $key -Name "PauseQualityUpdatesEndTime" -ErrorAction SilentlyContinue
        @{ Success = $true; Message = "Updates resumed" } | ConvertTo-Json
        '''
        result = await self._run_powershell(script)
        if result["success"] and result["output"]:
            try:
                return json.loads(result["output"])
            except:
                return {"raw_output": result["output"]}
        return {"error": result.get("error", "Failed to resume updates")}
    
    async def _get_pause_status(self, **kwargs) -> Dict[str, Any]:
        """Get current pause status for updates."""
        script = '''
        $key = "HKLM:\\SOFTWARE\\Microsoft\\WindowsUpdate\\UX\\Settings"
        $expiry = (Get-ItemProperty -Path $key -Name "PauseUpdatesExpiryTime" -ErrorAction SilentlyContinue).PauseUpdatesExpiryTime
        if ($expiry) {
            $expiryDate = [DateTime]::Parse($expiry)
            $isPaused = $expiryDate -gt (Get-Date)
            @{ 
                IsPaused = $isPaused
                PausedUntil = $expiry
                DaysRemaining = if ($isPaused) { [Math]::Ceiling(($expiryDate - (Get-Date)).TotalDays) } else { 0 }
            } | ConvertTo-Json
        } else {
            @{ IsPaused = $false; PausedUntil = $null; DaysRemaining = 0 } | ConvertTo-Json
        }
        '''
        result = await self._run_powershell(script)
        if result["success"] and result["output"]:
            try:
                return json.loads(result["output"])
            except:
                return {"raw_output": result["output"]}
        return {"error": result.get("error", "Failed to get pause status")}
    
    # Service Actions
    async def _get_service_status(self, **kwargs) -> Dict[str, Any]:
        """Get Windows Update service status."""
        script = '''
        $services = @("wuauserv", "bits", "cryptsvc", "msiserver")
        $status = @{}
        foreach ($svc in $services) {
            $s = Get-Service -Name $svc -ErrorAction SilentlyContinue
            if ($s) {
                $status[$svc] = @{
                    DisplayName = $s.DisplayName
                    Status = $s.Status.ToString()
                    StartType = $s.StartType.ToString()
                }
            }
        }
        $status | ConvertTo-Json -Depth 2
        '''
        result = await self._run_powershell(script)
        if result["success"] and result["output"]:
            try:
                return json.loads(result["output"])
            except:
                return {"raw_output": result["output"]}
        return {"error": result.get("error", "Failed to get service status")}
    
    async def _start_service(self, **kwargs) -> Dict[str, Any]:
        """Start Windows Update service."""
        script = '''
        Start-Service wuauserv -ErrorAction SilentlyContinue
        $status = (Get-Service wuauserv).Status.ToString()
        @{ Success = $status -eq "Running"; Status = $status } | ConvertTo-Json
        '''
        result = await self._run_powershell(script)
        if result["success"] and result["output"]:
            try:
                return json.loads(result["output"])
            except:
                return {"raw_output": result["output"]}
        return {"error": result.get("error", "Failed to start service")}
    
    async def _stop_service(self, **kwargs) -> Dict[str, Any]:
        """Stop Windows Update service."""
        script = '''
        Stop-Service wuauserv -Force -ErrorAction SilentlyContinue
        $status = (Get-Service wuauserv).Status.ToString()
        @{ Success = $status -eq "Stopped"; Status = $status } | ConvertTo-Json
        '''
        result = await self._run_powershell(script)
        if result["success"] and result["output"]:
            try:
                return json.loads(result["output"])
            except:
                return {"raw_output": result["output"]}
        return {"error": result.get("error", "Failed to stop service")}
    
    async def _restart_service(self, **kwargs) -> Dict[str, Any]:
        """Restart Windows Update service."""
        script = '''
        Restart-Service wuauserv -Force -ErrorAction SilentlyContinue
        $status = (Get-Service wuauserv).Status.ToString()
        @{ Success = $status -eq "Running"; Status = $status } | ConvertTo-Json
        '''
        result = await self._run_powershell(script)
        if result["success"] and result["output"]:
            try:
                return json.loads(result["output"])
            except:
                return {"raw_output": result["output"]}
        return {"error": result.get("error", "Failed to restart service")}
    
    # Restart Management
    async def _get_restart_required(self, **kwargs) -> Dict[str, Any]:
        """Check if a restart is required for pending updates."""
        script = '''
        $rebootPending = $false
        $reasons = @()
        
        # Check Component Based Servicing
        if (Test-Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Component Based Servicing\\RebootPending") {
            $rebootPending = $true
            $reasons += "Component Based Servicing"
        }
        
        # Check Windows Update
        if (Test-Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\WindowsUpdate\\Auto Update\\RebootRequired") {
            $rebootPending = $true
            $reasons += "Windows Update"
        }
        
        # Check Pending File Rename Operations
        $pfro = Get-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Session Manager" -Name "PendingFileRenameOperations" -ErrorAction SilentlyContinue
        if ($pfro.PendingFileRenameOperations) {
            $rebootPending = $true
            $reasons += "Pending File Rename Operations"
        }
        
        @{ RebootRequired = $rebootPending; Reasons = $reasons } | ConvertTo-Json
        '''
        result = await self._run_powershell(script)
        if result["success"] and result["output"]:
            try:
                return json.loads(result["output"])
            except:
                return {"raw_output": result["output"]}
        return {"error": result.get("error", "Failed to check restart status")}
    
    async def _schedule_restart(self, **kwargs) -> Dict[str, Any]:
        """Schedule a system restart."""
        delay_seconds = kwargs.get("delay_seconds", 300)
        script = f'''
        shutdown /r /t {delay_seconds} /c "Scheduled restart for Windows Updates"
        @{{ Success = $true; DelaySeconds = {delay_seconds}; Message = "Restart scheduled" }} | ConvertTo-Json
        '''
        result = await self._run_powershell(script)
        if result["success"] and result["output"]:
            try:
                return json.loads(result["output"])
            except:
                return {"raw_output": result["output"]}
        return {"error": result.get("error", "Failed to schedule restart")}
    
    async def _cancel_scheduled_restart(self, **kwargs) -> Dict[str, Any]:
        """Cancel a scheduled restart."""
        script = '''
        shutdown /a
        @{ Success = $true; Message = "Scheduled restart cancelled" } | ConvertTo-Json
        '''
        result = await self._run_powershell(script)
        if result["success"] and result["output"]:
            try:
                return json.loads(result["output"])
            except:
                return {"raw_output": result["output"]}
        return {"error": result.get("error", "Failed to cancel restart")}
    
    async def _get_scheduled_restart(self, **kwargs) -> Dict[str, Any]:
        """Get scheduled restart information."""
        script = '''
        $key = "HKLM:\\SOFTWARE\\Microsoft\\WindowsUpdate\\UX\\Settings"
        $scheduledReboot = Get-ItemProperty -Path $key -Name "PendingRebootStartTime" -ErrorAction SilentlyContinue
        if ($scheduledReboot.PendingRebootStartTime) {
            @{ Scheduled = $true; Time = $scheduledReboot.PendingRebootStartTime } | ConvertTo-Json
        } else {
            @{ Scheduled = $false } | ConvertTo-Json
        }
        '''
        result = await self._run_powershell(script)
        if result["success"] and result["output"]:
            try:
                return json.loads(result["output"])
            except:
                return {"raw_output": result["output"]}
        return {"error": result.get("error", "Failed to get scheduled restart")}
    
    # Delivery Optimization
    async def _get_delivery_optimization(self, **kwargs) -> Dict[str, Any]:
        """Get Delivery Optimization settings."""
        script = '''
        $DOConfig = Get-DeliveryOptimizationStatus -ErrorAction SilentlyContinue
        if ($DOConfig) {
            $DOConfig | Select-Object FileId, FileSize, TotalBytesDownloaded, 
                PercentPeerCaching, BytesFromPeers, BytesFromHttp, Status |
            ConvertTo-Json -Depth 2
        } else {
            @{ Message = "Delivery Optimization not available" } | ConvertTo-Json
        }
        '''
        result = await self._run_powershell(script)
        if result["success"] and result["output"]:
            try:
                return json.loads(result["output"])
            except:
                return {"raw_output": result["output"]}
        return {"error": result.get("error", "Failed to get DO settings")}
    
    async def _set_delivery_optimization(self, **kwargs) -> Dict[str, Any]:
        """Set Delivery Optimization mode."""
        mode = kwargs.get("mode", 1)  # 0=Off, 1=LAN, 2=Internet, 3=Internet+LAN
        script = f'''
        $key = "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\DeliveryOptimization"
        if (-not (Test-Path $key)) {{ New-Item -Path $key -Force | Out-Null }}
        Set-ItemProperty -Path $key -Name "DODownloadMode" -Value {mode} -Type DWord
        @{{ Success = $true; Mode = {mode}; ModeDescription = @("Off", "LAN only", "Internet", "LAN and Internet")[{mode}] }} | ConvertTo-Json
        '''
        result = await self._run_powershell(script)
        if result["success"] and result["output"]:
            try:
                return json.loads(result["output"])
            except:
                return {"raw_output": result["output"]}
        return {"error": result.get("error", "Failed to set DO mode")}
    
    async def _get_do_statistics(self, **kwargs) -> Dict[str, Any]:
        """Get Delivery Optimization statistics."""
        script = '''
        $stats = Get-DeliveryOptimizationPerfSnapThisMonth -ErrorAction SilentlyContinue
        if ($stats) {
            @{
                DownloadedBytes = $stats.DownloadedBytes
                UploadedBytes = $stats.UploadedBytes
                CacheServerBytes = $stats.CacheServerBytes
                LanBytes = $stats.LanBytes
                InternetBytes = $stats.InternetBytes
            } | ConvertTo-Json
        } else {
            @{ Message = "Statistics not available" } | ConvertTo-Json
        }
        '''
        result = await self._run_powershell(script)
        if result["success"] and result["output"]:
            try:
                return json.loads(result["output"])
            except:
                return {"raw_output": result["output"]}
        return {"error": result.get("error", "Failed to get DO statistics")}
    
    # WSUS Configuration
    async def _get_wsus_settings(self, **kwargs) -> Dict[str, Any]:
        """Get WSUS server settings."""
        script = '''
        $key = "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate"
        if (Test-Path $key) {
            $props = Get-ItemProperty -Path $key -ErrorAction SilentlyContinue
            @{
                WUServer = $props.WUServer
                WUStatusServer = $props.WUStatusServer
                UseWUServer = $props.UseWUServer
            } | ConvertTo-Json
        } else {
            @{ Configured = $false; Message = "WSUS not configured" } | ConvertTo-Json
        }
        '''
        result = await self._run_powershell(script)
        if result["success"] and result["output"]:
            try:
                return json.loads(result["output"])
            except:
                return {"raw_output": result["output"]}
        return {"error": result.get("error", "Failed to get WSUS settings")}
    
    async def _set_wsus_server(self, **kwargs) -> Dict[str, Any]:
        """Configure WSUS server."""
        server_url = kwargs.get("server_url", "")
        if not server_url:
            return {"error": "WSUS server URL is required"}
        
        script = f'''
        $key = "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate"
        $auKey = "$key\\AU"
        
        if (-not (Test-Path $key)) {{ New-Item -Path $key -Force | Out-Null }}
        if (-not (Test-Path $auKey)) {{ New-Item -Path $auKey -Force | Out-Null }}
        
        Set-ItemProperty -Path $key -Name "WUServer" -Value "{server_url}"
        Set-ItemProperty -Path $key -Name "WUStatusServer" -Value "{server_url}"
        Set-ItemProperty -Path $auKey -Name "UseWUServer" -Value 1 -Type DWord
        
        @{{ Success = $true; WUServer = "{server_url}" }} | ConvertTo-Json
        '''
        result = await self._run_powershell(script)
        if result["success"] and result["output"]:
            try:
                return json.loads(result["output"])
            except:
                return {"raw_output": result["output"]}
        return {"error": result.get("error", "Failed to set WSUS server")}
    
    async def _clear_wsus_settings(self, **kwargs) -> Dict[str, Any]:
        """Clear WSUS configuration to use Microsoft Update."""
        script = '''
        $key = "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate"
        if (Test-Path $key) {
            Remove-ItemProperty -Path $key -Name "WUServer" -ErrorAction SilentlyContinue
            Remove-ItemProperty -Path $key -Name "WUStatusServer" -ErrorAction SilentlyContinue
            Remove-ItemProperty -Path "$key\\AU" -Name "UseWUServer" -ErrorAction SilentlyContinue
        }
        @{ Success = $true; Message = "WSUS settings cleared" } | ConvertTo-Json
        '''
        result = await self._run_powershell(script)
        if result["success"] and result["output"]:
            try:
                return json.loads(result["output"])
            except:
                return {"raw_output": result["output"]}
        return {"error": result.get("error", "Failed to clear WSUS settings")}
    
    # Diagnostics
    async def _run_troubleshooter(self, **kwargs) -> Dict[str, Any]:
        """Run Windows Update troubleshooter."""
        script = '''
        Get-TroubleshootingPack -Path "C:\\Windows\\diagnostics\\system\\WindowsUpdate" | 
        Invoke-TroubleshootingPack -Unattended -Result result.xml
        @{ Success = $true; Message = "Troubleshooter completed" } | ConvertTo-Json
        '''
        result = await self._run_powershell(script)
        if result["success"] and result["output"]:
            try:
                return json.loads(result["output"])
            except:
                return {"raw_output": result["output"]}
        return {"error": result.get("error", "Failed to run troubleshooter")}
    
    async def _get_update_errors(self, **kwargs) -> Dict[str, Any]:
        """Get recent Windows Update errors from event log."""
        script = '''
        Get-WinEvent -FilterHashtable @{
            LogName = "System"
            ProviderName = "Microsoft-Windows-WindowsUpdateClient"
            Level = 2  # Error
        } -MaxEvents 20 -ErrorAction SilentlyContinue |
        Select-Object TimeCreated, Id, Message | ConvertTo-Json -Depth 2
        '''
        result = await self._run_powershell(script)
        if result["success"] and result["output"]:
            try:
                return json.loads(result["output"])
            except:
                return {"raw_output": result["output"]}
        return {"error": result.get("error", "Failed to get update errors")}
    
    async def _clear_update_cache(self, **kwargs) -> Dict[str, Any]:
        """Clear Windows Update cache."""
        script = '''
        Stop-Service wuauserv -Force -ErrorAction SilentlyContinue
        Stop-Service bits -Force -ErrorAction SilentlyContinue
        
        $cacheDir = "$env:windir\\SoftwareDistribution\\Download"
        $dataStoreDir = "$env:windir\\SoftwareDistribution\\DataStore"
        
        Remove-Item -Path "$cacheDir\\*" -Recurse -Force -ErrorAction SilentlyContinue
        Remove-Item -Path "$dataStoreDir\\*" -Recurse -Force -ErrorAction SilentlyContinue
        
        Start-Service bits -ErrorAction SilentlyContinue
        Start-Service wuauserv -ErrorAction SilentlyContinue
        
        @{ Success = $true; Message = "Update cache cleared" } | ConvertTo-Json
        '''
        result = await self._run_powershell(script)
        if result["success"] and result["output"]:
            try:
                return json.loads(result["output"])
            except:
                return {"raw_output": result["output"]}
        return {"error": result.get("error", "Failed to clear update cache")}
    
    async def _get_update_log(self, **kwargs) -> Dict[str, Any]:
        """Get Windows Update log."""
        lines = kwargs.get("lines", 100)
        script = f'''
        $logPath = "$env:TEMP\\WindowsUpdate.log"
        Get-WindowsUpdateLog -LogPath $logPath -ErrorAction SilentlyContinue
        if (Test-Path $logPath) {{
            Get-Content $logPath -Tail {lines}
        }} else {{
            "Windows Update log not available"
        }}
        '''
        result = await self._run_powershell(script)
        return {"log": result.get("output", "Log not available")}
    
    async def cleanup(self):
        """Cleanup plugin resources."""
        self._initialized = False
        logger.info("Windows Update plugin cleaned up")
