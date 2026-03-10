"""
Windows Management Instrumentation (WMI) Provider Integration - PRODUCTION
Query WMI classes, execute methods, list namespaces, subscribe to events, get system info.
"""
import os
import asyncio
import json
from typing import Dict, Any, Optional, List
from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType
import logging

logger = logging.getLogger(__name__)


class WindowsWMIProviderPlugin(IntegrationPlugin):
    def __init__(self):
        metadata = PluginMetadata(
            id="windows_wmi_provider",
            name="Windows WMI Provider",
            description=(
                "Interface with Windows Management Instrumentation (WMI): run queries, "
                "get class info, list namespaces, execute methods, and retrieve system/hardware info."
            ),
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["windows", "wmi", "management", "system", "hardware", "query"],
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
            "query_wmi": self._query_wmi,
            "get_wmi_class": self._get_wmi_class,
            "list_namespaces": self._list_namespaces,
            "execute_method": self._execute_method,
            "subscribe_event": self._subscribe_event,
            "get_system_info": self._get_system_info,
            "get_hardware_info": self._get_hardware_info,
            "get_process_info": self._get_process_info,
            "get_service_info": self._get_service_info,
            "get_disk_info": self._get_disk_info,
            "get_network_info": self._get_network_info,
            "list_wmi_classes": self._list_wmi_classes,
        }

        handler = actions.get(action)
        if handler is None:
            return {"success": False, "error": f"Unknown action: {action}. Available: {list(actions)}"}
        return await handler(parameters)

    async def _run_ps(self, cmd: str, timeout: int = 45) -> Dict[str, Any]:
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

    async def _query_wmi(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a WMI query (WQL) and return results."""
        query = params.get("query")
        namespace = params.get("namespace", "root\\cimv2")
        limit = params.get("limit", 50)
        if not query:
            return {"success": False, "error": "Parameter 'query' (WQL query) is required"}

        safe_query = query.replace('"', "'").replace(";", "")
        safe_ns = namespace.replace('"', "").replace(";", "")
        cmd = f"""
try {{
    $results = Get-WmiObject -Namespace "{safe_ns}" -Query "{safe_query}" -ErrorAction Stop |
        Select-Object -First {limit}
    $output = @($results | ForEach-Object {{
        $obj = @{{}}
        $_.PSObject.Properties | Where-Object {{ $_.Name -notmatch "^__" }} | ForEach-Object {{
            $obj[$_.Name] = $_.Value
        }}
        $obj
    }})
    @{{ "results" = $output; "count" = $output.Count; "namespace" = "{safe_ns}" }} | ConvertTo-Json -Depth 3
}} catch {{
    @{{ "error" = $_.Exception.Message; "query" = "{safe_query}" }} | ConvertTo-Json
}}
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _get_wmi_class(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get information about a WMI class including its properties."""
        class_name = params.get("class_name")
        namespace = params.get("namespace", "root\\cimv2")
        if not class_name:
            return {"success": False, "error": "Parameter 'class_name' is required"}

        safe_class = class_name.replace('"', "").replace(";", "")
        safe_ns = namespace.replace('"', "").replace(";", "")
        cmd = f"""
try {{
    $class = [WMIClass]("{safe_ns}:{safe_class}")
    $props = @($class.Properties | ForEach-Object {{
        @{{ "name"=$_.Name; "type"=$_.Type.ToString(); "is_array"=$_.IsArray; "is_local"=$_.IsLocal }}
    }})
    $methods = @($class.Methods | ForEach-Object {{ $_.Name }})
    @{{
        "class_name" = "{safe_class}"
        "namespace" = "{safe_ns}"
        "property_count" = $props.Count
        "properties" = $props
        "methods" = $methods
        "method_count" = $methods.Count
    }} | ConvertTo-Json -Depth 3
}} catch {{
    @{{ "error" = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _list_namespaces(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List available WMI namespaces."""
        parent = params.get("parent_namespace", "root")
        recursive = params.get("recursive", False)
        safe_parent = parent.replace('"', "").replace(";", "")

        if recursive:
            cmd = f"""
function Get-WmiNamespaces($ns) {{
    $result = @()
    try {{
        $children = Get-WmiObject -Namespace $ns -Class "__Namespace" -ErrorAction SilentlyContinue
        foreach ($c in $children) {{
            $fullPath = "$ns\\$($c.Name)"
            $result += $fullPath
            $result += Get-WmiNamespaces $fullPath
        }}
    }} catch {{}}
    return $result
}}
$ns = @(Get-WmiNamespaces "{safe_parent}")
@{{ "namespaces" = $ns; "count" = $ns.Count; "parent" = "{safe_parent}" }} | ConvertTo-Json -Depth 2
"""
        else:
            cmd = f"""
try {{
    $ns = @(Get-WmiObject -Namespace "{safe_parent}" -Class "__Namespace" -ErrorAction Stop |
        ForEach-Object {{ "{safe_parent}\\$($_.Name)" }})
    @{{ "namespaces" = $ns; "count" = $ns.Count; "parent" = "{safe_parent}" }} | ConvertTo-Json
}} catch {{
    @{{ "error" = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        result = await self._run_ps(cmd, timeout=60)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _execute_method(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a WMI method on an object."""
        class_name = params.get("class_name")
        method_name = params.get("method_name")
        namespace = params.get("namespace", "root\\cimv2")
        filter_wql = params.get("filter", "")
        method_params = params.get("method_params", {})

        if not class_name or not method_name:
            return {"success": False, "error": "Parameters 'class_name' and 'method_name' are required"}

        safe_class = class_name.replace('"', "").replace(";", "")
        safe_method = method_name.replace('"', "").replace(";", "")
        safe_ns = namespace.replace('"', "").replace(";", "")
        safe_filter = filter_wql.replace('"', "'")

        where_clause = f"| Where-Object {{ {safe_filter} }}" if safe_filter else ""
        params_str = " ".join([f'-{k.replace(chr(34), "")} "{str(v).replace(chr(34), chr(39))}"'
                                for k, v in method_params.items()])

        cmd = f"""
try {{
    $obj = Get-WmiObject -Namespace "{safe_ns}" -Class "{safe_class}" -ErrorAction Stop {where_clause} |
        Select-Object -First 1
    if ($obj) {{
        $result = $obj.{safe_method}({params_str})
        @{{ "success" = $true; "return_value" = $result.ReturnValue; "result" = ($result | ConvertTo-Json -Depth 2 -ErrorAction SilentlyContinue) }} | ConvertTo-Json
    }} else {{
        @{{ "error" = "No object found matching filter" }} | ConvertTo-Json
    }}
}} catch {{
    @{{ "error" = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _subscribe_event(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Return info about WMI event subscription (polling-based check)."""
        event_class = params.get("event_class", "__InstanceCreationEvent")
        target_class = params.get("target_class", "Win32_Process")
        return {
            "success": True,
            "note": "WMI event subscriptions are long-running and require a dedicated thread/process.",
            "event_class": event_class,
            "target_class": target_class,
            "usage": f"Use: Register-WmiEvent -Class '{event_class}' -Query \"SELECT * FROM {event_class} WHERE TargetInstance ISA '{target_class}'\"",
        }

    async def _get_system_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get comprehensive system information via WMI."""
        cmd = r"""
$os = Get-WmiObject Win32_OperatingSystem -ErrorAction SilentlyContinue
$cs = Get-WmiObject Win32_ComputerSystem -ErrorAction SilentlyContinue
$bios = Get-WmiObject Win32_BIOS -ErrorAction SilentlyContinue
$proc = Get-WmiObject Win32_Processor -ErrorAction SilentlyContinue | Select-Object -First 1

@{
    "os" = @{
        "caption" = $os.Caption
        "version" = $os.Version
        "build_number" = $os.BuildNumber
        "service_pack" = $os.ServicePackMajorVersion
        "architecture" = $os.OSArchitecture
        "serial_number" = $os.SerialNumber
        "install_date" = $os.InstallDate
        "last_boot" = $os.LastBootUpTime
        "total_ram_gb" = [math]::Round($os.TotalVisibleMemorySize / 1MB, 2)
        "free_ram_gb" = [math]::Round($os.FreePhysicalMemory / 1MB, 2)
    }
    "computer" = @{
        "name" = $cs.Name
        "domain" = $cs.Domain
        "manufacturer" = $cs.Manufacturer
        "model" = $cs.Model
        "system_type" = $cs.SystemType
        "total_physical_memory_gb" = [math]::Round($cs.TotalPhysicalMemory / 1GB, 2)
    }
    "bios" = @{
        "version" = $bios.SMBIOSBIOSVersion
        "manufacturer" = $bios.Manufacturer
        "release_date" = $bios.ReleaseDate
        "serial_number" = $bios.SerialNumber
    }
    "processor" = @{
        "name" = $proc.Name
        "manufacturer" = $proc.Manufacturer
        "cores" = $proc.NumberOfCores
        "logical_processors" = $proc.NumberOfLogicalProcessors
        "max_clock_speed_mhz" = $proc.MaxClockSpeed
        "socket" = $proc.SocketDesignation
    }
} | ConvertTo-Json -Depth 3
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _get_hardware_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get hardware information (memory, storage, GPU) via WMI."""
        cmd = r"""
$memory = @(Get-WmiObject Win32_PhysicalMemory -ErrorAction SilentlyContinue | ForEach-Object {
    @{ "bank"=$_.BankLabel; "capacity_gb"=[math]::Round($_.Capacity/1GB,1)
       "speed_mhz"=$_.Speed; "manufacturer"=$_.Manufacturer; "type"=$_.MemoryType }
})
$disks = @(Get-WmiObject Win32_DiskDrive -ErrorAction SilentlyContinue | ForEach-Object {
    @{ "model"=$_.Model; "size_gb"=[math]::Round($_.Size/1GB,1)
       "media_type"=$_.MediaType; "interface_type"=$_.InterfaceType; "serial"=$_.SerialNumber }
})
$gpu = @(Get-WmiObject Win32_VideoController -ErrorAction SilentlyContinue | ForEach-Object {
    @{ "name"=$_.Name; "driver_version"=$_.DriverVersion
       "vram_mb"=[math]::Round($_.AdapterRAM/1MB,0); "resolution"="$($_.CurrentHorizontalResolution)x$($_.CurrentVerticalResolution)" }
})
@{ "memory_modules"=$memory; "disks"=$disks; "gpus"=$gpu
   "total_ram_gb"=($memory | Measure-Object capacity_gb -Sum).Sum } | ConvertTo-Json -Depth 3
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _get_process_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get process information via WMI."""
        filter_name = params.get("name", "")
        limit = params.get("limit", 30)
        where = f" | Where-Object {{ $_.Name -like '*{filter_name.replace(chr(39), chr(39)*2)}*' }}" if filter_name else ""
        cmd = f"""
$procs = @(Get-WmiObject Win32_Process -ErrorAction SilentlyContinue{where} | Select-Object -First {limit} |
    ForEach-Object {{
        @{{ "pid"=$_.ProcessId; "name"=$_.Name; "cmd"=$_.CommandLine
            "priority"=$_.Priority; "threads"=$_.ThreadCount; "handles"=$_.HandleCount
            "parent_pid"=$_.ParentProcessId; "creation_date"=$_.CreationDate }}
    }})
@{{ "processes"=$procs; "count"=$procs.Count }} | ConvertTo-Json -Depth 2
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _get_service_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get Windows service information via WMI."""
        filter_name = params.get("name", "")
        limit = params.get("limit", 50)
        where = f" -Filter \"Name LIKE '%{filter_name.replace(chr(39), chr(39)*2)}%'\"" if filter_name else ""
        cmd = f"""
$svcs = @(Get-WmiObject Win32_Service{where} -ErrorAction SilentlyContinue | Select-Object -First {limit} |
    ForEach-Object {{
        @{{ "name"=$_.Name; "display_name"=$_.DisplayName; "state"=$_.State
            "start_mode"=$_.StartMode; "path"=$_.PathName; "pid"=$_.ProcessId
            "description"=$_.Description }}
    }})
@{{ "services"=$svcs; "count"=$svcs.Count }} | ConvertTo-Json -Depth 2
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _get_disk_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get disk and partition information via WMI."""
        cmd = r"""
$drives = @(Get-WmiObject Win32_DiskDrive -ErrorAction SilentlyContinue | ForEach-Object {
    $parts = @(Get-WmiObject -Query "ASSOCIATORS OF {Win32_DiskDrive.DeviceID='$($_.DeviceID.Replace('\','\\'))'} WHERE AssocClass=Win32_DiskDriveToDiskPartition" -ErrorAction SilentlyContinue)
    @{
        "model" = $_.Model
        "size_gb" = [math]::Round($_.Size/1GB, 1)
        "media_type" = $_.MediaType
        "interface_type" = $_.InterfaceType
        "serial" = $_.SerialNumber
        "status" = $_.Status
        "partitions" = @($parts | ForEach-Object {
            $logDisk = Get-WmiObject -Query "ASSOCIATORS OF {Win32_DiskPartition.DeviceID='$($_.DeviceID)'} WHERE AssocClass=Win32_LogicalDiskToPartition" -ErrorAction SilentlyContinue
            @{ "name"=$_.Name; "size_gb"=[math]::Round($_.Size/1GB,1)
               "drive_letter"=if($logDisk){$logDisk.DeviceID}else{""} }
        })
    }
})
@{ "drives" = $drives; "count" = $drives.Count } | ConvertTo-Json -Depth 4
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _get_network_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get network adapter info via WMI."""
        cmd = r"""
$adapters = @(Get-WmiObject Win32_NetworkAdapterConfiguration -Filter "IPEnabled=True" -ErrorAction SilentlyContinue |
    ForEach-Object {
        @{ "description"=$_.Description; "mac"=$_.MACAddress
           "ip_addresses"=@($_.IPAddress); "subnets"=@($_.IPSubnet)
           "gateways"=@($_.DefaultIPGateway); "dns_servers"=@($_.DNSServerSearchOrder)
           "dhcp_enabled"=$_.DHCPEnabled; "dhcp_server"=$_.DHCPServer }
    })
@{ "adapters" = $adapters; "count" = $adapters.Count } | ConvertTo-Json -Depth 3
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _list_wmi_classes(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List WMI classes in a namespace."""
        namespace = params.get("namespace", "root\\cimv2")
        filter_str = params.get("filter", "Win32_")
        limit = params.get("limit", 100)
        safe_ns = namespace.replace('"', "").replace(";", "")
        safe_filter = filter_str.replace('"', "").replace(";", "")
        cmd = f"""
try {{
    $classes = @(Get-WmiObject -Namespace "{safe_ns}" -List -ErrorAction Stop |
        Where-Object {{ $_.Name -like "*{safe_filter}*" }} | Select-Object -First {limit} |
        ForEach-Object {{ $_.Name }})
    @{{ "classes" = $classes; "count" = $classes.Count; "namespace" = "{safe_ns}" }} | ConvertTo-Json
}} catch {{
    @{{ "error" = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        result = await self._run_ps(cmd, timeout=60)
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
                "query_wmi": {"description": "Run WQL query", "params": {"query": "str", "namespace": "str", "limit": "int"}},
                "get_wmi_class": {"description": "Get class info", "params": {"class_name": "str", "namespace": "str"}},
                "list_namespaces": {"description": "List WMI namespaces", "params": {"parent_namespace": "str", "recursive": "bool"}},
                "execute_method": {"description": "Execute WMI method", "params": {"class_name": "str", "method_name": "str"}},
                "subscribe_event": {"description": "Get event subscription info"},
                "get_system_info": {"description": "Get comprehensive system info via WMI"},
                "get_hardware_info": {"description": "Get hardware info (RAM, disks, GPU)"},
                "get_process_info": {"description": "Get process info via WMI", "params": {"name": "str", "limit": "int"}},
                "get_service_info": {"description": "Get service info via WMI", "params": {"name": "str", "limit": "int"}},
                "get_disk_info": {"description": "Get disk and partition info"},
                "get_network_info": {"description": "Get network adapter info via WMI"},
                "list_wmi_classes": {"description": "List WMI classes", "params": {"namespace": "str", "filter": "str", "limit": "int"}},
            },
        }


plugin = WindowsWMIProviderPlugin()
