"""
Bluetooth Plugin for Windows AI
Comprehensive Bluetooth device management and configuration
"""

from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType
from typing import Dict, Any, Optional
import asyncio
import subprocess
import json
import logging

logger = logging.getLogger(__name__)


class BluetoothPlugin(IntegrationPlugin):
    """
    Windows Bluetooth Management Plugin
    
    Provides comprehensive Bluetooth device discovery, pairing,
    connection management, and configuration capabilities.
    """
    
    def __init__(self):
        metadata = PluginMetadata(
            id="windows-bluetooth",
            name="Windows Bluetooth Management",
            description="Comprehensive Bluetooth device management including discovery, pairing, connections, and audio device configuration",
            version="1.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["bluetooth", "devices", "wireless", "audio", "pairing", "windows"],
            requirements=[]
        )
        super().__init__(metadata)
        
        self._actions = {
            # Bluetooth Radio Management
            "get_bluetooth_status": self._get_bluetooth_status,
            "enable_bluetooth": self._enable_bluetooth,
            "disable_bluetooth": self._disable_bluetooth,
            "get_bluetooth_adapter": self._get_bluetooth_adapter,
            "get_adapter_properties": self._get_adapter_properties,
            
            # Device Discovery
            "discover_devices": self._discover_devices,
            "get_nearby_devices": self._get_nearby_devices,
            "start_discovery": self._start_discovery,
            "stop_discovery": self._stop_discovery,
            
            # Paired Devices Management
            "list_paired_devices": self._list_paired_devices,
            "get_device_info": self._get_device_info,
            "pair_device": self._pair_device,
            "unpair_device": self._unpair_device,
            "remove_device": self._remove_device,
            
            # Connection Management
            "connect_device": self._connect_device,
            "disconnect_device": self._disconnect_device,
            "get_connected_devices": self._get_connected_devices,
            "get_connection_status": self._get_connection_status,
            "reconnect_device": self._reconnect_device,
            
            # Audio Device Management
            "get_audio_devices": self._get_audio_devices,
            "set_default_audio_device": self._set_default_audio_device,
            "get_default_audio_device": self._get_default_audio_device,
            "get_audio_device_properties": self._get_audio_device_properties,
            
            # Device Services
            "get_device_services": self._get_device_services,
            "get_service_info": self._get_service_info,
            "list_supported_profiles": self._list_supported_profiles,
            
            # File Transfer
            "send_file": self._send_file,
            "receive_file_settings": self._receive_file_settings,
            "open_bluetooth_file_transfer": self._open_bluetooth_file_transfer,
            
            # Settings and Configuration
            "open_bluetooth_settings": self._open_bluetooth_settings,
            "set_device_name": self._set_device_name,
            "get_device_name": self._get_device_name,
            "set_discoverable": self._set_discoverable,
            "get_discoverable_status": self._get_discoverable_status,
            
            # Diagnostics
            "get_bluetooth_info": self._get_bluetooth_info,
            "troubleshoot_bluetooth": self._troubleshoot_bluetooth,
            "restart_bluetooth_service": self._restart_bluetooth_service,
            "get_bluetooth_logs": self._get_bluetooth_logs
        }
    
    async def initialize(self) -> bool:
        """Initialize the Bluetooth plugin"""
        self._initialized = True
        logger.info("Windows Bluetooth plugin initialized")
        return True
    

    async def connect(self, credentials: Dict[str, str]) -> bool:
        """Connect to the service"""
        return True

    async def disconnect(self) -> bool:
        """Disconnect from the service"""
        return True

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute a Bluetooth management action"""
        action = kwargs.get("action", "get_bluetooth_status")
        params = kwargs.get("params", {})
        
        if action not in self._actions:
            return {
                "success": False,
                "error": f"Unknown action: {action}",
                "available_actions": list(self._actions.keys())
            }
        
        try:
            result = await self._actions[action](params)
            return {"success": True, "result": result, "action": action}
        except Exception as e:
            logger.error(f"Bluetooth action '{action}' failed: {e}")
            return {"success": False, "error": str(e), "action": action}
    
    async def _run_powershell(self, script: str) -> Dict[str, Any]:
        """Execute PowerShell script and return results"""
        try:
            process = await asyncio.create_subprocess_exec(
                "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            return {
                "stdout": stdout.decode("utf-8", errors="replace").strip(),
                "stderr": stderr.decode("utf-8", errors="replace").strip(),
                "return_code": process.returncode
            }
        except Exception as e:
            return {"stdout": "", "stderr": str(e), "return_code": -1}
    
    # Bluetooth Radio Management
    async def _get_bluetooth_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get Bluetooth adapter status"""
        script = '''
        $adapter = Get-PnpDevice -Class Bluetooth -FriendlyName "*Radio*" -ErrorAction SilentlyContinue | Select-Object -First 1
        if (-not $adapter) {
            $adapter = Get-PnpDevice -Class Bluetooth -ErrorAction SilentlyContinue | Where-Object { $_.FriendlyName -match "Adapter|Radio|Controller" } | Select-Object -First 1
        }
        if ($adapter) {
            @{
                Status = $adapter.Status
                Enabled = $adapter.Status -eq 'OK'
                Name = $adapter.FriendlyName
                InstanceId = $adapter.InstanceId
                Present = $adapter.Present
            } | ConvertTo-Json
        } else {
            @{ Status = "Not Found"; Enabled = $false; Name = "No Bluetooth adapter detected" } | ConvertTo-Json
        }
        '''
        result = await self._run_powershell(script)
        if result["return_code"] == 0 and result["stdout"]:
            return json.loads(result["stdout"])
        return {"enabled": False, "error": result["stderr"] or "Could not determine status"}
    
    async def _enable_bluetooth(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Enable Bluetooth adapter"""
        script = '''
        $adapter = Get-PnpDevice -Class Bluetooth -ErrorAction SilentlyContinue | Where-Object { $_.FriendlyName -match "Radio|Adapter|Controller" } | Select-Object -First 1
        if ($adapter) {
            Enable-PnpDevice -InstanceId $adapter.InstanceId -Confirm:$false
            Start-Sleep -Seconds 2
            $adapter = Get-PnpDevice -InstanceId $adapter.InstanceId
            @{ Success = $true; Status = $adapter.Status; Message = "Bluetooth enabled" } | ConvertTo-Json
        } else {
            @{ Success = $false; Message = "No Bluetooth adapter found" } | ConvertTo-Json
        }
        '''
        result = await self._run_powershell(script)
        if result["return_code"] == 0 and result["stdout"]:
            return json.loads(result["stdout"])
        return {"success": False, "error": result["stderr"]}
    
    async def _disable_bluetooth(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Disable Bluetooth adapter"""
        script = '''
        $adapter = Get-PnpDevice -Class Bluetooth -ErrorAction SilentlyContinue | Where-Object { $_.FriendlyName -match "Radio|Adapter|Controller" } | Select-Object -First 1
        if ($adapter) {
            Disable-PnpDevice -InstanceId $adapter.InstanceId -Confirm:$false
            Start-Sleep -Seconds 2
            $adapter = Get-PnpDevice -InstanceId $adapter.InstanceId
            @{ Success = $true; Status = $adapter.Status; Message = "Bluetooth disabled" } | ConvertTo-Json
        } else {
            @{ Success = $false; Message = "No Bluetooth adapter found" } | ConvertTo-Json
        }
        '''
        result = await self._run_powershell(script)
        if result["return_code"] == 0 and result["stdout"]:
            return json.loads(result["stdout"])
        return {"success": False, "error": result["stderr"]}
    
    async def _get_bluetooth_adapter(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get Bluetooth adapter information"""
        script = '''
        $adapters = Get-PnpDevice -Class Bluetooth -ErrorAction SilentlyContinue | Where-Object { $_.FriendlyName -match "Radio|Adapter|Controller|Realtek|Intel|Broadcom|Qualcomm" }
        $result = @()
        foreach ($adapter in $adapters) {
            $props = Get-PnpDeviceProperty -InstanceId $adapter.InstanceId -ErrorAction SilentlyContinue
            $result += @{
                Name = $adapter.FriendlyName
                Status = $adapter.Status
                InstanceId = $adapter.InstanceId
                Manufacturer = $adapter.Manufacturer
                Present = $adapter.Present
            }
        }
        $result | ConvertTo-Json -Depth 3
        '''
        result = await self._run_powershell(script)
        if result["return_code"] == 0 and result["stdout"]:
            return json.loads(result["stdout"])
        return {"adapters": [], "error": result["stderr"]}
    
    async def _get_adapter_properties(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed Bluetooth adapter properties"""
        script = '''
        $adapter = Get-PnpDevice -Class Bluetooth -ErrorAction SilentlyContinue | Where-Object { $_.FriendlyName -match "Radio|Adapter|Controller" } | Select-Object -First 1
        if ($adapter) {
            $props = Get-PnpDeviceProperty -InstanceId $adapter.InstanceId -ErrorAction SilentlyContinue
            $details = @{
                Name = $adapter.FriendlyName
                Status = $adapter.Status
                Class = $adapter.Class
                InstanceId = $adapter.InstanceId
                Manufacturer = $adapter.Manufacturer
                DriverVersion = ($props | Where-Object KeyName -eq "DEVPKEY_Device_DriverVersion").Data
                HardwareIds = ($props | Where-Object KeyName -eq "DEVPKEY_Device_HardwareIds").Data
            }
            $details | ConvertTo-Json -Depth 3
        } else {
            @{ Error = "No Bluetooth adapter found" } | ConvertTo-Json
        }
        '''
        result = await self._run_powershell(script)
        if result["return_code"] == 0 and result["stdout"]:
            return json.loads(result["stdout"])
        return {"error": result["stderr"]}
    
    # Device Discovery
    async def _discover_devices(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Discover nearby Bluetooth devices"""
        timeout = params.get("timeout", 10)
        script = f'''
        Add-Type -AssemblyName System.Runtime.WindowsRuntime
        $asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {{ $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' }})[0]
        Function Await($WinRtTask, $ResultType) {{
            $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
            $netTask = $asTask.Invoke($null, @($WinRtTask))
            $netTask.Wait(-1) | Out-Null
            $netTask.Result
        }}
        
        try {{
            [Windows.Devices.Enumeration.DeviceInformation,Windows.Devices.Enumeration,ContentType=WindowsRuntime] | Out-Null
            $selector = [Windows.Devices.Bluetooth.BluetoothDevice]::GetDeviceSelector()
            $devices = Await ([Windows.Devices.Enumeration.DeviceInformation]::FindAllAsync($selector)) ([Windows.Devices.Enumeration.DeviceInformationCollection])
            $result = @()
            foreach ($device in $devices) {{
                $result += @{{
                    Id = $device.Id
                    Name = $device.Name
                    IsPaired = $device.Pairing.IsPaired
                    CanPair = $device.Pairing.CanPair
                    IsEnabled = $device.IsEnabled
                }}
            }}
            $result | ConvertTo-Json -Depth 3
        }} catch {{
            @{{ Error = $_.Exception.Message }} | ConvertTo-Json
        }}
        '''
        result = await self._run_powershell(script)
        if result["return_code"] == 0 and result["stdout"]:
            return json.loads(result["stdout"])
        return {"devices": [], "note": "Discovery requires Windows Bluetooth APIs"}
    
    async def _get_nearby_devices(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get list of nearby Bluetooth devices using PnP"""
        script = '''
        $devices = Get-PnpDevice -Class Bluetooth -ErrorAction SilentlyContinue | Where-Object { $_.FriendlyName -notmatch "Radio|Adapter|Controller|Enumerator" }
        $result = @()
        foreach ($device in $devices) {
            $result += @{
                Name = $device.FriendlyName
                Status = $device.Status
                InstanceId = $device.InstanceId
                Present = $device.Present
                Class = $device.Class
            }
        }
        @{ Devices = $result; Count = $result.Count } | ConvertTo-Json -Depth 3
        '''
        result = await self._run_powershell(script)
        if result["return_code"] == 0 and result["stdout"]:
            return json.loads(result["stdout"])
        return {"devices": [], "count": 0}
    
    async def _start_discovery(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Start Bluetooth device discovery mode"""
        script = '''
        Start-Process "ms-settings:bluetooth" -WindowStyle Normal
        @{ Success = $true; Message = "Bluetooth settings opened for device discovery" } | ConvertTo-Json
        '''
        result = await self._run_powershell(script)
        return {"success": True, "message": "Discovery initiated via Bluetooth settings"}
    
    async def _stop_discovery(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Stop Bluetooth device discovery"""
        return {"success": True, "message": "Discovery can be stopped via Bluetooth settings"}
    
    # Paired Devices Management
    async def _list_paired_devices(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List all paired Bluetooth devices"""
        script = '''
        $devices = Get-PnpDevice -Class Bluetooth -ErrorAction SilentlyContinue | Where-Object { 
            $_.Status -eq 'OK' -and $_.FriendlyName -notmatch "Radio|Adapter|Controller|Enumerator|Microsoft|Generic"
        }
        $result = @()
        foreach ($device in $devices) {
            $result += @{
                Name = $device.FriendlyName
                Status = $device.Status
                InstanceId = $device.InstanceId
                Manufacturer = $device.Manufacturer
                Connected = $device.Present
            }
        }
        @{ PairedDevices = $result; Count = $result.Count } | ConvertTo-Json -Depth 3
        '''
        result = await self._run_powershell(script)
        if result["return_code"] == 0 and result["stdout"]:
            return json.loads(result["stdout"])
        return {"paired_devices": [], "count": 0}
    
    async def _get_device_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed information about a specific Bluetooth device"""
        device_name = params.get("device_name", "")
        instance_id = params.get("instance_id", "")
        
        if instance_id:
            query = f'-InstanceId "{instance_id}"'
        elif device_name:
            query = f'-FriendlyName "*{device_name}*"'
        else:
            return {"error": "Provide device_name or instance_id"}
        
        script = f'''
        $device = Get-PnpDevice -Class Bluetooth {query} -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($device) {{
            $props = Get-PnpDeviceProperty -InstanceId $device.InstanceId -ErrorAction SilentlyContinue
            @{{
                Name = $device.FriendlyName
                Status = $device.Status
                InstanceId = $device.InstanceId
                Manufacturer = $device.Manufacturer
                Class = $device.Class
                Present = $device.Present
                HardwareId = ($props | Where-Object KeyName -eq "DEVPKEY_Device_HardwareIds").Data
                Driver = ($props | Where-Object KeyName -eq "DEVPKEY_Device_DriverVersion").Data
            }} | ConvertTo-Json -Depth 3
        }} else {{
            @{{ Error = "Device not found" }} | ConvertTo-Json
        }}
        '''
        result = await self._run_powershell(script)
        if result["return_code"] == 0 and result["stdout"]:
            return json.loads(result["stdout"])
        return {"error": result["stderr"]}
    
    async def _pair_device(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Initiate pairing with a Bluetooth device"""
        device_id = params.get("device_id", "")
        script = '''
        Start-Process "ms-settings:bluetooth" -WindowStyle Normal
        @{ Success = $true; Message = "Bluetooth settings opened. Select device to pair." } | ConvertTo-Json
        '''
        result = await self._run_powershell(script)
        return {"success": True, "message": "Bluetooth settings opened for pairing. Select the device to pair."}
    
    async def _unpair_device(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Unpair/remove a Bluetooth device"""
        device_name = params.get("device_name", "")
        instance_id = params.get("instance_id", "")
        
        if not device_name and not instance_id:
            return {"error": "Provide device_name or instance_id"}
        
        if instance_id:
            query = f'-InstanceId "{instance_id}"'
        else:
            query = f'-FriendlyName "*{device_name}*"'
        
        script = f'''
        $device = Get-PnpDevice -Class Bluetooth {query} -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($device) {{
            $result = pnputil /remove-device $device.InstanceId 2>&1
            @{{ Success = $true; Device = $device.FriendlyName; Output = $result }} | ConvertTo-Json
        }} else {{
            @{{ Success = $false; Error = "Device not found" }} | ConvertTo-Json
        }}
        '''
        result = await self._run_powershell(script)
        if result["return_code"] == 0 and result["stdout"]:
            return json.loads(result["stdout"])
        return {"success": False, "error": result["stderr"]}
    
    async def _remove_device(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove a Bluetooth device from the system"""
        return await self._unpair_device(params)
    
    # Connection Management
    async def _connect_device(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Connect to a paired Bluetooth device"""
        device_name = params.get("device_name", "")
        instance_id = params.get("instance_id", "")
        
        if instance_id:
            query = f'-InstanceId "{instance_id}"'
        elif device_name:
            query = f'-FriendlyName "*{device_name}*"'
        else:
            return {"error": "Provide device_name or instance_id"}
        
        script = f'''
        $device = Get-PnpDevice -Class Bluetooth {query} -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($device) {{
            Enable-PnpDevice -InstanceId $device.InstanceId -Confirm:$false -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 2
            $updated = Get-PnpDevice -InstanceId $device.InstanceId
            @{{ Success = $true; Device = $device.FriendlyName; Status = $updated.Status }} | ConvertTo-Json
        }} else {{
            @{{ Success = $false; Error = "Device not found" }} | ConvertTo-Json
        }}
        '''
        result = await self._run_powershell(script)
        if result["return_code"] == 0 and result["stdout"]:
            return json.loads(result["stdout"])
        return {"success": False, "error": result["stderr"]}
    
    async def _disconnect_device(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Disconnect a Bluetooth device"""
        device_name = params.get("device_name", "")
        instance_id = params.get("instance_id", "")
        
        if instance_id:
            query = f'-InstanceId "{instance_id}"'
        elif device_name:
            query = f'-FriendlyName "*{device_name}*"'
        else:
            return {"error": "Provide device_name or instance_id"}
        
        script = f'''
        $device = Get-PnpDevice -Class Bluetooth {query} -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($device) {{
            Disable-PnpDevice -InstanceId $device.InstanceId -Confirm:$false -ErrorAction SilentlyContinue
            @{{ Success = $true; Device = $device.FriendlyName; Message = "Device disconnected" }} | ConvertTo-Json
        }} else {{
            @{{ Success = $false; Error = "Device not found" }} | ConvertTo-Json
        }}
        '''
        result = await self._run_powershell(script)
        if result["return_code"] == 0 and result["stdout"]:
            return json.loads(result["stdout"])
        return {"success": False, "error": result["stderr"]}
    
    async def _get_connected_devices(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get list of currently connected Bluetooth devices"""
        script = '''
        $devices = Get-PnpDevice -Class Bluetooth -Status OK -ErrorAction SilentlyContinue | Where-Object { 
            $_.FriendlyName -notmatch "Radio|Adapter|Controller|Enumerator|Microsoft|Generic" -and $_.Present -eq $true
        }
        $result = @()
        foreach ($device in $devices) {
            $result += @{
                Name = $device.FriendlyName
                Status = $device.Status
                InstanceId = $device.InstanceId
                Connected = $true
            }
        }
        @{ ConnectedDevices = $result; Count = $result.Count } | ConvertTo-Json -Depth 3
        '''
        result = await self._run_powershell(script)
        if result["return_code"] == 0 and result["stdout"]:
            return json.loads(result["stdout"])
        return {"connected_devices": [], "count": 0}
    
    async def _get_connection_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get connection status of a specific device"""
        return await self._get_device_info(params)
    
    async def _reconnect_device(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Reconnect a Bluetooth device"""
        await self._disconnect_device(params)
        await asyncio.sleep(1)
        return await self._connect_device(params)
    
    # Audio Device Management
    async def _get_audio_devices(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get Bluetooth audio devices"""
        script = '''
        $audioDevices = Get-PnpDevice -Class AudioEndpoint -Status OK -ErrorAction SilentlyContinue
        $btAudio = Get-PnpDevice -Class Bluetooth -Status OK -ErrorAction SilentlyContinue | Where-Object { 
            $_.FriendlyName -match "Headphone|Headset|Speaker|Audio|AirPods|Buds|Earbuds|JBL|Sony|Bose|Beats"
        }
        $result = @()
        foreach ($device in $btAudio) {
            $result += @{
                Name = $device.FriendlyName
                Status = $device.Status
                InstanceId = $device.InstanceId
                Type = "Bluetooth Audio"
            }
        }
        @{ AudioDevices = $result; Count = $result.Count } | ConvertTo-Json -Depth 3
        '''
        result = await self._run_powershell(script)
        if result["return_code"] == 0 and result["stdout"]:
            return json.loads(result["stdout"])
        return {"audio_devices": [], "count": 0}
    
    async def _set_default_audio_device(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set default audio device"""
        device_name = params.get("device_name", "")
        script = '''
        Start-Process "ms-settings:sound" -WindowStyle Normal
        @{ Success = $true; Message = "Sound settings opened. Select your default audio device." } | ConvertTo-Json
        '''
        result = await self._run_powershell(script)
        return {"success": True, "message": "Sound settings opened to configure default audio device"}
    
    async def _get_default_audio_device(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get default audio playback device"""
        script = '''
        Add-Type -TypeDefinition @"
        using System.Runtime.InteropServices;
        [Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
        interface IMMDevice { }
        [Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
        interface IMMDeviceEnumerator { }
"@ -ErrorAction SilentlyContinue
        
        $audioDevices = Get-PnpDevice -Class AudioEndpoint -Status OK -ErrorAction SilentlyContinue | Select-Object -First 5
        @{ DefaultDevices = ($audioDevices | Select-Object FriendlyName, Status, InstanceId) } | ConvertTo-Json -Depth 3
        '''
        result = await self._run_powershell(script)
        if result["return_code"] == 0 and result["stdout"]:
            return json.loads(result["stdout"])
        return {"message": "Use Sound settings to view default audio device"}
    
    async def _get_audio_device_properties(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get audio device properties"""
        device_name = params.get("device_name", "")
        return await self._get_device_info({"device_name": device_name})
    
    # Device Services
    async def _get_device_services(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get services provided by a Bluetooth device"""
        device_name = params.get("device_name", "")
        script = f'''
        $services = @(
            @{{ Name = "Audio Sink (A2DP)"; UUID = "0000110b-0000-1000-8000-00805f9b34fb"; Description = "High-quality audio streaming" }}
            @{{ Name = "Headset (HSP)"; UUID = "00001108-0000-1000-8000-00805f9b34fb"; Description = "Headset profile for calls" }}
            @{{ Name = "Hands-Free (HFP)"; UUID = "0000111e-0000-1000-8000-00805f9b34fb"; Description = "Hands-free calling" }}
            @{{ Name = "HID"; UUID = "00001124-0000-1000-8000-00805f9b34fb"; Description = "Human Interface Device" }}
            @{{ Name = "Serial Port (SPP)"; UUID = "00001101-0000-1000-8000-00805f9b34fb"; Description = "Serial communication" }}
            @{{ Name = "Object Push (OPP)"; UUID = "00001105-0000-1000-8000-00805f9b34fb"; Description = "File transfer" }}
        )
        @{{ CommonServices = $services; Note = "Actual services depend on device capabilities" }} | ConvertTo-Json -Depth 3
        '''
        result = await self._run_powershell(script)
        if result["return_code"] == 0 and result["stdout"]:
            return json.loads(result["stdout"])
        return {"services": []}
    
    async def _get_service_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get information about a specific Bluetooth service"""
        service_name = params.get("service_name", "")
        services = {
            "a2dp": {"name": "Advanced Audio Distribution Profile", "description": "High-quality audio streaming"},
            "hsp": {"name": "Headset Profile", "description": "Mono audio for calls"},
            "hfp": {"name": "Hands-Free Profile", "description": "Hands-free calling in vehicles"},
            "hid": {"name": "Human Interface Device", "description": "Keyboards, mice, game controllers"},
            "pbap": {"name": "Phone Book Access Profile", "description": "Phone book synchronization"},
            "map": {"name": "Message Access Profile", "description": "Message notifications"}
        }
        return services.get(service_name.lower(), {"error": f"Unknown service: {service_name}", "available": list(services.keys())})
    
    async def _list_supported_profiles(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List common Bluetooth profiles"""
        profiles = [
            {"profile": "A2DP", "description": "Advanced Audio Distribution Profile - stereo audio"},
            {"profile": "AVRCP", "description": "Audio/Video Remote Control Profile - media controls"},
            {"profile": "HFP", "description": "Hands-Free Profile - car audio/calls"},
            {"profile": "HSP", "description": "Headset Profile - mono audio"},
            {"profile": "HID", "description": "Human Interface Device - keyboards/mice"},
            {"profile": "PAN", "description": "Personal Area Network - internet sharing"},
            {"profile": "SPP", "description": "Serial Port Profile - data transfer"},
            {"profile": "OPP", "description": "Object Push Profile - file transfer"},
            {"profile": "PBAP", "description": "Phone Book Access Profile"},
            {"profile": "MAP", "description": "Message Access Profile"}
        ]
        return {"profiles": profiles, "count": len(profiles)}
    
    # File Transfer
    async def _send_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Open Bluetooth file transfer to send a file"""
        file_path = params.get("file_path", "")
        script = '''
        Start-Process "fsquirt.exe"
        @{ Success = $true; Message = "Bluetooth File Transfer wizard opened" } | ConvertTo-Json
        '''
        result = await self._run_powershell(script)
        return {"success": True, "message": "Bluetooth File Transfer wizard opened. Select device and file to send."}
    
    async def _receive_file_settings(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Configure Bluetooth file receive settings"""
        script = '''
        Start-Process "fsquirt.exe"
        @{ Success = $true; Message = "Bluetooth File Transfer wizard opened. Select 'Receive files'." } | ConvertTo-Json
        '''
        result = await self._run_powershell(script)
        return {"success": True, "message": "Use the wizard to receive files via Bluetooth"}
    
    async def _open_bluetooth_file_transfer(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Open Bluetooth file transfer wizard"""
        script = '''
        Start-Process "fsquirt.exe"
        @{ Success = $true; Message = "Bluetooth File Transfer wizard opened" } | ConvertTo-Json
        '''
        await self._run_powershell(script)
        return {"success": True, "message": "Bluetooth File Transfer wizard opened"}
    
    # Settings and Configuration
    async def _open_bluetooth_settings(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Open Windows Bluetooth settings"""
        script = '''
        Start-Process "ms-settings:bluetooth"
        @{ Success = $true; Message = "Bluetooth settings opened" } | ConvertTo-Json
        '''
        await self._run_powershell(script)
        return {"success": True, "message": "Bluetooth settings opened"}
    
    async def _set_device_name(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set the Bluetooth device name (computer name for Bluetooth)"""
        new_name = params.get("name", "")
        if not new_name:
            return {"error": "Provide 'name' parameter"}
        
        script = '''
        Start-Process "ms-settings:bluetooth"
        @{ Success = $true; Message = "Open Bluetooth settings > More Bluetooth options to change device name" } | ConvertTo-Json
        '''
        await self._run_powershell(script)
        return {"success": True, "message": "Bluetooth device name can be changed in Bluetooth settings > More Bluetooth options"}
    
    async def _get_device_name(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get the Bluetooth device name"""
        script = '''
        $name = $env:COMPUTERNAME
        @{ DeviceName = $name; Message = "This computer appears as '$name' to other Bluetooth devices" } | ConvertTo-Json
        '''
        result = await self._run_powershell(script)
        if result["return_code"] == 0 and result["stdout"]:
            return json.loads(result["stdout"])
        return {"device_name": "Unknown"}
    
    async def _set_discoverable(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set Bluetooth discoverable mode"""
        enabled = params.get("enabled", True)
        script = '''
        Start-Process "ms-settings:bluetooth"
        @{ Success = $true; Message = "Bluetooth settings opened. Toggle 'Discovery' option as needed." } | ConvertTo-Json
        '''
        await self._run_powershell(script)
        return {"success": True, "message": "Configure discoverability in Bluetooth settings"}
    
    async def _get_discoverable_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get Bluetooth discoverable status"""
        return {"message": "Discoverability status can be viewed in Bluetooth settings", "note": "Open ms-settings:bluetooth to check"}
    
    # Diagnostics
    async def _get_bluetooth_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get comprehensive Bluetooth system information"""
        script = '''
        $adapters = Get-PnpDevice -Class Bluetooth -ErrorAction SilentlyContinue
        $radioAdapters = $adapters | Where-Object { $_.FriendlyName -match "Radio|Adapter|Controller" }
        $pairedDevices = $adapters | Where-Object { $_.FriendlyName -notmatch "Radio|Adapter|Controller|Enumerator|Microsoft|Generic" }
        $service = Get-Service -Name "bthserv" -ErrorAction SilentlyContinue
        
        @{
            BluetoothService = @{
                Name = $service.Name
                Status = $service.Status.ToString()
                StartType = $service.StartType.ToString()
            }
            Adapters = @($radioAdapters | Select-Object FriendlyName, Status, InstanceId)
            PairedDevices = @($pairedDevices | Select-Object FriendlyName, Status, Present)
            AdapterCount = $radioAdapters.Count
            PairedDeviceCount = $pairedDevices.Count
        } | ConvertTo-Json -Depth 4
        '''
        result = await self._run_powershell(script)
        if result["return_code"] == 0 and result["stdout"]:
            return json.loads(result["stdout"])
        return {"error": result["stderr"]}
    
    async def _troubleshoot_bluetooth(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run Bluetooth troubleshooter"""
        script = '''
        Start-Process "msdt.exe" -ArgumentList "/id BluetoothDiagnostic" -Wait:$false
        @{ Success = $true; Message = "Bluetooth troubleshooter launched" } | ConvertTo-Json
        '''
        await self._run_powershell(script)
        return {"success": True, "message": "Bluetooth troubleshooter launched"}
    
    async def _restart_bluetooth_service(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Restart the Bluetooth Support Service"""
        script = '''
        try {
            Restart-Service -Name "bthserv" -Force -ErrorAction Stop
            Start-Sleep -Seconds 3
            $service = Get-Service -Name "bthserv"
            @{ Success = $true; ServiceStatus = $service.Status.ToString(); Message = "Bluetooth service restarted" } | ConvertTo-Json
        } catch {
            @{ Success = $false; Error = $_.Exception.Message } | ConvertTo-Json
        }
        '''
        result = await self._run_powershell(script)
        if result["return_code"] == 0 and result["stdout"]:
            return json.loads(result["stdout"])
        return {"success": False, "error": result["stderr"], "note": "Requires administrator privileges"}
    
    async def _get_bluetooth_logs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get recent Bluetooth-related event logs"""
        max_events = params.get("max_events", 20)
        script = f'''
        $events = Get-WinEvent -LogName "Microsoft-Windows-Bluetooth-BthLEPrepairing/Operational" -MaxEvents {max_events} -ErrorAction SilentlyContinue
        if (-not $events) {{
            $events = Get-WinEvent -FilterHashtable @{{ LogName = "System"; ProviderName = "*Bluetooth*" }} -MaxEvents {max_events} -ErrorAction SilentlyContinue
        }}
        if ($events) {{
            $result = $events | Select-Object TimeCreated, Id, LevelDisplayName, Message | ForEach-Object {{
                @{{
                    Time = $_.TimeCreated.ToString("yyyy-MM-dd HH:mm:ss")
                    EventId = $_.Id
                    Level = $_.LevelDisplayName
                    Message = $_.Message.Substring(0, [Math]::Min(200, $_.Message.Length))
                }}
            }}
            @{{ Events = $result; Count = $result.Count }} | ConvertTo-Json -Depth 3
        }} else {{
            @{{ Events = @(); Message = "No Bluetooth events found" }} | ConvertTo-Json
        }}
        '''
        result = await self._run_powershell(script)
        if result["return_code"] == 0 and result["stdout"]:
            return json.loads(result["stdout"])
        return {"events": [], "message": "Could not retrieve Bluetooth logs"}
    
    async def cleanup(self):
        """Cleanup plugin resources"""
        self._initialized = False
        logger.info("Bluetooth plugin cleaned up")


# Export the plugin class
__all__ = ["BluetoothPlugin"]


plugin = BluetoothPlugin()
