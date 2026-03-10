"""
Windows Multi-Monitor Management Integration - PRODUCTION
Manage multiple displays: list monitors, get info, set resolution, DPI, arrange displays.
"""
import os
import asyncio
import json
from typing import Dict, Any, Optional, List
from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType
import logging

logger = logging.getLogger(__name__)


class WindowsMultiMonitorPlugin(IntegrationPlugin):
    def __init__(self):
        metadata = PluginMetadata(
            id="windows_multi_monitor",
            name="Windows Multi-Monitor Manager",
            description=(
                "Manage multiple display monitors: list displays, get/set resolution, "
                "adjust refresh rate, rearrange display layout, set primary display, and query DPI."
            ),
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["windows", "display", "monitor", "resolution", "multi-monitor", "screen"],
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
            "list_displays": self._list_displays,
            "get_display_info": self._get_display_info,
            "set_resolution": self._set_resolution,
            "set_refresh_rate": self._set_refresh_rate,
            "rearrange_displays": self._rearrange_displays,
            "set_primary_display": self._set_primary_display,
            "get_dpi": self._get_dpi,
            "set_dpi": self._set_dpi,
            "get_display_modes": self._get_display_modes,
            "mirror_display": self._mirror_display,
            "extend_display": self._extend_display,
            "disable_display": self._disable_display,
            "enable_display": self._enable_display,
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

    async def _list_displays(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List all connected display monitors."""
        cmd = r"""
$displays = @()
$monitors = Get-WmiObject -Class Win32_DesktopMonitor -ErrorAction SilentlyContinue
foreach ($m in $monitors) {
    $displays += @{
        'device_id' = $m.DeviceID
        'name' = $m.Caption
        'status' = $m.Status
        'screen_height' = $m.ScreenHeight
        'screen_width' = $m.ScreenWidth
        'monitor_type' = $m.MonitorType
        'pixels_per_x_logical_inch' = $m.PixelsPerXLogicalInch
        'pixels_per_y_logical_inch' = $m.PixelsPerYLogicalInch
    }
}
$controllers = Get-WmiObject Win32_VideoController -ErrorAction SilentlyContinue
$ctrl_info = @($controllers | ForEach-Object {
    @{
        'controller_name' = $_.Name
        'resolution' = "$($_.CurrentHorizontalResolution)x$($_.CurrentVerticalResolution)"
        'refresh_rate' = $_.CurrentRefreshRate
        'bits_per_pixel' = $_.CurrentBitsPerPixel
        'video_mode' = $_.VideoModeDescription
    }
})
@{
    'monitors' = $displays
    'controllers' = $ctrl_info
    'monitor_count' = $displays.Count
    'controller_count' = $ctrl_info.Count
} | ConvertTo-Json -Depth 3
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _get_display_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed information about a specific display."""
        display_id = int(params.get("display_id", 0))
        cmd = f"""
Add-Type -AssemblyName System.Windows.Forms -ErrorAction SilentlyContinue
$screens = [System.Windows.Forms.Screen]::AllScreens
$idx = {display_id}
if ($idx -ge $screens.Count) {{
    @{{'error' = 'Display index out of range'; 'total' = $screens.Count}} | ConvertTo-Json
}} else {{
    $s = $screens[$idx]
    @{{
        'index' = $idx
        'device_name' = $s.DeviceName
        'primary' = $s.Primary
        'bounds_x' = $s.Bounds.X
        'bounds_y' = $s.Bounds.Y
        'bounds_width' = $s.Bounds.Width
        'bounds_height' = $s.Bounds.Height
        'working_area' = "$($s.WorkingArea.Width)x$($s.WorkingArea.Height)"
        'bits_per_pixel' = $s.BitsPerPixel
        'total_displays' = $screens.Count
    }} | ConvertTo-Json
}}
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _set_resolution(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set display resolution using P/Invoke ChangeDisplaySettingsEx."""
        width = params.get("width")
        height = params.get("height")
        display_name = params.get("display_name", r"\\.\DISPLAY1")
        if not width or not height:
            return {"success": False, "error": "Parameters 'width' and 'height' are required"}
        safe_display = str(display_name).replace("'", "")
        cmd = f"""
$code = @'
using System; using System.Runtime.InteropServices;
public class DisplayChanger {{
    [DllImport("user32.dll")] public static extern int ChangeDisplaySettingsEx(string d, ref DEVMODE m, IntPtr h, int f, IntPtr p);
    [DllImport("user32.dll")] public static extern bool EnumDisplaySettings(string d, int n, ref DEVMODE m);
    [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
    public struct DEVMODE {{
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst=32)] public string dmDeviceName;
        public short dmSpecVersion, dmDriverVersion, dmSize, dmDriverExtra;
        public int dmFields, dmPositionX, dmPositionY, dmDisplayOrientation, dmDisplayFixedOutput;
        public short dmColor, dmDuplex, dmYResolution, dmTTOption, dmCollate;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst=32)] public string dmFormName;
        public short dmLogPixels; public int dmBitsPerPel, dmPelsWidth, dmPelsHeight;
        public int dmDisplayFlags, dmDisplayFrequency, dmICMMethod, dmICMIntent, dmMediaType, dmDitherType, dmReserved1, dmReserved2, dmPanningWidth, dmPanningHeight;
    }}
}}
'@
Add-Type -TypeDefinition $code -ErrorAction SilentlyContinue
$dm = New-Object DisplayChanger+DEVMODE
$dm.dmSize = [System.Runtime.InteropServices.Marshal]::SizeOf($dm)
[DisplayChanger]::EnumDisplaySettings('{safe_display}', -1, [ref]$dm) | Out-Null
$dm.dmPelsWidth = {int(width)}
$dm.dmPelsHeight = {int(height)}
$dm.dmFields = 0x180000
$r = [DisplayChanger]::ChangeDisplaySettingsEx('{safe_display}', [ref]$dm, [IntPtr]::Zero, 0, [IntPtr]::Zero)
@{{'success'=($r -ge 0);'result_code'=$r;'width'={int(width)};'height'={int(height)}}} | ConvertTo-Json
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _set_refresh_rate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set display refresh rate."""
        refresh_rate = params.get("refresh_rate")
        display_name = params.get("display_name", r"\\.\DISPLAY1")
        if not refresh_rate:
            return {"success": False, "error": "Parameter 'refresh_rate' is required"}
        safe_display = str(display_name).replace("'", "")
        cmd = f"""
$code = @'
using System; using System.Runtime.InteropServices;
public class RateChanger {{
    [DllImport("user32.dll")] public static extern int ChangeDisplaySettingsEx(string d, ref DEVMODE m, IntPtr h, int f, IntPtr p);
    [DllImport("user32.dll")] public static extern bool EnumDisplaySettings(string d, int n, ref DEVMODE m);
    [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
    public struct DEVMODE {{
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst=32)] public string dmDeviceName;
        public short dmSpecVersion, dmDriverVersion, dmSize, dmDriverExtra;
        public int dmFields, dmPositionX, dmPositionY, dmDisplayOrientation, dmDisplayFixedOutput;
        public short dmColor, dmDuplex, dmYResolution, dmTTOption, dmCollate;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst=32)] public string dmFormName;
        public short dmLogPixels; public int dmBitsPerPel, dmPelsWidth, dmPelsHeight;
        public int dmDisplayFlags, dmDisplayFrequency, dmICMMethod, dmICMIntent, dmMediaType, dmDitherType, dmReserved1, dmReserved2, dmPanningWidth, dmPanningHeight;
    }}
}}
'@
Add-Type -TypeDefinition $code -ErrorAction SilentlyContinue
$dm = New-Object RateChanger+DEVMODE
$dm.dmSize = [System.Runtime.InteropServices.Marshal]::SizeOf($dm)
[RateChanger]::EnumDisplaySettings('{safe_display}', -1, [ref]$dm) | Out-Null
$dm.dmDisplayFrequency = {int(refresh_rate)}
$dm.dmFields = 0x400000
$r = [RateChanger]::ChangeDisplaySettingsEx('{safe_display}', [ref]$dm, [IntPtr]::Zero, 0, [IntPtr]::Zero)
@{{'success'=($r -ge 0);'result_code'=$r;'refresh_rate'={int(refresh_rate)}}} | ConvertTo-Json
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _rearrange_displays(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Rearrange display positions - advises using DisplaySwitch or Settings."""
        return {
            "success": False,
            "error": "Display rearrangement requires CDS P/Invoke with position fields.",
            "tip": "Use 'extend_display', 'mirror_display', or Windows Settings > Display > Rearrange displays.",
        }

    async def _set_primary_display(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Inform user how to set primary display."""
        display_name = params.get("display_name", "")
        return {
            "success": False,
            "error": "Setting primary display programmatically requires ChangeDisplaySettingsEx with CDS_SET_PRIMARY.",
            "tip": f"Go to Windows Settings > System > Display, select the display ('{display_name}'), then check 'Make this my main display'.",
        }

    async def _get_dpi(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get DPI/scaling information."""
        cmd = r"""
Add-Type -AssemblyName System.Windows.Forms -ErrorAction SilentlyContinue
$dpiInfo = @()
try {
    $form = New-Object System.Windows.Forms.Form
    $form.Visible = $false
    $g = $form.CreateGraphics()
    $dpiInfo += @{ 'display' = 'primary'; 'dpi_x' = $g.DpiX; 'dpi_y' = $g.DpiY
                   'scale_percent' = [math]::Round(($g.DpiX / 96) * 100) }
    $g.Dispose(); $form.Dispose()
} catch {
    $dpiInfo += @{ 'error' = $_.Exception.Message }
}
$regDpi = (Get-ItemProperty 'HKCU:\Control Panel\Desktop\WindowMetrics' -Name 'AppliedDPI' -ErrorAction SilentlyContinue).AppliedDPI
@{ 'dpi_info' = $dpiInfo; 'registry_dpi' = $regDpi } | ConvertTo-Json -Depth 2
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _set_dpi(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set DPI scaling level."""
        dpi = int(params.get("dpi", 96))
        valid_dpis = [96, 120, 144, 168, 192, 216, 240]
        if dpi not in valid_dpis:
            return {"success": False, "error": f"DPI must be one of: {valid_dpis}"}
        scale = round((dpi / 96) * 100)
        cmd = f"""
Set-ItemProperty 'HKCU:\\Control Panel\\Desktop' -Name 'LogPixels' -Value {dpi} -Type DWord -Force
Set-ItemProperty 'HKCU:\\Control Panel\\Desktop' -Name 'Win8DpiScaling' -Value 1 -Type DWord -Force
Write-Output 'DPI set to {dpi} ({scale}%). Log off and back on for changes to take effect.'
"""
        result = await self._run_ps(cmd)
        result["dpi"] = dpi
        result["scale_percent"] = scale
        return result

    async def _get_display_modes(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get all supported display modes for a monitor."""
        display_name = params.get("display_name", r"\\.\DISPLAY1")
        safe_display = str(display_name).replace("'", "")
        cmd = f"""
$code = @'
using System; using System.Runtime.InteropServices;
public class ModeEnumerator {{
    [DllImport("user32.dll")] public static extern bool EnumDisplaySettings(string d, int n, ref DEVMODE m);
    [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
    public struct DEVMODE {{
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst=32)] public string dmDeviceName;
        public short dmSpecVersion, dmDriverVersion, dmSize, dmDriverExtra;
        public int dmFields, dmPositionX, dmPositionY, dmDisplayOrientation, dmDisplayFixedOutput;
        public short dmColor, dmDuplex, dmYResolution, dmTTOption, dmCollate;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst=32)] public string dmFormName;
        public short dmLogPixels; public int dmBitsPerPel, dmPelsWidth, dmPelsHeight;
        public int dmDisplayFlags, dmDisplayFrequency, dmICMMethod, dmICMIntent, dmMediaType, dmDitherType, dmReserved1, dmReserved2, dmPanningWidth, dmPanningHeight;
    }}
}}
'@
Add-Type -TypeDefinition $code -ErrorAction SilentlyContinue
$modes = @()
$i = 0
$dm = New-Object ModeEnumerator+DEVMODE
$dm.dmSize = [System.Runtime.InteropServices.Marshal]::SizeOf($dm)
while ([ModeEnumerator]::EnumDisplaySettings('{safe_display}', $i, [ref]$dm)) {{
    $modes += "$($dm.dmPelsWidth)x$($dm.dmPelsHeight)@$($dm.dmDisplayFrequency)Hz ($($dm.dmBitsPerPel)bpp)"
    $i++
}}
@{{'modes' = ($modes | Sort-Object -Unique); 'count' = $modes.Count; 'display' = '{safe_display}'}} | ConvertTo-Json
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _mirror_display(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set display to mirror/clone mode."""
        cmd = "Start-Process DisplaySwitch.exe -ArgumentList '/clone' -NoNewWindow; Write-Output 'Switched to clone mode'"
        return await self._run_ps(cmd)

    async def _extend_display(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set display to extended/span mode."""
        cmd = "Start-Process DisplaySwitch.exe -ArgumentList '/extend' -NoNewWindow; Write-Output 'Switched to extend mode'"
        return await self._run_ps(cmd)

    async def _disable_display(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Switch to internal display only (disable external)."""
        cmd = "Start-Process DisplaySwitch.exe -ArgumentList '/internal' -NoNewWindow; Write-Output 'Switched to internal only'"
        return await self._run_ps(cmd)

    async def _enable_display(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Switch to external display only."""
        cmd = "Start-Process DisplaySwitch.exe -ArgumentList '/external' -NoNewWindow; Write-Output 'Switched to external only'"
        return await self._run_ps(cmd)

    async def shutdown(self):
        self._initialized = False

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "actions": {
                "list_displays": {"description": "List all connected displays"},
                "get_display_info": {"description": "Get display details", "params": {"display_id": "int"}},
                "set_resolution": {"description": "Set display resolution", "params": {"width": "int", "height": "int", "display_name": "str"}},
                "set_refresh_rate": {"description": "Set refresh rate", "params": {"refresh_rate": "int", "display_name": "str"}},
                "rearrange_displays": {"description": "Rearrange display layout"},
                "set_primary_display": {"description": "Set primary display", "params": {"display_name": "str"}},
                "get_dpi": {"description": "Get DPI/scaling info"},
                "set_dpi": {"description": "Set DPI scaling", "params": {"dpi": "int (96,120,144,168,192)"}},
                "get_display_modes": {"description": "List available display modes", "params": {"display_name": "str"}},
                "mirror_display": {"description": "Set clone/mirror mode"},
                "extend_display": {"description": "Set extended display mode"},
                "disable_display": {"description": "Switch to internal display only"},
                "enable_display": {"description": "Switch to external display only"},
            },
        }


plugin = WindowsMultiMonitorPlugin()
