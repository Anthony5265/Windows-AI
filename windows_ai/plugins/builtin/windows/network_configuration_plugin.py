"""
Network Configuration Plugin for Windows AI
Comprehensive Windows network management and configuration
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class NetworkConfigurationPlugin(IntegrationPlugin):
    """
    Comprehensive network configuration plugin for Windows AI.
    
    Provides 55+ actions for:
    - Network adapter management
    - IP configuration
    - DNS settings
    - Network profiles
    - Firewall management
    - Network shares
    - Connection monitoring
    - Wi-Fi management
    - VPN configuration
    - Network diagnostics
    """

    def __init__(self):
        metadata = PluginMetadata(
            id="network-configuration",
            name="Network Configuration",
            description="Comprehensive Windows network management and configuration",
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["network", "windows", "dns", "firewall", "wifi", "vpn"]
        )
        super().__init__(metadata)

    async def _run_powershell(self, script: str, as_json: bool = True, timeout: int = 60) -> Dict[str, Any]:
        """Execute PowerShell script and return results."""
        try:
            json_suffix = " | ConvertTo-Json -Depth 10 -Compress" if as_json else ""
            full_script = f"$ErrorActionPreference = 'Stop'; {script}{json_suffix}"
            
            process = await asyncio.create_subprocess_exec(
                "powershell.exe", "-NoProfile", "-NonInteractive", "-Command", full_script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                process.kill()
                return {"success": False, "error": f"Command timed out after {timeout} seconds"}
            
            if process.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='replace').strip()
                return {"success": False, "error": error_msg, "returncode": process.returncode}
            
            output = stdout.decode('utf-8', errors='replace').strip()
            if as_json and output:
                import json
                try:
                    return {"success": True, "data": json.loads(output)}
                except json.JSONDecodeError:
                    return {"success": True, "data": output}
            return {"success": True, "data": output if output else None}
        except Exception as e:
            logger.error(f"PowerShell execution failed: {e}")
            return {"success": False, "error": str(e)}


    async def connect(self, credentials: Dict[str, str]) -> bool:
        """Connect to the service"""
        return True

    async def disconnect(self) -> bool:
        """Disconnect from the service"""
        return True

    async def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """Execute network configuration actions."""
        actions = {
            # Network Adapters
            "list_adapters": self._list_adapters,
            "get_adapter_info": self._get_adapter_info,
            "enable_adapter": self._enable_adapter,
            "disable_adapter": self._disable_adapter,
            "rename_adapter": self._rename_adapter,
            "restart_adapter": self._restart_adapter,
            "get_adapter_statistics": self._get_adapter_statistics,
            "get_adapter_hardware": self._get_adapter_hardware,
            "set_adapter_property": self._set_adapter_property,
            
            # IP Configuration
            "get_ip_configuration": self._get_ip_configuration,
            "set_static_ip": self._set_static_ip,
            "set_dhcp": self._set_dhcp,
            "add_ip_address": self._add_ip_address,
            "remove_ip_address": self._remove_ip_address,
            "get_ip_routes": self._get_ip_routes,
            "add_route": self._add_route,
            "remove_route": self._remove_route,
            "get_default_gateway": self._get_default_gateway,
            "set_default_gateway": self._set_default_gateway,
            
            # DNS Configuration
            "get_dns_servers": self._get_dns_servers,
            "set_dns_servers": self._set_dns_servers,
            "clear_dns_cache": self._clear_dns_cache,
            "get_dns_cache": self._get_dns_cache,
            "resolve_dns": self._resolve_dns,
            "get_dns_client_settings": self._get_dns_client_settings,
            "register_dns": self._register_dns,
            
            # Network Profiles
            "get_network_profiles": self._get_network_profiles,
            "set_network_category": self._set_network_category,
            "get_connection_profiles": self._get_connection_profiles,
            
            # Firewall
            "get_firewall_status": self._get_firewall_status,
            "enable_firewall": self._enable_firewall,
            "disable_firewall": self._disable_firewall,
            "get_firewall_rules": self._get_firewall_rules,
            "add_firewall_rule": self._add_firewall_rule,
            "remove_firewall_rule": self._remove_firewall_rule,
            "enable_firewall_rule": self._enable_firewall_rule,
            "disable_firewall_rule": self._disable_firewall_rule,
            
            # Network Shares
            "list_shares": self._list_shares,
            "create_share": self._create_share,
            "remove_share": self._remove_share,
            "get_share_access": self._get_share_access,
            "set_share_access": self._set_share_access,
            "list_mapped_drives": self._list_mapped_drives,
            "map_network_drive": self._map_network_drive,
            "remove_mapped_drive": self._remove_mapped_drive,
            
            # Connection Monitoring
            "get_active_connections": self._get_active_connections,
            "get_tcp_connections": self._get_tcp_connections,
            "get_udp_endpoints": self._get_udp_endpoints,
            "get_connection_by_port": self._get_connection_by_port,
            "get_listening_ports": self._get_listening_ports,
            
            # Wi-Fi Management
            "list_wifi_networks": self._list_wifi_networks,
            "get_wifi_profile": self._get_wifi_profile,
            "list_wifi_profiles": self._list_wifi_profiles,
            "connect_wifi": self._connect_wifi,
            "disconnect_wifi": self._disconnect_wifi,
            "remove_wifi_profile": self._remove_wifi_profile,
            "export_wifi_profile": self._export_wifi_profile,
            
            # VPN Configuration
            "list_vpn_connections": self._list_vpn_connections,
            "add_vpn_connection": self._add_vpn_connection,
            "remove_vpn_connection": self._remove_vpn_connection,
            "connect_vpn": self._connect_vpn,
            "disconnect_vpn": self._disconnect_vpn,
            "get_vpn_status": self._get_vpn_status,
            
            # Diagnostics
            "test_connection": self._test_connection,
            "trace_route": self._trace_route,
            "get_network_statistics": self._get_network_statistics,
            "reset_network_stack": self._reset_network_stack,
            "get_arp_table": self._get_arp_table,
            "get_netstat": self._get_netstat,
        }
        
        if action not in actions:
            return {
                "success": False,
                "error": f"Unknown action: {action}",
                "available_actions": list(actions.keys())
            }
        
        try:
            return await actions[action](**kwargs)
        except Exception as e:
            logger.error(f"Action {action} failed: {e}")
            return {"success": False, "error": str(e)}

    # Network Adapters
    async def _list_adapters(self, physical_only: bool = False, **kwargs) -> Dict[str, Any]:
        """List all network adapters."""
        filter_clause = "| Where-Object { $_.Physical -eq $true }" if physical_only else ""
        script = f'''
        Get-NetAdapter {filter_clause} | Select-Object Name, InterfaceDescription, Status, 
        MacAddress, LinkSpeed, MediaType, InterfaceIndex, ifIndex,
        @{{N='PhysicalAddress';E={{$_.MacAddress}}}},
        @{{N='IsPhysical';E={{$_.Physical}}}},
        @{{N='MediaConnectionState';E={{$_.MediaConnectionState.ToString()}}}}
        '''
        return await self._run_powershell(script)

    async def _get_adapter_info(self, adapter_name: str, **kwargs) -> Dict[str, Any]:
        """Get detailed information about a network adapter."""
        script = f'''
        $adapter = Get-NetAdapter -Name "{adapter_name}"
        $ipConfig = Get-NetIPConfiguration -InterfaceIndex $adapter.ifIndex
        $ipAddresses = Get-NetIPAddress -InterfaceIndex $adapter.ifIndex
        
        @{{
            Name = $adapter.Name
            Description = $adapter.InterfaceDescription
            Status = $adapter.Status.ToString()
            MacAddress = $adapter.MacAddress
            LinkSpeed = $adapter.LinkSpeed
            MediaType = $adapter.MediaType
            InterfaceIndex = $adapter.ifIndex
            DriverVersion = $adapter.DriverVersion
            DriverDate = $adapter.DriverDate
            DriverDescription = $adapter.DriverDescription
            DriverProvider = $adapter.DriverProvider
            IsPhysical = $adapter.Physical
            MediaConnectionState = $adapter.MediaConnectionState.ToString()
            AdminStatus = $adapter.AdminStatus.ToString()
            IPv4Addresses = @($ipAddresses | Where-Object {{ $_.AddressFamily -eq "IPv4" }} | Select-Object IPAddress, PrefixLength)
            IPv6Addresses = @($ipAddresses | Where-Object {{ $_.AddressFamily -eq "IPv6" }} | Select-Object IPAddress, PrefixLength)
            DNSServers = $ipConfig.DNSServer.ServerAddresses
            DefaultGateway = $ipConfig.IPv4DefaultGateway.NextHop
        }}
        '''
        return await self._run_powershell(script)

    async def _enable_adapter(self, adapter_name: str, **kwargs) -> Dict[str, Any]:
        """Enable a network adapter."""
        script = f'''
        Enable-NetAdapter -Name "{adapter_name}" -Confirm:$false
        Start-Sleep -Seconds 2
        $adapter = Get-NetAdapter -Name "{adapter_name}"
        @{{ Success = $true; Status = $adapter.Status.ToString() }}
        '''
        return await self._run_powershell(script)

    async def _disable_adapter(self, adapter_name: str, **kwargs) -> Dict[str, Any]:
        """Disable a network adapter."""
        script = f'''
        Disable-NetAdapter -Name "{adapter_name}" -Confirm:$false
        Start-Sleep -Seconds 2
        $adapter = Get-NetAdapter -Name "{adapter_name}"
        @{{ Success = $true; Status = $adapter.Status.ToString() }}
        '''
        return await self._run_powershell(script)

    async def _rename_adapter(self, adapter_name: str, new_name: str, **kwargs) -> Dict[str, Any]:
        """Rename a network adapter."""
        script = f'''
        Rename-NetAdapter -Name "{adapter_name}" -NewName "{new_name}"
        @{{ Success = $true; NewName = "{new_name}" }}
        '''
        return await self._run_powershell(script)

    async def _restart_adapter(self, adapter_name: str, **kwargs) -> Dict[str, Any]:
        """Restart a network adapter."""
        script = f'''
        Restart-NetAdapter -Name "{adapter_name}" -Confirm:$false
        Start-Sleep -Seconds 3
        $adapter = Get-NetAdapter -Name "{adapter_name}"
        @{{ Success = $true; Status = $adapter.Status.ToString() }}
        '''
        return await self._run_powershell(script)

    async def _get_adapter_statistics(self, adapter_name: str, **kwargs) -> Dict[str, Any]:
        """Get network adapter statistics."""
        script = f'''
        $stats = Get-NetAdapterStatistics -Name "{adapter_name}"
        @{{
            Name = $stats.Name
            ReceivedBytes = $stats.ReceivedBytes
            SentBytes = $stats.SentBytes
            ReceivedUnicastPackets = $stats.ReceivedUnicastPackets
            SentUnicastPackets = $stats.SentUnicastPackets
            ReceivedMulticastPackets = $stats.ReceivedMulticastPackets
            SentMulticastPackets = $stats.SentMulticastPackets
            ReceivedBroadcastPackets = $stats.ReceivedBroadcastPackets
            SentBroadcastPackets = $stats.SentBroadcastPackets
            ReceivedDiscardedPackets = $stats.ReceivedDiscardedPackets
            OutboundDiscardedPackets = $stats.OutboundDiscardedPackets
            ReceivedPacketErrors = $stats.ReceivedPacketErrors
            OutboundPacketErrors = $stats.OutboundPacketErrors
        }}
        '''
        return await self._run_powershell(script)

    async def _get_adapter_hardware(self, adapter_name: str, **kwargs) -> Dict[str, Any]:
        """Get network adapter hardware information."""
        script = f'''
        $adapter = Get-NetAdapter -Name "{adapter_name}"
        $hw = Get-NetAdapterHardwareInfo -Name "{adapter_name}"
        @{{
            Name = $adapter.Name
            InterfaceDescription = $adapter.InterfaceDescription
            DeviceID = $hw.DeviceID
            LocationInformationString = $hw.LocationInformationString
            Bus = $hw.Bus
            Device = $hw.Device
            Function = $hw.Function
            Slot = $hw.Slot
            NumaNode = $hw.NumaNode
            PciDeviceLabelString = $hw.PciDeviceLabelString
        }}
        '''
        return await self._run_powershell(script)

    async def _set_adapter_property(self, adapter_name: str, property_name: str, 
                                     value: str, **kwargs) -> Dict[str, Any]:
        """Set a network adapter advanced property."""
        script = f'''
        Set-NetAdapterAdvancedProperty -Name "{adapter_name}" -DisplayName "{property_name}" -DisplayValue "{value}"
        @{{ Success = $true; Property = "{property_name}"; Value = "{value}" }}
        '''
        return await self._run_powershell(script)

    # IP Configuration
    async def _get_ip_configuration(self, adapter_name: str = None, **kwargs) -> Dict[str, Any]:
        """Get IP configuration for adapters."""
        filter_clause = f'-InterfaceAlias "{adapter_name}"' if adapter_name else ""
        script = f'''
        Get-NetIPConfiguration {filter_clause} | ForEach-Object {{
            @{{
                InterfaceAlias = $_.InterfaceAlias
                InterfaceIndex = $_.InterfaceIndex
                IPv4Address = $_.IPv4Address.IPAddress
                IPv4SubnetMask = $_.IPv4Address.PrefixLength
                IPv6Address = $_.IPv6Address.IPAddress
                IPv4DefaultGateway = $_.IPv4DefaultGateway.NextHop
                IPv6DefaultGateway = $_.IPv6DefaultGateway.NextHop
                DNSServer = $_.DNSServer.ServerAddresses
                NetProfile = @{{
                    Name = $_.NetProfile.Name
                    NetworkCategory = $_.NetProfile.NetworkCategory.ToString()
                }}
            }}
        }}
        '''
        return await self._run_powershell(script)

    async def _set_static_ip(self, adapter_name: str, ip_address: str, 
                             prefix_length: int, gateway: str = None,
                             dns_servers: List[str] = None, **kwargs) -> Dict[str, Any]:
        """Set a static IP address on an adapter."""
        dns_params = ""
        if dns_servers:
            dns_list = ", ".join([f'"{d}"' for d in dns_servers])
            dns_params = f'Set-DnsClientServerAddress -InterfaceAlias "{adapter_name}" -ServerAddresses @({dns_list})'
        
        gateway_params = ""
        if gateway:
            gateway_params = f'New-NetRoute -InterfaceAlias "{adapter_name}" -DestinationPrefix "0.0.0.0/0" -NextHop "{gateway}" -ErrorAction SilentlyContinue'
        
        script = f'''
        # Remove existing IP and routes
        Remove-NetIPAddress -InterfaceAlias "{adapter_name}" -Confirm:$false -ErrorAction SilentlyContinue
        Remove-NetRoute -InterfaceAlias "{adapter_name}" -DestinationPrefix "0.0.0.0/0" -Confirm:$false -ErrorAction SilentlyContinue
        
        # Set new static IP
        New-NetIPAddress -InterfaceAlias "{adapter_name}" -IPAddress "{ip_address}" -PrefixLength {prefix_length}
        
        # Set gateway
        {gateway_params}
        
        # Set DNS
        {dns_params}
        
        # Get new configuration
        $config = Get-NetIPConfiguration -InterfaceAlias "{adapter_name}"
        @{{
            Success = $true
            IPAddress = $config.IPv4Address.IPAddress
            Gateway = $config.IPv4DefaultGateway.NextHop
            DNS = $config.DNSServer.ServerAddresses
        }}
        '''
        return await self._run_powershell(script, timeout=30)

    async def _set_dhcp(self, adapter_name: str, **kwargs) -> Dict[str, Any]:
        """Enable DHCP on an adapter."""
        script = f'''
        # Enable DHCP for IP
        Set-NetIPInterface -InterfaceAlias "{adapter_name}" -Dhcp Enabled
        
        # Enable DHCP for DNS
        Set-DnsClientServerAddress -InterfaceAlias "{adapter_name}" -ResetServerAddresses
        
        # Remove static routes
        Remove-NetRoute -InterfaceAlias "{adapter_name}" -DestinationPrefix "0.0.0.0/0" -Confirm:$false -ErrorAction SilentlyContinue
        
        @{{ Success = $true; Message = "DHCP enabled" }}
        '''
        return await self._run_powershell(script)

    async def _add_ip_address(self, adapter_name: str, ip_address: str, 
                              prefix_length: int, **kwargs) -> Dict[str, Any]:
        """Add an additional IP address to an adapter."""
        script = f'''
        New-NetIPAddress -InterfaceAlias "{adapter_name}" -IPAddress "{ip_address}" -PrefixLength {prefix_length} -SkipAsSource $true
        @{{ Success = $true; IPAddress = "{ip_address}" }}
        '''
        return await self._run_powershell(script)

    async def _remove_ip_address(self, adapter_name: str, ip_address: str, **kwargs) -> Dict[str, Any]:
        """Remove an IP address from an adapter."""
        script = f'''
        Remove-NetIPAddress -InterfaceAlias "{adapter_name}" -IPAddress "{ip_address}" -Confirm:$false
        @{{ Success = $true; Removed = "{ip_address}" }}
        '''
        return await self._run_powershell(script)

    async def _get_ip_routes(self, destination: str = None, **kwargs) -> Dict[str, Any]:
        """Get IP routing table."""
        filter_clause = f'-DestinationPrefix "{destination}"' if destination else ""
        script = f'''
        Get-NetRoute {filter_clause} | Select-Object DestinationPrefix, NextHop, 
        @{{N='InterfaceAlias';E={{(Get-NetAdapter -InterfaceIndex $_.ifIndex).Name}}}},
        InterfaceIndex, RouteMetric,
        @{{N='Protocol';E={{$_.Protocol.ToString()}}}},
        @{{N='State';E={{$_.State.ToString()}}}}
        '''
        return await self._run_powershell(script)

    async def _add_route(self, destination: str, next_hop: str, 
                         adapter_name: str = None, metric: int = None, **kwargs) -> Dict[str, Any]:
        """Add a network route."""
        params = [f'-DestinationPrefix "{destination}"', f'-NextHop "{next_hop}"']
        if adapter_name:
            params.append(f'-InterfaceAlias "{adapter_name}"')
        if metric:
            params.append(f'-RouteMetric {metric}')
        
        script = f'''
        New-NetRoute {" ".join(params)}
        @{{ Success = $true; Destination = "{destination}"; NextHop = "{next_hop}" }}
        '''
        return await self._run_powershell(script)

    async def _remove_route(self, destination: str, next_hop: str = None, **kwargs) -> Dict[str, Any]:
        """Remove a network route."""
        hop_filter = f'-NextHop "{next_hop}"' if next_hop else ""
        script = f'''
        Remove-NetRoute -DestinationPrefix "{destination}" {hop_filter} -Confirm:$false
        @{{ Success = $true; Removed = "{destination}" }}
        '''
        return await self._run_powershell(script)

    async def _get_default_gateway(self, adapter_name: str = None, **kwargs) -> Dict[str, Any]:
        """Get default gateway configuration."""
        filter_clause = f'-InterfaceAlias "{adapter_name}"' if adapter_name else ""
        script = f'''
        Get-NetRoute -DestinationPrefix "0.0.0.0/0" {filter_clause} | Select-Object NextHop, 
        @{{N='InterfaceAlias';E={{(Get-NetAdapter -InterfaceIndex $_.ifIndex).Name}}}},
        InterfaceIndex, RouteMetric
        '''
        return await self._run_powershell(script)

    async def _set_default_gateway(self, adapter_name: str, gateway: str, **kwargs) -> Dict[str, Any]:
        """Set the default gateway for an adapter."""
        script = f'''
        Remove-NetRoute -InterfaceAlias "{adapter_name}" -DestinationPrefix "0.0.0.0/0" -Confirm:$false -ErrorAction SilentlyContinue
        New-NetRoute -InterfaceAlias "{adapter_name}" -DestinationPrefix "0.0.0.0/0" -NextHop "{gateway}"
        @{{ Success = $true; Gateway = "{gateway}" }}
        '''
        return await self._run_powershell(script)

    # DNS Configuration
    async def _get_dns_servers(self, adapter_name: str = None, **kwargs) -> Dict[str, Any]:
        """Get DNS server configuration."""
        filter_clause = f'-InterfaceAlias "{adapter_name}"' if adapter_name else ""
        script = f'''
        Get-DnsClientServerAddress {filter_clause} | Where-Object {{ $_.AddressFamily -eq 2 }} |
        Select-Object InterfaceAlias, InterfaceIndex, 
        @{{N='ServerAddresses';E={{$_.ServerAddresses}}}}
        '''
        return await self._run_powershell(script)

    async def _set_dns_servers(self, adapter_name: str, dns_servers: List[str], **kwargs) -> Dict[str, Any]:
        """Set DNS servers for an adapter."""
        dns_list = ", ".join([f'"{d}"' for d in dns_servers])
        script = f'''
        Set-DnsClientServerAddress -InterfaceAlias "{adapter_name}" -ServerAddresses @({dns_list})
        @{{ Success = $true; DNSServers = @({dns_list}) }}
        '''
        return await self._run_powershell(script)

    async def _clear_dns_cache(self, **kwargs) -> Dict[str, Any]:
        """Clear the DNS resolver cache."""
        script = '''
        Clear-DnsClientCache
        @{ Success = $true; Message = "DNS cache cleared" }
        '''
        return await self._run_powershell(script)

    async def _get_dns_cache(self, name: str = None, **kwargs) -> Dict[str, Any]:
        """Get DNS resolver cache entries."""
        filter_clause = f'| Where-Object {{ $_.Entry -like "*{name}*" }}' if name else "| Select-Object -First 100"
        script = f'''
        Get-DnsClientCache {filter_clause} | Select-Object Entry, Name, Type, 
        @{{N='Status';E={{$_.Status.ToString()}}}}, Section, TimeToLive, DataLength, Data
        '''
        return await self._run_powershell(script)

    async def _resolve_dns(self, hostname: str, record_type: str = "A", **kwargs) -> Dict[str, Any]:
        """Resolve a DNS name."""
        script = f'''
        $result = Resolve-DnsName -Name "{hostname}" -Type {record_type} -ErrorAction SilentlyContinue
        if ($result) {{
            $result | Select-Object Name, Type, TTL, Section, 
            @{{N='IPAddress';E={{if($_.IP4Address){{$_.IP4Address}}elseif($_.IP6Address){{$_.IP6Address}}else{{$null}}}}}},
            @{{N='Data';E={{if($_.NameHost){{$_.NameHost}}elseif($_.Strings){{$_.Strings}}else{{$null}}}}}}
        }} else {{
            @{{ Success = $false; Error = "DNS resolution failed" }}
        }}
        '''
        return await self._run_powershell(script)

    async def _get_dns_client_settings(self, **kwargs) -> Dict[str, Any]:
        """Get DNS client global settings."""
        script = '''
        $settings = Get-DnsClient
        $global = Get-DnsClientGlobalSetting
        @{
            Interfaces = @($settings | Select-Object InterfaceAlias, InterfaceIndex, 
                @{N='ConnectionSpecificSuffix';E={$_.ConnectionSpecificSuffix}},
                @{N='RegisterThisConnectionsAddress';E={$_.RegisterThisConnectionsAddress}},
                @{N='UseSuffixWhenRegistering';E={$_.UseSuffixWhenRegistering}})
            GlobalSettings = @{
                SuffixSearchList = $global.SuffixSearchList
                UseDevolution = $global.UseDevolution
                DevolutionLevel = $global.DevolutionLevel
            }
        }
        '''
        return await self._run_powershell(script)

    async def _register_dns(self, **kwargs) -> Dict[str, Any]:
        """Register DNS with the configured DNS server."""
        script = '''
        Register-DnsClient
        @{ Success = $true; Message = "DNS registration initiated" }
        '''
        return await self._run_powershell(script)

    # Network Profiles
    async def _get_network_profiles(self, **kwargs) -> Dict[str, Any]:
        """Get network connection profiles."""
        script = '''
        Get-NetConnectionProfile | Select-Object Name, InterfaceAlias, InterfaceIndex,
        @{N='NetworkCategory';E={$_.NetworkCategory.ToString()}},
        @{N='IPv4Connectivity';E={$_.IPv4Connectivity.ToString()}},
        @{N='IPv6Connectivity';E={$_.IPv6Connectivity.ToString()}}
        '''
        return await self._run_powershell(script)

    async def _set_network_category(self, adapter_name: str, category: str, **kwargs) -> Dict[str, Any]:
        """Set the network category (Public, Private, DomainAuthenticated)."""
        script = f'''
        Set-NetConnectionProfile -InterfaceAlias "{adapter_name}" -NetworkCategory {category}
        @{{ Success = $true; Category = "{category}" }}
        '''
        return await self._run_powershell(script)

    async def _get_connection_profiles(self, **kwargs) -> Dict[str, Any]:
        """Get detailed connection profiles."""
        script = '''
        Get-NetConnectionProfile | ForEach-Object {
            $adapter = Get-NetAdapter -InterfaceIndex $_.InterfaceIndex
            @{
                Name = $_.Name
                InterfaceAlias = $_.InterfaceAlias
                NetworkCategory = $_.NetworkCategory.ToString()
                IPv4Connectivity = $_.IPv4Connectivity.ToString()
                IPv6Connectivity = $_.IPv6Connectivity.ToString()
                AdapterStatus = $adapter.Status.ToString()
                LinkSpeed = $adapter.LinkSpeed
                MediaType = $adapter.MediaType
            }
        }
        '''
        return await self._run_powershell(script)

    # Firewall
    async def _get_firewall_status(self, **kwargs) -> Dict[str, Any]:
        """Get Windows Firewall status for all profiles."""
        script = '''
        Get-NetFirewallProfile | Select-Object Name, Enabled, 
        @{N='DefaultInboundAction';E={$_.DefaultInboundAction.ToString()}},
        @{N='DefaultOutboundAction';E={$_.DefaultOutboundAction.ToString()}},
        AllowInboundRules, AllowLocalFirewallRules, AllowLocalIPsecRules,
        AllowUserApps, AllowUserPorts, AllowUnicastResponseToMulticast,
        NotifyOnListen, LogFileName, LogMaxSizeKilobytes, LogAllowed, LogBlocked
        '''
        return await self._run_powershell(script)

    async def _enable_firewall(self, profile: str = "All", **kwargs) -> Dict[str, Any]:
        """Enable Windows Firewall for a profile."""
        script = f'''
        Set-NetFirewallProfile -Profile {profile} -Enabled True
        @{{ Success = $true; Profile = "{profile}"; Enabled = $true }}
        '''
        return await self._run_powershell(script)

    async def _disable_firewall(self, profile: str = "All", **kwargs) -> Dict[str, Any]:
        """Disable Windows Firewall for a profile."""
        script = f'''
        Set-NetFirewallProfile -Profile {profile} -Enabled False
        @{{ Success = $true; Profile = "{profile}"; Enabled = $false }}
        '''
        return await self._run_powershell(script)

    async def _get_firewall_rules(self, enabled: bool = None, direction: str = None, 
                                   action: str = None, name_filter: str = None, **kwargs) -> Dict[str, Any]:
        """Get firewall rules with filters."""
        filters = []
        if enabled is not None:
            filters.append(f'$_.Enabled -eq "{str(enabled)}"')
        if direction:
            filters.append(f'$_.Direction -eq "{direction}"')
        if action:
            filters.append(f'$_.Action -eq "{action}"')
        if name_filter:
            filters.append(f'$_.DisplayName -like "*{name_filter}*"')
        
        filter_clause = f'| Where-Object {{ {" -and ".join(filters)} }}' if filters else ""
        script = f'''
        Get-NetFirewallRule {filter_clause} | Select-Object -First 100 Name, DisplayName, 
        @{{N='Enabled';E={{$_.Enabled.ToString()}}}},
        @{{N='Direction';E={{$_.Direction.ToString()}}}},
        @{{N='Action';E={{$_.Action.ToString()}}}},
        @{{N='Profile';E={{$_.Profile.ToString()}}}},
        Description
        '''
        return await self._run_powershell(script)

    async def _add_firewall_rule(self, name: str, display_name: str, direction: str,
                                  action: str, protocol: str = None, local_port: str = None,
                                  remote_port: str = None, program: str = None,
                                  profile: str = "Any", **kwargs) -> Dict[str, Any]:
        """Add a new firewall rule."""
        params = [
            f'-Name "{name}"',
            f'-DisplayName "{display_name}"',
            f'-Direction {direction}',
            f'-Action {action}',
            f'-Profile {profile}'
        ]
        if protocol:
            params.append(f'-Protocol {protocol}')
        if local_port:
            params.append(f'-LocalPort {local_port}')
        if remote_port:
            params.append(f'-RemotePort {remote_port}')
        if program:
            params.append(f'-Program "{program}"')
        
        script = f'''
        New-NetFirewallRule {" ".join(params)}
        @{{ Success = $true; Name = "{name}" }}
        '''
        return await self._run_powershell(script)

    async def _remove_firewall_rule(self, name: str, **kwargs) -> Dict[str, Any]:
        """Remove a firewall rule."""
        script = f'''
        Remove-NetFirewallRule -Name "{name}"
        @{{ Success = $true; Removed = "{name}" }}
        '''
        return await self._run_powershell(script)

    async def _enable_firewall_rule(self, name: str, **kwargs) -> Dict[str, Any]:
        """Enable a firewall rule."""
        script = f'''
        Enable-NetFirewallRule -Name "{name}"
        @{{ Success = $true; Name = "{name}"; Enabled = $true }}
        '''
        return await self._run_powershell(script)

    async def _disable_firewall_rule(self, name: str, **kwargs) -> Dict[str, Any]:
        """Disable a firewall rule."""
        script = f'''
        Disable-NetFirewallRule -Name "{name}"
        @{{ Success = $true; Name = "{name}"; Enabled = $false }}
        '''
        return await self._run_powershell(script)

    # Network Shares
    async def _list_shares(self, **kwargs) -> Dict[str, Any]:
        """List SMB shares on this computer."""
        script = '''
        Get-SmbShare | Select-Object Name, Path, Description, 
        @{N='ShareType';E={$_.ShareType.ToString()}},
        @{N='ShareState';E={$_.ShareState.ToString()}},
        CurrentUsers, ConcurrentUserLimit
        '''
        return await self._run_powershell(script)

    async def _create_share(self, name: str, path: str, description: str = None,
                            full_access: List[str] = None, read_access: List[str] = None, **kwargs) -> Dict[str, Any]:
        """Create a new SMB share."""
        params = [f'-Name "{name}"', f'-Path "{path}"']
        if description:
            params.append(f'-Description "{description}"')
        if full_access:
            access_list = ", ".join([f'"{u}"' for u in full_access])
            params.append(f'-FullAccess @({access_list})')
        if read_access:
            access_list = ", ".join([f'"{u}"' for u in read_access])
            params.append(f'-ReadAccess @({access_list})')
        
        script = f'''
        New-SmbShare {" ".join(params)}
        @{{ Success = $true; Name = "{name}"; Path = "{path}" }}
        '''
        return await self._run_powershell(script)

    async def _remove_share(self, name: str, **kwargs) -> Dict[str, Any]:
        """Remove an SMB share."""
        script = f'''
        Remove-SmbShare -Name "{name}" -Force
        @{{ Success = $true; Removed = "{name}" }}
        '''
        return await self._run_powershell(script)

    async def _get_share_access(self, name: str, **kwargs) -> Dict[str, Any]:
        """Get access permissions for an SMB share."""
        script = f'''
        Get-SmbShareAccess -Name "{name}" | Select-Object Name, ScopeName, AccountName,
        @{{N='AccessControlType';E={{$_.AccessControlType.ToString()}}}},
        @{{N='AccessRight';E={{$_.AccessRight.ToString()}}}}
        '''
        return await self._run_powershell(script)

    async def _set_share_access(self, name: str, account: str, access_right: str, **kwargs) -> Dict[str, Any]:
        """Set access permissions for an SMB share."""
        script = f'''
        Grant-SmbShareAccess -Name "{name}" -AccountName "{account}" -AccessRight {access_right} -Force
        @{{ Success = $true; Share = "{name}"; Account = "{account}"; AccessRight = "{access_right}" }}
        '''
        return await self._run_powershell(script)

    async def _list_mapped_drives(self, **kwargs) -> Dict[str, Any]:
        """List mapped network drives."""
        script = '''
        Get-PSDrive -PSProvider FileSystem | Where-Object { $_.DisplayRoot -like "\\\\*" } |
        Select-Object Name, @{N='DriveLetter';E={"$($_.Name):"}}, 
        @{N='UNCPath';E={$_.DisplayRoot}},
        @{N='UsedGB';E={[math]::Round($_.Used/1GB, 2)}},
        @{N='FreeGB';E={[math]::Round($_.Free/1GB, 2)}}
        '''
        return await self._run_powershell(script)

    async def _map_network_drive(self, drive_letter: str, unc_path: str, 
                                  persistent: bool = True, username: str = None, **kwargs) -> Dict[str, Any]:
        """Map a network drive."""
        persist_flag = "/persistent:yes" if persistent else "/persistent:no"
        user_param = f'/user:"{username}"' if username else ""
        
        script = f'''
        net use {drive_letter}: "{unc_path}" {user_param} {persist_flag}
        @{{ Success = $true; DriveLetter = "{drive_letter}:"; UNCPath = "{unc_path}" }}
        '''
        return await self._run_powershell(script, as_json=False)

    async def _remove_mapped_drive(self, drive_letter: str, **kwargs) -> Dict[str, Any]:
        """Remove a mapped network drive."""
        script = f'''
        net use {drive_letter}: /delete /y
        @{{ Success = $true; Removed = "{drive_letter}:" }}
        '''
        return await self._run_powershell(script, as_json=False)

    # Connection Monitoring
    async def _get_active_connections(self, **kwargs) -> Dict[str, Any]:
        """Get all active network connections."""
        script = '''
        Get-NetTCPConnection -State Established | Select-Object LocalAddress, LocalPort,
        RemoteAddress, RemotePort, @{N='State';E={$_.State.ToString()}},
        OwningProcess, @{N='ProcessName';E={(Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).Name}}
        '''
        return await self._run_powershell(script)

    async def _get_tcp_connections(self, state: str = None, local_port: int = None, **kwargs) -> Dict[str, Any]:
        """Get TCP connections with filters."""
        filters = []
        if state:
            filters.append(f'-State {state}')
        if local_port:
            filters.append(f'-LocalPort {local_port}')
        
        script = f'''
        Get-NetTCPConnection {" ".join(filters)} | Select-Object LocalAddress, LocalPort,
        RemoteAddress, RemotePort, @{{N='State';E={{$_.State.ToString()}}}},
        OwningProcess, @{{N='ProcessName';E={{(Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).Name}}}},
        CreationTime, @{{N='OffloadState';E={{$_.OffloadState.ToString()}}}}
        '''
        return await self._run_powershell(script)

    async def _get_udp_endpoints(self, **kwargs) -> Dict[str, Any]:
        """Get UDP endpoints."""
        script = '''
        Get-NetUDPEndpoint | Select-Object LocalAddress, LocalPort,
        OwningProcess, @{N='ProcessName';E={(Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).Name}},
        CreationTime
        '''
        return await self._run_powershell(script)

    async def _get_connection_by_port(self, port: int, **kwargs) -> Dict[str, Any]:
        """Get connections on a specific port."""
        script = f'''
        $tcp = Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue
        $udp = Get-NetUDPEndpoint -LocalPort {port} -ErrorAction SilentlyContinue
        @{{
            TCP = @($tcp | Select-Object LocalAddress, LocalPort, RemoteAddress, RemotePort,
                @{{N='State';E={{$_.State.ToString()}}}},
                @{{N='ProcessName';E={{(Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).Name}}}})
            UDP = @($udp | Select-Object LocalAddress, LocalPort,
                @{{N='ProcessName';E={{(Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).Name}}}})
        }}
        '''
        return await self._run_powershell(script)

    async def _get_listening_ports(self, **kwargs) -> Dict[str, Any]:
        """Get all listening ports."""
        script = '''
        Get-NetTCPConnection -State Listen | Select-Object LocalAddress, LocalPort,
        OwningProcess, @{N='ProcessName';E={(Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).Name}} |
        Sort-Object LocalPort
        '''
        return await self._run_powershell(script)

    # Wi-Fi Management
    async def _list_wifi_networks(self, **kwargs) -> Dict[str, Any]:
        """List available Wi-Fi networks."""
        script = '''
        $output = netsh wlan show networks mode=bssid
        $networks = @()
        $current = @{}
        
        foreach ($line in $output) {
            if ($line -match "^SSID \d+ : (.*)$") {
                if ($current.Count -gt 0) { $networks += [PSCustomObject]$current }
                $current = @{ SSID = $matches[1].Trim() }
            }
            elseif ($line -match "Network type\s*:\s*(.*)$") { $current.NetworkType = $matches[1].Trim() }
            elseif ($line -match "Authentication\s*:\s*(.*)$") { $current.Authentication = $matches[1].Trim() }
            elseif ($line -match "Encryption\s*:\s*(.*)$") { $current.Encryption = $matches[1].Trim() }
            elseif ($line -match "Signal\s*:\s*(.*)$") { $current.Signal = $matches[1].Trim() }
            elseif ($line -match "Channel\s*:\s*(.*)$") { $current.Channel = $matches[1].Trim() }
        }
        if ($current.Count -gt 0) { $networks += [PSCustomObject]$current }
        
        $networks
        '''
        return await self._run_powershell(script)

    async def _get_wifi_profile(self, profile_name: str, show_key: bool = False, **kwargs) -> Dict[str, Any]:
        """Get Wi-Fi profile details."""
        key_param = "key=clear" if show_key else ""
        script = f'''
        $output = netsh wlan show profile name="{profile_name}" {key_param}
        @{{
            ProfileName = "{profile_name}"
            Output = $output -join "`n"
        }}
        '''
        return await self._run_powershell(script, as_json=False)

    async def _list_wifi_profiles(self, **kwargs) -> Dict[str, Any]:
        """List all saved Wi-Fi profiles."""
        script = '''
        $output = netsh wlan show profiles
        $profiles = @()
        foreach ($line in $output) {
            if ($line -match "All User Profile\s*:\s*(.*)$") {
                $profiles += $matches[1].Trim()
            }
        }
        @{ Profiles = $profiles }
        '''
        return await self._run_powershell(script)

    async def _connect_wifi(self, profile_name: str, interface: str = None, **kwargs) -> Dict[str, Any]:
        """Connect to a Wi-Fi network."""
        interface_param = f'interface="{interface}"' if interface else ""
        script = f'''
        $result = netsh wlan connect name="{profile_name}" {interface_param}
        @{{ Success = $result -match "success"; Output = $result }}
        '''
        return await self._run_powershell(script)

    async def _disconnect_wifi(self, interface: str = None, **kwargs) -> Dict[str, Any]:
        """Disconnect from Wi-Fi."""
        interface_param = f'interface="{interface}"' if interface else ""
        script = f'''
        $result = netsh wlan disconnect {interface_param}
        @{{ Success = $true; Output = $result }}
        '''
        return await self._run_powershell(script)

    async def _remove_wifi_profile(self, profile_name: str, **kwargs) -> Dict[str, Any]:
        """Remove a saved Wi-Fi profile."""
        script = f'''
        $result = netsh wlan delete profile name="{profile_name}"
        @{{ Success = $result -match "deleted"; Output = $result }}
        '''
        return await self._run_powershell(script)

    async def _export_wifi_profile(self, profile_name: str, folder: str, 
                                    include_key: bool = False, **kwargs) -> Dict[str, Any]:
        """Export a Wi-Fi profile to XML."""
        key_param = "key=clear" if include_key else ""
        script = f'''
        $result = netsh wlan export profile name="{profile_name}" folder="{folder}" {key_param}
        @{{ Success = $result -match "successfully"; Output = $result }}
        '''
        return await self._run_powershell(script)

    # VPN Configuration
    async def _list_vpn_connections(self, **kwargs) -> Dict[str, Any]:
        """List VPN connections."""
        script = '''
        Get-VpnConnection | Select-Object Name, ServerAddress, 
        @{N='TunnelType';E={$_.TunnelType.ToString()}},
        @{N='AuthenticationMethod';E={$_.AuthenticationMethod -join ", "}},
        @{N='ConnectionStatus';E={$_.ConnectionStatus.ToString()}},
        SplitTunneling, RememberCredential, AllUserConnection
        '''
        return await self._run_powershell(script)

    async def _add_vpn_connection(self, name: str, server_address: str, 
                                   tunnel_type: str = "Automatic",
                                   auth_method: str = "MSChapv2",
                                   split_tunneling: bool = False,
                                   remember_credential: bool = True, **kwargs) -> Dict[str, Any]:
        """Add a VPN connection."""
        split_param = "-SplitTunneling" if split_tunneling else ""
        remember_param = "-RememberCredential" if remember_credential else ""
        
        script = f'''
        Add-VpnConnection -Name "{name}" -ServerAddress "{server_address}" -TunnelType {tunnel_type} `
            -AuthenticationMethod {auth_method} {split_param} {remember_param} -Force
        @{{ Success = $true; Name = "{name}"; Server = "{server_address}" }}
        '''
        return await self._run_powershell(script)

    async def _remove_vpn_connection(self, name: str, **kwargs) -> Dict[str, Any]:
        """Remove a VPN connection."""
        script = f'''
        Remove-VpnConnection -Name "{name}" -Force
        @{{ Success = $true; Removed = "{name}" }}
        '''
        return await self._run_powershell(script)

    async def _connect_vpn(self, name: str, **kwargs) -> Dict[str, Any]:
        """Connect to a VPN."""
        script = f'''
        rasdial "{name}"
        $vpn = Get-VpnConnection -Name "{name}"
        @{{ Success = $vpn.ConnectionStatus -eq "Connected"; Status = $vpn.ConnectionStatus.ToString() }}
        '''
        return await self._run_powershell(script, timeout=30)

    async def _disconnect_vpn(self, name: str, **kwargs) -> Dict[str, Any]:
        """Disconnect from a VPN."""
        script = f'''
        rasdial "{name}" /disconnect
        @{{ Success = $true; Message = "Disconnected from {name}" }}
        '''
        return await self._run_powershell(script)

    async def _get_vpn_status(self, name: str = None, **kwargs) -> Dict[str, Any]:
        """Get VPN connection status."""
        filter_clause = f'-Name "{name}"' if name else ""
        script = f'''
        Get-VpnConnection {filter_clause} | Select-Object Name, ServerAddress,
        @{{N='ConnectionStatus';E={{$_.ConnectionStatus.ToString()}}}},
        @{{N='TunnelType';E={{$_.TunnelType.ToString()}}}}
        '''
        return await self._run_powershell(script)

    # Diagnostics
    async def _test_connection(self, target: str, count: int = 4, **kwargs) -> Dict[str, Any]:
        """Test network connection (ping)."""
        script = f'''
        $results = Test-Connection -ComputerName "{target}" -Count {count} -ErrorAction SilentlyContinue
        if ($results) {{
            @{{
                Success = $true
                Target = "{target}"
                Results = @($results | Select-Object Address, 
                    @{{N='ResponseTime';E={{$_.ResponseTime}}}},
                    @{{N='StatusCode';E={{$_.StatusCode}}}},
                    BufferSize, ReplySize)
                Statistics = @{{
                    Sent = {count}
                    Received = $results.Count
                    Lost = {count} - $results.Count
                    AverageResponseTime = ($results | Measure-Object -Property ResponseTime -Average).Average
                    MinResponseTime = ($results | Measure-Object -Property ResponseTime -Minimum).Minimum
                    MaxResponseTime = ($results | Measure-Object -Property ResponseTime -Maximum).Maximum
                }}
            }}
        }} else {{
            @{{ Success = $false; Target = "{target}"; Error = "No response" }}
        }}
        '''
        return await self._run_powershell(script, timeout=count * 5 + 10)

    async def _trace_route(self, target: str, max_hops: int = 30, **kwargs) -> Dict[str, Any]:
        """Trace route to a destination."""
        script = f'''
        $results = Test-NetConnection -ComputerName "{target}" -TraceRoute
        @{{
            Target = "{target}"
            ResolvedAddress = $results.RemoteAddress.ToString()
            InterfaceAlias = $results.InterfaceAlias
            SourceAddress = $results.SourceAddress.ToString()
            PingSucceeded = $results.PingSucceeded
            PingReplyDetails = @{{
                Address = $results.PingReplyDetails.Address.ToString()
                RoundtripTime = $results.PingReplyDetails.RoundtripTime
                Status = $results.PingReplyDetails.Status.ToString()
            }}
            TraceRoute = $results.TraceRoute
        }}
        '''
        return await self._run_powershell(script, timeout=60)

    async def _get_network_statistics(self, **kwargs) -> Dict[str, Any]:
        """Get network interface statistics."""
        script = '''
        Get-NetAdapterStatistics | Select-Object Name,
        @{N='ReceivedGB';E={[math]::Round($_.ReceivedBytes/1GB, 3)}},
        @{N='SentGB';E={[math]::Round($_.SentBytes/1GB, 3)}},
        ReceivedUnicastPackets, SentUnicastPackets,
        ReceivedMulticastPackets, SentMulticastPackets,
        ReceivedBroadcastPackets, SentBroadcastPackets,
        ReceivedDiscardedPackets, OutboundDiscardedPackets,
        ReceivedPacketErrors, OutboundPacketErrors
        '''
        return await self._run_powershell(script)

    async def _reset_network_stack(self, **kwargs) -> Dict[str, Any]:
        """Reset network stack (requires elevation)."""
        script = '''
        netsh winsock reset
        netsh int ip reset
        @{ Success = $true; Message = "Network stack reset. Restart required." }
        '''
        return await self._run_powershell(script)

    async def _get_arp_table(self, **kwargs) -> Dict[str, Any]:
        """Get ARP table."""
        script = '''
        Get-NetNeighbor | Where-Object { $_.State -ne "Unreachable" } |
        Select-Object IPAddress, LinkLayerAddress, 
        @{N='State';E={$_.State.ToString()}},
        @{N='InterfaceAlias';E={(Get-NetAdapter -InterfaceIndex $_.ifIndex).Name}},
        InterfaceIndex
        '''
        return await self._run_powershell(script)

    async def _get_netstat(self, **kwargs) -> Dict[str, Any]:
        """Get netstat-style output."""
        script = '''
        @{
            TCP = @(Get-NetTCPConnection | Select-Object LocalAddress, LocalPort, 
                RemoteAddress, RemotePort, @{N='State';E={$_.State.ToString()}},
                @{N='Process';E={(Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).Name}})
            UDP = @(Get-NetUDPEndpoint | Select-Object LocalAddress, LocalPort,
                @{N='Process';E={(Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).Name}})
            ListeningTCPPorts = @(Get-NetTCPConnection -State Listen | Select-Object LocalPort,
                @{N='Process';E={(Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).Name}} | 
                Sort-Object LocalPort)
        }
        '''
        return await self._run_powershell(script)
