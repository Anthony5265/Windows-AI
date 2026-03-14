"""
Windows Defender Plugin for Windows AI
Provides comprehensive antivirus and security management
"""

import asyncio
import logging
import subprocess
from typing import Any, Dict, Optional

from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType


class WindowsDefenderPlugin(IntegrationPlugin):
    """Plugin for Windows Defender/Windows Security management"""

    def __init__(self):
        metadata = PluginMetadata(
            id="windows-defender",
            name="Windows Defender",
            description="Manage Windows Defender antivirus and security features",
            version="1.0.0",
            author="Windows AI Team",
            category="security",
            platforms=["windows"],
            dependencies=[],
        )
        super().__init__(metadata)
        self.logger = logging.getLogger(__name__)
        self._actions = {
            # Status and info
            "status": self._get_status,
            "get_status": self._get_status,
            "get_computer_status": self._get_computer_status,
            "get_threat_detection_status": self._get_threat_detection_status,
            # Scanning
            "quick_scan": self._quick_scan,
            "full_scan": self._full_scan,
            "custom_scan": self._custom_scan,
            "offline_scan": self._offline_scan,
            "cancel_scan": self._cancel_scan,
            "get_scan_history": self._get_scan_history,
            # Real-time protection
            "get_realtime_protection": self._get_realtime_protection,
            "enable_realtime_protection": self._enable_realtime_protection,
            "disable_realtime_protection": self._disable_realtime_protection,
            # Threat management
            "get_threats": self._get_threats,
            "get_threat_history": self._get_threat_history,
            "remove_threat": self._remove_threat,
            "quarantine_threat": self._quarantine_threat,
            "restore_from_quarantine": self._restore_from_quarantine,
            "get_quarantine_items": self._get_quarantine_items,
            # Exclusions
            "get_exclusions": self._get_exclusions,
            "add_exclusion_path": self._add_exclusion_path,
            "add_exclusion_extension": self._add_exclusion_extension,
            "add_exclusion_process": self._add_exclusion_process,
            "remove_exclusion_path": self._remove_exclusion_path,
            "remove_exclusion_extension": self._remove_exclusion_extension,
            "remove_exclusion_process": self._remove_exclusion_process,
            # Definitions/signatures
            "get_definitions": self._get_definitions,
            "update_definitions": self._update_definitions,
            "get_definition_age": self._get_definition_age,
            # Preferences/settings
            "get_preferences": self._get_preferences,
            "set_scan_schedule": self._set_scan_schedule,
            "set_definition_update_schedule": self._set_definition_update_schedule,
            "enable_cloud_protection": self._enable_cloud_protection,
            "disable_cloud_protection": self._disable_cloud_protection,
            "set_submission_sample_consent": self._set_submission_sample_consent,
            # Controlled folder access
            "get_controlled_folder_access": self._get_controlled_folder_access,
            "enable_controlled_folder_access": self._enable_controlled_folder_access,
            "disable_controlled_folder_access": self._disable_controlled_folder_access,
            "get_protected_folders": self._get_protected_folders,
            "add_protected_folder": self._add_protected_folder,
            "remove_protected_folder": self._remove_protected_folder,
            "get_allowed_apps": self._get_allowed_apps,
            "add_allowed_app": self._add_allowed_app,
            "remove_allowed_app": self._remove_allowed_app,
            # Attack Surface Reduction
            "get_asr_rules": self._get_asr_rules,
            "set_asr_rule": self._set_asr_rule,
            "enable_asr_rule": self._enable_asr_rule,
            "disable_asr_rule": self._disable_asr_rule,
            # Exploit protection
            "get_exploit_protection": self._get_exploit_protection,
            "set_exploit_protection": self._set_exploit_protection,
            # Network protection
            "get_network_protection": self._get_network_protection,
            "enable_network_protection": self._enable_network_protection,
            "disable_network_protection": self._disable_network_protection,
            # PUA protection
            "get_pua_protection": self._get_pua_protection,
            "enable_pua_protection": self._enable_pua_protection,
            "disable_pua_protection": self._disable_pua_protection,
        }

    async def initialize(self) -> bool:
        """Initialize the plugin"""
        self.logger.info("Initializing Windows Defender plugin")
        return True


    async def connect(self, credentials: Dict[str, str]) -> bool:
        """Connect to the service"""
        return True

    async def disconnect(self) -> bool:
        """Disconnect from the service"""
        return True

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute Windows Defender operations"""
        action = kwargs.get("action", "status")
        params = kwargs.get("params", {})
        
        if action in self._actions:
            try:
                return await self._actions[action](**params)
            except Exception as e:
                self.logger.error(f"Error executing {action}: {e}")
                return {"success": False, "error": str(e)}
        else:
            return {"success": False, "error": f"Unknown action: {action}", "available_actions": list(self._actions.keys())}

    async def _run_powershell(self, command: str) -> Dict[str, Any]:
        """Run a PowerShell command and return results"""
        try:
            process = await asyncio.create_subprocess_exec(
                "powershell", "-NoProfile", "-Command", command,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return {"success": True, "output": stdout.decode("utf-8", errors="replace").strip()}
            else:
                return {"success": False, "error": stderr.decode("utf-8", errors="replace").strip()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Status and info
    async def _get_status(self, **kwargs) -> Dict[str, Any]:
        """Get Windows Defender overall status"""
        cmd = """
        $status = Get-MpComputerStatus
        [PSCustomObject]@{
            AntivirusEnabled = $status.AntivirusEnabled
            AntispywareEnabled = $status.AntispywareEnabled
            RealTimeProtectionEnabled = $status.RealTimeProtectionEnabled
            BehaviorMonitorEnabled = $status.BehaviorMonitorEnabled
            OnAccessProtectionEnabled = $status.OnAccessProtectionEnabled
            IoavProtectionEnabled = $status.IoavProtectionEnabled
            NISEnabled = $status.NISEnabled
            QuickScanAge = $status.QuickScanAge
            FullScanAge = $status.FullScanAge
            AntivirusSignatureAge = $status.AntivirusSignatureAge
            AntivirusSignatureLastUpdated = $status.AntivirusSignatureLastUpdated
            AntivirusSignatureVersion = $status.AntivirusSignatureVersion
            DefenderSignaturesOutOfDate = $status.DefenderSignaturesOutOfDate
        } | ConvertTo-Json
        """
        return await self._run_powershell(cmd)

    async def _get_computer_status(self, **kwargs) -> Dict[str, Any]:
        """Get full computer security status"""
        cmd = "Get-MpComputerStatus | ConvertTo-Json -Depth 3"
        return await self._run_powershell(cmd)

    async def _get_threat_detection_status(self, **kwargs) -> Dict[str, Any]:
        """Get threat detection status"""
        cmd = """
        $status = Get-MpComputerStatus
        [PSCustomObject]@{
            ThreatStatusID = $status.ThreatStatusID
            ThreatStatusErrorCode = $status.ThreatStatusErrorCode
            LastQuickScanSource = $status.LastQuickScanSource
            LastFullScanSource = $status.LastFullScanSource
            QuickScanStartTime = $status.QuickScanStartTime
            QuickScanEndTime = $status.QuickScanEndTime
            FullScanStartTime = $status.FullScanStartTime
            FullScanEndTime = $status.FullScanEndTime
        } | ConvertTo-Json
        """
        return await self._run_powershell(cmd)

    # Scanning
    async def _quick_scan(self, **kwargs) -> Dict[str, Any]:
        """Start a quick scan"""
        cmd = "Start-MpScan -ScanType QuickScan; Write-Output 'Quick scan started'"
        return await self._run_powershell(cmd)

    async def _full_scan(self, **kwargs) -> Dict[str, Any]:
        """Start a full system scan"""
        cmd = "Start-MpScan -ScanType FullScan; Write-Output 'Full scan started'"
        return await self._run_powershell(cmd)

    async def _custom_scan(self, path: str, **kwargs) -> Dict[str, Any]:
        """Scan a specific path"""
        cmd = f"Start-MpScan -ScanType CustomScan -ScanPath '{path}'; Write-Output 'Custom scan started for: {path}'"
        return await self._run_powershell(cmd)

    async def _offline_scan(self, **kwargs) -> Dict[str, Any]:
        """Start Windows Defender Offline scan (requires reboot)"""
        cmd = "Start-MpWDOScan; Write-Output 'Offline scan scheduled - computer will restart'"
        return await self._run_powershell(cmd)

    async def _cancel_scan(self, **kwargs) -> Dict[str, Any]:
        """Cancel current scan"""
        cmd = "Stop-MpScan; Write-Output 'Scan cancelled'"
        return await self._run_powershell(cmd)

    async def _get_scan_history(self, **kwargs) -> Dict[str, Any]:
        """Get scan history"""
        cmd = """
        $status = Get-MpComputerStatus
        [PSCustomObject]@{
            QuickScanStartTime = $status.QuickScanStartTime
            QuickScanEndTime = $status.QuickScanEndTime
            QuickScanAge = $status.QuickScanAge
            FullScanStartTime = $status.FullScanStartTime
            FullScanEndTime = $status.FullScanEndTime
            FullScanAge = $status.FullScanAge
            FullScanRequired = $status.FullScanRequired
        } | ConvertTo-Json
        """
        return await self._run_powershell(cmd)

    # Real-time protection
    async def _get_realtime_protection(self, **kwargs) -> Dict[str, Any]:
        """Get real-time protection status"""
        cmd = """
        $prefs = Get-MpPreference
        $status = Get-MpComputerStatus
        [PSCustomObject]@{
            RealTimeProtectionEnabled = $status.RealTimeProtectionEnabled
            DisableRealtimeMonitoring = $prefs.DisableRealtimeMonitoring
            DisableBehaviorMonitoring = $prefs.DisableBehaviorMonitoring
            DisableOnAccessProtection = $prefs.DisableOnAccessProtection
            DisableIOAVProtection = $prefs.DisableIOAVProtection
            DisableScriptScanning = $prefs.DisableScriptScanning
        } | ConvertTo-Json
        """
        return await self._run_powershell(cmd)

    async def _enable_realtime_protection(self, **kwargs) -> Dict[str, Any]:
        """Enable real-time protection"""
        cmd = "Set-MpPreference -DisableRealtimeMonitoring $false; Write-Output 'Real-time protection enabled'"
        return await self._run_powershell(cmd)

    async def _disable_realtime_protection(self, **kwargs) -> Dict[str, Any]:
        """Disable real-time protection (requires admin)"""
        cmd = "Set-MpPreference -DisableRealtimeMonitoring $true; Write-Output 'Real-time protection disabled'"
        return await self._run_powershell(cmd)

    # Threat management
    async def _get_threats(self, **kwargs) -> Dict[str, Any]:
        """Get detected threats"""
        cmd = "Get-MpThreat | ConvertTo-Json -Depth 3"
        result = await self._run_powershell(cmd)
        if result.get("output") == "":
            return {"success": True, "output": "[]", "message": "No active threats detected"}
        return result

    async def _get_threat_history(self, days: int = 30, **kwargs) -> Dict[str, Any]:
        """Get threat detection history"""
        cmd = f"""
        Get-MpThreatDetection | Where-Object {{ $_.InitialDetectionTime -gt (Get-Date).AddDays(-{days}) }} |
        Select-Object ThreatID, ThreatStatusID, InitialDetectionTime, LastThreatStatusChangeTime, 
                      ProcessName, DomainUser, Resources | ConvertTo-Json -Depth 3
        """
        result = await self._run_powershell(cmd)
        if result.get("output") == "":
            return {"success": True, "output": "[]", "message": f"No threats detected in the last {days} days"}
        return result

    async def _remove_threat(self, threat_id: str, **kwargs) -> Dict[str, Any]:
        """Remove a specific threat"""
        cmd = f"Remove-MpThreat -ThreatID {threat_id}; Write-Output 'Threat {threat_id} removed'"
        return await self._run_powershell(cmd)

    async def _quarantine_threat(self, threat_id: str, **kwargs) -> Dict[str, Any]:
        """Quarantine a specific threat"""
        cmd = f"""
        $threat = Get-MpThreat | Where-Object {{ $_.ThreatID -eq {threat_id} }}
        if ($threat) {{
            Set-MpPreference -ThreatIDDefaultAction_Ids {threat_id} -ThreatIDDefaultAction_Actions Quarantine
            Write-Output 'Threat {threat_id} quarantined'
        }} else {{
            Write-Error 'Threat not found'
        }}
        """
        return await self._run_powershell(cmd)

    async def _restore_from_quarantine(self, threat_id: str, **kwargs) -> Dict[str, Any]:
        """Restore an item from quarantine"""
        cmd = f"Restore-MpThreat -ThreatID {threat_id}; Write-Output 'Threat {threat_id} restored from quarantine'"
        return await self._run_powershell(cmd)

    async def _get_quarantine_items(self, **kwargs) -> Dict[str, Any]:
        """Get quarantined items"""
        cmd = """
        Get-MpThreat | Where-Object { $_.ThreatStatusID -eq 6 } |
        Select-Object ThreatID, ThreatName, Resources, InitialDetectionTime | ConvertTo-Json -Depth 3
        """
        result = await self._run_powershell(cmd)
        if result.get("output") == "":
            return {"success": True, "output": "[]", "message": "No quarantined items"}
        return result

    # Exclusions
    async def _get_exclusions(self, **kwargs) -> Dict[str, Any]:
        """Get all exclusions"""
        cmd = """
        $prefs = Get-MpPreference
        [PSCustomObject]@{
            ExclusionPath = $prefs.ExclusionPath
            ExclusionExtension = $prefs.ExclusionExtension
            ExclusionProcess = $prefs.ExclusionProcess
            ExclusionIpAddress = $prefs.ExclusionIpAddress
        } | ConvertTo-Json
        """
        return await self._run_powershell(cmd)

    async def _add_exclusion_path(self, path: str, **kwargs) -> Dict[str, Any]:
        """Add path exclusion"""
        cmd = f"Add-MpPreference -ExclusionPath '{path}'; Write-Output 'Path exclusion added: {path}'"
        return await self._run_powershell(cmd)

    async def _add_exclusion_extension(self, extension: str, **kwargs) -> Dict[str, Any]:
        """Add extension exclusion"""
        ext = extension.lstrip(".")
        cmd = f"Add-MpPreference -ExclusionExtension '.{ext}'; Write-Output 'Extension exclusion added: .{ext}'"
        return await self._run_powershell(cmd)

    async def _add_exclusion_process(self, process: str, **kwargs) -> Dict[str, Any]:
        """Add process exclusion"""
        cmd = f"Add-MpPreference -ExclusionProcess '{process}'; Write-Output 'Process exclusion added: {process}'"
        return await self._run_powershell(cmd)

    async def _remove_exclusion_path(self, path: str, **kwargs) -> Dict[str, Any]:
        """Remove path exclusion"""
        cmd = f"Remove-MpPreference -ExclusionPath '{path}'; Write-Output 'Path exclusion removed: {path}'"
        return await self._run_powershell(cmd)

    async def _remove_exclusion_extension(self, extension: str, **kwargs) -> Dict[str, Any]:
        """Remove extension exclusion"""
        ext = extension.lstrip(".")
        cmd = f"Remove-MpPreference -ExclusionExtension '.{ext}'; Write-Output 'Extension exclusion removed: .{ext}'"
        return await self._run_powershell(cmd)

    async def _remove_exclusion_process(self, process: str, **kwargs) -> Dict[str, Any]:
        """Remove process exclusion"""
        cmd = f"Remove-MpPreference -ExclusionProcess '{process}'; Write-Output 'Process exclusion removed: {process}'"
        return await self._run_powershell(cmd)

    # Definitions
    async def _get_definitions(self, **kwargs) -> Dict[str, Any]:
        """Get signature/definition info"""
        cmd = """
        $status = Get-MpComputerStatus
        [PSCustomObject]@{
            AntivirusSignatureVersion = $status.AntivirusSignatureVersion
            AntivirusSignatureAge = $status.AntivirusSignatureAge
            AntivirusSignatureLastUpdated = $status.AntivirusSignatureLastUpdated
            AntispywareSignatureVersion = $status.AntispywareSignatureVersion
            AntispywareSignatureAge = $status.AntispywareSignatureAge
            AntispywareSignatureLastUpdated = $status.AntispywareSignatureLastUpdated
            NISSignatureVersion = $status.NISSignatureVersion
            NISSignatureAge = $status.NISSignatureAge
            NISSignatureLastUpdated = $status.NISSignatureLastUpdated
            DefenderSignaturesOutOfDate = $status.DefenderSignaturesOutOfDate
        } | ConvertTo-Json
        """
        return await self._run_powershell(cmd)

    async def _update_definitions(self, **kwargs) -> Dict[str, Any]:
        """Update virus definitions"""
        cmd = "Update-MpSignature; Write-Output 'Definition update initiated'"
        return await self._run_powershell(cmd)

    async def _get_definition_age(self, **kwargs) -> Dict[str, Any]:
        """Get definition age in days"""
        cmd = """
        $status = Get-MpComputerStatus
        [PSCustomObject]@{
            AntivirusSignatureAge = $status.AntivirusSignatureAge
            AntispywareSignatureAge = $status.AntispywareSignatureAge
            NISSignatureAge = $status.NISSignatureAge
            OutOfDate = $status.DefenderSignaturesOutOfDate
        } | ConvertTo-Json
        """
        return await self._run_powershell(cmd)

    # Preferences
    async def _get_preferences(self, **kwargs) -> Dict[str, Any]:
        """Get all Defender preferences"""
        cmd = "Get-MpPreference | ConvertTo-Json -Depth 3"
        return await self._run_powershell(cmd)

    async def _set_scan_schedule(self, day: int = 0, time: str = "02:00", **kwargs) -> Dict[str, Any]:
        """Set scheduled scan (day: 0=daily, 1-7=Sun-Sat)"""
        cmd = f"""
        Set-MpPreference -ScanScheduleDay {day} -ScanScheduleTime {time}
        Write-Output 'Scan schedule set: Day={day}, Time={time}'
        """
        return await self._run_powershell(cmd)

    async def _set_definition_update_schedule(self, interval: int = 24, **kwargs) -> Dict[str, Any]:
        """Set definition update interval in hours"""
        cmd = f"""
        Set-MpPreference -SignatureUpdateInterval {interval}
        Write-Output 'Definition update interval set to {interval} hours'
        """
        return await self._run_powershell(cmd)

    async def _enable_cloud_protection(self, **kwargs) -> Dict[str, Any]:
        """Enable cloud-delivered protection"""
        cmd = """
        Set-MpPreference -MAPSReporting Advanced -SubmitSamplesConsent SendAllSamples
        Write-Output 'Cloud protection enabled'
        """
        return await self._run_powershell(cmd)

    async def _disable_cloud_protection(self, **kwargs) -> Dict[str, Any]:
        """Disable cloud-delivered protection"""
        cmd = """
        Set-MpPreference -MAPSReporting Disabled
        Write-Output 'Cloud protection disabled'
        """
        return await self._run_powershell(cmd)

    async def _set_submission_sample_consent(self, consent: str = "SendSafeSamples", **kwargs) -> Dict[str, Any]:
        """Set sample submission consent (AlwaysPrompt, SendSafeSamples, NeverSend, SendAllSamples)"""
        cmd = f"Set-MpPreference -SubmitSamplesConsent {consent}; Write-Output 'Sample consent set to: {consent}'"
        return await self._run_powershell(cmd)

    # Controlled folder access
    async def _get_controlled_folder_access(self, **kwargs) -> Dict[str, Any]:
        """Get controlled folder access status"""
        cmd = """
        $prefs = Get-MpPreference
        [PSCustomObject]@{
            EnableControlledFolderAccess = $prefs.EnableControlledFolderAccess
            ControlledFolderAccessProtectedFolders = $prefs.ControlledFolderAccessProtectedFolders
            ControlledFolderAccessAllowedApplications = $prefs.ControlledFolderAccessAllowedApplications
        } | ConvertTo-Json
        """
        return await self._run_powershell(cmd)

    async def _enable_controlled_folder_access(self, **kwargs) -> Dict[str, Any]:
        """Enable controlled folder access"""
        cmd = "Set-MpPreference -EnableControlledFolderAccess Enabled; Write-Output 'Controlled folder access enabled'"
        return await self._run_powershell(cmd)

    async def _disable_controlled_folder_access(self, **kwargs) -> Dict[str, Any]:
        """Disable controlled folder access"""
        cmd = "Set-MpPreference -EnableControlledFolderAccess Disabled; Write-Output 'Controlled folder access disabled'"
        return await self._run_powershell(cmd)

    async def _get_protected_folders(self, **kwargs) -> Dict[str, Any]:
        """Get protected folders list"""
        cmd = "(Get-MpPreference).ControlledFolderAccessProtectedFolders | ConvertTo-Json"
        return await self._run_powershell(cmd)

    async def _add_protected_folder(self, path: str, **kwargs) -> Dict[str, Any]:
        """Add protected folder"""
        cmd = f"Add-MpPreference -ControlledFolderAccessProtectedFolders '{path}'; Write-Output 'Protected folder added: {path}'"
        return await self._run_powershell(cmd)

    async def _remove_protected_folder(self, path: str, **kwargs) -> Dict[str, Any]:
        """Remove protected folder"""
        cmd = f"Remove-MpPreference -ControlledFolderAccessProtectedFolders '{path}'; Write-Output 'Protected folder removed: {path}'"
        return await self._run_powershell(cmd)

    async def _get_allowed_apps(self, **kwargs) -> Dict[str, Any]:
        """Get apps allowed through controlled folder access"""
        cmd = "(Get-MpPreference).ControlledFolderAccessAllowedApplications | ConvertTo-Json"
        return await self._run_powershell(cmd)

    async def _add_allowed_app(self, path: str, **kwargs) -> Dict[str, Any]:
        """Add app to controlled folder access allowed list"""
        cmd = f"Add-MpPreference -ControlledFolderAccessAllowedApplications '{path}'; Write-Output 'Allowed app added: {path}'"
        return await self._run_powershell(cmd)

    async def _remove_allowed_app(self, path: str, **kwargs) -> Dict[str, Any]:
        """Remove app from controlled folder access allowed list"""
        cmd = f"Remove-MpPreference -ControlledFolderAccessAllowedApplications '{path}'; Write-Output 'Allowed app removed: {path}'"
        return await self._run_powershell(cmd)

    # Attack Surface Reduction
    async def _get_asr_rules(self, **kwargs) -> Dict[str, Any]:
        """Get Attack Surface Reduction rules"""
        cmd = """
        $prefs = Get-MpPreference
        $rules = @{
            'BE9BA2D9-53EA-4CDC-84E5-9B1EEEE46550' = 'Block executable content from email client and webmail'
            'D4F940AB-401B-4EFC-AADC-AD5F3C50688A' = 'Block all Office applications from creating child processes'
            '3B576869-A4EC-4529-8536-B80A7769E899' = 'Block Office applications from creating executable content'
            '75668C1F-73B5-4CF0-BB93-3ECF5CB7CC84' = 'Block Office applications from injecting code into other processes'
            'D3E037E1-3EB8-44C8-A917-57927947596D' = 'Block JavaScript or VBScript from launching downloaded executable content'
            '5BEB7EFE-FD9A-4556-801D-275E5FFC04CC' = 'Block execution of potentially obfuscated scripts'
            '92E97FA1-2EDF-4476-BDD6-9DD0B4DDDC7B' = 'Block Win32 API calls from Office macros'
            '01443614-CD74-433A-B99E-2ECDC07BFC25' = 'Block executable files from running unless they meet a prevalence, age, or trusted list criterion'
            'C1DB55AB-C21A-4637-BB3F-A12568109D35' = 'Use advanced protection against ransomware'
            '9E6C4E1F-7D60-472F-BA1A-A39EF669E4B2' = 'Block credential stealing from the Windows local security authority subsystem (lsass.exe)'
            'D1E49AAC-8F56-4280-B9BA-993A6D77406C' = 'Block process creations originating from PSExec and WMI commands'
            'B2B3F03D-6A65-4F7B-A9C7-1C7EF74A9BA4' = 'Block untrusted and unsigned processes that run from USB'
            '26190899-1602-49E8-8B27-EB1D0A1CE869' = 'Block Office communication application from creating child processes'
            '7674BA52-37EB-4A4F-A9A1-F0F9A1619A2C' = 'Block Adobe Reader from creating child processes'
            'E6DB77E5-3DF2-4CF1-B95A-636979351E5B' = 'Block persistence through WMI event subscription'
        }
        $results = @()
        foreach ($rule in $rules.GetEnumerator()) {{
            $state = ($prefs.AttackSurfaceReductionRules_Ids -contains $rule.Key)
            $action = if ($state) {{ ($prefs.AttackSurfaceReductionRules_Actions[$prefs.AttackSurfaceReductionRules_Ids.IndexOf($rule.Key)]) }} else {{ 'NotConfigured' }}
            $results += [PSCustomObject]@{{
                RuleId = $rule.Key
                RuleName = $rule.Value
                Action = $action
            }}
        }}
        $results | ConvertTo-Json -Depth 3
        """
        return await self._run_powershell(cmd)

    async def _set_asr_rule(self, rule_id: str, action: int = 1, **kwargs) -> Dict[str, Any]:
        """Set ASR rule action (0=Disabled, 1=Block, 2=Audit, 6=Warn)"""
        cmd = f"Set-MpPreference -AttackSurfaceReductionRules_Ids {rule_id} -AttackSurfaceReductionRules_Actions {action}; Write-Output 'ASR rule {rule_id} set to action {action}'"
        return await self._run_powershell(cmd)

    async def _enable_asr_rule(self, rule_id: str, **kwargs) -> Dict[str, Any]:
        """Enable (block) ASR rule"""
        return await self._set_asr_rule(rule_id, 1)

    async def _disable_asr_rule(self, rule_id: str, **kwargs) -> Dict[str, Any]:
        """Disable ASR rule"""
        return await self._set_asr_rule(rule_id, 0)

    # Exploit protection
    async def _get_exploit_protection(self, **kwargs) -> Dict[str, Any]:
        """Get exploit protection settings"""
        cmd = "Get-ProcessMitigation -System | ConvertTo-Json -Depth 3"
        return await self._run_powershell(cmd)

    async def _set_exploit_protection(self, process: str, mitigation: str, enable: bool = True, **kwargs) -> Dict[str, Any]:
        """Set exploit protection for a process"""
        action = "Enable" if enable else "Disable"
        cmd = f"Set-ProcessMitigation -Name '{process}' -{action} {mitigation}; Write-Output 'Exploit protection {mitigation} {action.lower()}d for {process}'"
        return await self._run_powershell(cmd)

    # Network protection
    async def _get_network_protection(self, **kwargs) -> Dict[str, Any]:
        """Get network protection status"""
        cmd = """
        $prefs = Get-MpPreference
        [PSCustomObject]@{
            EnableNetworkProtection = $prefs.EnableNetworkProtection
        } | ConvertTo-Json
        """
        return await self._run_powershell(cmd)

    async def _enable_network_protection(self, **kwargs) -> Dict[str, Any]:
        """Enable network protection"""
        cmd = "Set-MpPreference -EnableNetworkProtection Enabled; Write-Output 'Network protection enabled'"
        return await self._run_powershell(cmd)

    async def _disable_network_protection(self, **kwargs) -> Dict[str, Any]:
        """Disable network protection"""
        cmd = "Set-MpPreference -EnableNetworkProtection Disabled; Write-Output 'Network protection disabled'"
        return await self._run_powershell(cmd)

    # PUA protection
    async def _get_pua_protection(self, **kwargs) -> Dict[str, Any]:
        """Get potentially unwanted application protection status"""
        cmd = """
        $prefs = Get-MpPreference
        [PSCustomObject]@{
            PUAProtection = $prefs.PUAProtection
        } | ConvertTo-Json
        """
        return await self._run_powershell(cmd)

    async def _enable_pua_protection(self, **kwargs) -> Dict[str, Any]:
        """Enable PUA protection"""
        cmd = "Set-MpPreference -PUAProtection Enabled; Write-Output 'PUA protection enabled'"
        return await self._run_powershell(cmd)

    async def _disable_pua_protection(self, **kwargs) -> Dict[str, Any]:
        """Disable PUA protection"""
        cmd = "Set-MpPreference -PUAProtection Disabled; Write-Output 'PUA protection disabled'"
        return await self._run_powershell(cmd)

    async def cleanup(self) -> None:
        """Cleanup plugin resources"""
        self.logger.info("Windows Defender plugin cleaned up")
