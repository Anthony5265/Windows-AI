"""
Windows Network Management Plugin - PRODUCTION

Provides comprehensive network management including:
- Network adapter configuration
- IP address management
- DNS configuration
- Routing tables
- Network diagnostics
- Wi-Fi management
"""
import asyncio
import json
from typing import Dict, Any, List, Optional
from windows_ai.plugins.base import Plugin, PluginMetadata, PluginType
import logging

logger = logging.getLogger(__name__)


class WindowsNetworkManagementPlugin(Plugin):
    """Windows network management plugin with comprehensive networking support."""
    
    def __init__(self):
        metadata = PluginMetadata(
            id="windows_network_management",
            name="Windows Network Management",
            description="Network adapter, IP, DNS, routing, and diagnostics management",
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["windows", "network", "adapter", "ip", "dns", "routing", "wifi"]
        )
        super().__init__(metadata)

    async def initialize(self) -> bool:
        """Initialize plugin."""
        self._initialized = True
        return True

    async def _run_powershell(self, command: str, timeout: int = 60) -> Dict[str, Any]:
        """Execute a PowerShell command."""
        try:
            process = await asyncio.create_subprocess_exec(
                "powershell", "-NoProfile", "-Command", command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            return {
                "success": process.returncode == 0,
                "output": stdout.decode('utf-8', errors='replace').strip(),
                "error": stderr.decode('utf-8', errors='replace').strip() if stderr else None,
                "return_code": process.returncode
            }
        except asyncio.TimeoutError:
            return {"success": False, "error": "Command timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def execute(self, action: str = "status", parameters: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """Execute a network management operation."""
        if parameters is None:
            parameters = kwargs

        actions = {
            # Adapter management
            "status": self._get_status,
            "list_adapters": self._list_adapters,
            "get_adapter": self._get_adapter,
            "enable_adapter": self._enable_adapter,
            "disable_adapter": self._disable_adapter,
            "rename_adapter": self._rename_adapter,
            "restart_adapter": self._restart_adapter,
            # IP configuration
            "get_ip_config": self._get_ip_config,
            "set_static_ip": self._set_static_ip,
            "set_dhcp": self._set_dhcp,
            "get_ip_addresses": self._get_ip_addresses,
            "add_ip_address": self._add_ip_address,
            "remove_ip_address": self._remove_ip_address,
            # DNS
            "get_dns": self._get_dns,
            "set_dns": self._set_dns,
            "clear_dns_cache": self._clear_dns_cache,
            "get_dns_cache": self._get_dns_cache,
            # Routing
            "get_routes": self._get_routes,
            "add_route": self._add_route,
            "remove_route": self._remove_route,
            "get_default_gateway": self._get_default_gateway,
            # Diagnostics
            "ping": self._ping,
            "traceroute": self._traceroute,
            "test_port": self._test_port,
            "get_connections": self._get_connections,
            "resolve_dns": self._resolve_dns,
            # Wi-Fi
            "list_wifi_networks": self._list_wifi_networks,
            "get_wifi_profile": self._get_wifi_profile,
            "connect_wifi": self._connect_wifi,
            "disconnect_wifi": self._disconnect_wifi,
            "forget_wifi": self._forget_wifi,
            # Network profiles
            "get_network_profile": self._get_network_profile,
            "set_network_category": self._set_network_category,
            # Statistics
            "get_adapter_statistics": self._get_adapter_statistics,
            "get_bandwidth_usage": self._get_bandwidth_usage,
        }

        if action not in actions:
            return {"success": False, "error": f"Unknown action: {action}. Available: {list(actions.keys())}"}

        try:
            return await actions[action](parameters)
        except Exception as e:
            logger.error(f"Network operation failed: {e}")
            return {"success": False, "error": str(e)}

    # Adapter management
    async def _get_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get network status overview."""
        cmd = "Get-NetAdapter | Select-Object Name,Status,MacAddress,LinkSpeed,InterfaceDescription | ConvertTo-Json"
        result = await self._run_powershell(cmd)
        if result["success"]:
            try:
                adapters = json.loads(result["output"]) if result["output"] else []
                if isinstance(adapters, dict):
                    adapters = [adapters]
                return {"success": True, "adapters": adapters, "count": len(adapters)}
            except json.JSONDecodeError:
                return result
        return result

    async def _list_adapters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List all network adapters with details."""
        include_hidden = params.get("include_hidden", False)
        cmd = "Get-NetAdapter"
        if include_hidden:
            cmd += " -IncludeHidden"
        cmd += " | Select-Object Name,InterfaceIndex,InterfaceDescription,Status,MacAddress,LinkSpeed,MediaType,PhysicalMediaType,AdminStatus,MediaConnectionState | ConvertTo-Json"
        result = await self._run_powershell(cmd)
        if result["success"]:
            try:
                adapters = json.loads(result["output"]) if result["output"] else []
                if isinstance(adapters, dict):
                    adapters = [adapters]
                return {"success": True, "adapters": adapters, "count": len(adapters)}
            except json.JSONDecodeError:
                return result
        return result

    async def _get_adapter(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get details for a specific adapter."""
        name = params.get("name") or params.get("adapter")
        if not name:
            return {"success": False, "error": "adapter name required"}
        
        cmd = f"Get-NetAdapter -Name '{name}' | Select-Object * | ConvertTo-Json -Depth 2"
        result = await self._run_powershell(cmd)
        if result["success"]:
            try:
                adapter = json.loads(result["output"]) if result["output"] else None
                return {"success": True, "adapter": adapter}
            except json.JSONDecodeError:
                return result
        return result

    async def _enable_adapter(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Enable a network adapter."""
        name = params.get("name") or params.get("adapter")
        if not name:
            return {"success": False, "error": "adapter name required"}
        
        cmd = f"Enable-NetAdapter -Name '{name}' -Confirm:$false"
        result = await self._run_powershell(cmd)
        if result["success"]:
            return {"success": True, "message": f"Adapter '{name}' enabled"}
        return result

    async def _disable_adapter(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Disable a network adapter."""
        name = params.get("name") or params.get("adapter")
        if not name:
            return {"success": False, "error": "adapter name required"}
        
        cmd = f"Disable-NetAdapter -Name '{name}' -Confirm:$false"
        result = await self._run_powershell(cmd)
        if result["success"]:
            return {"success": True, "message": f"Adapter '{name}' disabled"}
        return result

    async def _rename_adapter(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Rename a network adapter."""
        name = params.get("name") or params.get("adapter")
        new_name = params.get("new_name")
        if not name or not new_name:
            return {"success": False, "error": "name and new_name required"}
        
        cmd = f"Rename-NetAdapter -Name '{name}' -NewName '{new_name}'"
        result = await self._run_powershell(cmd)
        if result["success"]:
            return {"success": True, "message": f"Adapter renamed from '{name}' to '{new_name}'"}
        return result

    async def _restart_adapter(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Restart a network adapter."""
        name = params.get("name") or params.get("adapter")
        if not name:
            return {"success": False, "error": "adapter name required"}
        
        cmd = f"Restart-NetAdapter -Name '{name}' -Confirm:$false"
        result = await self._run_powershell(cmd)
        if result["success"]:
            return {"success": True, "message": f"Adapter '{name}' restarted"}
        return result

    # IP configuration
    async def _get_ip_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get IP configuration."""
        adapter = params.get("adapter") or params.get("name")
        cmd = "Get-NetIPConfiguration"
        if adapter:
            cmd += f" -InterfaceAlias '{adapter}'"
        cmd += " | Select-Object InterfaceAlias,InterfaceIndex,IPv4Address,IPv6Address,IPv4DefaultGateway,DNSServer | ConvertTo-Json -Depth 3"
        result = await self._run_powershell(cmd)
        if result["success"]:
            try:
                config = json.loads(result["output"]) if result["output"] else []
                if isinstance(config, dict):
                    config = [config]
                return {"success": True, "configurations": config}
            except json.JSONDecodeError:
                return result
        return result

    async def _set_static_ip(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set static IP address."""
        adapter = params.get("adapter") or params.get("name")
        ip = params.get("ip") or params.get("ip_address")
        prefix = params.get("prefix_length", 24)
        gateway = params.get("gateway")
        
        if not adapter or not ip:
            return {"success": False, "error": "adapter and ip required"}
        
        # Remove existing IP
        remove_cmd = f"Remove-NetIPAddress -InterfaceAlias '{adapter}' -Confirm:$false -ErrorAction SilentlyContinue"
        await self._run_powershell(remove_cmd)
        
        # Set new IP
        cmd = f"New-NetIPAddress -InterfaceAlias '{adapter}' -IPAddress '{ip}' -PrefixLength {prefix}"
        if gateway:
            cmd += f" -DefaultGateway '{gateway}'"
        
        result = await self._run_powershell(cmd)
        if result["success"]:
            return {"success": True, "message": f"Static IP {ip}/{prefix} set on {adapter}"}
        return result

    async def _set_dhcp(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Enable DHCP on adapter."""
        adapter = params.get("adapter") or params.get("name")
        if not adapter:
            return {"success": False, "error": "adapter required"}
        
        cmd = f"Set-NetIPInterface -InterfaceAlias '{adapter}' -Dhcp Enabled"
        result = await self._run_powershell(cmd)
        if result["success"]:
            return {"success": True, "message": f"DHCP enabled on {adapter}"}
        return result

    async def _get_ip_addresses(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get all IP addresses."""
        adapter = params.get("adapter")
        cmd = "Get-NetIPAddress"
        if adapter:
            cmd += f" -InterfaceAlias '{adapter}'"
        cmd += " | Select-Object InterfaceAlias,IPAddress,AddressFamily,PrefixLength,Type,ValidLifetime | ConvertTo-Json"
        result = await self._run_powershell(cmd)
        if result["success"]:
            try:
                addresses = json.loads(result["output"]) if result["output"] else []
                if isinstance(addresses, dict):
                    addresses = [addresses]
                return {"success": True, "addresses": addresses, "count": len(addresses)}
            except json.JSONDecodeError:
                return result
        return result

    async def _add_ip_address(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add an IP address to adapter."""
        adapter = params.get("adapter")
        ip = params.get("ip")
        prefix = params.get("prefix_length", 24)
        
        if not adapter or not ip:
            return {"success": False, "error": "adapter and ip required"}
        
        cmd = f"New-NetIPAddress -InterfaceAlias '{adapter}' -IPAddress '{ip}' -PrefixLength {prefix} -SkipAsSource:$false"
        return await self._run_powershell(cmd)

    async def _remove_ip_address(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove an IP address."""
        adapter = params.get("adapter")
        ip = params.get("ip")
        
        if not ip:
            return {"success": False, "error": "ip required"}
        
        cmd = f"Remove-NetIPAddress -IPAddress '{ip}' -Confirm:$false"
        if adapter:
            cmd = f"Remove-NetIPAddress -InterfaceAlias '{adapter}' -IPAddress '{ip}' -Confirm:$false"
        
        return await self._run_powershell(cmd)

    # DNS
    async def _get_dns(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get DNS server addresses."""
        adapter = params.get("adapter")
        cmd = "Get-DnsClientServerAddress"
        if adapter:
            cmd += f" -InterfaceAlias '{adapter}'"
        cmd += " | Select-Object InterfaceAlias,ServerAddresses,AddressFamily | ConvertTo-Json"
        result = await self._run_powershell(cmd)
        if result["success"]:
            try:
                dns = json.loads(result["output"]) if result["output"] else []
                if isinstance(dns, dict):
                    dns = [dns]
                return {"success": True, "dns_servers": dns}
            except json.JSONDecodeError:
                return result
        return result

    async def _set_dns(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set DNS servers."""
        adapter = params.get("adapter")
        servers = params.get("servers") or params.get("dns")
        
        if not adapter:
            return {"success": False, "error": "adapter required"}
        if not servers:
            return {"success": False, "error": "servers list required"}
        
        if isinstance(servers, list):
            servers_str = "','".join(servers)
            servers_str = f"'{servers_str}'"
        else:
            servers_str = f"'{servers}'"
        
        cmd = f"Set-DnsClientServerAddress -InterfaceAlias '{adapter}' -ServerAddresses ({servers_str})"
        result = await self._run_powershell(cmd)
        if result["success"]:
            return {"success": True, "message": f"DNS servers set on {adapter}"}
        return result

    async def _clear_dns_cache(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Clear DNS cache."""
        cmd = "Clear-DnsClientCache"
        result = await self._run_powershell(cmd)
        if result["success"]:
            return {"success": True, "message": "DNS cache cleared"}
        return result

    async def _get_dns_cache(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get DNS cache entries."""
        cmd = "Get-DnsClientCache | Select-Object Entry,Data,DataLength,TimeToLive,Type,Status | ConvertTo-Json"
        result = await self._run_powershell(cmd)
        if result["success"]:
            try:
                cache = json.loads(result["output"]) if result["output"] else []
                if isinstance(cache, dict):
                    cache = [cache]
                return {"success": True, "cache_entries": cache, "count": len(cache)}
            except json.JSONDecodeError:
                return result
        return result

    # Routing
    async def _get_routes(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get routing table."""
        cmd = "Get-NetRoute | Select-Object DestinationPrefix,NextHop,InterfaceAlias,InterfaceIndex,RouteMetric,Protocol | ConvertTo-Json"
        result = await self._run_powershell(cmd)
        if result["success"]:
            try:
                routes = json.loads(result["output"]) if result["output"] else []
                if isinstance(routes, dict):
                    routes = [routes]
                return {"success": True, "routes": routes, "count": len(routes)}
            except json.JSONDecodeError:
                return result
        return result

    async def _add_route(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add a route."""
        destination = params.get("destination")
        next_hop = params.get("next_hop") or params.get("gateway")
        interface = params.get("interface") or params.get("adapter")
        metric = params.get("metric")
        
        if not destination:
            return {"success": False, "error": "destination required"}
        
        cmd = f"New-NetRoute -DestinationPrefix '{destination}'"
        if next_hop:
            cmd += f" -NextHop '{next_hop}'"
        if interface:
            cmd += f" -InterfaceAlias '{interface}'"
        if metric:
            cmd += f" -RouteMetric {metric}"
        
        return await self._run_powershell(cmd)

    async def _remove_route(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove a route."""
        destination = params.get("destination")
        if not destination:
            return {"success": False, "error": "destination required"}
        
        cmd = f"Remove-NetRoute -DestinationPrefix '{destination}' -Confirm:$false"
        return await self._run_powershell(cmd)

    async def _get_default_gateway(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get default gateway."""
        cmd = "Get-NetRoute -DestinationPrefix '0.0.0.0/0' | Select-Object NextHop,InterfaceAlias,RouteMetric | ConvertTo-Json"
        result = await self._run_powershell(cmd)
        if result["success"]:
            try:
                gateways = json.loads(result["output"]) if result["output"] else []
                if isinstance(gateways, dict):
                    gateways = [gateways]
                return {"success": True, "gateways": gateways}
            except json.JSONDecodeError:
                return result
        return result

    # Diagnostics
    async def _ping(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Ping a host."""
        target = params.get("target") or params.get("host")
        count = params.get("count", 4)
        
        if not target:
            return {"success": False, "error": "target required"}
        
        cmd = f"Test-Connection -ComputerName '{target}' -Count {count} | Select-Object Address,Latency,Status | ConvertTo-Json"
        result = await self._run_powershell(cmd, timeout=30)
        if result["success"]:
            try:
                pings = json.loads(result["output"]) if result["output"] else []
                if isinstance(pings, dict):
                    pings = [pings]
                return {"success": True, "results": pings, "target": target}
            except json.JSONDecodeError:
                return {"success": True, "target": target, "raw_output": result["output"]}
        return result

    async def _traceroute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Trace route to host."""
        target = params.get("target") or params.get("host")
        hops = params.get("hops", 30)
        
        if not target:
            return {"success": False, "error": "target required"}
        
        cmd = f"Test-NetConnection -ComputerName '{target}' -TraceRoute | Select-Object -ExpandProperty TraceRoute"
        result = await self._run_powershell(cmd, timeout=120)
        if result["success"]:
            hops_list = result["output"].split('\n') if result["output"] else []
            return {"success": True, "target": target, "hops": [h.strip() for h in hops_list if h.strip()]}
        return result

    async def _test_port(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Test TCP port connectivity."""
        target = params.get("target") or params.get("host")
        port = params.get("port")
        
        if not target or not port:
            return {"success": False, "error": "target and port required"}
        
        cmd = f"Test-NetConnection -ComputerName '{target}' -Port {port} | Select-Object ComputerName,RemotePort,TcpTestSucceeded,PingSucceeded | ConvertTo-Json"
        result = await self._run_powershell(cmd, timeout=30)
        if result["success"]:
            try:
                test = json.loads(result["output"]) if result["output"] else None
                return {"success": True, "test_result": test}
            except json.JSONDecodeError:
                return result
        return result

    async def _get_connections(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get active TCP connections."""
        state = params.get("state")
        cmd = "Get-NetTCPConnection"
        if state:
            cmd += f" -State {state}"
        cmd += " | Select-Object LocalAddress,LocalPort,RemoteAddress,RemotePort,State,OwningProcess | ConvertTo-Json"
        result = await self._run_powershell(cmd)
        if result["success"]:
            try:
                connections = json.loads(result["output"]) if result["output"] else []
                if isinstance(connections, dict):
                    connections = [connections]
                return {"success": True, "connections": connections, "count": len(connections)}
            except json.JSONDecodeError:
                return result
        return result

    async def _resolve_dns(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve DNS name."""
        name = params.get("name") or params.get("hostname")
        record_type = params.get("type", "A")
        
        if not name:
            return {"success": False, "error": "name required"}
        
        cmd = f"Resolve-DnsName -Name '{name}' -Type {record_type} | ConvertTo-Json"
        result = await self._run_powershell(cmd)
        if result["success"]:
            try:
                records = json.loads(result["output"]) if result["output"] else []
                if isinstance(records, dict):
                    records = [records]
                return {"success": True, "records": records}
            except json.JSONDecodeError:
                return result
        return result

    # Wi-Fi
    async def _list_wifi_networks(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List available Wi-Fi networks."""
        cmd = "netsh wlan show networks mode=bssid"
        result = await self._run_powershell(cmd)
        if result["success"]:
            return {"success": True, "networks_raw": result["output"]}
        return result

    async def _get_wifi_profile(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get Wi-Fi profile details."""
        name = params.get("name") or params.get("ssid")
        if not name:
            return {"success": False, "error": "profile name/ssid required"}
        
        cmd = f"netsh wlan show profile name='{name}' key=clear"
        result = await self._run_powershell(cmd)
        if result["success"]:
            return {"success": True, "profile": result["output"]}
        return result

    async def _connect_wifi(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Connect to Wi-Fi network."""
        name = params.get("name") or params.get("ssid")
        if not name:
            return {"success": False, "error": "network name/ssid required"}
        
        cmd = f"netsh wlan connect name='{name}'"
        result = await self._run_powershell(cmd)
        if result["success"]:
            return {"success": True, "message": f"Connecting to {name}"}
        return result

    async def _disconnect_wifi(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Disconnect from Wi-Fi."""
        cmd = "netsh wlan disconnect"
        result = await self._run_powershell(cmd)
        if result["success"]:
            return {"success": True, "message": "Disconnected from Wi-Fi"}
        return result

    async def _forget_wifi(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Forget/delete a Wi-Fi profile."""
        name = params.get("name") or params.get("ssid")
        if not name:
            return {"success": False, "error": "profile name/ssid required"}
        
        cmd = f"netsh wlan delete profile name='{name}'"
        result = await self._run_powershell(cmd)
        if result["success"]:
            return {"success": True, "message": f"Profile '{name}' deleted"}
        return result

    # Network profiles
    async def _get_network_profile(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get network connection profiles."""
        cmd = "Get-NetConnectionProfile | Select-Object Name,InterfaceAlias,NetworkCategory,IPv4Connectivity,IPv6Connectivity | ConvertTo-Json"
        result = await self._run_powershell(cmd)
        if result["success"]:
            try:
                profiles = json.loads(result["output"]) if result["output"] else []
                if isinstance(profiles, dict):
                    profiles = [profiles]
                return {"success": True, "profiles": profiles}
            except json.JSONDecodeError:
                return result
        return result

    async def _set_network_category(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set network category (Public/Private/DomainAuthenticated)."""
        adapter = params.get("adapter") or params.get("interface")
        category = params.get("category")
        
        if not adapter or not category:
            return {"success": False, "error": "adapter and category required"}
        
        if category not in ["Public", "Private", "DomainAuthenticated"]:
            return {"success": False, "error": "category must be Public, Private, or DomainAuthenticated"}
        
        cmd = f"Set-NetConnectionProfile -InterfaceAlias '{adapter}' -NetworkCategory {category}"
        result = await self._run_powershell(cmd)
        if result["success"]:
            return {"success": True, "message": f"Network category set to {category}"}
        return result

    # Statistics
    async def _get_adapter_statistics(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get adapter statistics."""
        adapter = params.get("adapter")
        cmd = "Get-NetAdapterStatistics"
        if adapter:
            cmd += f" -Name '{adapter}'"
        cmd += " | Select-Object Name,ReceivedBytes,SentBytes,ReceivedUnicastPackets,SentUnicastPackets,ReceivedDiscards,OutboundDiscards | ConvertTo-Json"
        result = await self._run_powershell(cmd)
        if result["success"]:
            try:
                stats = json.loads(result["output"]) if result["output"] else []
                if isinstance(stats, dict):
                    stats = [stats]
                return {"success": True, "statistics": stats}
            except json.JSONDecodeError:
                return result
        return result

    async def _get_bandwidth_usage(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get bandwidth usage per process."""
        cmd = "Get-NetTCPConnection | Group-Object OwningProcess | ForEach-Object { $proc = Get-Process -Id $_.Name -ErrorAction SilentlyContinue; [PSCustomObject]@{ProcessId=$_.Name; ProcessName=$proc.ProcessName; Connections=$_.Count} } | ConvertTo-Json"
        result = await self._run_powershell(cmd)
        if result["success"]:
            try:
                usage = json.loads(result["output"]) if result["output"] else []
                if isinstance(usage, dict):
                    usage = [usage]
                return {"success": True, "usage": usage}
            except json.JSONDecodeError:
                return result
        return result

    def get_schema(self) -> Dict[str, Any]:
        """Return the plugin schema."""
        return {
            "type": "object",
            "actions": {
                "status": "Get network overview",
                "list_adapters": "List all network adapters",
                "get_adapter": "Get adapter details",
                "enable_adapter": "Enable adapter",
                "disable_adapter": "Disable adapter",
                "get_ip_config": "Get IP configuration",
                "set_static_ip": "Set static IP",
                "set_dhcp": "Enable DHCP",
                "get_dns": "Get DNS servers",
                "set_dns": "Set DNS servers",
                "clear_dns_cache": "Clear DNS cache",
                "get_routes": "Get routing table",
                "add_route": "Add route",
                "ping": "Ping host",
                "traceroute": "Trace route",
                "test_port": "Test TCP port",
                "get_connections": "Get TCP connections",
                "list_wifi_networks": "List Wi-Fi networks",
                "connect_wifi": "Connect to Wi-Fi",
                "disconnect_wifi": "Disconnect Wi-Fi"
            }
        }


plugin = WindowsNetworkManagementPlugin()
