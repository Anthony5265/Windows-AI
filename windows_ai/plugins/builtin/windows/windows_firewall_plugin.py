"""
Windows Firewall Plugin - Manage Windows Defender Firewall rules and settings
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class WindowsFirewallPlugin(IntegrationPlugin):
    """Plugin for managing Windows Defender Firewall"""

    def __init__(self):
        metadata = PluginMetadata(
            id="windows.firewall",
            name="Windows Firewall",
            description="Manage Windows Defender Firewall rules, profiles, and settings",
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["firewall", "security", "network", "rules", "windows"],
        )
        super().__init__(metadata)

    async def initialize(self) -> bool:
        """Initialize Windows Firewall plugin"""
        try:
            result = await self._run_powershell("Get-NetFirewallProfile | Select-Object -First 1 | ConvertTo-Json")
            logger.info("Windows Firewall plugin initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Windows Firewall: {e}")
            return False

    async def _run_powershell(self, script: str, timeout: int = 60) -> Dict[str, Any]:
        """Execute a PowerShell command"""
        try:
            process = await asyncio.create_subprocess_exec(
                "powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            return {
                "success": process.returncode == 0,
                "output": stdout.decode("utf-8", errors="replace").strip(),
                "error": stderr.decode("utf-8", errors="replace").strip() if stderr else None
            }
        except asyncio.TimeoutError:
            return {"success": False, "error": f"Command timed out after {timeout} seconds"}
        except Exception as e:
            return {"success": False, "error": str(e)}


    async def connect(self, credentials: Dict[str, str]) -> bool:
        """Connect to the service"""
        return True

    async def disconnect(self) -> bool:
        """Disconnect from the service"""
        return True

    async def execute(self, action: str = "status", params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute firewall management actions"""
        params = params or {}
        
        actions = {
            # Status and profiles
            "status": self._get_status,
            "get_profiles": self._get_profiles,
            "get_profile": self._get_profile,
            "enable_profile": self._enable_profile,
            "disable_profile": self._disable_profile,
            "set_profile": self._set_profile,
            
            # Firewall rules
            "list_rules": self._list_rules,
            "get_rule": self._get_rule,
            "create_rule": self._create_rule,
            "remove_rule": self._remove_rule,
            "enable_rule": self._enable_rule,
            "disable_rule": self._disable_rule,
            "set_rule": self._set_rule,
            
            # Rule search
            "find_rules_by_port": self._find_rules_by_port,
            "find_rules_by_program": self._find_rules_by_program,
            "find_rules_by_protocol": self._find_rules_by_protocol,
            
            # Application rules
            "allow_app": self._allow_app,
            "block_app": self._block_app,
            "get_app_rules": self._get_app_rules,
            
            # Port rules
            "allow_port": self._allow_port,
            "block_port": self._block_port,
            
            # Connections
            "get_active_connections": self._get_active_connections,
            "get_listening_ports": self._get_listening_ports,
            
            # Logging
            "get_log_settings": self._get_log_settings,
            "set_log_settings": self._set_log_settings,
            "get_log_entries": self._get_log_entries,
            
            # Import/Export
            "export_rules": self._export_rules,
            "import_rules": self._import_rules,
            "backup_policy": self._backup_policy,
            "restore_policy": self._restore_policy,
            
            # Reset
            "reset_to_defaults": self._reset_to_defaults
        }
        
        if action not in actions:
            return {"success": False, "error": f"Unknown action: {action}. Available: {list(actions.keys())}"}
        
        try:
            return await actions[action](params)
        except Exception as e:
            logger.error(f"Firewall action '{action}' failed: {e}")
            return {"success": False, "error": str(e)}

    async def _get_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get overall firewall status"""
        script = """
        $profiles = Get-NetFirewallProfile
        $rules = Get-NetFirewallRule
        @{
            Profiles = $profiles | Select-Object Name, Enabled, DefaultInboundAction, DefaultOutboundAction
            RuleCount = $rules.Count
            EnabledRules = ($rules | Where-Object { $_.Enabled -eq 'True' }).Count
            DisabledRules = ($rules | Where-Object { $_.Enabled -eq 'False' }).Count
            InboundRules = ($rules | Where-Object { $_.Direction -eq 'Inbound' }).Count
            OutboundRules = ($rules | Where-Object { $_.Direction -eq 'Outbound' }).Count
        } | ConvertTo-Json -Depth 5
        """
        return await self._run_powershell(script)

    async def _get_profiles(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get all firewall profiles"""
        script = """
        Get-NetFirewallProfile | Select-Object Name, Enabled, 
            DefaultInboundAction, DefaultOutboundAction,
            AllowInboundRules, AllowLocalFirewallRules,
            AllowLocalIPsecRules, AllowUnicastResponseToMulticast,
            NotifyOnListen, LogFileName, LogMaxSizeKilobytes,
            LogAllowed, LogBlocked | ConvertTo-Json -Depth 3
        """
        return await self._run_powershell(script)

    async def _get_profile(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get specific firewall profile"""
        profile = params.get("profile", "Domain")  # Domain, Private, Public
        script = f"""
        Get-NetFirewallProfile -Name '{profile}' | 
        Select-Object Name, Enabled, DefaultInboundAction, DefaultOutboundAction,
            AllowInboundRules, AllowLocalFirewallRules, NotifyOnListen,
            LogFileName, LogMaxSizeKilobytes, LogAllowed, LogBlocked |
        ConvertTo-Json
        """
        return await self._run_powershell(script)

    async def _enable_profile(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Enable firewall profile"""
        profile = params.get("profile", "all")  # Domain, Private, Public, or all
        
        if profile.lower() == "all":
            script = """
            Set-NetFirewallProfile -All -Enabled True
            @{ success = $true; message = "All profiles enabled" } | ConvertTo-Json
            """
        else:
            script = f"""
            Set-NetFirewallProfile -Name '{profile}' -Enabled True
            @{{ success = $true; message = "{profile} profile enabled" }} | ConvertTo-Json
            """
        return await self._run_powershell(script)

    async def _disable_profile(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Disable firewall profile"""
        profile = params.get("profile", "all")
        
        if profile.lower() == "all":
            script = """
            Set-NetFirewallProfile -All -Enabled False
            @{ success = $true; message = "All profiles disabled" } | ConvertTo-Json
            """
        else:
            script = f"""
            Set-NetFirewallProfile -Name '{profile}' -Enabled False
            @{{ success = $true; message = "{profile} profile disabled" }} | ConvertTo-Json
            """
        return await self._run_powershell(script)

    async def _set_profile(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set firewall profile settings"""
        profile = params.get("profile", "Domain")
        inbound = params.get("default_inbound")  # Allow, Block
        outbound = params.get("default_outbound")  # Allow, Block
        
        settings = []
        if inbound:
            settings.append(f"-DefaultInboundAction {inbound}")
        if outbound:
            settings.append(f"-DefaultOutboundAction {outbound}")
        
        if not settings:
            return {"success": False, "error": "No settings specified"}
        
        script = f"""
        Set-NetFirewallProfile -Name '{profile}' {' '.join(settings)}
        Get-NetFirewallProfile -Name '{profile}' | 
        Select-Object Name, DefaultInboundAction, DefaultOutboundAction | ConvertTo-Json
        """
        return await self._run_powershell(script)

    async def _list_rules(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List firewall rules"""
        direction = params.get("direction")  # Inbound, Outbound
        enabled = params.get("enabled")  # True, False
        action_filter = params.get("action")  # Allow, Block
        limit = params.get("limit", 100)
        
        filters = []
        if direction:
            filters.append(f"$_.Direction -eq '{direction}'")
        if enabled is not None:
            filters.append(f"$_.Enabled -eq '{str(enabled)}'")
        if action_filter:
            filters.append(f"$_.Action -eq '{action_filter}'")
        
        where_clause = f"| Where-Object {{ {' -and '.join(filters)} }}" if filters else ""
        
        script = f"""
        Get-NetFirewallRule {where_clause} | Select-Object -First {limit} |
        Select-Object Name, DisplayName, Description, Direction, Action, 
            Enabled, Profile, @{{N='Protocol';E={{($_ | Get-NetFirewallPortFilter).Protocol}}}},
            @{{N='LocalPort';E={{($_ | Get-NetFirewallPortFilter).LocalPort}}}},
            @{{N='RemotePort';E={{($_ | Get-NetFirewallPortFilter).RemotePort}}}},
            @{{N='Program';E={{($_ | Get-NetFirewallApplicationFilter).Program}}}} |
        ConvertTo-Json -Depth 3
        """
        return await self._run_powershell(script)

    async def _get_rule(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get specific firewall rule"""
        name = params.get("name")
        display_name = params.get("display_name")
        
        if name:
            filter_param = f"-Name '{name}'"
        elif display_name:
            filter_param = f"-DisplayName '{display_name}'"
        else:
            return {"success": False, "error": "Rule name or display_name required"}
        
        script = f"""
        $rule = Get-NetFirewallRule {filter_param}
        $portFilter = $rule | Get-NetFirewallPortFilter
        $appFilter = $rule | Get-NetFirewallApplicationFilter
        $addrFilter = $rule | Get-NetFirewallAddressFilter
        @{{
            Name = $rule.Name
            DisplayName = $rule.DisplayName
            Description = $rule.Description
            Direction = $rule.Direction.ToString()
            Action = $rule.Action.ToString()
            Enabled = $rule.Enabled.ToString()
            Profile = $rule.Profile.ToString()
            Protocol = $portFilter.Protocol
            LocalPort = $portFilter.LocalPort
            RemotePort = $portFilter.RemotePort
            Program = $appFilter.Program
            LocalAddress = $addrFilter.LocalAddress
            RemoteAddress = $addrFilter.RemoteAddress
        }} | ConvertTo-Json -Depth 3
        """
        return await self._run_powershell(script)

    async def _create_rule(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create new firewall rule"""
        name = params.get("name")
        display_name = params.get("display_name", name)
        direction = params.get("direction", "Inbound")  # Inbound, Outbound
        action = params.get("action", "Allow")  # Allow, Block
        protocol = params.get("protocol")  # TCP, UDP, Any
        local_port = params.get("local_port")
        remote_port = params.get("remote_port")
        program = params.get("program")
        profile = params.get("profile", "Any")  # Domain, Private, Public, Any
        description = params.get("description", "")
        enabled = params.get("enabled", True)
        
        if not name:
            return {"success": False, "error": "Rule name required"}
        
        cmd_parts = [
            f"New-NetFirewallRule -Name '{name}'",
            f"-DisplayName '{display_name}'",
            f"-Direction {direction}",
            f"-Action {action}",
            f"-Profile {profile}",
            f"-Enabled {str(enabled)}"
        ]
        
        if protocol:
            cmd_parts.append(f"-Protocol {protocol}")
        if local_port:
            cmd_parts.append(f"-LocalPort {local_port}")
        if remote_port:
            cmd_parts.append(f"-RemotePort {remote_port}")
        if program:
            cmd_parts.append(f"-Program '{program}'")
        if description:
            cmd_parts.append(f"-Description '{description}'")
        
        script = f"""
        {' '.join(cmd_parts)}
        @{{ success = $true; message = "Rule '{name}' created" }} | ConvertTo-Json
        """
        return await self._run_powershell(script)

    async def _remove_rule(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove firewall rule"""
        name = params.get("name")
        display_name = params.get("display_name")
        
        if name:
            filter_param = f"-Name '{name}'"
        elif display_name:
            filter_param = f"-DisplayName '{display_name}'"
        else:
            return {"success": False, "error": "Rule name or display_name required"}
        
        script = f"""
        Remove-NetFirewallRule {filter_param}
        @{{ success = $true; message = "Rule removed" }} | ConvertTo-Json
        """
        return await self._run_powershell(script)

    async def _enable_rule(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Enable firewall rule"""
        name = params.get("name")
        display_name = params.get("display_name")
        
        if name:
            filter_param = f"-Name '{name}'"
        elif display_name:
            filter_param = f"-DisplayName '{display_name}'"
        else:
            return {"success": False, "error": "Rule name or display_name required"}
        
        script = f"""
        Enable-NetFirewallRule {filter_param}
        @{{ success = $true; message = "Rule enabled" }} | ConvertTo-Json
        """
        return await self._run_powershell(script)

    async def _disable_rule(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Disable firewall rule"""
        name = params.get("name")
        display_name = params.get("display_name")
        
        if name:
            filter_param = f"-Name '{name}'"
        elif display_name:
            filter_param = f"-DisplayName '{display_name}'"
        else:
            return {"success": False, "error": "Rule name or display_name required"}
        
        script = f"""
        Disable-NetFirewallRule {filter_param}
        @{{ success = $true; message = "Rule disabled" }} | ConvertTo-Json
        """
        return await self._run_powershell(script)

    async def _set_rule(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Modify existing firewall rule"""
        name = params.get("name")
        if not name:
            return {"success": False, "error": "Rule name required"}
        
        settings = []
        if new_name := params.get("new_name"):
            settings.append(f"-NewDisplayName '{new_name}'")
        if action := params.get("action"):
            settings.append(f"-Action {action}")
        if protocol := params.get("protocol"):
            settings.append(f"-Protocol {protocol}")
        if local_port := params.get("local_port"):
            settings.append(f"-LocalPort {local_port}")
        if remote_port := params.get("remote_port"):
            settings.append(f"-RemotePort {remote_port}")
        if profile := params.get("profile"):
            settings.append(f"-Profile {profile}")
        
        if not settings:
            return {"success": False, "error": "No settings to change"}
        
        script = f"""
        Set-NetFirewallRule -Name '{name}' {' '.join(settings)}
        @{{ success = $true; message = "Rule updated" }} | ConvertTo-Json
        """
        return await self._run_powershell(script)

    async def _find_rules_by_port(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Find rules for a specific port"""
        port = params.get("port")
        if not port:
            return {"success": False, "error": "Port number required"}
        
        script = f"""
        Get-NetFirewallRule | Where-Object {{
            $portFilter = $_ | Get-NetFirewallPortFilter
            $portFilter.LocalPort -eq '{port}' -or $portFilter.RemotePort -eq '{port}'
        }} | Select-Object Name, DisplayName, Direction, Action, Enabled |
        ConvertTo-Json -Depth 3
        """
        return await self._run_powershell(script)

    async def _find_rules_by_program(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Find rules for a specific program"""
        program = params.get("program")
        if not program:
            return {"success": False, "error": "Program path required"}
        
        script = f"""
        Get-NetFirewallRule | Where-Object {{
            ($_ | Get-NetFirewallApplicationFilter).Program -like '*{program}*'
        }} | Select-Object Name, DisplayName, Direction, Action, Enabled,
            @{{N='Program';E={{($_ | Get-NetFirewallApplicationFilter).Program}}}} |
        ConvertTo-Json -Depth 3
        """
        return await self._run_powershell(script)

    async def _find_rules_by_protocol(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Find rules for a specific protocol"""
        protocol = params.get("protocol")
        if not protocol:
            return {"success": False, "error": "Protocol required (TCP, UDP)"}
        
        script = f"""
        Get-NetFirewallRule | Where-Object {{
            ($_ | Get-NetFirewallPortFilter).Protocol -eq '{protocol}'
        }} | Select-Object -First 50 Name, DisplayName, Direction, Action, Enabled |
        ConvertTo-Json -Depth 3
        """
        return await self._run_powershell(script)

    async def _allow_app(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create allow rule for an application"""
        program = params.get("program")
        name = params.get("name", f"Allow-{program.split('\\')[-1] if program else 'App'}")
        direction = params.get("direction", "Inbound")
        
        if not program:
            return {"success": False, "error": "Program path required"}
        
        script = f"""
        New-NetFirewallRule -Name '{name}' -DisplayName '{name}' -Program '{program}' `
            -Direction {direction} -Action Allow -Enabled True
        @{{ success = $true; message = "Application allowed: {program}" }} | ConvertTo-Json
        """
        return await self._run_powershell(script)

    async def _block_app(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create block rule for an application"""
        program = params.get("program")
        name = params.get("name", f"Block-{program.split('\\')[-1] if program else 'App'}")
        direction = params.get("direction", "Inbound")
        
        if not program:
            return {"success": False, "error": "Program path required"}
        
        script = f"""
        New-NetFirewallRule -Name '{name}' -DisplayName '{name}' -Program '{program}' `
            -Direction {direction} -Action Block -Enabled True
        @{{ success = $true; message = "Application blocked: {program}" }} | ConvertTo-Json
        """
        return await self._run_powershell(script)

    async def _get_app_rules(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get all application-based rules"""
        script = """
        Get-NetFirewallRule | Where-Object {
            ($_ | Get-NetFirewallApplicationFilter).Program -ne $null -and
            ($_ | Get-NetFirewallApplicationFilter).Program -ne '*'
        } | Select-Object Name, DisplayName, Direction, Action, Enabled,
            @{N='Program';E={($_ | Get-NetFirewallApplicationFilter).Program}} |
        ConvertTo-Json -Depth 3
        """
        return await self._run_powershell(script)

    async def _allow_port(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create allow rule for a port"""
        port = params.get("port")
        protocol = params.get("protocol", "TCP")
        direction = params.get("direction", "Inbound")
        name = params.get("name", f"Allow-{protocol}-{port}-{direction}")
        
        if not port:
            return {"success": False, "error": "Port number required"}
        
        script = f"""
        New-NetFirewallRule -Name '{name}' -DisplayName '{name}' `
            -Protocol {protocol} -LocalPort {port} -Direction {direction} `
            -Action Allow -Enabled True
        @{{ success = $true; message = "Port {port}/{protocol} allowed" }} | ConvertTo-Json
        """
        return await self._run_powershell(script)

    async def _block_port(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create block rule for a port"""
        port = params.get("port")
        protocol = params.get("protocol", "TCP")
        direction = params.get("direction", "Inbound")
        name = params.get("name", f"Block-{protocol}-{port}-{direction}")
        
        if not port:
            return {"success": False, "error": "Port number required"}
        
        script = f"""
        New-NetFirewallRule -Name '{name}' -DisplayName '{name}' `
            -Protocol {protocol} -LocalPort {port} -Direction {direction} `
            -Action Block -Enabled True
        @{{ success = $true; message = "Port {port}/{protocol} blocked" }} | ConvertTo-Json
        """
        return await self._run_powershell(script)

    async def _get_active_connections(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get active network connections"""
        state = params.get("state", "Established")  # Established, Listen, TimeWait, etc.
        limit = params.get("limit", 50)
        
        script = f"""
        Get-NetTCPConnection -State {state} -ErrorAction SilentlyContinue | 
        Select-Object -First {limit} LocalAddress, LocalPort, RemoteAddress, RemotePort, State,
            @{{N='Process';E={{(Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).Name}}}} |
        ConvertTo-Json -Depth 3
        """
        return await self._run_powershell(script)

    async def _get_listening_ports(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get all listening ports"""
        script = """
        Get-NetTCPConnection -State Listen | 
        Select-Object LocalAddress, LocalPort,
            @{N='Process';E={(Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).Name}},
            @{N='PID';E={$_.OwningProcess}} |
        Sort-Object LocalPort | ConvertTo-Json -Depth 3
        """
        return await self._run_powershell(script)

    async def _get_log_settings(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get firewall log settings"""
        script = """
        Get-NetFirewallProfile | Select-Object Name, LogFileName, LogMaxSizeKilobytes,
            LogAllowed, LogBlocked, LogIgnored | ConvertTo-Json -Depth 3
        """
        return await self._run_powershell(script)

    async def _set_log_settings(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set firewall log settings"""
        profile = params.get("profile", "Domain")
        log_allowed = params.get("log_allowed")
        log_blocked = params.get("log_blocked")
        log_path = params.get("log_path")
        max_size = params.get("max_size_kb")
        
        settings = []
        if log_allowed is not None:
            settings.append(f"-LogAllowed {str(log_allowed)}")
        if log_blocked is not None:
            settings.append(f"-LogBlocked {str(log_blocked)}")
        if log_path:
            settings.append(f"-LogFileName '{log_path}'")
        if max_size:
            settings.append(f"-LogMaxSizeKilobytes {max_size}")
        
        if not settings:
            return {"success": False, "error": "No log settings specified"}
        
        script = f"""
        Set-NetFirewallProfile -Name '{profile}' {' '.join(settings)}
        @{{ success = $true; message = "Log settings updated" }} | ConvertTo-Json
        """
        return await self._run_powershell(script)

    async def _get_log_entries(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get firewall log entries"""
        profile = params.get("profile", "Domain")
        lines = params.get("lines", 100)
        
        script = f"""
        $logPath = (Get-NetFirewallProfile -Name '{profile}').LogFileName
        if (Test-Path $logPath) {{
            Get-Content $logPath -Tail {lines} | ConvertTo-Json
        }} else {{
            @{{ error = "Log file not found: $logPath" }} | ConvertTo-Json
        }}
        """
        return await self._run_powershell(script)

    async def _export_rules(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Export firewall rules"""
        path = params.get("path", "$env:TEMP\\firewall_rules.wfw")
        
        script = f"""
        netsh advfirewall export '{path}'
        @{{ success = $true; path = '{path}'; message = "Rules exported" }} | ConvertTo-Json
        """
        return await self._run_powershell(script)

    async def _import_rules(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Import firewall rules"""
        path = params.get("path")
        if not path:
            return {"success": False, "error": "Import path required"}
        
        script = f"""
        if (Test-Path '{path}') {{
            netsh advfirewall import '{path}'
            @{{ success = $true; message = "Rules imported from {path}" }} | ConvertTo-Json
        }} else {{
            @{{ success = $false; error = "File not found: {path}" }} | ConvertTo-Json
        }}
        """
        return await self._run_powershell(script)

    async def _backup_policy(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Backup firewall policy"""
        path = params.get("path", "$env:TEMP\\firewall_backup.wfw")
        
        script = f"""
        netsh advfirewall export '{path}'
        @{{ success = $true; path = '{path}'; message = "Policy backed up" }} | ConvertTo-Json
        """
        return await self._run_powershell(script)

    async def _restore_policy(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Restore firewall policy from backup"""
        path = params.get("path")
        if not path:
            return {"success": False, "error": "Backup path required"}
        
        script = f"""
        if (Test-Path '{path}') {{
            netsh advfirewall import '{path}'
            @{{ success = $true; message = "Policy restored from {path}" }} | ConvertTo-Json
        }} else {{
            @{{ success = $false; error = "Backup not found: {path}" }} | ConvertTo-Json
        }}
        """
        return await self._run_powershell(script)

    async def _reset_to_defaults(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Reset firewall to default settings"""
        confirm = params.get("confirm", False)
        
        if not confirm:
            return {"success": False, "error": "Set confirm=True to reset firewall to defaults"}
        
        script = """
        netsh advfirewall reset
        @{ success = $true; message = "Firewall reset to defaults" } | ConvertTo-Json
        """
        return await self._run_powershell(script)

    async def cleanup(self) -> None:
        """Cleanup plugin resources"""
        logger.info("Windows Firewall plugin cleaned up")


plugin = WindowsFirewallPlugin()
