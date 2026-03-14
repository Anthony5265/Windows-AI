"""
Windows Event Log Plugin for Windows AI
Provides comprehensive event log reading and management
"""

import asyncio
import logging
import subprocess
from typing import Any, Dict, Optional, List

from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType


class EventLogPlugin(IntegrationPlugin):
    """Plugin for Windows Event Log management and querying"""

    def __init__(self):
        metadata = PluginMetadata(
            id="event-log",
            name="Event Log",
            description="Read and manage Windows Event Logs",
            version="1.0.0",
            author="Windows AI Team",
            category="system",
            platforms=["windows"],
            dependencies=[],
        )
        super().__init__(metadata)
        self.logger = logging.getLogger(__name__)
        self._actions = {
            # Log listing and info
            "list_logs": self._list_logs,
            "get_log_info": self._get_log_info,
            "get_log_configuration": self._get_log_configuration,
            # Event querying
            "get_events": self._get_events,
            "get_recent_events": self._get_recent_events,
            "get_events_by_id": self._get_events_by_id,
            "get_events_by_level": self._get_events_by_level,
            "get_events_by_source": self._get_events_by_source,
            "get_events_by_time": self._get_events_by_time,
            "search_events": self._search_events,
            # Common logs shortcuts
            "get_system_events": self._get_system_events,
            "get_application_events": self._get_application_events,
            "get_security_events": self._get_security_events,
            "get_setup_events": self._get_setup_events,
            "get_powershell_events": self._get_powershell_events,
            # Error/warning specific
            "get_errors": self._get_errors,
            "get_warnings": self._get_warnings,
            "get_critical_events": self._get_critical_events,
            # Log management
            "clear_log": self._clear_log,
            "export_log": self._export_log,
            "backup_log": self._backup_log,
            "set_log_size": self._set_log_size,
            "enable_log": self._enable_log,
            "disable_log": self._disable_log,
            # Event details
            "get_event_details": self._get_event_details,
            "get_event_xml": self._get_event_xml,
            # Statistics
            "get_log_statistics": self._get_log_statistics,
            "get_event_count_by_level": self._get_event_count_by_level,
            "get_top_event_sources": self._get_top_event_sources,
            # Custom queries
            "run_xpath_query": self._run_xpath_query,
            "get_forwarded_events": self._get_forwarded_events,
        }

    async def initialize(self) -> bool:
        """Initialize the plugin"""
        self.logger.info("Initializing Event Log plugin")
        return True


    async def connect(self, credentials: Dict[str, str]) -> bool:
        """Connect to the service"""
        return True

    async def disconnect(self) -> bool:
        """Disconnect from the service"""
        return True

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute event log operations"""
        action = kwargs.get("action", "list_logs")
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

    # Log listing and info
    async def _list_logs(self, **kwargs) -> Dict[str, Any]:
        """List all available event logs"""
        cmd = """
        Get-WinEvent -ListLog * -ErrorAction SilentlyContinue | 
        Select-Object LogName, LogMode, RecordCount, MaximumSizeInBytes, IsEnabled |
        Sort-Object RecordCount -Descending |
        ConvertTo-Json -Depth 2
        """
        return await self._run_powershell(cmd)

    async def _get_log_info(self, log_name: str = "System", **kwargs) -> Dict[str, Any]:
        """Get detailed information about a specific log"""
        cmd = f"""
        $log = Get-WinEvent -ListLog '{log_name}' -ErrorAction Stop
        [PSCustomObject]@{{
            LogName = $log.LogName
            LogType = $log.LogType
            LogMode = $log.LogMode
            IsEnabled = $log.IsEnabled
            RecordCount = $log.RecordCount
            FileSize = $log.FileSize
            MaximumSizeInBytes = $log.MaximumSizeInBytes
            LogFilePath = $log.LogFilePath
            LastAccessTime = $log.LastAccessTime
            LastWriteTime = $log.LastWriteTime
            OldestRecordNumber = $log.OldestRecordNumber
            ProviderNames = ($log.ProviderNames | Select-Object -First 20)
        }} | ConvertTo-Json -Depth 2
        """
        return await self._run_powershell(cmd)

    async def _get_log_configuration(self, log_name: str = "System", **kwargs) -> Dict[str, Any]:
        """Get log configuration settings"""
        cmd = f"""
        $log = Get-WinEvent -ListLog '{log_name}'
        [PSCustomObject]@{{
            LogName = $log.LogName
            LogMode = $log.LogMode
            IsEnabled = $log.IsEnabled
            MaximumSizeInBytes = $log.MaximumSizeInBytes
            LogFilePath = $log.LogFilePath
            SecurityDescriptor = $log.SecurityDescriptor
            AutoBackupLogFiles = $log.AutoBackupLogFiles
        }} | ConvertTo-Json
        """
        return await self._run_powershell(cmd)

    # Event querying
    async def _get_events(self, log_name: str = "System", max_events: int = 50, **kwargs) -> Dict[str, Any]:
        """Get events from a log"""
        cmd = f"""
        Get-WinEvent -LogName '{log_name}' -MaxEvents {max_events} -ErrorAction SilentlyContinue |
        Select-Object TimeCreated, Id, LevelDisplayName, ProviderName, Message |
        ConvertTo-Json -Depth 2
        """
        return await self._run_powershell(cmd)

    async def _get_recent_events(self, log_name: str = "System", hours: int = 24, max_events: int = 100, **kwargs) -> Dict[str, Any]:
        """Get events from the last N hours"""
        cmd = f"""
        $startTime = (Get-Date).AddHours(-{hours})
        Get-WinEvent -FilterHashtable @{{LogName='{log_name}'; StartTime=$startTime}} -MaxEvents {max_events} -ErrorAction SilentlyContinue |
        Select-Object TimeCreated, Id, LevelDisplayName, ProviderName, Message |
        ConvertTo-Json -Depth 2
        """
        return await self._run_powershell(cmd)

    async def _get_events_by_id(self, log_name: str = "System", event_id: int = 1, max_events: int = 50, **kwargs) -> Dict[str, Any]:
        """Get events with a specific ID"""
        cmd = f"""
        Get-WinEvent -FilterHashtable @{{LogName='{log_name}'; Id={event_id}}} -MaxEvents {max_events} -ErrorAction SilentlyContinue |
        Select-Object TimeCreated, Id, LevelDisplayName, ProviderName, Message |
        ConvertTo-Json -Depth 2
        """
        return await self._run_powershell(cmd)

    async def _get_events_by_level(self, log_name: str = "System", level: int = 2, max_events: int = 50, **kwargs) -> Dict[str, Any]:
        """Get events by level (1=Critical, 2=Error, 3=Warning, 4=Information)"""
        cmd = f"""
        Get-WinEvent -FilterHashtable @{{LogName='{log_name}'; Level={level}}} -MaxEvents {max_events} -ErrorAction SilentlyContinue |
        Select-Object TimeCreated, Id, LevelDisplayName, ProviderName, Message |
        ConvertTo-Json -Depth 2
        """
        return await self._run_powershell(cmd)

    async def _get_events_by_source(self, log_name: str = "System", source: str = "", max_events: int = 50, **kwargs) -> Dict[str, Any]:
        """Get events from a specific source/provider"""
        cmd = f"""
        Get-WinEvent -FilterHashtable @{{LogName='{log_name}'; ProviderName='{source}'}} -MaxEvents {max_events} -ErrorAction SilentlyContinue |
        Select-Object TimeCreated, Id, LevelDisplayName, ProviderName, Message |
        ConvertTo-Json -Depth 2
        """
        return await self._run_powershell(cmd)

    async def _get_events_by_time(self, log_name: str = "System", start_time: str = "", end_time: str = "", max_events: int = 100, **kwargs) -> Dict[str, Any]:
        """Get events in a time range"""
        time_filter = ""
        if start_time:
            time_filter += f"StartTime='{start_time}'; "
        if end_time:
            time_filter += f"EndTime='{end_time}'; "
        
        cmd = f"""
        Get-WinEvent -FilterHashtable @{{LogName='{log_name}'; {time_filter}}} -MaxEvents {max_events} -ErrorAction SilentlyContinue |
        Select-Object TimeCreated, Id, LevelDisplayName, ProviderName, Message |
        ConvertTo-Json -Depth 2
        """
        return await self._run_powershell(cmd)

    async def _search_events(self, log_name: str = "System", keyword: str = "", max_events: int = 50, **kwargs) -> Dict[str, Any]:
        """Search events by keyword in message"""
        cmd = f"""
        Get-WinEvent -LogName '{log_name}' -MaxEvents 1000 -ErrorAction SilentlyContinue |
        Where-Object {{ $_.Message -like '*{keyword}*' }} |
        Select-Object -First {max_events} TimeCreated, Id, LevelDisplayName, ProviderName, Message |
        ConvertTo-Json -Depth 2
        """
        return await self._run_powershell(cmd)

    # Common logs shortcuts
    async def _get_system_events(self, max_events: int = 50, **kwargs) -> Dict[str, Any]:
        """Get System log events"""
        return await self._get_events(log_name="System", max_events=max_events)

    async def _get_application_events(self, max_events: int = 50, **kwargs) -> Dict[str, Any]:
        """Get Application log events"""
        return await self._get_events(log_name="Application", max_events=max_events)

    async def _get_security_events(self, max_events: int = 50, **kwargs) -> Dict[str, Any]:
        """Get Security log events"""
        return await self._get_events(log_name="Security", max_events=max_events)

    async def _get_setup_events(self, max_events: int = 50, **kwargs) -> Dict[str, Any]:
        """Get Setup log events"""
        return await self._get_events(log_name="Setup", max_events=max_events)

    async def _get_powershell_events(self, max_events: int = 50, **kwargs) -> Dict[str, Any]:
        """Get PowerShell operational events"""
        return await self._get_events(log_name="Microsoft-Windows-PowerShell/Operational", max_events=max_events)

    # Error/warning specific
    async def _get_errors(self, log_name: str = "System", hours: int = 24, max_events: int = 100, **kwargs) -> Dict[str, Any]:
        """Get error events from the last N hours"""
        cmd = f"""
        $startTime = (Get-Date).AddHours(-{hours})
        Get-WinEvent -FilterHashtable @{{LogName='{log_name}'; Level=2; StartTime=$startTime}} -MaxEvents {max_events} -ErrorAction SilentlyContinue |
        Select-Object TimeCreated, Id, LevelDisplayName, ProviderName, Message |
        ConvertTo-Json -Depth 2
        """
        return await self._run_powershell(cmd)

    async def _get_warnings(self, log_name: str = "System", hours: int = 24, max_events: int = 100, **kwargs) -> Dict[str, Any]:
        """Get warning events from the last N hours"""
        cmd = f"""
        $startTime = (Get-Date).AddHours(-{hours})
        Get-WinEvent -FilterHashtable @{{LogName='{log_name}'; Level=3; StartTime=$startTime}} -MaxEvents {max_events} -ErrorAction SilentlyContinue |
        Select-Object TimeCreated, Id, LevelDisplayName, ProviderName, Message |
        ConvertTo-Json -Depth 2
        """
        return await self._run_powershell(cmd)

    async def _get_critical_events(self, log_name: str = "System", hours: int = 168, max_events: int = 50, **kwargs) -> Dict[str, Any]:
        """Get critical events from the last N hours (default 1 week)"""
        cmd = f"""
        $startTime = (Get-Date).AddHours(-{hours})
        Get-WinEvent -FilterHashtable @{{LogName='{log_name}'; Level=1; StartTime=$startTime}} -MaxEvents {max_events} -ErrorAction SilentlyContinue |
        Select-Object TimeCreated, Id, LevelDisplayName, ProviderName, Message |
        ConvertTo-Json -Depth 2
        """
        return await self._run_powershell(cmd)

    # Log management
    async def _clear_log(self, log_name: str = "", **kwargs) -> Dict[str, Any]:
        """Clear an event log (requires admin)"""
        if not log_name:
            return {"success": False, "error": "log_name is required"}
        cmd = f"wevtutil cl '{log_name}'; Write-Output 'Log {log_name} cleared'"
        return await self._run_powershell(cmd)

    async def _export_log(self, log_name: str = "System", path: str = "", **kwargs) -> Dict[str, Any]:
        """Export log to file"""
        if not path:
            safe_name = log_name.replace('/', '_')
            path = f"$env:TEMP\\{safe_name}_$(Get-Date -Format 'yyyyMMdd_HHmmss').evtx"
        cmd = f"""
        $exportPath = "{path}"
        wevtutil epl '{log_name}' $exportPath
        Write-Output "Log exported to: $exportPath"
        """
        return await self._run_powershell(cmd)

    async def _backup_log(self, log_name: str = "System", path: str = "", **kwargs) -> Dict[str, Any]:
        """Backup log to file with archive"""
        if not path:
            path = f"$env:TEMP\\{log_name}_backup.evtx"
        cmd = f"""
        $backupPath = "{path}"
        wevtutil al '{log_name}' $backupPath
        Write-Output "Log backed up to: $backupPath"
        """
        return await self._run_powershell(cmd)

    async def _set_log_size(self, log_name: str = "System", size_mb: int = 20, **kwargs) -> Dict[str, Any]:
        """Set maximum log size in MB"""
        size_bytes = size_mb * 1024 * 1024
        cmd = f"wevtutil sl '{log_name}' /ms:{size_bytes}; Write-Output 'Log {log_name} max size set to {size_mb}MB'"
        return await self._run_powershell(cmd)

    async def _enable_log(self, log_name: str = "", **kwargs) -> Dict[str, Any]:
        """Enable an event log"""
        if not log_name:
            return {"success": False, "error": "log_name is required"}
        cmd = f"wevtutil sl '{log_name}' /e:true; Write-Output 'Log {log_name} enabled'"
        return await self._run_powershell(cmd)

    async def _disable_log(self, log_name: str = "", **kwargs) -> Dict[str, Any]:
        """Disable an event log"""
        if not log_name:
            return {"success": False, "error": "log_name is required"}
        cmd = f"wevtutil sl '{log_name}' /e:false; Write-Output 'Log {log_name} disabled'"
        return await self._run_powershell(cmd)

    # Event details
    async def _get_event_details(self, log_name: str = "System", record_id: int = 0, **kwargs) -> Dict[str, Any]:
        """Get detailed info about a specific event"""
        cmd = f"""
        Get-WinEvent -LogName '{log_name}' -MaxEvents 1000 -ErrorAction SilentlyContinue |
        Where-Object {{ $_.RecordId -eq {record_id} }} |
        Select-Object TimeCreated, Id, RecordId, Level, LevelDisplayName, 
                      LogName, ProviderName, ProviderId, UserId, ProcessId, 
                      ThreadId, MachineName, Message, @{{N='Properties';E={{$_.Properties.Value}}}} |
        ConvertTo-Json -Depth 3
        """
        return await self._run_powershell(cmd)

    async def _get_event_xml(self, log_name: str = "System", record_id: int = 0, **kwargs) -> Dict[str, Any]:
        """Get event in XML format"""
        cmd = f"""
        Get-WinEvent -LogName '{log_name}' -MaxEvents 1000 -ErrorAction SilentlyContinue |
        Where-Object {{ $_.RecordId -eq {record_id} }} |
        ForEach-Object {{ $_.ToXml() }}
        """
        return await self._run_powershell(cmd)

    # Statistics
    async def _get_log_statistics(self, log_name: str = "System", **kwargs) -> Dict[str, Any]:
        """Get statistics for a log"""
        cmd = f"""
        $events = Get-WinEvent -LogName '{log_name}' -MaxEvents 10000 -ErrorAction SilentlyContinue
        $stats = $events | Group-Object LevelDisplayName | Select-Object Name, Count
        $firstEvent = $events | Select-Object -Last 1
        $lastEvent = $events | Select-Object -First 1
        
        [PSCustomObject]@{{
            LogName = '{log_name}'
            TotalEventsAnalyzed = $events.Count
            EventsByLevel = $stats
            OldestEvent = $firstEvent.TimeCreated
            NewestEvent = $lastEvent.TimeCreated
            UniqueProviders = ($events | Select-Object -Unique ProviderName).Count
            UniqueEventIds = ($events | Select-Object -Unique Id).Count
        }} | ConvertTo-Json -Depth 3
        """
        return await self._run_powershell(cmd)

    async def _get_event_count_by_level(self, log_name: str = "System", hours: int = 24, **kwargs) -> Dict[str, Any]:
        """Get event counts by severity level"""
        cmd = f"""
        $startTime = (Get-Date).AddHours(-{hours})
        Get-WinEvent -FilterHashtable @{{LogName='{log_name}'; StartTime=$startTime}} -MaxEvents 10000 -ErrorAction SilentlyContinue |
        Group-Object LevelDisplayName |
        Select-Object @{{N='Level';E={{$_.Name}}}}, Count |
        ConvertTo-Json
        """
        return await self._run_powershell(cmd)

    async def _get_top_event_sources(self, log_name: str = "System", top: int = 10, hours: int = 24, **kwargs) -> Dict[str, Any]:
        """Get top event sources by count"""
        cmd = f"""
        $startTime = (Get-Date).AddHours(-{hours})
        Get-WinEvent -FilterHashtable @{{LogName='{log_name}'; StartTime=$startTime}} -MaxEvents 10000 -ErrorAction SilentlyContinue |
        Group-Object ProviderName |
        Sort-Object Count -Descending |
        Select-Object -First {top} @{{N='Source';E={{$_.Name}}}}, Count |
        ConvertTo-Json
        """
        return await self._run_powershell(cmd)

    # Custom queries
    async def _run_xpath_query(self, log_name: str = "System", xpath: str = "*", max_events: int = 50, **kwargs) -> Dict[str, Any]:
        """Run a custom XPath query"""
        cmd = f"""
        Get-WinEvent -LogName '{log_name}' -FilterXPath '{xpath}' -MaxEvents {max_events} -ErrorAction SilentlyContinue |
        Select-Object TimeCreated, Id, LevelDisplayName, ProviderName, Message |
        ConvertTo-Json -Depth 2
        """
        return await self._run_powershell(cmd)

    async def _get_forwarded_events(self, max_events: int = 50, **kwargs) -> Dict[str, Any]:
        """Get forwarded events (from other machines)"""
        cmd = f"""
        Get-WinEvent -LogName 'ForwardedEvents' -MaxEvents {max_events} -ErrorAction SilentlyContinue |
        Select-Object TimeCreated, Id, LevelDisplayName, ProviderName, MachineName, Message |
        ConvertTo-Json -Depth 2
        """
        return await self._run_powershell(cmd)

    async def cleanup(self) -> None:
        """Cleanup plugin resources"""
        self.logger.info("Event Log plugin cleaned up")
