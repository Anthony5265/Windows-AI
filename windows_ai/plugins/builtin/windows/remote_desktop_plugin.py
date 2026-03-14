"""
Remote Desktop Plugin for Windows AI
Provides RDP configuration and remote session management
"""

from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType
from typing import Dict, Any
import asyncio
import logging

logger = logging.getLogger(__name__)


class RemoteDesktopPlugin(IntegrationPlugin):
    """
    Windows Remote Desktop management plugin
    
    Provides comprehensive RDP operations including:
    - Remote Desktop enable/disable
    - RDP settings configuration
    - Connection management
    - Session management
    - Firewall rules
    - Network Level Authentication
    """
    
    def __init__(self):
        metadata = PluginMetadata(
            id="windows-remote-desktop",
            name="Windows Remote Desktop",
            description="Remote Desktop configuration and session management",
            version="1.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["windows", "rdp", "remote", "desktop", "connection"],
            requirements=[]
        )
        super().__init__(metadata)
        
        self.actions = {
            # RDP Enable/Disable
            "get_rdp_status": {
                "description": "Get Remote Desktop status",
                "script": """
$rdpEnabled = (Get-ItemProperty -Path 'HKLM:\\System\\CurrentControlSet\\Control\\Terminal Server' -Name 'fDenyTSConnections').fDenyTSConnections -eq 0
$nlaEnabled = (Get-ItemProperty -Path 'HKLM:\\System\\CurrentControlSet\\Control\\Terminal Server\\WinStations\\RDP-Tcp' -Name 'UserAuthentication' -ErrorAction SilentlyContinue).UserAuthentication -eq 1
$firewallRule = Get-NetFirewallRule -DisplayGroup 'Remote Desktop' -ErrorAction SilentlyContinue | Select-Object -First 1

@{
    rdp_enabled = $rdpEnabled
    nla_enabled = $nlaEnabled
    firewall_rule_enabled = if ($firewallRule) { $firewallRule.Enabled -eq 'True' } else { $false }
    port = (Get-ItemProperty -Path 'HKLM:\\System\\CurrentControlSet\\Control\\Terminal Server\\WinStations\\RDP-Tcp' -Name 'PortNumber').PortNumber
} | ConvertTo-Json
"""
            },
            "enable_rdp": {
                "description": "Enable Remote Desktop",
                "script": """
Set-ItemProperty -Path 'HKLM:\\System\\CurrentControlSet\\Control\\Terminal Server' -Name 'fDenyTSConnections' -Value 0 -Type DWord
Enable-NetFirewallRule -DisplayGroup 'Remote Desktop'
Write-Output 'Remote Desktop enabled'
"""
            },
            "disable_rdp": {
                "description": "Disable Remote Desktop",
                "script": """
Set-ItemProperty -Path 'HKLM:\\System\\CurrentControlSet\\Control\\Terminal Server' -Name 'fDenyTSConnections' -Value 1 -Type DWord
Disable-NetFirewallRule -DisplayGroup 'Remote Desktop'
Write-Output 'Remote Desktop disabled'
"""
            },
            
            # Network Level Authentication
            "enable_nla": {
                "description": "Enable Network Level Authentication (more secure)",
                "script": """
Set-ItemProperty -Path 'HKLM:\\System\\CurrentControlSet\\Control\\Terminal Server\\WinStations\\RDP-Tcp' -Name 'UserAuthentication' -Value 1 -Type DWord
Write-Output 'Network Level Authentication enabled'
"""
            },
            "disable_nla": {
                "description": "Disable Network Level Authentication",
                "script": """
Set-ItemProperty -Path 'HKLM:\\System\\CurrentControlSet\\Control\\Terminal Server\\WinStations\\RDP-Tcp' -Name 'UserAuthentication' -Value 0 -Type DWord
Write-Output 'Network Level Authentication disabled'
"""
            },
            
            # Port Configuration
            "get_rdp_port": {
                "description": "Get current RDP port",
                "script": """
$port = (Get-ItemProperty -Path 'HKLM:\\System\\CurrentControlSet\\Control\\Terminal Server\\WinStations\\RDP-Tcp' -Name 'PortNumber').PortNumber
@{ port = $port } | ConvertTo-Json
"""
            },
            "set_rdp_port": {
                "description": "Change RDP port (requires restart)",
                "script": """
$newPort = {port}
Set-ItemProperty -Path 'HKLM:\\System\\CurrentControlSet\\Control\\Terminal Server\\WinStations\\RDP-Tcp' -Name 'PortNumber' -Value $newPort -Type DWord
# Update firewall rule
$rule = Get-NetFirewallRule -DisplayName 'Remote Desktop - User Mode (TCP-In)' -ErrorAction SilentlyContinue
if ($rule) {
    Set-NetFirewallRule -DisplayName 'Remote Desktop - User Mode (TCP-In)' -LocalPort $newPort
}
@{ success = $true; new_port = $newPort; note = 'Restart required' } | ConvertTo-Json
""",
                "params": ["port"]
            },
            
            # Session Management
            "get_active_sessions": {
                "description": "Get active RDP sessions",
                "script": """
$sessions = qwinsta 2>$null | Select-Object -Skip 1 | ForEach-Object {
    $line = $_ -split '\\s+'
    if ($line.Count -ge 4) {
        @{
            session_name = $line[0]
            username = $line[1]
            id = $line[2]
            state = $line[3]
        }
    }
}
$sessions | ConvertTo-Json
"""
            },
            "disconnect_session": {
                "description": "Disconnect an RDP session",
                "script": """
$sessionId = {session_id}
tsdiscon $sessionId
@{ success = $true; disconnected_session = $sessionId } | ConvertTo-Json
""",
                "params": ["session_id"]
            },
            "logoff_session": {
                "description": "Log off an RDP session",
                "script": """
$sessionId = {session_id}
logoff $sessionId
@{ success = $true; logged_off_session = $sessionId } | ConvertTo-Json
""",
                "params": ["session_id"]
            },
            "send_message_to_session": {
                "description": "Send message to RDP session",
                "script": """
$sessionId = {session_id}
$message = '{message}'
msg $sessionId $message
@{ success = $true; session = $sessionId } | ConvertTo-Json
""",
                "params": ["session_id", "message"]
            },
            
            # Connection Settings
            "connect_rdp": {
                "description": "Launch RDP connection to a remote computer",
                "script": """
$computer = '{computer}'
$fullscreen = '{fullscreen}' -eq 'true'
$args = '/v:' + $computer
if ($fullscreen) { $args += ' /f' }
Start-Process mstsc.exe -ArgumentList $args
@{ success = $true; connecting_to = $computer } | ConvertTo-Json
""",
                "params": ["computer", "fullscreen"]
            },
            "create_rdp_file": {
                "description": "Create an RDP connection file",
                "script": """
$computer = '{computer}'
$username = '{username}'
$path = '{output_path}'
if (!$path) { $path = Join-Path $env:USERPROFILE "Desktop\\$computer.rdp" }

$content = @"
full address:s:$computer
username:s:$username
screen mode id:i:2
use multimon:i:0
desktopwidth:i:1920
desktopheight:i:1080
session bpp:i:32
compression:i:1
keyboardhook:i:2
audiocapturemode:i:0
videoplaybackmode:i:1
connection type:i:7
networkautodetect:i:1
bandwidthautodetect:i:1
displayconnectionbar:i:1
enableworkspacereconnect:i:0
disable wallpaper:i:0
allow font smoothing:i:1
allow desktop composition:i:1
disable full window drag:i:0
disable menu anims:i:0
disable themes:i:0
disable cursor setting:i:0
bitmapcachepersistenable:i:1
audiomode:i:0
redirectprinters:i:1
redirectcomports:i:0
redirectsmartcards:i:1
redirectclipboard:i:1
redirectposdevices:i:0
drivestoredirect:s:
autoreconnection enabled:i:1
authentication level:i:2
prompt for credentials:i:0
negotiate security layer:i:1
remoteapplicationmode:i:0
alternate shell:s:
shell working directory:s:
gatewayhostname:s:
gatewayusagemethod:i:4
gatewaycredentialssource:i:4
gatewayprofileusagemethod:i:0
promptcredentialonce:i:0
gatewaybrokeringtype:i:0
use redirection server name:i:0
rdgiskdcproxy:i:0
kdcproxyname:s:
"@

Set-Content -Path $path -Value $content -Encoding ASCII
@{ success = $true; path = $path } | ConvertTo-Json
""",
                "params": ["computer", "username", "output_path"]
            },
            
            # Remote Desktop Users
            "get_rdp_users": {
                "description": "Get users allowed for Remote Desktop",
                "script": """
$members = Get-LocalGroupMember -Group 'Remote Desktop Users' -ErrorAction SilentlyContinue
$users = @()
foreach ($member in $members) {
    $users += @{
        name = $member.Name
        object_class = $member.ObjectClass
        principal_source = $member.PrincipalSource
    }
}
@{ users = $users; count = $users.Count } | ConvertTo-Json
"""
            },
            "add_rdp_user": {
                "description": "Add user to Remote Desktop Users group",
                "script": """
$username = '{username}'
Add-LocalGroupMember -Group 'Remote Desktop Users' -Member $username
@{ success = $true; added_user = $username } | ConvertTo-Json
""",
                "params": ["username"]
            },
            "remove_rdp_user": {
                "description": "Remove user from Remote Desktop Users group",
                "script": """
$username = '{username}'
Remove-LocalGroupMember -Group 'Remote Desktop Users' -Member $username
@{ success = $true; removed_user = $username } | ConvertTo-Json
""",
                "params": ["username"]
            },
            
            # Session Limits
            "get_session_limits": {
                "description": "Get RDP session time limits",
                "script": """
$path = 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows NT\\Terminal Services'
$limits = @{}
if (Test-Path $path) {
    $props = Get-ItemProperty -Path $path -ErrorAction SilentlyContinue
    $limits = @{
        max_idle_time = $props.MaxIdleTime
        max_connection_time = $props.MaxConnectionTime
        max_disconnection_time = $props.MaxDisconnectionTime
        reconnection_policy = $props.fResetBroken
    }
}
$limits | ConvertTo-Json
"""
            },
            "set_idle_timeout": {
                "description": "Set session idle timeout (minutes)",
                "script": """
$minutes = {minutes}
$ms = $minutes * 60 * 1000
$path = 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows NT\\Terminal Services'
if (!(Test-Path $path)) { New-Item -Path $path -Force }
Set-ItemProperty -Path $path -Name 'MaxIdleTime' -Value $ms -Type DWord
@{ success = $true; idle_timeout_minutes = $minutes } | ConvertTo-Json
""",
                "params": ["minutes"]
            },
            
            # Firewall Rules
            "get_rdp_firewall_rules": {
                "description": "Get RDP firewall rules",
                "script": """
$rules = Get-NetFirewallRule -DisplayGroup 'Remote Desktop' | Select-Object DisplayName, Enabled, Direction, Action, Profile
$rules | ConvertTo-Json
"""
            },
            "enable_rdp_firewall": {
                "description": "Enable RDP firewall rules",
                "script": """
Enable-NetFirewallRule -DisplayGroup 'Remote Desktop'
Write-Output 'RDP firewall rules enabled'
"""
            },
            "disable_rdp_firewall": {
                "description": "Disable RDP firewall rules",
                "script": """
Disable-NetFirewallRule -DisplayGroup 'Remote Desktop'
Write-Output 'RDP firewall rules disabled'
"""
            },
            "restrict_rdp_to_subnet": {
                "description": "Restrict RDP to specific subnet",
                "script": """
$subnet = '{subnet}'
$rule = Get-NetFirewallRule -DisplayName 'Remote Desktop - User Mode (TCP-In)'
Set-NetFirewallRule -DisplayName 'Remote Desktop - User Mode (TCP-In)' -RemoteAddress $subnet
@{ success = $true; restricted_to = $subnet } | ConvertTo-Json
""",
                "params": ["subnet"]
            },
            
            # RDP Gateway
            "get_rdp_gateway_settings": {
                "description": "Get RD Gateway settings",
                "script": """
$path = 'HKCU:\\Software\\Microsoft\\Terminal Server Client\\Default'
$settings = @{}
if (Test-Path $path) {
    $props = Get-ItemProperty -Path $path -ErrorAction SilentlyContinue
    $settings = @{
        gateway_hostname = $props.GatewayHostname
        gateway_usage_method = $props.GatewayUsageMethod
    }
}
$settings | ConvertTo-Json
"""
            },
            
            # Remote App
            "get_remote_apps": {
                "description": "Get configured RemoteApps",
                "script": """
$path = 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Terminal Server\\TSAppAllowList\\Applications'
if (Test-Path $path) {
    $apps = Get-ChildItem -Path $path | ForEach-Object {
        $appProps = Get-ItemProperty -Path $_.PSPath
        @{
            name = $_.PSChildName
            path = $appProps.Path
            command_line_setting = $appProps.CommandLineSetting
        }
    }
    $apps | ConvertTo-Json
} else {
    @{ apps = @() } | ConvertTo-Json
}
"""
            },
            
            # Licensing
            "get_rdp_licensing_info": {
                "description": "Get RDP licensing information",
                "script": """
$mode = (Get-ItemProperty -Path 'HKLM:\\System\\CurrentControlSet\\Control\\Terminal Server' -Name 'LicensingMode' -ErrorAction SilentlyContinue).LicensingMode
$type = switch ($mode) {
    2 { 'Per Device' }
    4 { 'Per User' }
    default { 'Not Configured' }
}
@{
    licensing_mode = $mode
    licensing_type = $type
} | ConvertTo-Json
"""
            },
            
            # Shadow Sessions
            "shadow_session": {
                "description": "Shadow (view) an RDP session",
                "script": """
$sessionId = {session_id}
$control = '{control}' -eq 'true'
$args = "/shadow:$sessionId /noConsentPrompt"
if ($control) { $args += ' /control' }
Start-Process mstsc.exe -ArgumentList $args
@{ success = $true; shadowing_session = $sessionId; control = $control } | ConvertTo-Json
""",
                "params": ["session_id", "control"]
            },
            
            # Connection History
            "get_connection_history": {
                "description": "Get RDP connection history",
                "script": """
$path = 'HKCU:\\Software\\Microsoft\\Terminal Server Client\\Default'
$servers = @()
if (Test-Path $path) {
    $props = Get-ItemProperty -Path $path
    $i = 1
    while ($props."MRU$i") {
        $servers += $props."MRU$i"
        $i++
    }
}
@{ recent_connections = $servers; count = $servers.Count } | ConvertTo-Json
"""
            },
            "clear_connection_history": {
                "description": "Clear RDP connection history",
                "script": """
$paths = @(
    'HKCU:\\Software\\Microsoft\\Terminal Server Client\\Default',
    'HKCU:\\Software\\Microsoft\\Terminal Server Client\\Servers'
)
foreach ($path in $paths) {
    if (Test-Path $path) {
        Remove-Item -Path $path -Recurse -Force
    }
}
Write-Output 'RDP connection history cleared'
"""
            },
            
            # Security Settings
            "get_security_settings": {
                "description": "Get RDP security settings",
                "script": """
$tcp = Get-ItemProperty -Path 'HKLM:\\System\\CurrentControlSet\\Control\\Terminal Server\\WinStations\\RDP-Tcp' -ErrorAction SilentlyContinue
@{
    security_layer = $tcp.SecurityLayer
    min_encryption_level = $tcp.MinEncryptionLevel
    user_authentication = $tcp.UserAuthentication
    fips_compliant = $tcp.fFIPS
} | ConvertTo-Json
"""
            },
            "set_security_layer": {
                "description": "Set RDP security layer (0=RDP, 1=Negotiate, 2=SSL/TLS)",
                "script": """
$level = {level}
Set-ItemProperty -Path 'HKLM:\\System\\CurrentControlSet\\Control\\Terminal Server\\WinStations\\RDP-Tcp' -Name 'SecurityLayer' -Value $level -Type DWord
@{ success = $true; security_layer = $level } | ConvertTo-Json
""",
                "params": ["level"]
            },
            "set_encryption_level": {
                "description": "Set encryption level (1=Low, 2=Client Compatible, 3=High, 4=FIPS)",
                "script": """
$level = {level}
Set-ItemProperty -Path 'HKLM:\\System\\CurrentControlSet\\Control\\Terminal Server\\WinStations\\RDP-Tcp' -Name 'MinEncryptionLevel' -Value $level -Type DWord
@{ success = $true; encryption_level = $level } | ConvertTo-Json
""",
                "params": ["level"]
            },
            
            # Display Settings
            "get_display_settings": {
                "description": "Get RDP display settings",
                "script": """
$path = 'HKCU:\\Software\\Microsoft\\Terminal Server Client'
$settings = Get-ItemProperty -Path $path -ErrorAction SilentlyContinue
@{
    bitmap_caching = $settings.BitmapPersistCacheSize
    font_smoothing = $settings.FontSmoothing
} | ConvertTo-Json
"""
            },
            
            # Service Management
            "get_rdp_service_status": {
                "description": "Get Remote Desktop Services status",
                "script": """
$services = @('TermService', 'UmRdpService', 'SessionEnv')
$results = @()
foreach ($svc in $services) {
    $service = Get-Service -Name $svc -ErrorAction SilentlyContinue
    if ($service) {
        $results += @{
            name = $service.Name
            display_name = $service.DisplayName
            status = $service.Status.ToString()
            start_type = $service.StartType.ToString()
        }
    }
}
$results | ConvertTo-Json
"""
            },
            "restart_rdp_services": {
                "description": "Restart Remote Desktop Services",
                "script": """
Restart-Service -Name 'TermService' -Force
@{ success = $true; message = 'Terminal Services restarted' } | ConvertTo-Json
"""
            },
            
            # Diagnostics
            "test_rdp_connectivity": {
                "description": "Test RDP connectivity to remote host",
                "script": """
$computer = '{computer}'
$port = {port}
if (!$port) { $port = 3389 }
$result = Test-NetConnection -ComputerName $computer -Port $port
@{
    computer = $computer
    port = $port
    tcp_test_succeeded = $result.TcpTestSucceeded
    ping_succeeded = $result.PingSucceeded
    remote_address = $result.RemoteAddress.ToString()
} | ConvertTo-Json
""",
                "params": ["computer", "port"]
            },
            "get_rdp_logs": {
                "description": "Get recent RDP connection logs",
                "script": """
$events = Get-WinEvent -LogName 'Microsoft-Windows-TerminalServices-LocalSessionManager/Operational' -MaxEvents 20 -ErrorAction SilentlyContinue |
    Select-Object TimeCreated, Id, Message |
    ForEach-Object {
        @{
            time = $_.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss')
            event_id = $_.Id
            message = $_.Message.Substring(0, [Math]::Min(200, $_.Message.Length))
        }
    }
$events | ConvertTo-Json
"""
            },
            
            # Open Settings
            "open_rdp_settings": {
                "description": "Open System Remote Desktop settings",
                "script": "Start-Process 'ms-settings:remotedesktop'"
            }
        }
    
    async def initialize(self) -> bool:
        """Initialize the Remote Desktop plugin"""
        self._initialized = True
        logger.info(f"Plugin {self.metadata.id} initialized with {len(self.actions)} actions")
        return True
    

    async def connect(self, credentials: Dict[str, str]) -> bool:
        """Connect to the service"""
        return True

    async def disconnect(self) -> bool:
        """Disconnect from the service"""
        return True

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute a Remote Desktop action"""
        action = kwargs.get("action", "get_rdp_status")
        
        if action not in self.actions:
            return {
                "status": "error",
                "error": f"Unknown action: {action}. Available: {list(self.actions.keys())}"
            }
        
        action_info = self.actions[action]
        script = action_info["script"]
        
        if "params" in action_info:
            for param in action_info["params"]:
                value = kwargs.get(param, "")
                script = script.replace("{" + param + "}", str(value))
        
        try:
            result = await self._run_powershell(script)
            return {
                "status": "success",
                "action": action,
                "result": result
            }
        except Exception as e:
            logger.error(f"RDP action {action} failed: {e}")
            return {
                "status": "error",
                "action": action,
                "error": str(e)
            }
    
    async def _run_powershell(self, script: str) -> str:
        """Execute PowerShell script and return output"""
        process = await asyncio.create_subprocess_exec(
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-Command", script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode("utf-8", errors="ignore").strip()
            raise RuntimeError(f"PowerShell error: {error_msg}")
        
        return stdout.decode("utf-8", errors="ignore").strip()
    
    async def cleanup(self):
        """Cleanup plugin resources"""
        self._initialized = False
        logger.info(f"Plugin {self.metadata.id} cleaned up")


__all__ = ["RemoteDesktopPlugin"]


plugin = RemoteDesktopPlugin()
