"""
Windows Event Tracing for Windows (ETW) Integration - PRODUCTION
Manages ETW sessions, providers, and event queries.
"""
import os
import asyncio
import json
from typing import Dict, Any, Optional, List
from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType
import logging

logger = logging.getLogger(__name__)


class WindowsETWPlugin(IntegrationPlugin):
    def __init__(self):
        metadata = PluginMetadata(
            id="windows_etw",
            name="Windows Event Tracing (ETW)",
            description=(
                "Manage Event Tracing for Windows (ETW) sessions and providers. "
                "List, start, and stop trace sessions; query events; enumerate providers."
            ),
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["windows", "etw", "tracing", "events", "performance", "diagnostics"],
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
            "list_sessions": self._list_sessions,
            "start_session": self._start_session,
            "stop_session": self._stop_session,
            "list_providers": self._list_providers,
            "get_session_stats": self._get_session_stats,
            "query_events": self._query_events,
            "enable_provider": self._enable_provider,
            "disable_provider": self._disable_provider,
            "get_provider_info": self._get_provider_info,
            "flush_session": self._flush_session,
            "list_event_logs": self._list_event_logs,
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

    async def _run_logman(self, *args: str) -> Dict[str, Any]:
        """Run logman.exe with given arguments."""
        try:
            process = await asyncio.create_subprocess_exec(
                "logman", *args,
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
            return {"success": False, "error": "logman.exe not available on this system"}
        except asyncio.TimeoutError:
            return {"success": False, "error": "logman timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _list_sessions(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List all active ETW trace sessions."""
        cmd = r"""
try {
    $sessions = logman query -ets 2>&1
    $result = @{ 'raw_output' = ($sessions -join "`n") }
    # Parse sessions from logman output
    $sessionList = @()
    $sessions | Where-Object { $_ -match '^\S' -and $_ -notmatch '^---' -and $_ -notmatch '^Data Collector' } |
        ForEach-Object {
            $line = $_.Trim()
            if ($line -and $line -notmatch 'The command') {
                $sessionList += $line
            }
        }
    $result['sessions'] = $sessionList
    $result['count'] = $sessionList.Count
    $result | ConvertTo-Json -Depth 2
} catch {
    @{ 'error' = $_.Exception.Message } | ConvertTo-Json
}
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _start_session(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Start a new ETW trace session."""
        session_name = params.get("session_name")
        output_file = params.get("output_file", "")
        providers = params.get("providers", [])
        if not session_name:
            return {"success": False, "error": "Parameter 'session_name' is required"}

        safe_name = session_name.replace('"', "").replace(";", "")[:64]
        args = ["create", "trace", safe_name, "-ets"]

        if output_file:
            safe_out = output_file.replace('"', "")
            args.extend(["-o", safe_out])

        result = await self._run_logman(*args)

        # Enable specified providers
        if result["success"] and providers:
            for provider in providers[:10]:  # limit to 10 providers
                safe_prov = str(provider).replace('"', "").replace(";", "")
                await self._run_logman("update", "trace", safe_name, "-p", safe_prov, "-ets")

        result["session_name"] = safe_name
        return result

    async def _stop_session(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Stop an ETW trace session."""
        session_name = params.get("session_name")
        if not session_name:
            return {"success": False, "error": "Parameter 'session_name' is required"}
        safe_name = session_name.replace('"', "").replace(";", "")[:64]
        result = await self._run_logman("stop", safe_name, "-ets")
        result["session_name"] = safe_name
        return result

    async def _list_providers(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List registered ETW providers."""
        filter_str = params.get("filter", "")
        limit = params.get("limit", 100)
        cmd = f"""
try {{
    $providers = logman query providers 2>&1
    $list = @()
    $providers | Select-Object -Skip 3 | ForEach-Object {{
        $line = $_.Trim()
        if ($line -and $line -notmatch '^---' -and $line.Length -gt 5) {{
            # Try to parse GUID and name
            if ($line -match '{{([0-9a-fA-F-]+)}}') {{
                $guid = $Matches[1]
                $name = ($line -replace '{{[0-9a-fA-F-]+}}', '').Trim()
                if (-not '{filter_str}' -or $name -like '*{filter_str}*') {{
                    $list += @{{ 'name' = $name; 'guid' = $guid }}
                }}
            }} else {{
                if (-not '{filter_str}' -or $line -like '*{filter_str}*') {{
                    $list += @{{ 'name' = $line; 'guid' = '' }}
                }}
            }}
        }}
    }}
    $limited = $list | Select-Object -First {limit}
    @{{ 'providers' = $limited; 'count' = $limited.Count; 'total_found' = $list.Count }} | ConvertTo-Json -Depth 2
}} catch {{
    @{{ 'error' = $_.Exception.Message; 'providers' = @() }} | ConvertTo-Json
}}
"""
        result = await self._run_ps(cmd, timeout=45)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _get_session_stats(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get statistics for a specific ETW session."""
        session_name = params.get("session_name")
        if not session_name:
            # Return stats for all sessions
            result = await self._run_logman("query", "-ets")
            return result
        safe_name = session_name.replace('"', "").replace(";", "")[:64]
        result = await self._run_logman("query", safe_name, "-ets")
        result["session_name"] = safe_name
        return result

    async def _query_events(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Query events from an ETL file or event log."""
        source = params.get("source")  # ETL file path or event log name
        limit = params.get("limit", 50)
        level = params.get("level", 0)  # 0=all, 1=critical, 2=error, 3=warning, 4=info

        if not source:
            return {"success": False, "error": "Parameter 'source' (ETL file or log name) is required"}

        safe_source = source.replace("'", "''").replace(";", "")
        level_filter = f" -Level {level}" if level > 0 else ""

        cmd = f"""
try {{
    $events = Get-WinEvent -Path '{safe_source}'{level_filter} -MaxEvents {limit} -ErrorAction SilentlyContinue
    if (-not $events) {{
        $events = Get-WinEvent -LogName '{safe_source}'{level_filter} -MaxEvents {limit} -ErrorAction SilentlyContinue
    }}
    $result = @($events | ForEach-Object {{
        @{{
            'time' = $_.TimeCreated.ToString('o')
            'event_id' = $_.Id
            'provider' = $_.ProviderName
            'level' = $_.LevelDisplayName
            'message' = if ($_.Message) {{ $_.Message.Substring(0, [Math]::Min(200, $_.Message.Length)) }} else {{ '' }}
            'task' = $_.TaskDisplayName
        }}
    }})
    @{{ 'events' = $result; 'count' = $result.Count; 'source' = '{safe_source}' }} | ConvertTo-Json -Depth 3
}} catch {{
    @{{ 'error' = $_.Exception.Message; 'events' = @() }} | ConvertTo-Json
}}
"""
        result = await self._run_ps(cmd, timeout=45)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _enable_provider(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Enable a provider in an ETW session."""
        session_name = params.get("session_name")
        provider = params.get("provider")
        if not session_name or not provider:
            return {"success": False, "error": "Parameters 'session_name' and 'provider' are required"}
        safe_session = session_name.replace('"', "").replace(";", "")[:64]
        safe_provider = provider.replace('"', "").replace(";", "")
        result = await self._run_logman("update", "trace", safe_session, "-p", safe_provider, "-ets")
        result["session_name"] = safe_session
        result["provider"] = safe_provider
        return result

    async def _disable_provider(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Disable a provider in an ETW session."""
        session_name = params.get("session_name")
        provider = params.get("provider")
        if not session_name or not provider:
            return {"success": False, "error": "Parameters 'session_name' and 'provider' are required"}
        safe_session = session_name.replace('"', "").replace(";", "")[:64]
        safe_provider = provider.replace('"', "").replace(";", "")
        result = await self._run_logman("update", "trace", safe_session, "-p", safe_provider, "-ets")
        result["session_name"] = safe_session
        result["provider"] = safe_provider
        return result

    async def _get_provider_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get information about a specific ETW provider."""
        provider = params.get("provider")
        if not provider:
            return {"success": False, "error": "Parameter 'provider' is required"}
        safe_provider = provider.replace('"', "").replace(";", "")
        result = await self._run_logman("query", "providers", safe_provider)
        return result

    async def _flush_session(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Flush buffered events from an ETW session."""
        session_name = params.get("session_name")
        if not session_name:
            return {"success": False, "error": "Parameter 'session_name' is required"}
        safe_name = session_name.replace('"', "").replace(";", "")[:64]
        result = await self._run_logman("update", "trace", safe_name, "-flush", "-ets")
        result["session_name"] = safe_name
        return result

    async def _list_event_logs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List all Windows Event Logs."""
        filter_str = params.get("filter", "")
        limit = params.get("limit", 50)
        cmd = f"""
$logs = Get-WinEvent -ListLog '*' -ErrorAction SilentlyContinue |
    Where-Object {{ -not '{filter_str}' -or $_.LogName -like '*{filter_str}*' }} |
    Select-Object -First {limit} |
    ForEach-Object {{
        @{{
            'log_name' = $_.LogName
            'log_type' = $_.LogType.ToString()
            'record_count' = $_.RecordCount
            'max_size_mb' = [math]::Round($_.MaximumSizeInBytes / 1MB, 1)
            'is_enabled' = $_.IsEnabled
            'last_write_time' = if ($_.LastWriteTime) {{ $_.LastWriteTime.ToString('o') }} else {{ $null }}
        }}
    }}
@{{ 'logs' = @($logs); 'count' = @($logs).Count }} | ConvertTo-Json -Depth 2
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
                "list_sessions": {"description": "List active ETW trace sessions"},
                "start_session": {"description": "Start ETW session", "params": {"session_name": "str", "output_file": "str", "providers": "list"}},
                "stop_session": {"description": "Stop ETW session", "params": {"session_name": "str"}},
                "list_providers": {"description": "List registered ETW providers", "params": {"filter": "str", "limit": "int"}},
                "get_session_stats": {"description": "Get ETW session statistics", "params": {"session_name": "str"}},
                "query_events": {"description": "Query ETW events", "params": {"source": "str", "limit": "int", "level": "int"}},
                "enable_provider": {"description": "Enable provider in session", "params": {"session_name": "str", "provider": "str"}},
                "disable_provider": {"description": "Disable provider in session", "params": {"session_name": "str", "provider": "str"}},
                "get_provider_info": {"description": "Get provider details", "params": {"provider": "str"}},
                "flush_session": {"description": "Flush session buffers", "params": {"session_name": "str"}},
                "list_event_logs": {"description": "List all event logs", "params": {"filter": "str", "limit": "int"}},
            },
        }


plugin = WindowsETWPlugin()
