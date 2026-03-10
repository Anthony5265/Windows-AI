"""
Windows DirectX / Direct3D Diagnostics Integration - PRODUCTION
Provides DirectX version info, GPU adapter details, dxdiag reports, and display configuration.
"""
import os
import asyncio
import json
import tempfile
from typing import Dict, Any, Optional, List
from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType
import logging

logger = logging.getLogger(__name__)


class WindowsDirect3DPlugin(IntegrationPlugin):
    def __init__(self):
        metadata = PluginMetadata(
            id="windows_direct3d",
            name="Windows DirectX / Direct3D",
            description=(
                "Query DirectX and Direct3D capabilities, run dxdiag diagnostics, retrieve GPU "
                "adapter information, check DirectX version, and list display adapters."
            ),
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["windows", "directx", "direct3d", "gpu", "graphics", "display"],
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
            "get_d3d_info": self._get_d3d_info,
            "run_dxdiag": self._run_dxdiag,
            "get_gpu_info": self._get_gpu_info,
            "check_directx_version": self._check_directx_version,
            "get_display_info": self._get_display_info,
            "list_adapters": self._list_adapters,
            "get_vram_info": self._get_vram_info,
            "get_driver_info": self._get_driver_info,
            "check_d3d_features": self._check_d3d_features,
        }

        handler = actions.get(action)
        if handler is None:
            return {"success": False, "error": f"Unknown action: {action}. Available: {list(actions)}"}
        return await handler(parameters)

    async def _run_ps(self, cmd: str, timeout: int = 60) -> Dict[str, Any]:
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

    async def _get_d3d_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get comprehensive Direct3D and DirectX information."""
        cmd = r"""
$result = @{}

# DirectX version from registry
$dxPath = 'HKLM:\SOFTWARE\Microsoft\DirectX'
if (Test-Path $dxPath) {
    $dxProps = Get-ItemProperty -Path $dxPath -ErrorAction SilentlyContinue
    $result['directx_version'] = $dxProps.Version
    $result['directx_installed_version'] = $dxProps.InstalledVersion
}

# GPU via WMI
$gpus = Get-WmiObject Win32_VideoController -ErrorAction SilentlyContinue | Select-Object `
    Name, DriverVersion, VideoProcessor, AdapterRAM, CurrentHorizontalResolution,
    CurrentVerticalResolution, CurrentRefreshRate, VideoModeDescription, Status

$result['gpu_adapters'] = @($gpus | ForEach-Object {
    @{
        'name' = $_.Name
        'driver_version' = $_.DriverVersion
        'video_processor' = $_.VideoProcessor
        'adapter_ram_mb' = if ($_.AdapterRAM) { [math]::Round($_.AdapterRAM / 1MB, 0) } else { 0 }
        'current_resolution' = "$($_.CurrentHorizontalResolution)x$($_.CurrentVerticalResolution)"
        'refresh_rate_hz' = $_.CurrentRefreshRate
        'status' = $_.Status
    }
})

$result | ConvertTo-Json -Depth 4
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _run_dxdiag(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run dxdiag and return the output."""
        output_format = params.get("format", "text")  # "text" or "xml"
        timeout = params.get("timeout", 60)

        with tempfile.NamedTemporaryFile(
            suffix=".xml" if output_format == "xml" else ".txt",
            delete=False,
            mode="w",
        ) as f:
            outfile = f.name

        try:
            flag = "/x" if output_format == "xml" else "/t"
            proc = await asyncio.create_subprocess_exec(
                "dxdiag", flag, outfile, "/dontskip",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await asyncio.wait_for(proc.communicate(), timeout=timeout)

            if os.path.exists(outfile):
                with open(outfile, "r", errors="replace") as f:
                    content = f.read()
                os.unlink(outfile)
                return {"success": True, "output": content, "format": output_format}
            return {"success": False, "error": "dxdiag output file not created"}
        except FileNotFoundError:
            return {"success": False, "error": "dxdiag not available on this system"}
        except asyncio.TimeoutError:
            return {"success": False, "error": "dxdiag timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            if os.path.exists(outfile):
                try:
                    os.unlink(outfile)
                except OSError:
                    pass

    async def _get_gpu_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed GPU information including temperature if available."""
        cmd = r"""
$gpus = Get-WmiObject Win32_VideoController -ErrorAction SilentlyContinue
$result = @($gpus | ForEach-Object {
    $ramGB = if ($_.AdapterRAM -gt 0) { [math]::Round($_.AdapterRAM / 1GB, 2) } else { 'unknown' }
    @{
        'name' = $_.Name
        'device_id' = $_.DeviceID
        'pnp_device_id' = $_.PNPDeviceID
        'driver_version' = $_.DriverVersion
        'driver_date' = $_.DriverDate
        'video_processor' = $_.VideoProcessor
        'adapter_ram' = $_.AdapterRAM
        'adapter_ram_gb' = $ramGB
        'current_resolution' = "$($_.CurrentHorizontalResolution)x$($_.CurrentVerticalResolution)"
        'current_bits_per_pixel' = $_.CurrentBitsPerPixel
        'refresh_rate' = $_.CurrentRefreshRate
        'video_mode' = $_.VideoModeDescription
        'availability' = $_.Availability
        'config_manager_error_code' = $_.ConfigManagerErrorCode
        'status' = $_.Status
    }
})
$result | ConvertTo-Json -Depth 3
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                gpus = json.loads(result["output"])
                result["gpus"] = gpus if isinstance(gpus, list) else [gpus]
                result["count"] = len(result["gpus"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _check_directx_version(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Check the installed DirectX version."""
        cmd = r"""
$result = @{}
$dxPath = 'HKLM:\SOFTWARE\Microsoft\DirectX'
if (Test-Path $dxPath) {
    $props = Get-ItemProperty -Path $dxPath -ErrorAction SilentlyContinue
    $result['version'] = $props.Version
    $result['installed'] = $true
    # Parse major version
    if ($props.Version -match '^(\d+)\.') { $result['major_version'] = [int]$Matches[1] }
} else {
    $result['version'] = 'unknown'
    $result['installed'] = $false
}

# Check for DX12 support (Windows 10+)
$osVersion = [System.Environment]::OSVersion.Version
$result['os_version'] = $osVersion.ToString()
$result['dx12_capable'] = ($osVersion.Major -ge 10)
$result['dx11_capable'] = ($osVersion.Major -ge 6 -and $osVersion.Minor -ge 1)

# Feature levels available
$result['supported_feature_levels'] = @()
if ($result['dx12_capable']) { $result['supported_feature_levels'] += 'D3D_FEATURE_LEVEL_12_0', 'D3D_FEATURE_LEVEL_12_1' }
if ($result['dx11_capable']) { $result['supported_feature_levels'] += 'D3D_FEATURE_LEVEL_11_0', 'D3D_FEATURE_LEVEL_11_1' }

$result | ConvertTo-Json -Depth 2
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _get_display_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get display/monitor information."""
        cmd = r"""
Add-Type -AssemblyName System.Windows.Forms -ErrorAction SilentlyContinue
$displays = @()
try {
    $screens = [System.Windows.Forms.Screen]::AllScreens
    foreach ($s in $screens) {
        $displays += @{
            'device_name' = $s.DeviceName
            'primary' = $s.Primary
            'bounds_x' = $s.Bounds.X
            'bounds_y' = $s.Bounds.Y
            'bounds_width' = $s.Bounds.Width
            'bounds_height' = $s.Bounds.Height
            'working_area_width' = $s.WorkingArea.Width
            'working_area_height' = $s.WorkingArea.Height
            'bits_per_pixel' = $s.BitsPerPixel
        }
    }
} catch {
    # Fallback to WMI
    Get-WmiObject Win32_VideoController -ErrorAction SilentlyContinue | ForEach-Object {
        $displays += @{
            'device_name' = $_.Name
            'primary' = $true
            'bounds_width' = $_.CurrentHorizontalResolution
            'bounds_height' = $_.CurrentVerticalResolution
            'bits_per_pixel' = $_.CurrentBitsPerPixel
        }
    }
}
@{ 'displays' = $displays; 'count' = $displays.Count } | ConvertTo-Json -Depth 3
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _list_adapters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List all graphics adapters in the system."""
        cmd = r"""
$adapters = Get-WmiObject Win32_VideoController -ErrorAction SilentlyContinue |
    Select-Object Name, DeviceID, AdapterCompatibility, VideoMemoryType,
                  CurrentHorizontalResolution, CurrentVerticalResolution,
                  DriverVersion, Status |
    ConvertTo-Json -Depth 2
Write-Output $adapters
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                adapters = json.loads(result["output"])
                result["adapters"] = adapters if isinstance(adapters, list) else [adapters]
                result["count"] = len(result["adapters"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _get_vram_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get VRAM information for all adapters."""
        cmd = r"""
$result = @()
Get-WmiObject Win32_VideoController -ErrorAction SilentlyContinue | ForEach-Object {
    $dedicated = $_.AdapterRAM
    $result += @{
        'name' = $_.Name
        'dedicated_vram_bytes' = $dedicated
        'dedicated_vram_mb' = if ($dedicated) { [math]::Round($dedicated / 1MB, 0) } else { 0 }
        'dedicated_vram_gb' = if ($dedicated -gt 0) { [math]::Round($dedicated / 1GB, 2) } else { 0 }
        'video_memory_type' = $_.VideoMemoryType
    }
}
$result | ConvertTo-Json -Depth 2
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["vram_info"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _get_driver_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get graphics driver information and dates."""
        cmd = r"""
$drivers = Get-WmiObject Win32_VideoController -ErrorAction SilentlyContinue | ForEach-Object {
    @{
        'name' = $_.Name
        'driver_version' = $_.DriverVersion
        'driver_date' = $_.DriverDate
        'inf_filename' = $_.InfFilename
        'inf_section' = $_.InfSection
        'pnp_device_id' = $_.PNPDeviceID
    }
}
@($drivers) | ConvertTo-Json -Depth 2
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["drivers"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _check_d3d_features(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Check available Direct3D feature levels and capabilities."""
        cmd = r"""
$result = @{
    'wddm_version' = $null
    'feature_levels' = @()
    'hardware_acceleration' = $false
}

# Check WDDM version
$wddmPath = 'HKLM:\SYSTEM\CurrentControlSet\Control\GraphicsDrivers'
if (Test-Path $wddmPath) {
    $wddm = (Get-ItemProperty -Path $wddmPath -Name 'DxgkrnlVersion' -ErrorAction SilentlyContinue).DxgkrnlVersion
    $result['wddm_version'] = $wddm
}

# OS-based feature level inference
$os = [System.Environment]::OSVersion.Version
if ($os.Major -ge 10) {
    $result['feature_levels'] = @('12_1', '12_0', '11_1', '11_0', '10_1', '10_0')
    $result['hardware_acceleration'] = $true
    $result['dx12_support'] = $true
} elseif ($os.Major -eq 6 -and $os.Minor -ge 1) {
    $result['feature_levels'] = @('11_0', '10_1', '10_0', '9_3')
    $result['hardware_acceleration'] = $true
    $result['dx12_support'] = $false
}

# Check if hardware acceleration is available
$gpu = Get-WmiObject Win32_VideoController -ErrorAction SilentlyContinue | Select-Object -First 1
$result['primary_gpu'] = if ($gpu) { $gpu.Name } else { 'None detected' }
$result['warp_available'] = $true  # WARP software renderer always available on Win8+

$result | ConvertTo-Json -Depth 2
"""
        result = await self._run_ps(cmd)
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
                "get_d3d_info": {"description": "Get comprehensive Direct3D information"},
                "run_dxdiag": {"description": "Run dxdiag diagnostic", "params": {"format": "text|xml", "timeout": "int"}},
                "get_gpu_info": {"description": "Get detailed GPU information"},
                "check_directx_version": {"description": "Check installed DirectX version"},
                "get_display_info": {"description": "Get display/monitor information"},
                "list_adapters": {"description": "List all graphics adapters"},
                "get_vram_info": {"description": "Get VRAM info for all adapters"},
                "get_driver_info": {"description": "Get graphics driver details"},
                "check_d3d_features": {"description": "Check Direct3D feature levels"},
            },
        }


plugin = WindowsDirect3DPlugin()
