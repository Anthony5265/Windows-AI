"""
Clipboard Sync Plugin for Windows AI
Provides clipboard management, history, and sync capabilities
"""

from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType
from typing import Dict, Any
import asyncio
import subprocess
import json
import logging

logger = logging.getLogger(__name__)


class ClipboardSyncPlugin(IntegrationPlugin):
    """
    Windows Clipboard management plugin
    
    Provides comprehensive clipboard operations including:
    - Clipboard history management
    - Text/image/file clipboard operations
    - Cross-device clipboard sync
    - Clipboard monitoring
    - Data format handling
    """
    
    def __init__(self):
        metadata = PluginMetadata(
            id="windows-clipboard-sync",
            name="Windows Clipboard Sync",
            description="Clipboard management, history, and sync operations",
            version="1.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["windows", "clipboard", "sync", "copy", "paste"],
            requirements=[]
        )
        super().__init__(metadata)
        
        self.actions = {
            # Clipboard Content Operations
            "get_clipboard_text": {
                "description": "Get current text from clipboard",
                "script": "Get-Clipboard -Format Text"
            },
            "set_clipboard_text": {
                "description": "Set text to clipboard",
                "script": "Set-Clipboard -Value '{text}'",
                "params": ["text"]
            },
            "clear_clipboard": {
                "description": "Clear the clipboard",
                "script": "Set-Clipboard -Value $null"
            },
            "get_clipboard_formats": {
                "description": "Get available clipboard formats",
                "script": """
Add-Type -AssemblyName System.Windows.Forms
$formats = [System.Windows.Forms.Clipboard]::GetDataObject().GetFormats()
$formats | ConvertTo-Json
"""
            },
            
            # Clipboard History
            "enable_clipboard_history": {
                "description": "Enable clipboard history feature",
                "script": """
Set-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Clipboard' -Name 'EnableClipboardHistory' -Value 1 -Type DWord
Write-Output 'Clipboard history enabled'
"""
            },
            "disable_clipboard_history": {
                "description": "Disable clipboard history feature",
                "script": """
Set-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Clipboard' -Name 'EnableClipboardHistory' -Value 0 -Type DWord
Write-Output 'Clipboard history disabled'
"""
            },
            "get_clipboard_history_status": {
                "description": "Check if clipboard history is enabled",
                "script": """
$path = 'HKCU:\\Software\\Microsoft\\Clipboard'
if (Test-Path $path) {
    $value = Get-ItemProperty -Path $path -Name 'EnableClipboardHistory' -ErrorAction SilentlyContinue
    @{
        enabled = $value.EnableClipboardHistory -eq 1
        path = $path
    } | ConvertTo-Json
} else {
    @{ enabled = $false; path = $path } | ConvertTo-Json
}
"""
            },
            "clear_clipboard_history": {
                "description": "Clear clipboard history",
                "script": """
Add-Type -AssemblyName System.Windows.Forms
# Clear current clipboard
[System.Windows.Forms.Clipboard]::Clear()
# Trigger history clear via settings
Start-Process 'ms-settings:clipboard' -Wait
Write-Output 'Clipboard cleared. History can be cleared via Settings window.'
"""
            },
            
            # Cloud Sync
            "enable_cloud_sync": {
                "description": "Enable clipboard cloud sync across devices",
                "script": """
$path = 'HKCU:\\Software\\Microsoft\\Clipboard'
if (!(Test-Path $path)) { New-Item -Path $path -Force }
Set-ItemProperty -Path $path -Name 'CloudClipboardAutomaticUpload' -Value 1 -Type DWord
Write-Output 'Cloud clipboard sync enabled'
"""
            },
            "disable_cloud_sync": {
                "description": "Disable clipboard cloud sync",
                "script": """
Set-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Clipboard' -Name 'CloudClipboardAutomaticUpload' -Value 0 -Type DWord
Write-Output 'Cloud clipboard sync disabled'
"""
            },
            "get_cloud_sync_status": {
                "description": "Get cloud sync status",
                "script": """
$path = 'HKCU:\\Software\\Microsoft\\Clipboard'
if (Test-Path $path) {
    $props = Get-ItemProperty -Path $path -ErrorAction SilentlyContinue
    @{
        cloud_sync_enabled = $props.CloudClipboardAutomaticUpload -eq 1
        history_enabled = $props.EnableClipboardHistory -eq 1
    } | ConvertTo-Json
} else {
    @{ cloud_sync_enabled = $false; history_enabled = $false } | ConvertTo-Json
}
"""
            },
            
            # Image Clipboard Operations
            "get_clipboard_image": {
                "description": "Save clipboard image to file",
                "script": """
Add-Type -AssemblyName System.Windows.Forms
$img = [System.Windows.Forms.Clipboard]::GetImage()
if ($img) {
    $path = '{output_path}'
    if (!$path) { $path = [System.IO.Path]::Combine($env:TEMP, 'clipboard_image.png') }
    $img.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
    @{ success = $true; path = $path; width = $img.Width; height = $img.Height } | ConvertTo-Json
} else {
    @{ success = $false; error = 'No image in clipboard' } | ConvertTo-Json
}
""",
                "params": ["output_path"]
            },
            "set_clipboard_image": {
                "description": "Set image to clipboard from file",
                "script": """
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$path = '{image_path}'
if (Test-Path $path) {
    $img = [System.Drawing.Image]::FromFile($path)
    [System.Windows.Forms.Clipboard]::SetImage($img)
    @{ success = $true; path = $path } | ConvertTo-Json
} else {
    @{ success = $false; error = 'Image file not found' } | ConvertTo-Json
}
""",
                "params": ["image_path"]
            },
            "has_clipboard_image": {
                "description": "Check if clipboard contains an image",
                "script": """
Add-Type -AssemblyName System.Windows.Forms
$hasImage = [System.Windows.Forms.Clipboard]::ContainsImage()
@{ has_image = $hasImage } | ConvertTo-Json
"""
            },
            
            # File Clipboard Operations
            "get_clipboard_files": {
                "description": "Get file paths from clipboard",
                "script": """
Add-Type -AssemblyName System.Windows.Forms
$files = [System.Windows.Forms.Clipboard]::GetFileDropList()
if ($files.Count -gt 0) {
    @{ files = @($files); count = $files.Count } | ConvertTo-Json
} else {
    @{ files = @(); count = 0 } | ConvertTo-Json
}
"""
            },
            "set_clipboard_files": {
                "description": "Set files to clipboard (for copy/paste)",
                "script": """
Add-Type -AssemblyName System.Windows.Forms
$paths = '{file_paths}'.Split(',')
$collection = New-Object System.Collections.Specialized.StringCollection
foreach ($path in $paths) {
    if (Test-Path $path.Trim()) {
        $collection.Add($path.Trim())
    }
}
if ($collection.Count -gt 0) {
    [System.Windows.Forms.Clipboard]::SetFileDropList($collection)
    @{ success = $true; files_set = $collection.Count } | ConvertTo-Json
} else {
    @{ success = $false; error = 'No valid files found' } | ConvertTo-Json
}
""",
                "params": ["file_paths"]
            },
            "has_clipboard_files": {
                "description": "Check if clipboard contains files",
                "script": """
Add-Type -AssemblyName System.Windows.Forms
$hasFiles = [System.Windows.Forms.Clipboard]::ContainsFileDropList()
@{ has_files = $hasFiles } | ConvertTo-Json
"""
            },
            
            # HTML/RTF Operations
            "get_clipboard_html": {
                "description": "Get HTML content from clipboard",
                "script": """
Add-Type -AssemblyName System.Windows.Forms
$html = [System.Windows.Forms.Clipboard]::GetText([System.Windows.Forms.TextDataFormat]::Html)
if ($html) {
    @{ html = $html; length = $html.Length } | ConvertTo-Json
} else {
    @{ html = $null; error = 'No HTML in clipboard' } | ConvertTo-Json
}
"""
            },
            "set_clipboard_html": {
                "description": "Set HTML content to clipboard",
                "script": """
Add-Type -AssemblyName System.Windows.Forms
$html = '{html_content}'
[System.Windows.Forms.Clipboard]::SetText($html, [System.Windows.Forms.TextDataFormat]::Html)
@{ success = $true } | ConvertTo-Json
""",
                "params": ["html_content"]
            },
            "get_clipboard_rtf": {
                "description": "Get RTF content from clipboard",
                "script": """
Add-Type -AssemblyName System.Windows.Forms
$rtf = [System.Windows.Forms.Clipboard]::GetText([System.Windows.Forms.TextDataFormat]::Rtf)
if ($rtf) {
    @{ rtf = $rtf; length = $rtf.Length } | ConvertTo-Json
} else {
    @{ rtf = $null; error = 'No RTF in clipboard' } | ConvertTo-Json
}
"""
            },
            
            # Clipboard Monitoring
            "start_clipboard_monitor": {
                "description": "Start monitoring clipboard changes",
                "script": """
$script = {
    Add-Type -AssemblyName System.Windows.Forms
    $lastContent = ''
    while ($true) {
        $current = [System.Windows.Forms.Clipboard]::GetText()
        if ($current -ne $lastContent -and $current) {
            $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
            Write-Output "[$timestamp] Clipboard changed: $($current.Substring(0, [Math]::Min(50, $current.Length)))..."
            $lastContent = $current
        }
        Start-Sleep -Milliseconds 500
    }
}
Start-Job -ScriptBlock $script -Name 'ClipboardMonitor'
Write-Output 'Clipboard monitor started as background job'
"""
            },
            "stop_clipboard_monitor": {
                "description": "Stop clipboard monitoring",
                "script": """
$job = Get-Job -Name 'ClipboardMonitor' -ErrorAction SilentlyContinue
if ($job) {
    Stop-Job -Job $job
    Remove-Job -Job $job
    Write-Output 'Clipboard monitor stopped'
} else {
    Write-Output 'No clipboard monitor running'
}
"""
            },
            "get_monitor_status": {
                "description": "Get clipboard monitor status",
                "script": """
$job = Get-Job -Name 'ClipboardMonitor' -ErrorAction SilentlyContinue
if ($job) {
    @{
        running = $true
        state = $job.State
        started = $job.PSBeginTime
    } | ConvertTo-Json
} else {
    @{ running = $false } | ConvertTo-Json
}
"""
            },
            
            # Data Type Detection
            "detect_clipboard_content": {
                "description": "Detect type of content in clipboard",
                "script": """
Add-Type -AssemblyName System.Windows.Forms
$result = @{
    has_text = [System.Windows.Forms.Clipboard]::ContainsText()
    has_image = [System.Windows.Forms.Clipboard]::ContainsImage()
    has_files = [System.Windows.Forms.Clipboard]::ContainsFileDropList()
    has_audio = [System.Windows.Forms.Clipboard]::ContainsAudio()
    formats = @([System.Windows.Forms.Clipboard]::GetDataObject().GetFormats())
}
$result | ConvertTo-Json
"""
            },
            
            # Clipboard Settings
            "open_clipboard_settings": {
                "description": "Open Windows clipboard settings",
                "script": "Start-Process 'ms-settings:clipboard'"
            },
            "get_clipboard_settings": {
                "description": "Get all clipboard-related settings",
                "script": """
$path = 'HKCU:\\Software\\Microsoft\\Clipboard'
if (Test-Path $path) {
    $props = Get-ItemProperty -Path $path
    @{
        history_enabled = $props.EnableClipboardHistory -eq 1
        cloud_sync = $props.CloudClipboardAutomaticUpload -eq 1
        cross_device = $props.EnableCrossDeviceClipboard -eq 1
    } | ConvertTo-Json
} else {
    @{ history_enabled = $false; cloud_sync = $false; cross_device = $false } | ConvertTo-Json
}
"""
            },
            
            # Utility Actions
            "copy_file_contents": {
                "description": "Copy file contents to clipboard",
                "script": """
$path = '{file_path}'
if (Test-Path $path) {
    $content = Get-Content -Path $path -Raw
    Set-Clipboard -Value $content
    @{ success = $true; characters = $content.Length } | ConvertTo-Json
} else {
    @{ success = $false; error = 'File not found' } | ConvertTo-Json
}
""",
                "params": ["file_path"]
            },
            "paste_to_file": {
                "description": "Paste clipboard text to file",
                "script": """
$path = '{file_path}'
$content = Get-Clipboard -Format Text
if ($content) {
    Set-Content -Path $path -Value $content -Encoding UTF8
    @{ success = $true; path = $path; characters = $content.Length } | ConvertTo-Json
} else {
    @{ success = $false; error = 'No text in clipboard' } | ConvertTo-Json
}
""",
                "params": ["file_path"]
            },
            "append_to_clipboard": {
                "description": "Append text to existing clipboard content",
                "script": """
$current = Get-Clipboard -Format Text
$append = '{text}'
$new = $current + $append
Set-Clipboard -Value $new
@{ success = $true; total_length = $new.Length } | ConvertTo-Json
""",
                "params": ["text"]
            },
            "prepend_to_clipboard": {
                "description": "Prepend text to existing clipboard content",
                "script": """
$current = Get-Clipboard -Format Text
$prepend = '{text}'
$new = $prepend + $current
Set-Clipboard -Value $new
@{ success = $true; total_length = $new.Length } | ConvertTo-Json
""",
                "params": ["text"]
            },
            
            # Cross-Device Operations
            "enable_cross_device": {
                "description": "Enable cross-device clipboard",
                "script": """
$path = 'HKCU:\\Software\\Microsoft\\Clipboard'
if (!(Test-Path $path)) { New-Item -Path $path -Force }
Set-ItemProperty -Path $path -Name 'EnableCrossDeviceClipboard' -Value 1 -Type DWord
Write-Output 'Cross-device clipboard enabled'
"""
            },
            "disable_cross_device": {
                "description": "Disable cross-device clipboard",
                "script": """
Set-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Clipboard' -Name 'EnableCrossDeviceClipboard' -Value 0 -Type DWord
Write-Output 'Cross-device clipboard disabled'
"""
            },
            
            # Clipboard Info
            "get_clipboard_info": {
                "description": "Get comprehensive clipboard information",
                "script": """
Add-Type -AssemblyName System.Windows.Forms
$data = [System.Windows.Forms.Clipboard]::GetDataObject()
$formats = $data.GetFormats()
$text = Get-Clipboard -Format Text
$regPath = 'HKCU:\\Software\\Microsoft\\Clipboard'
$settings = if (Test-Path $regPath) { Get-ItemProperty -Path $regPath } else { $null }

@{
    current_content = @{
        has_text = [System.Windows.Forms.Clipboard]::ContainsText()
        has_image = [System.Windows.Forms.Clipboard]::ContainsImage()
        has_files = [System.Windows.Forms.Clipboard]::ContainsFileDropList()
        text_length = if ($text) { $text.Length } else { 0 }
        formats = $formats
    }
    settings = @{
        history_enabled = $settings.EnableClipboardHistory -eq 1
        cloud_sync = $settings.CloudClipboardAutomaticUpload -eq 1
        cross_device = $settings.EnableCrossDeviceClipboard -eq 1
    }
} | ConvertTo-Json -Depth 3
"""
            }
        }
    
    async def initialize(self) -> bool:
        """Initialize the clipboard plugin"""
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
        """Execute a clipboard action"""
        action = kwargs.get("action", "get_clipboard_text")
        
        if action not in self.actions:
            return {
                "status": "error",
                "error": f"Unknown action: {action}. Available: {list(self.actions.keys())}"
            }
        
        action_info = self.actions[action]
        script = action_info["script"]
        
        # Replace parameters in script
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
            logger.error(f"Clipboard action {action} failed: {e}")
            return {
                "status": "error",
                "action": action,
                "error": str(e)
            }
    
    async def _run_powershell(self, script: str) -> str:
        """Execute PowerShell script and return output"""
        try:
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
        except Exception as e:
            logger.error(f"PowerShell execution failed: {e}")
            raise
    
    async def cleanup(self):
        """Cleanup plugin resources"""
        self._initialized = False
        logger.info(f"Plugin {self.metadata.id} cleaned up")


# Export the plugin class
__all__ = ["ClipboardSyncPlugin"]


plugin = ClipboardSyncPlugin()
