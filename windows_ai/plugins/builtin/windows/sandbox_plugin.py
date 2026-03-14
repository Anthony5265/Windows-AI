"""
Windows Sandbox Plugin for Windows AI
Provides Windows Sandbox management and configuration
"""

from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType
from typing import Dict, Any
import asyncio
import logging

logger = logging.getLogger(__name__)


class SandboxPlugin(IntegrationPlugin):
    """
    Windows Sandbox management plugin
    
    Provides comprehensive sandbox operations including:
    - Sandbox enable/disable
    - Sandbox configuration
    - WSB file creation
    - Sandbox launching
    - Network and folder mapping
    """
    
    def __init__(self):
        metadata = PluginMetadata(
            id="windows-sandbox",
            name="Windows Sandbox",
            description="Windows Sandbox management and configuration",
            version="1.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["windows", "sandbox", "isolation", "security", "virtualization"],
            requirements=[]
        )
        super().__init__(metadata)
        
        self.actions = {
            # Sandbox Feature Status
            "get_sandbox_status": {
                "description": "Check if Windows Sandbox is enabled",
                "script": """
$feature = Get-WindowsOptionalFeature -Online -FeatureName 'Containers-DisposableClientVM' -ErrorAction SilentlyContinue
@{
    feature_name = 'Windows Sandbox'
    enabled = if ($feature) { $feature.State -eq 'Enabled' } else { $false }
    state = if ($feature) { $feature.State.ToString() } else { 'Not Available' }
    restart_needed = if ($feature) { $feature.RestartNeeded } else { $false }
} | ConvertTo-Json
"""
            },
            "enable_sandbox": {
                "description": "Enable Windows Sandbox feature",
                "script": """
$result = Enable-WindowsOptionalFeature -Online -FeatureName 'Containers-DisposableClientVM' -NoRestart -ErrorAction Stop
@{
    success = $true
    restart_needed = $result.RestartNeeded
    message = if ($result.RestartNeeded) { 'Windows Sandbox enabled. Restart required.' } else { 'Windows Sandbox enabled.' }
} | ConvertTo-Json
"""
            },
            "disable_sandbox": {
                "description": "Disable Windows Sandbox feature",
                "script": """
$result = Disable-WindowsOptionalFeature -Online -FeatureName 'Containers-DisposableClientVM' -NoRestart -ErrorAction Stop
@{
    success = $true
    restart_needed = $result.RestartNeeded
    message = if ($result.RestartNeeded) { 'Windows Sandbox disabled. Restart required.' } else { 'Windows Sandbox disabled.' }
} | ConvertTo-Json
"""
            },
            
            # Sandbox Configuration
            "create_wsb_config": {
                "description": "Create a Windows Sandbox configuration file",
                "script": """
$outputPath = '{output_path}'
$vGpu = '{vgpu}'  # Enable, Disable, Default
$networking = '{networking}'  # Enable, Disable, Default
$audioInput = '{audio_input}'  # Enable, Disable
$videoInput = '{video_input}'  # Enable, Disable
$protectedClient = '{protected_client}'  # Enable, Disable
$printerRedirection = '{printer_redirection}'  # Enable, Disable
$clipboardRedirection = '{clipboard_redirection}'  # Enable, Disable
$memoryInMB = '{memory_mb}'

$config = @"
<Configuration>
  <VGpu>$vGpu</VGpu>
  <Networking>$networking</Networking>
  <AudioInput>$audioInput</AudioInput>
  <VideoInput>$videoInput</VideoInput>
  <ProtectedClient>$protectedClient</ProtectedClient>
  <PrinterRedirection>$printerRedirection</PrinterRedirection>
  <ClipboardRedirection>$clipboardRedirection</ClipboardRedirection>
  <MemoryInMB>$memoryInMB</MemoryInMB>
</Configuration>
"@

$config | Set-Content -Path $outputPath -Encoding UTF8
@{ success = $true; path = $outputPath } | ConvertTo-Json
"""
            },
            "add_mapped_folder": {
                "description": "Add a mapped folder to WSB config",
                "script": """
$wsbPath = '{wsb_path}'
$hostFolder = '{host_folder}'
$sandboxFolder = '{sandbox_folder}'
$readOnly = '{read_only}' -eq 'true'

[xml]$config = Get-Content $wsbPath
if (-not $config.Configuration.MappedFolders) {
    $mappedFolders = $config.CreateElement('MappedFolders')
    $config.Configuration.AppendChild($mappedFolders) | Out-Null
}

$folder = $config.CreateElement('MappedFolder')
$hostFolderEl = $config.CreateElement('HostFolder')
$hostFolderEl.InnerText = $hostFolder
$folder.AppendChild($hostFolderEl) | Out-Null

if ($sandboxFolder) {
    $sandboxFolderEl = $config.CreateElement('SandboxFolder')
    $sandboxFolderEl.InnerText = $sandboxFolder
    $folder.AppendChild($sandboxFolderEl) | Out-Null
}

$readOnlyEl = $config.CreateElement('ReadOnly')
$readOnlyEl.InnerText = $readOnly.ToString().ToLower()
$folder.AppendChild($readOnlyEl) | Out-Null

$config.Configuration.MappedFolders.AppendChild($folder) | Out-Null
$config.Save($wsbPath)
@{ success = $true; message = 'Mapped folder added' } | ConvertTo-Json
"""
            },
            "add_logon_command": {
                "description": "Add a logon command to WSB config",
                "script": """
$wsbPath = '{wsb_path}'
$command = '{command}'

[xml]$config = Get-Content $wsbPath
if (-not $config.Configuration.LogonCommand) {
    $logonCommand = $config.CreateElement('LogonCommand')
    $config.Configuration.AppendChild($logonCommand) | Out-Null
}

$cmdEl = $config.CreateElement('Command')
$cmdEl.InnerText = $command
$config.Configuration.LogonCommand.AppendChild($cmdEl) | Out-Null

$config.Save($wsbPath)
@{ success = $true; message = 'Logon command added' } | ConvertTo-Json
"""
            },
            
            # Sandbox Launching
            "launch_sandbox": {
                "description": "Launch Windows Sandbox with default settings",
                "script": """
Start-Process 'WindowsSandbox.exe'
@{ success = $true; message = 'Windows Sandbox launched' } | ConvertTo-Json
"""
            },
            "launch_sandbox_with_config": {
                "description": "Launch Windows Sandbox with WSB config file",
                "script": """
$wsbPath = '{wsb_path}'
if (Test-Path $wsbPath) {
    Start-Process $wsbPath
    @{ success = $true; message = "Sandbox launched with config: $wsbPath" } | ConvertTo-Json
} else {
    @{ success = $false; error = "Config file not found: $wsbPath" } | ConvertTo-Json
}
"""
            },
            "check_sandbox_running": {
                "description": "Check if Windows Sandbox is currently running",
                "script": """
$sandbox = Get-Process -Name 'WindowsSandbox' -ErrorAction SilentlyContinue
$sandboxClient = Get-Process -Name 'WindowsSandboxClient' -ErrorAction SilentlyContinue
@{
    running = $null -ne $sandbox -or $null -ne $sandboxClient
    processes = @(
        if ($sandbox) { @{ name = 'WindowsSandbox'; pid = $sandbox.Id; memory_mb = [math]::Round($sandbox.WorkingSet64 / 1MB, 2) } }
        if ($sandboxClient) { @{ name = 'WindowsSandboxClient'; pid = $sandboxClient.Id; memory_mb = [math]::Round($sandboxClient.WorkingSet64 / 1MB, 2) } }
    )
} | ConvertTo-Json -Depth 3
"""
            },
            "close_sandbox": {
                "description": "Close running Windows Sandbox",
                "script": """
$closed = @()
Get-Process -Name 'WindowsSandbox*' -ErrorAction SilentlyContinue | ForEach-Object {
    $closed += $_.Name
    $_ | Stop-Process -Force
}
@{
    success = $true
    closed_processes = $closed
    message = if ($closed.Count -gt 0) { "Closed: $($closed -join ', ')" } else { 'No sandbox processes found' }
} | ConvertTo-Json
"""
            },
            
            # System Requirements
            "check_requirements": {
                "description": "Check system requirements for Windows Sandbox",
                "script": """
$cpu = Get-WmiObject Win32_Processor
$os = Get-WmiObject Win32_OperatingSystem
$memory = [math]::Round($os.TotalVisibleMemorySize / 1MB, 2)

$requirements = @{
    windows_pro_or_enterprise = $os.Caption -match '(Pro|Enterprise|Education)'
    architecture_64bit = $cpu.AddressWidth -eq 64
    virtualization_enabled = $cpu.VirtualizationFirmwareEnabled
    minimum_4gb_ram = $memory -ge 4
    total_ram_gb = $memory
    cpu_cores = $cpu.NumberOfCores
    hyper_v_available = (Get-WindowsOptionalFeature -Online -FeatureName 'Microsoft-Hyper-V' -ErrorAction SilentlyContinue) -ne $null
}

$requirements.meets_all_requirements = $requirements.windows_pro_or_enterprise -and 
    $requirements.architecture_64bit -and 
    $requirements.virtualization_enabled -and 
    $requirements.minimum_4gb_ram

$requirements | ConvertTo-Json
"""
            },
            
            # WSB Templates
            "create_dev_sandbox": {
                "description": "Create a developer sandbox config",
                "script": """
$outputPath = '{output_path}'
$config = @"
<Configuration>
  <VGpu>Enable</VGpu>
  <Networking>Enable</Networking>
  <AudioInput>Enable</AudioInput>
  <VideoInput>Disable</VideoInput>
  <ProtectedClient>Enable</ProtectedClient>
  <PrinterRedirection>Disable</PrinterRedirection>
  <ClipboardRedirection>Enable</ClipboardRedirection>
  <MemoryInMB>8192</MemoryInMB>
  <LogonCommand>
    <Command>powershell -ExecutionPolicy Bypass -Command "Write-Host 'Developer Sandbox Ready'"</Command>
  </LogonCommand>
</Configuration>
"@
$config | Set-Content -Path $outputPath -Encoding UTF8
@{ success = $true; path = $outputPath; template = 'developer' } | ConvertTo-Json
"""
            },
            "create_testing_sandbox": {
                "description": "Create a testing/malware analysis sandbox config",
                "script": """
$outputPath = '{output_path}'
$config = @"
<Configuration>
  <VGpu>Disable</VGpu>
  <Networking>Disable</Networking>
  <AudioInput>Disable</AudioInput>
  <VideoInput>Disable</VideoInput>
  <ProtectedClient>Enable</ProtectedClient>
  <PrinterRedirection>Disable</PrinterRedirection>
  <ClipboardRedirection>Disable</ClipboardRedirection>
  <MemoryInMB>4096</MemoryInMB>
</Configuration>
"@
$config | Set-Content -Path $outputPath -Encoding UTF8
@{ success = $true; path = $outputPath; template = 'isolated_testing' } | ConvertTo-Json
"""
            },
            "create_browser_sandbox": {
                "description": "Create a web browsing sandbox config",
                "script": """
$outputPath = '{output_path}'
$config = @"
<Configuration>
  <VGpu>Enable</VGpu>
  <Networking>Enable</Networking>
  <AudioInput>Enable</AudioInput>
  <VideoInput>Enable</VideoInput>
  <ProtectedClient>Enable</ProtectedClient>
  <PrinterRedirection>Disable</PrinterRedirection>
  <ClipboardRedirection>Enable</ClipboardRedirection>
  <MemoryInMB>4096</MemoryInMB>
  <LogonCommand>
    <Command>start msedge.exe</Command>
  </LogonCommand>
</Configuration>
"@
$config | Set-Content -Path $outputPath -Encoding UTF8
@{ success = $true; path = $outputPath; template = 'browser' } | ConvertTo-Json
"""
            },
            
            # Configuration Management
            "list_wsb_configs": {
                "description": "List all WSB config files in a directory",
                "script": """
$searchPath = '{search_path}'
if (-not $searchPath) { $searchPath = [Environment]::GetFolderPath('Desktop') }

$configs = Get-ChildItem -Path $searchPath -Filter '*.wsb' -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
    @{
        name = $_.Name
        path = $_.FullName
        size_bytes = $_.Length
        created = $_.CreationTime.ToString('yyyy-MM-dd HH:mm:ss')
        modified = $_.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss')
    }
}
@{ configs = @($configs); count = @($configs).Count } | ConvertTo-Json -Depth 3
"""
            },
            "read_wsb_config": {
                "description": "Read and parse a WSB config file",
                "script": """
$wsbPath = '{wsb_path}'
if (Test-Path $wsbPath) {
    [xml]$config = Get-Content $wsbPath
    $result = @{
        path = $wsbPath
        vgpu = $config.Configuration.VGpu
        networking = $config.Configuration.Networking
        audio_input = $config.Configuration.AudioInput
        video_input = $config.Configuration.VideoInput
        protected_client = $config.Configuration.ProtectedClient
        printer_redirection = $config.Configuration.PrinterRedirection
        clipboard_redirection = $config.Configuration.ClipboardRedirection
        memory_mb = $config.Configuration.MemoryInMB
        mapped_folders = @($config.Configuration.MappedFolders.MappedFolder | ForEach-Object {
            @{
                host_folder = $_.HostFolder
                sandbox_folder = $_.SandboxFolder
                read_only = $_.ReadOnly
            }
        })
        logon_commands = @($config.Configuration.LogonCommand.Command)
    }
    $result | ConvertTo-Json -Depth 3
} else {
    @{ error = "Config file not found: $wsbPath" } | ConvertTo-Json
}
"""
            },
            "delete_wsb_config": {
                "description": "Delete a WSB config file",
                "script": """
$wsbPath = '{wsb_path}'
if (Test-Path $wsbPath) {
    Remove-Item $wsbPath -Force
    @{ success = $true; message = "Deleted: $wsbPath" } | ConvertTo-Json
} else {
    @{ success = $false; error = "File not found: $wsbPath" } | ConvertTo-Json
}
"""
            },
            
            # Advanced Configuration
            "set_sandbox_memory": {
                "description": "Set memory allocation for sandbox",
                "script": """
$wsbPath = '{wsb_path}'
$memoryMB = '{memory_mb}'

[xml]$config = Get-Content $wsbPath
if (-not $config.Configuration.MemoryInMB) {
    $memEl = $config.CreateElement('MemoryInMB')
    $config.Configuration.AppendChild($memEl) | Out-Null
}
$config.Configuration.MemoryInMB = $memoryMB
$config.Save($wsbPath)
@{ success = $true; memory_mb = $memoryMB } | ConvertTo-Json
"""
            },
            "set_sandbox_networking": {
                "description": "Enable or disable networking in sandbox",
                "script": """
$wsbPath = '{wsb_path}'
$enabled = '{enabled}' -eq 'true'

[xml]$config = Get-Content $wsbPath
if (-not $config.Configuration.Networking) {
    $netEl = $config.CreateElement('Networking')
    $config.Configuration.AppendChild($netEl) | Out-Null
}
$config.Configuration.Networking = if ($enabled) { 'Enable' } else { 'Disable' }
$config.Save($wsbPath)
@{ success = $true; networking = $config.Configuration.Networking } | ConvertTo-Json
"""
            },
            "set_sandbox_vgpu": {
                "description": "Enable or disable vGPU in sandbox",
                "script": """
$wsbPath = '{wsb_path}'
$enabled = '{enabled}' -eq 'true'

[xml]$config = Get-Content $wsbPath
if (-not $config.Configuration.VGpu) {
    $vgpuEl = $config.CreateElement('VGpu')
    $config.Configuration.AppendChild($vgpuEl) | Out-Null
}
$config.Configuration.VGpu = if ($enabled) { 'Enable' } else { 'Disable' }
$config.Save($wsbPath)
@{ success = $true; vgpu = $config.Configuration.VGpu } | ConvertTo-Json
"""
            },
            
            # Sandbox Utilities
            "copy_to_sandbox": {
                "description": "Prepare files to be copied to sandbox via mapped folder",
                "script": """
$sourcePath = '{source_path}'
$stagingFolder = '{staging_folder}'
if (-not $stagingFolder) { $stagingFolder = "$env:TEMP\\SandboxStaging" }

if (-not (Test-Path $stagingFolder)) {
    New-Item -Path $stagingFolder -ItemType Directory -Force | Out-Null
}

if (Test-Path $sourcePath) {
    Copy-Item -Path $sourcePath -Destination $stagingFolder -Recurse -Force
    @{
        success = $true
        staging_folder = $stagingFolder
        message = "Files staged. Map '$stagingFolder' as a read-only folder in your sandbox config."
    } | ConvertTo-Json
} else {
    @{ success = $false; error = "Source not found: $sourcePath" } | ConvertTo-Json
}
"""
            },
            "clear_staging_folder": {
                "description": "Clear the sandbox staging folder",
                "script": """
$stagingFolder = '{staging_folder}'
if (-not $stagingFolder) { $stagingFolder = "$env:TEMP\\SandboxStaging" }

if (Test-Path $stagingFolder) {
    Remove-Item -Path $stagingFolder -Recurse -Force
    @{ success = $true; message = "Staging folder cleared: $stagingFolder" } | ConvertTo-Json
} else {
    @{ success = $true; message = "Staging folder does not exist" } | ConvertTo-Json
}
"""
            },
            "get_sandbox_logs": {
                "description": "Get Windows Sandbox related event logs",
                "script": """
$maxEvents = {max_events}
if ($maxEvents -eq 0) { $maxEvents = 50 }

$logs = Get-WinEvent -LogName 'Microsoft-Windows-Containers*' -MaxEvents $maxEvents -ErrorAction SilentlyContinue | ForEach-Object {
    @{
        time = $_.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss')
        level = $_.LevelDisplayName
        id = $_.Id
        message = $_.Message
    }
}
@{ logs = @($logs); count = @($logs).Count } | ConvertTo-Json -Depth 3
"""
            }
        }
    

    async def connect(self, credentials: Dict[str, str]) -> bool:
        """Connect to the service"""
        return True

    async def disconnect(self) -> bool:
        """Disconnect from the service"""
        return True

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute a sandbox action"""
        action = kwargs.get("action", "get_sandbox_status")
        
        if action not in self.actions:
            return {
                "status": "error",
                "error": f"Unknown action: {action}. Available: {list(self.actions.keys())}"
            }
        
        action_info = self.actions[action]
        script = action_info["script"]
        
        # Replace parameters in script
        for key, value in kwargs.items():
            if key != "action":
                script = script.replace(f"{{{key}}}", str(value) if value else "")
        
        try:
            result = await self._run_powershell(script)
            return {
                "status": "success",
                "action": action,
                "description": action_info["description"],
                "result": result
            }
        except Exception as e:
            logger.error(f"Sandbox action {action} failed: {e}")
            return {
                "status": "error",
                "action": action,
                "error": str(e)
            }
    
    async def _run_powershell(self, script: str) -> str:
        """Execute PowerShell script"""
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
            raise Exception(stderr.decode() if stderr else "PowerShell execution failed")
        
        return stdout.decode().strip()
