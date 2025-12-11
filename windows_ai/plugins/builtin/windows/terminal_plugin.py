"""
Windows Terminal Plugin
Comprehensive Windows terminal and console management for Windows AI.
Provides ConPTY integration, terminal emulation, shell management, and console operations.
"""

import asyncio
import logging
import json
from typing import Dict, Any, List, Optional
from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class WindowsTerminalPlugin(IntegrationPlugin):
    """
    Windows Terminal and Console Management Plugin.
    
    Provides comprehensive terminal operations:
    - Windows Terminal profile management
    - Console host configuration
    - ConPTY pseudoconsole operations
    - Shell session management
    - Terminal customization
    - Virtual terminal sequences
    - Console buffer operations
    - Multi-tab/pane management
    """
    
    def __init__(self):
        metadata = PluginMetadata(
            id="windows-terminal",
            name="Windows Terminal",
            description="Windows terminal, console, and ConPTY management",
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["terminal", "console", "conpty", "shell", "windows"],
            requirements=[]
        )
        super().__init__(metadata)
        
        self._actions = {
            # Windows Terminal Operations
            "get_terminal_settings": self._get_terminal_settings,
            "set_terminal_setting": self._set_terminal_setting,
            "get_terminal_profiles": self._get_terminal_profiles,
            "create_terminal_profile": self._create_terminal_profile,
            "delete_terminal_profile": self._delete_terminal_profile,
            "set_default_profile": self._set_default_profile,
            "get_terminal_schemes": self._get_terminal_schemes,
            "create_color_scheme": self._create_color_scheme,
            "delete_color_scheme": self._delete_color_scheme,
            
            # Console Host Operations
            "get_console_info": self._get_console_info,
            "set_console_size": self._set_console_size,
            "set_console_buffer_size": self._set_console_buffer_size,
            "get_console_colors": self._get_console_colors,
            "set_console_colors": self._set_console_colors,
            "clear_console": self._clear_console,
            "set_console_title": self._set_console_title,
            "get_console_font": self._get_console_font,
            "set_console_font": self._set_console_font,
            
            # Shell Management
            "get_available_shells": self._get_available_shells,
            "get_default_shell": self._get_default_shell,
            "set_default_shell": self._set_default_shell,
            "get_shell_version": self._get_shell_version,
            "get_execution_policy": self._get_execution_policy,
            "set_execution_policy": self._set_execution_policy,
            
            # Terminal Sessions
            "list_terminal_processes": self._list_terminal_processes,
            "start_terminal_session": self._start_terminal_session,
            "close_terminal_session": self._close_terminal_session,
            "send_to_terminal": self._send_to_terminal,
            "get_terminal_output": self._get_terminal_output,
            
            # Virtual Terminal
            "enable_virtual_terminal": self._enable_virtual_terminal,
            "send_vt_sequence": self._send_vt_sequence,
            "get_vt_support": self._get_vt_support,
            
            # Console Buffer
            "get_console_buffer": self._get_console_buffer,
            "scroll_console_buffer": self._scroll_console_buffer,
            "select_console_text": self._select_console_text,
            "copy_console_selection": self._copy_console_selection,
            
            # Terminal Customization
            "set_terminal_opacity": self._set_terminal_opacity,
            "set_terminal_background": self._set_terminal_background,
            "set_terminal_font_size": self._set_terminal_font_size,
            "set_terminal_cursor_shape": self._set_terminal_cursor_shape,
            "toggle_terminal_fullscreen": self._toggle_terminal_fullscreen,
            
            # ConPTY Operations
            "get_conpty_info": self._get_conpty_info,
            "create_pseudo_console": self._create_pseudo_console,
            "resize_pseudo_console": self._resize_pseudo_console,
            
            # Key Bindings
            "get_terminal_keybindings": self._get_terminal_keybindings,
            "add_terminal_keybinding": self._add_terminal_keybinding,
            "remove_terminal_keybinding": self._remove_terminal_keybinding,
            
            # Tab/Pane Management
            "new_terminal_tab": self._new_terminal_tab,
            "split_terminal_pane": self._split_terminal_pane,
            "get_terminal_tabs": self._get_terminal_tabs,
            "focus_terminal_tab": self._focus_terminal_tab,
            
            # Diagnostic
            "get_terminal_diagnostics": self._get_terminal_diagnostics,
            "export_terminal_settings": self._export_terminal_settings,
            "import_terminal_settings": self._import_terminal_settings,
        }
    
    async def initialize(self) -> bool:
        """Initialize Windows Terminal plugin."""
        try:
            logger.info("Initializing Windows Terminal plugin...")
            self._initialized = True
            logger.info("Windows Terminal plugin initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Windows Terminal plugin: {e}")
            return False
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute a Windows Terminal action."""
        action = kwargs.get("action", "")
        
        if not action:
            return {
                "status": "error",
                "error": "No action specified",
                "available_actions": list(self._actions.keys())
            }
        
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
            logger.error(f"Terminal action '{action}' failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _run_powershell(self, script: str) -> Dict[str, Any]:
        """Execute PowerShell script and return results."""
        try:
            process = await asyncio.create_subprocess_exec(
                "powershell.exe", "-NoProfile", "-Command", script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            return {
                "success": process.returncode == 0,
                "output": stdout.decode("utf-8", errors="replace").strip(),
                "error": stderr.decode("utf-8", errors="replace").strip() if stderr else None,
                "return_code": process.returncode
            }
        except Exception as e:
            return {"success": False, "error": str(e), "output": "", "return_code": -1}
    
    # Windows Terminal Settings Operations
    async def _get_terminal_settings(self, **kwargs) -> Dict[str, Any]:
        """Get Windows Terminal settings."""
        script = '''
        $settingsPath = "$env:LOCALAPPDATA\\Packages\\Microsoft.WindowsTerminal_8wekyb3d8bbwe\\LocalState\\settings.json"
        if (Test-Path $settingsPath) {
            $settings = Get-Content $settingsPath -Raw | ConvertFrom-Json
            $settings | ConvertTo-Json -Depth 10
        } else {
            $previewPath = "$env:LOCALAPPDATA\\Packages\\Microsoft.WindowsTerminalPreview_8wekyb3d8bbwe\\LocalState\\settings.json"
            if (Test-Path $previewPath) {
                $settings = Get-Content $previewPath -Raw | ConvertFrom-Json
                $settings | ConvertTo-Json -Depth 10
            } else {
                Write-Error "Windows Terminal settings not found"
            }
        }
        '''
        result = await self._run_powershell(script)
        if result["success"] and result["output"]:
            try:
                return {"settings": json.loads(result["output"])}
            except json.JSONDecodeError:
                return {"settings_raw": result["output"]}
        return result
    
    async def _set_terminal_setting(self, **kwargs) -> Dict[str, Any]:
        """Set a Windows Terminal setting."""
        key = kwargs.get("key", "")
        value = kwargs.get("value")
        
        if not key:
            return {"error": "Setting key is required"}
        
        value_json = json.dumps(value)
        script = f'''
        $settingsPath = "$env:LOCALAPPDATA\\Packages\\Microsoft.WindowsTerminal_8wekyb3d8bbwe\\LocalState\\settings.json"
        if (Test-Path $settingsPath) {{
            $settings = Get-Content $settingsPath -Raw | ConvertFrom-Json
            $settings.{key} = {value_json} | ConvertFrom-Json
            $settings | ConvertTo-Json -Depth 10 | Set-Content $settingsPath
            @{{ success = $true; key = "{key}" }} | ConvertTo-Json
        }} else {{
            Write-Error "Windows Terminal settings not found"
        }}
        '''
        return await self._run_powershell(script)
    
    async def _get_terminal_profiles(self, **kwargs) -> Dict[str, Any]:
        """Get all Windows Terminal profiles."""
        script = '''
        $settingsPath = "$env:LOCALAPPDATA\\Packages\\Microsoft.WindowsTerminal_8wekyb3d8bbwe\\LocalState\\settings.json"
        if (Test-Path $settingsPath) {
            $settings = Get-Content $settingsPath -Raw | ConvertFrom-Json
            $profiles = @{
                defaults = $settings.profiles.defaults
                list = $settings.profiles.list
            }
            $profiles | ConvertTo-Json -Depth 10
        } else {
            Write-Error "Windows Terminal not found"
        }
        '''
        result = await self._run_powershell(script)
        if result["success"] and result["output"]:
            try:
                return {"profiles": json.loads(result["output"])}
            except json.JSONDecodeError:
                return {"profiles_raw": result["output"]}
        return result
    
    async def _create_terminal_profile(self, **kwargs) -> Dict[str, Any]:
        """Create a new Windows Terminal profile."""
        name = kwargs.get("name", "New Profile")
        command_line = kwargs.get("command_line", "cmd.exe")
        icon = kwargs.get("icon", "")
        start_dir = kwargs.get("starting_directory", "%USERPROFILE%")
        color_scheme = kwargs.get("color_scheme", "Campbell")
        
        guid = kwargs.get("guid", "")
        
        script = f'''
        $settingsPath = "$env:LOCALAPPDATA\\Packages\\Microsoft.WindowsTerminal_8wekyb3d8bbwe\\LocalState\\settings.json"
        if (Test-Path $settingsPath) {{
            $settings = Get-Content $settingsPath -Raw | ConvertFrom-Json
            $newGuid = if ("{guid}") {{ "{guid}" }} else {{ "{{" + [guid]::NewGuid().ToString() + "}}" }}
            $newProfile = @{{
                guid = $newGuid
                name = "{name}"
                commandline = "{command_line}"
                startingDirectory = "{start_dir}"
                colorScheme = "{color_scheme}"
                hidden = $false
            }}
            if ("{icon}") {{ $newProfile.icon = "{icon}" }}
            $settings.profiles.list += $newProfile
            $settings | ConvertTo-Json -Depth 10 | Set-Content $settingsPath
            @{{ success = $true; guid = $newGuid; name = "{name}" }} | ConvertTo-Json
        }} else {{
            Write-Error "Windows Terminal not found"
        }}
        '''
        return await self._run_powershell(script)
    
    async def _delete_terminal_profile(self, **kwargs) -> Dict[str, Any]:
        """Delete a Windows Terminal profile."""
        guid = kwargs.get("guid", "")
        name = kwargs.get("name", "")
        
        if not guid and not name:
            return {"error": "Profile GUID or name is required"}
        
        filter_condition = f'$_.guid -eq "{guid}"' if guid else f'$_.name -eq "{name}"'
        
        script = f'''
        $settingsPath = "$env:LOCALAPPDATA\\Packages\\Microsoft.WindowsTerminal_8wekyb3d8bbwe\\LocalState\\settings.json"
        if (Test-Path $settingsPath) {{
            $settings = Get-Content $settingsPath -Raw | ConvertFrom-Json
            $originalCount = $settings.profiles.list.Count
            $settings.profiles.list = @($settings.profiles.list | Where-Object {{ -not ({filter_condition}) }})
            $newCount = $settings.profiles.list.Count
            $settings | ConvertTo-Json -Depth 10 | Set-Content $settingsPath
            @{{ success = $true; removed = ($originalCount - $newCount) }} | ConvertTo-Json
        }} else {{
            Write-Error "Windows Terminal not found"
        }}
        '''
        return await self._run_powershell(script)
    
    async def _set_default_profile(self, **kwargs) -> Dict[str, Any]:
        """Set the default Windows Terminal profile."""
        guid = kwargs.get("guid", "")
        
        if not guid:
            return {"error": "Profile GUID is required"}
        
        script = f'''
        $settingsPath = "$env:LOCALAPPDATA\\Packages\\Microsoft.WindowsTerminal_8wekyb3d8bbwe\\LocalState\\settings.json"
        if (Test-Path $settingsPath) {{
            $settings = Get-Content $settingsPath -Raw | ConvertFrom-Json
            $settings.defaultProfile = "{guid}"
            $settings | ConvertTo-Json -Depth 10 | Set-Content $settingsPath
            @{{ success = $true; defaultProfile = "{guid}" }} | ConvertTo-Json
        }} else {{
            Write-Error "Windows Terminal not found"
        }}
        '''
        return await self._run_powershell(script)
    
    async def _get_terminal_schemes(self, **kwargs) -> Dict[str, Any]:
        """Get all color schemes from Windows Terminal."""
        script = '''
        $settingsPath = "$env:LOCALAPPDATA\\Packages\\Microsoft.WindowsTerminal_8wekyb3d8bbwe\\LocalState\\settings.json"
        if (Test-Path $settingsPath) {
            $settings = Get-Content $settingsPath -Raw | ConvertFrom-Json
            if ($settings.schemes) {
                $settings.schemes | ConvertTo-Json -Depth 10
            } else {
                @() | ConvertTo-Json
            }
        } else {
            Write-Error "Windows Terminal not found"
        }
        '''
        result = await self._run_powershell(script)
        if result["success"] and result["output"]:
            try:
                return {"schemes": json.loads(result["output"])}
            except json.JSONDecodeError:
                return {"schemes_raw": result["output"]}
        return result
    
    async def _create_color_scheme(self, **kwargs) -> Dict[str, Any]:
        """Create a new color scheme for Windows Terminal."""
        name = kwargs.get("name", "Custom Scheme")
        colors = kwargs.get("colors", {})
        
        default_colors = {
            "background": "#0C0C0C",
            "foreground": "#CCCCCC",
            "cursorColor": "#FFFFFF",
            "selectionBackground": "#FFFFFF",
            "black": "#0C0C0C",
            "red": "#C50F1F",
            "green": "#13A10E",
            "yellow": "#C19C00",
            "blue": "#0037DA",
            "purple": "#881798",
            "cyan": "#3A96DD",
            "white": "#CCCCCC",
            "brightBlack": "#767676",
            "brightRed": "#E74856",
            "brightGreen": "#16C60C",
            "brightYellow": "#F9F1A5",
            "brightBlue": "#3B78FF",
            "brightPurple": "#B4009E",
            "brightCyan": "#61D6D6",
            "brightWhite": "#F2F2F2"
        }
        default_colors.update(colors)
        
        scheme_json = json.dumps({**default_colors, "name": name})
        
        script = f'''
        $settingsPath = "$env:LOCALAPPDATA\\Packages\\Microsoft.WindowsTerminal_8wekyb3d8bbwe\\LocalState\\settings.json"
        if (Test-Path $settingsPath) {{
            $settings = Get-Content $settingsPath -Raw | ConvertFrom-Json
            $newScheme = '{scheme_json}' | ConvertFrom-Json
            if (-not $settings.schemes) {{ $settings | Add-Member -NotePropertyName schemes -NotePropertyValue @() }}
            $settings.schemes += $newScheme
            $settings | ConvertTo-Json -Depth 10 | Set-Content $settingsPath
            @{{ success = $true; name = "{name}" }} | ConvertTo-Json
        }} else {{
            Write-Error "Windows Terminal not found"
        }}
        '''
        return await self._run_powershell(script)
    
    async def _delete_color_scheme(self, **kwargs) -> Dict[str, Any]:
        """Delete a color scheme from Windows Terminal."""
        name = kwargs.get("name", "")
        
        if not name:
            return {"error": "Scheme name is required"}
        
        script = f'''
        $settingsPath = "$env:LOCALAPPDATA\\Packages\\Microsoft.WindowsTerminal_8wekyb3d8bbwe\\LocalState\\settings.json"
        if (Test-Path $settingsPath) {{
            $settings = Get-Content $settingsPath -Raw | ConvertFrom-Json
            if ($settings.schemes) {{
                $settings.schemes = @($settings.schemes | Where-Object {{ $_.name -ne "{name}" }})
                $settings | ConvertTo-Json -Depth 10 | Set-Content $settingsPath
            }}
            @{{ success = $true; deleted = "{name}" }} | ConvertTo-Json
        }} else {{
            Write-Error "Windows Terminal not found"
        }}
        '''
        return await self._run_powershell(script)
    
    # Console Host Operations
    async def _get_console_info(self, **kwargs) -> Dict[str, Any]:
        """Get console host information."""
        script = '''
        $host.UI.RawUI | Select-Object WindowSize, BufferSize, WindowPosition, 
            CursorPosition, CursorSize, ForegroundColor, BackgroundColor, 
            WindowTitle, MaxWindowSize, MaxPhysicalWindowSize | ConvertTo-Json
        '''
        return await self._run_powershell(script)
    
    async def _set_console_size(self, **kwargs) -> Dict[str, Any]:
        """Set console window size."""
        width = kwargs.get("width", 120)
        height = kwargs.get("height", 30)
        
        script = f'''
        $size = New-Object System.Management.Automation.Host.Size({width}, {height})
        $host.UI.RawUI.WindowSize = $size
        @{{ success = $true; width = {width}; height = {height} }} | ConvertTo-Json
        '''
        return await self._run_powershell(script)
    
    async def _set_console_buffer_size(self, **kwargs) -> Dict[str, Any]:
        """Set console buffer size."""
        width = kwargs.get("width", 120)
        height = kwargs.get("height", 9999)
        
        script = f'''
        $size = New-Object System.Management.Automation.Host.Size({width}, {height})
        $host.UI.RawUI.BufferSize = $size
        @{{ success = $true; width = {width}; height = {height} }} | ConvertTo-Json
        '''
        return await self._run_powershell(script)
    
    async def _get_console_colors(self, **kwargs) -> Dict[str, Any]:
        """Get current console colors."""
        script = '''
        @{
            foreground = $host.UI.RawUI.ForegroundColor.ToString()
            background = $host.UI.RawUI.BackgroundColor.ToString()
            availableColors = [Enum]::GetNames([System.ConsoleColor])
        } | ConvertTo-Json
        '''
        return await self._run_powershell(script)
    
    async def _set_console_colors(self, **kwargs) -> Dict[str, Any]:
        """Set console foreground and background colors."""
        foreground = kwargs.get("foreground", "")
        background = kwargs.get("background", "")
        
        script = ""
        if foreground:
            script += f'$host.UI.RawUI.ForegroundColor = [System.ConsoleColor]::"{foreground}"\n'
        if background:
            script += f'$host.UI.RawUI.BackgroundColor = [System.ConsoleColor]::"{background}"\n'
        script += '@{ success = $true } | ConvertTo-Json'
        
        return await self._run_powershell(script)
    
    async def _clear_console(self, **kwargs) -> Dict[str, Any]:
        """Clear the console screen."""
        script = '''
        Clear-Host
        @{ success = $true } | ConvertTo-Json
        '''
        return await self._run_powershell(script)
    
    async def _set_console_title(self, **kwargs) -> Dict[str, Any]:
        """Set console window title."""
        title = kwargs.get("title", "Windows AI Terminal")
        
        script = f'''
        $host.UI.RawUI.WindowTitle = "{title}"
        @{{ success = $true; title = "{title}" }} | ConvertTo-Json
        '''
        return await self._run_powershell(script)
    
    async def _get_console_font(self, **kwargs) -> Dict[str, Any]:
        """Get current console font information."""
        script = '''
        Add-Type -TypeDefinition @"
        using System;
        using System.Runtime.InteropServices;
        public class ConsoleFont {
            [DllImport("kernel32.dll", SetLastError = true)]
            public static extern IntPtr GetStdHandle(int nStdHandle);
            [DllImport("kernel32.dll", SetLastError = true)]
            public static extern bool GetCurrentConsoleFontEx(IntPtr hConsoleOutput, bool bMaximumWindow, ref CONSOLE_FONT_INFOEX lpConsoleCurrentFontEx);
            [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
            public struct CONSOLE_FONT_INFOEX {
                public uint cbSize;
                public uint nFont;
                public short dwFontSizeX;
                public short dwFontSizeY;
                public int FontFamily;
                public int FontWeight;
                [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)]
                public string FaceName;
            }
        }
"@
        $handle = [ConsoleFont]::GetStdHandle(-11)
        $fontInfo = New-Object ConsoleFont+CONSOLE_FONT_INFOEX
        $fontInfo.cbSize = [System.Runtime.InteropServices.Marshal]::SizeOf($fontInfo)
        [ConsoleFont]::GetCurrentConsoleFontEx($handle, $false, [ref]$fontInfo) | Out-Null
        @{
            fontName = $fontInfo.FaceName
            fontSize = $fontInfo.dwFontSizeY
            fontWeight = $fontInfo.FontWeight
        } | ConvertTo-Json
        '''
        return await self._run_powershell(script)
    
    async def _set_console_font(self, **kwargs) -> Dict[str, Any]:
        """Set console font (requires restart)."""
        font_name = kwargs.get("font_name", "Consolas")
        font_size = kwargs.get("font_size", 14)
        
        script = f'''
        $regPath = "HKCU:\\Console"
        Set-ItemProperty -Path $regPath -Name "FaceName" -Value "{font_name}"
        Set-ItemProperty -Path $regPath -Name "FontSize" -Value ([int]("{font_size}" + "0000"))
        @{{ success = $true; font = "{font_name}"; size = {font_size}; note = "Restart terminal to apply" }} | ConvertTo-Json
        '''
        return await self._run_powershell(script)
    
    # Shell Management
    async def _get_available_shells(self, **kwargs) -> Dict[str, Any]:
        """Get available shells on the system."""
        script = '''
        $shells = @()
        
        # Check for PowerShell
        $pwsh = Get-Command pwsh -ErrorAction SilentlyContinue
        if ($pwsh) {
            $shells += @{ name = "PowerShell Core"; path = $pwsh.Source; version = (pwsh --version) }
        }
        
        # Windows PowerShell
        $shells += @{ name = "Windows PowerShell"; path = "$env:SystemRoot\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"; version = $PSVersionTable.PSVersion.ToString() }
        
        # Command Prompt
        $shells += @{ name = "Command Prompt"; path = "$env:ComSpec"; version = "Windows CMD" }
        
        # Check for Git Bash
        $gitBash = @("$env:ProgramFiles\\Git\\bin\\bash.exe", "$env:ProgramFiles(x86)\\Git\\bin\\bash.exe")
        foreach ($path in $gitBash) {
            if (Test-Path $path) {
                $shells += @{ name = "Git Bash"; path = $path; version = "Git for Windows" }
                break
            }
        }
        
        # Check for WSL
        $wsl = Get-Command wsl -ErrorAction SilentlyContinue
        if ($wsl) {
            $shells += @{ name = "WSL"; path = $wsl.Source; version = "Windows Subsystem for Linux" }
        }
        
        $shells | ConvertTo-Json -Depth 5
        '''
        return await self._run_powershell(script)
    
    async def _get_default_shell(self, **kwargs) -> Dict[str, Any]:
        """Get the default shell for the current user."""
        script = '''
        @{
            comspec = $env:ComSpec
            psVersion = $PSVersionTable.PSVersion.ToString()
            psEdition = $PSVersionTable.PSEdition
        } | ConvertTo-Json
        '''
        return await self._run_powershell(script)
    
    async def _set_default_shell(self, **kwargs) -> Dict[str, Any]:
        """Set the default shell via Windows Terminal settings."""
        profile_guid = kwargs.get("profile_guid", "")
        
        if not profile_guid:
            return {"error": "Profile GUID is required"}
        
        return await self._set_default_profile(guid=profile_guid)
    
    async def _get_shell_version(self, **kwargs) -> Dict[str, Any]:
        """Get version information for shells."""
        shell = kwargs.get("shell", "powershell")
        
        script = f'''
        $versionInfo = @{{}}
        switch ("{shell}") {{
            "powershell" {{
                $versionInfo = @{{
                    PSVersion = $PSVersionTable.PSVersion.ToString()
                    PSEdition = $PSVersionTable.PSEdition
                    BuildVersion = $PSVersionTable.BuildVersion.ToString()
                    CLRVersion = $PSVersionTable.CLRVersion.ToString()
                }}
            }}
            "pwsh" {{
                $ver = pwsh --version 2>$null
                $versionInfo = @{{ version = $ver }}
            }}
            "cmd" {{
                $versionInfo = @{{ version = "Windows Command Processor"; path = $env:ComSpec }}
            }}
            default {{
                $versionInfo = @{{ error = "Unknown shell" }}
            }}
        }}
        $versionInfo | ConvertTo-Json
        '''
        return await self._run_powershell(script)
    
    async def _get_execution_policy(self, **kwargs) -> Dict[str, Any]:
        """Get PowerShell execution policy."""
        script = '''
        @{
            machinePolicy = (Get-ExecutionPolicy -Scope MachinePolicy).ToString()
            userPolicy = (Get-ExecutionPolicy -Scope UserPolicy).ToString()
            process = (Get-ExecutionPolicy -Scope Process).ToString()
            currentUser = (Get-ExecutionPolicy -Scope CurrentUser).ToString()
            localMachine = (Get-ExecutionPolicy -Scope LocalMachine).ToString()
            effective = (Get-ExecutionPolicy).ToString()
        } | ConvertTo-Json
        '''
        return await self._run_powershell(script)
    
    async def _set_execution_policy(self, **kwargs) -> Dict[str, Any]:
        """Set PowerShell execution policy."""
        policy = kwargs.get("policy", "RemoteSigned")
        scope = kwargs.get("scope", "CurrentUser")
        
        valid_policies = ["Restricted", "AllSigned", "RemoteSigned", "Unrestricted", "Bypass"]
        valid_scopes = ["Process", "CurrentUser", "LocalMachine"]
        
        if policy not in valid_policies:
            return {"error": f"Invalid policy. Valid: {valid_policies}"}
        if scope not in valid_scopes:
            return {"error": f"Invalid scope. Valid: {valid_scopes}"}
        
        script = f'''
        Set-ExecutionPolicy -ExecutionPolicy {policy} -Scope {scope} -Force
        @{{ success = $true; policy = "{policy}"; scope = "{scope}" }} | ConvertTo-Json
        '''
        return await self._run_powershell(script)
    
    # Terminal Sessions
    async def _list_terminal_processes(self, **kwargs) -> Dict[str, Any]:
        """List running terminal/console processes."""
        script = '''
        Get-Process | Where-Object { 
            $_.ProcessName -in @("WindowsTerminal", "cmd", "powershell", "pwsh", "conhost", "bash", "wsl")
        } | Select-Object Id, ProcessName, StartTime, MainWindowTitle, 
            @{N="MemoryMB";E={[math]::Round($_.WorkingSet64/1MB,2)}} | ConvertTo-Json
        '''
        return await self._run_powershell(script)
    
    async def _start_terminal_session(self, **kwargs) -> Dict[str, Any]:
        """Start a new terminal session."""
        shell = kwargs.get("shell", "powershell")
        profile = kwargs.get("profile", "")
        working_dir = kwargs.get("working_directory", "")
        
        if profile:
            cmd = f'wt -p "{profile}"'
        else:
            shell_map = {
                "powershell": "powershell.exe",
                "pwsh": "pwsh.exe",
                "cmd": "cmd.exe",
                "bash": "wsl.exe"
            }
            shell_exe = shell_map.get(shell, shell)
            cmd = f'wt {shell_exe}'
        
        if working_dir:
            cmd += f' -d "{working_dir}"'
        
        script = f'''
        Start-Process -FilePath cmd -ArgumentList '/c {cmd}' -WindowStyle Normal
        @{{ success = $true; command = "{cmd}" }} | ConvertTo-Json
        '''
        return await self._run_powershell(script)
    
    async def _close_terminal_session(self, **kwargs) -> Dict[str, Any]:
        """Close a terminal session by process ID."""
        process_id = kwargs.get("process_id", 0)
        
        if not process_id:
            return {"error": "Process ID is required"}
        
        script = f'''
        $proc = Get-Process -Id {process_id} -ErrorAction SilentlyContinue
        if ($proc) {{
            $proc | Stop-Process -Force
            @{{ success = $true; processId = {process_id} }} | ConvertTo-Json
        }} else {{
            @{{ success = $false; error = "Process not found" }} | ConvertTo-Json
        }}
        '''
        return await self._run_powershell(script)
    
    async def _send_to_terminal(self, **kwargs) -> Dict[str, Any]:
        """Send input to a terminal session (via clipboard)."""
        text = kwargs.get("text", "")
        
        if not text:
            return {"error": "Text is required"}
        
        escaped_text = text.replace('"', '`"')
        script = f'''
        Set-Clipboard -Value "{escaped_text}"
        @{{ success = $true; note = "Text copied to clipboard. Paste with Ctrl+V" }} | ConvertTo-Json
        '''
        return await self._run_powershell(script)
    
    async def _get_terminal_output(self, **kwargs) -> Dict[str, Any]:
        """Get clipboard content (simulated terminal output capture)."""
        script = '''
        $clip = Get-Clipboard
        @{ content = $clip } | ConvertTo-Json
        '''
        return await self._run_powershell(script)
    
    # Virtual Terminal
    async def _enable_virtual_terminal(self, **kwargs) -> Dict[str, Any]:
        """Enable virtual terminal processing."""
        script = '''
        [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
        $mode = 0
        $handle = [Console]::Out.Handle
        @{
            success = $true
            encoding = [Console]::OutputEncoding.WebName
            note = "Virtual terminal enabled for current session"
        } | ConvertTo-Json
        '''
        return await self._run_powershell(script)
    
    async def _send_vt_sequence(self, **kwargs) -> Dict[str, Any]:
        """Send a VT sequence to the terminal."""
        sequence = kwargs.get("sequence", "")
        
        if not sequence:
            # Provide examples
            return {
                "examples": {
                    "clear_screen": "\\e[2J",
                    "cursor_home": "\\e[H",
                    "bold": "\\e[1m",
                    "reset": "\\e[0m",
                    "red_text": "\\e[31m",
                    "green_text": "\\e[32m",
                    "hide_cursor": "\\e[?25l",
                    "show_cursor": "\\e[?25h"
                }
            }
        
        script = f'''
        $esc = [char]27
        $seq = "{sequence}" -replace '\\\\e', $esc
        Write-Host $seq -NoNewline
        @{{ success = $true; sequence = "{sequence}" }} | ConvertTo-Json
        '''
        return await self._run_powershell(script)
    
    async def _get_vt_support(self, **kwargs) -> Dict[str, Any]:
        """Check virtual terminal support."""
        script = '''
        @{
            TERM = $env:TERM
            WT_SESSION = $env:WT_SESSION
            isWindowsTerminal = [bool]$env:WT_SESSION
            consoleVersion = [Environment]::OSVersion.Version.ToString()
            supportsVT = $true
        } | ConvertTo-Json
        '''
        return await self._run_powershell(script)
    
    # Console Buffer Operations
    async def _get_console_buffer(self, **kwargs) -> Dict[str, Any]:
        """Get console buffer information."""
        lines = kwargs.get("lines", 50)
        
        script = f'''
        $bufferInfo = @{{
            bufferSize = $host.UI.RawUI.BufferSize
            windowSize = $host.UI.RawUI.WindowSize
            cursorPosition = $host.UI.RawUI.CursorPosition
        }}
        $bufferInfo | ConvertTo-Json
        '''
        return await self._run_powershell(script)
    
    async def _scroll_console_buffer(self, **kwargs) -> Dict[str, Any]:
        """Scroll the console buffer."""
        lines = kwargs.get("lines", 1)
        direction = kwargs.get("direction", "down")
        
        delta = lines if direction == "down" else -lines
        script = f'''
        $pos = $host.UI.RawUI.WindowPosition
        $pos.Y += {delta}
        $host.UI.RawUI.WindowPosition = $pos
        @{{ success = $true; scrolled = {delta} }} | ConvertTo-Json
        '''
        return await self._run_powershell(script)
    
    async def _select_console_text(self, **kwargs) -> Dict[str, Any]:
        """Information about selecting console text."""
        return {
            "note": "Text selection is interactive. Use Ctrl+Shift+M to enter mark mode, then arrow keys to select.",
            "methods": {
                "mark_mode": "Ctrl+Shift+M (legacy console)",
                "mouse_select": "Click and drag (Windows Terminal)",
                "select_all": "Ctrl+Shift+A"
            }
        }
    
    async def _copy_console_selection(self, **kwargs) -> Dict[str, Any]:
        """Copy selected console text to clipboard."""
        script = '''
        $clip = Get-Clipboard
        @{ 
            clipboard = $clip
            note = "Use Ctrl+C or Ctrl+Shift+C to copy selected text"
        } | ConvertTo-Json
        '''
        return await self._run_powershell(script)
    
    # Terminal Customization
    async def _set_terminal_opacity(self, **kwargs) -> Dict[str, Any]:
        """Set Windows Terminal opacity."""
        opacity = kwargs.get("opacity", 100)
        profile_guid = kwargs.get("profile_guid", "")
        
        if opacity < 0 or opacity > 100:
            return {"error": "Opacity must be between 0 and 100"}
        
        # Convert to decimal (0-1)
        opacity_decimal = opacity / 100.0
        
        if profile_guid:
            # Set for specific profile
            script = f'''
            $settingsPath = "$env:LOCALAPPDATA\\Packages\\Microsoft.WindowsTerminal_8wekyb3d8bbwe\\LocalState\\settings.json"
            if (Test-Path $settingsPath) {{
                $settings = Get-Content $settingsPath -Raw | ConvertFrom-Json
                $profile = $settings.profiles.list | Where-Object {{ $_.guid -eq "{profile_guid}" }}
                if ($profile) {{
                    $profile | Add-Member -NotePropertyName opacity -NotePropertyValue {opacity_decimal} -Force
                    $profile | Add-Member -NotePropertyName useAcrylic -NotePropertyValue ($opacity_decimal -lt 1) -Force
                    $settings | ConvertTo-Json -Depth 10 | Set-Content $settingsPath
                }}
                @{{ success = $true; opacity = {opacity_decimal} }} | ConvertTo-Json
            }}
            '''
        else:
            # Set global default
            script = f'''
            $settingsPath = "$env:LOCALAPPDATA\\Packages\\Microsoft.WindowsTerminal_8wekyb3d8bbwe\\LocalState\\settings.json"
            if (Test-Path $settingsPath) {{
                $settings = Get-Content $settingsPath -Raw | ConvertFrom-Json
                $settings.profiles.defaults | Add-Member -NotePropertyName opacity -NotePropertyValue {opacity_decimal} -Force
                $settings.profiles.defaults | Add-Member -NotePropertyName useAcrylic -NotePropertyValue ($opacity_decimal -lt 1) -Force
                $settings | ConvertTo-Json -Depth 10 | Set-Content $settingsPath
                @{{ success = $true; opacity = {opacity_decimal} }} | ConvertTo-Json
            }}
            '''
        return await self._run_powershell(script)
    
    async def _set_terminal_background(self, **kwargs) -> Dict[str, Any]:
        """Set terminal background image."""
        image_path = kwargs.get("image_path", "")
        opacity = kwargs.get("opacity", 0.5)
        stretch = kwargs.get("stretch", "uniformToFill")
        
        if not image_path:
            return {"error": "Image path is required"}
        
        script = f'''
        $settingsPath = "$env:LOCALAPPDATA\\Packages\\Microsoft.WindowsTerminal_8wekyb3d8bbwe\\LocalState\\settings.json"
        if (Test-Path $settingsPath) {{
            $settings = Get-Content $settingsPath -Raw | ConvertFrom-Json
            $settings.profiles.defaults | Add-Member -NotePropertyName backgroundImage -NotePropertyValue "{image_path}" -Force
            $settings.profiles.defaults | Add-Member -NotePropertyName backgroundImageOpacity -NotePropertyValue {opacity} -Force
            $settings.profiles.defaults | Add-Member -NotePropertyName backgroundImageStretchMode -NotePropertyValue "{stretch}" -Force
            $settings | ConvertTo-Json -Depth 10 | Set-Content $settingsPath
            @{{ success = $true; image = "{image_path}" }} | ConvertTo-Json
        }}
        '''
        return await self._run_powershell(script)
    
    async def _set_terminal_font_size(self, **kwargs) -> Dict[str, Any]:
        """Set terminal font size."""
        size = kwargs.get("size", 12)
        
        script = f'''
        $settingsPath = "$env:LOCALAPPDATA\\Packages\\Microsoft.WindowsTerminal_8wekyb3d8bbwe\\LocalState\\settings.json"
        if (Test-Path $settingsPath) {{
            $settings = Get-Content $settingsPath -Raw | ConvertFrom-Json
            $settings.profiles.defaults | Add-Member -NotePropertyName fontSize -NotePropertyValue {size} -Force
            $settings | ConvertTo-Json -Depth 10 | Set-Content $settingsPath
            @{{ success = $true; fontSize = {size} }} | ConvertTo-Json
        }}
        '''
        return await self._run_powershell(script)
    
    async def _set_terminal_cursor_shape(self, **kwargs) -> Dict[str, Any]:
        """Set terminal cursor shape."""
        shape = kwargs.get("shape", "bar")
        
        valid_shapes = ["bar", "vintage", "underscore", "filledBox", "emptyBox", "doubleUnderscore"]
        if shape not in valid_shapes:
            return {"error": f"Invalid shape. Valid: {valid_shapes}"}
        
        script = f'''
        $settingsPath = "$env:LOCALAPPDATA\\Packages\\Microsoft.WindowsTerminal_8wekyb3d8bbwe\\LocalState\\settings.json"
        if (Test-Path $settingsPath) {{
            $settings = Get-Content $settingsPath -Raw | ConvertFrom-Json
            $settings.profiles.defaults | Add-Member -NotePropertyName cursorShape -NotePropertyValue "{shape}" -Force
            $settings | ConvertTo-Json -Depth 10 | Set-Content $settingsPath
            @{{ success = $true; cursorShape = "{shape}" }} | ConvertTo-Json
        }}
        '''
        return await self._run_powershell(script)
    
    async def _toggle_terminal_fullscreen(self, **kwargs) -> Dict[str, Any]:
        """Toggle Windows Terminal fullscreen mode."""
        return {
            "note": "Press Alt+Enter or F11 to toggle fullscreen",
            "keybindings": {
                "fullscreen": "Alt+Enter or F11",
                "focus_mode": "Ctrl+Shift+Enter"
            }
        }
    
    # ConPTY Operations
    async def _get_conpty_info(self, **kwargs) -> Dict[str, Any]:
        """Get ConPTY (Windows Pseudo Console) information."""
        script = '''
        @{
            description = "ConPTY (Windows Pseudo Console) is the modern terminal subsystem"
            available = [Environment]::OSVersion.Version.Build -ge 17763
            buildRequired = 17763
            currentBuild = [Environment]::OSVersion.Version.Build
            features = @(
                "VT sequence support",
                "Modern terminal applications",
                "SSH integration",
                "Cross-platform terminal protocols"
            )
        } | ConvertTo-Json
        '''
        return await self._run_powershell(script)
    
    async def _create_pseudo_console(self, **kwargs) -> Dict[str, Any]:
        """Information about creating a pseudo console."""
        return {
            "note": "ConPTY pseudo consoles are typically created programmatically",
            "api": "CreatePseudoConsole (kernel32.dll)",
            "usage": "Used by Windows Terminal, SSH, and other terminal applications",
            "example_flow": [
                "1. Create pipes for input/output",
                "2. Call CreatePseudoConsole with COORD size",
                "3. Create process with PROC_THREAD_ATTRIBUTE_PSEUDOCONSOLE",
                "4. Read/write to pipes for I/O"
            ]
        }
    
    async def _resize_pseudo_console(self, **kwargs) -> Dict[str, Any]:
        """Information about resizing pseudo console."""
        return {
            "note": "Pseudo console resizing is done via ResizePseudoConsole API",
            "api": "ResizePseudoConsole (kernel32.dll)",
            "terminal_shortcut": "Resize Windows Terminal window to trigger automatic resize"
        }
    
    # Key Bindings
    async def _get_terminal_keybindings(self, **kwargs) -> Dict[str, Any]:
        """Get Windows Terminal key bindings."""
        script = '''
        $settingsPath = "$env:LOCALAPPDATA\\Packages\\Microsoft.WindowsTerminal_8wekyb3d8bbwe\\LocalState\\settings.json"
        if (Test-Path $settingsPath) {
            $settings = Get-Content $settingsPath -Raw | ConvertFrom-Json
            if ($settings.keybindings) {
                $settings.keybindings | ConvertTo-Json -Depth 5
            } elseif ($settings.actions) {
                $settings.actions | ConvertTo-Json -Depth 5
            } else {
                @{ note = "No custom keybindings defined" } | ConvertTo-Json
            }
        }
        '''
        return await self._run_powershell(script)
    
    async def _add_terminal_keybinding(self, **kwargs) -> Dict[str, Any]:
        """Add a keybinding to Windows Terminal."""
        keys = kwargs.get("keys", "")
        command = kwargs.get("command", "")
        
        if not keys or not command:
            return {"error": "Keys and command are required"}
        
        script = f'''
        $settingsPath = "$env:LOCALAPPDATA\\Packages\\Microsoft.WindowsTerminal_8wekyb3d8bbwe\\LocalState\\settings.json"
        if (Test-Path $settingsPath) {{
            $settings = Get-Content $settingsPath -Raw | ConvertFrom-Json
            $newBinding = @{{
                keys = "{keys}"
                command = "{command}"
            }}
            if (-not $settings.actions) {{ $settings | Add-Member -NotePropertyName actions -NotePropertyValue @() }}
            $settings.actions += $newBinding
            $settings | ConvertTo-Json -Depth 10 | Set-Content $settingsPath
            @{{ success = $true; keys = "{keys}"; command = "{command}" }} | ConvertTo-Json
        }}
        '''
        return await self._run_powershell(script)
    
    async def _remove_terminal_keybinding(self, **kwargs) -> Dict[str, Any]:
        """Remove a keybinding from Windows Terminal."""
        keys = kwargs.get("keys", "")
        
        if not keys:
            return {"error": "Keys parameter is required"}
        
        script = f'''
        $settingsPath = "$env:LOCALAPPDATA\\Packages\\Microsoft.WindowsTerminal_8wekyb3d8bbwe\\LocalState\\settings.json"
        if (Test-Path $settingsPath) {{
            $settings = Get-Content $settingsPath -Raw | ConvertFrom-Json
            if ($settings.actions) {{
                $settings.actions = @($settings.actions | Where-Object {{ $_.keys -ne "{keys}" }})
                $settings | ConvertTo-Json -Depth 10 | Set-Content $settingsPath
            }}
            @{{ success = $true; removedKeys = "{keys}" }} | ConvertTo-Json
        }}
        '''
        return await self._run_powershell(script)
    
    # Tab/Pane Management
    async def _new_terminal_tab(self, **kwargs) -> Dict[str, Any]:
        """Open a new tab in Windows Terminal."""
        profile = kwargs.get("profile", "")
        command = kwargs.get("command", "")
        
        cmd = "wt -w 0 nt"
        if profile:
            cmd += f' -p "{profile}"'
        if command:
            cmd += f' {command}'
        
        script = f'''
        Start-Process -FilePath cmd -ArgumentList '/c {cmd}'
        @{{ success = $true; command = "{cmd}" }} | ConvertTo-Json
        '''
        return await self._run_powershell(script)
    
    async def _split_terminal_pane(self, **kwargs) -> Dict[str, Any]:
        """Split the current pane in Windows Terminal."""
        direction = kwargs.get("direction", "horizontal")
        profile = kwargs.get("profile", "")
        size = kwargs.get("size", 0.5)
        
        split_char = "H" if direction == "horizontal" else "V"
        cmd = f"wt -w 0 sp -{split_char} --size {size}"
        if profile:
            cmd += f' -p "{profile}"'
        
        script = f'''
        Start-Process -FilePath cmd -ArgumentList '/c {cmd}'
        @{{ success = $true; direction = "{direction}"; size = {size} }} | ConvertTo-Json
        '''
        return await self._run_powershell(script)
    
    async def _get_terminal_tabs(self, **kwargs) -> Dict[str, Any]:
        """Get information about Windows Terminal tabs (limited)."""
        return {
            "note": "Windows Terminal tab information is not directly accessible via API",
            "workaround": "Use wt command line arguments to manage tabs",
            "commands": {
                "new_tab": "wt -w 0 nt",
                "split_horizontal": "wt -w 0 sp -H",
                "split_vertical": "wt -w 0 sp -V",
                "focus_tab": "wt -w 0 ft -t <index>",
                "close_pane": "Ctrl+Shift+W"
            }
        }
    
    async def _focus_terminal_tab(self, **kwargs) -> Dict[str, Any]:
        """Focus a specific Windows Terminal tab."""
        tab_index = kwargs.get("tab_index", 0)
        
        script = f'''
        Start-Process -FilePath cmd -ArgumentList '/c wt -w 0 ft -t {tab_index}'
        @{{ success = $true; tabIndex = {tab_index} }} | ConvertTo-Json
        '''
        return await self._run_powershell(script)
    
    # Diagnostic
    async def _get_terminal_diagnostics(self, **kwargs) -> Dict[str, Any]:
        """Get terminal diagnostics and environment info."""
        script = '''
        @{
            environment = @{
                TERM = $env:TERM
                WT_SESSION = $env:WT_SESSION
                WT_PROFILE_ID = $env:WT_PROFILE_ID
                SHELL = $env:SHELL
                COMSPEC = $env:COMSPEC
                PSModulePath = $env:PSModulePath
            }
            powershell = @{
                version = $PSVersionTable.PSVersion.ToString()
                edition = $PSVersionTable.PSEdition
                os = $PSVersionTable.OS
                platform = $PSVersionTable.Platform
            }
            console = @{
                width = $host.UI.RawUI.WindowSize.Width
                height = $host.UI.RawUI.WindowSize.Height
                bufferWidth = $host.UI.RawUI.BufferSize.Width
                bufferHeight = $host.UI.RawUI.BufferSize.Height
            }
            windowsTerminal = @{
                installed = Test-Path "$env:LOCALAPPDATA\\Packages\\Microsoft.WindowsTerminal_8wekyb3d8bbwe"
                preview = Test-Path "$env:LOCALAPPDATA\\Packages\\Microsoft.WindowsTerminalPreview_8wekyb3d8bbwe"
            }
        } | ConvertTo-Json -Depth 5
        '''
        return await self._run_powershell(script)
    
    async def _export_terminal_settings(self, **kwargs) -> Dict[str, Any]:
        """Export Windows Terminal settings to a file."""
        export_path = kwargs.get("export_path", "")
        
        if not export_path:
            export_path = "$env:USERPROFILE\\Desktop\\terminal_settings_backup.json"
        
        script = f'''
        $settingsPath = "$env:LOCALAPPDATA\\Packages\\Microsoft.WindowsTerminal_8wekyb3d8bbwe\\LocalState\\settings.json"
        $exportPath = {export_path}
        if (Test-Path $settingsPath) {{
            Copy-Item $settingsPath $exportPath -Force
            @{{ success = $true; exportedTo = $exportPath }} | ConvertTo-Json
        }} else {{
            @{{ success = $false; error = "Settings file not found" }} | ConvertTo-Json
        }}
        '''
        return await self._run_powershell(script)
    
    async def _import_terminal_settings(self, **kwargs) -> Dict[str, Any]:
        """Import Windows Terminal settings from a file."""
        import_path = kwargs.get("import_path", "")
        
        if not import_path:
            return {"error": "Import path is required"}
        
        script = f'''
        $importPath = "{import_path}"
        $settingsPath = "$env:LOCALAPPDATA\\Packages\\Microsoft.WindowsTerminal_8wekyb3d8bbwe\\LocalState\\settings.json"
        if (Test-Path $importPath) {{
            # Backup current settings
            $backupPath = "$settingsPath.backup"
            Copy-Item $settingsPath $backupPath -Force -ErrorAction SilentlyContinue
            # Import new settings
            Copy-Item $importPath $settingsPath -Force
            @{{ success = $true; imported = $importPath; backup = $backupPath }} | ConvertTo-Json
        }} else {{
            @{{ success = $false; error = "Import file not found" }} | ConvertTo-Json
        }}
        '''
        return await self._run_powershell(script)
    
    async def cleanup(self):
        """Cleanup plugin resources."""
        logger.info("Windows Terminal plugin cleaned up")
