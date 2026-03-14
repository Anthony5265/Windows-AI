"""
Windows Print Management Plugin for Windows AI
Comprehensive printer and print job management
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class PrinterStatus(Enum):
    """Printer status values"""
    READY = "Ready"
    OFFLINE = "Offline"
    PAUSED = "Paused"
    ERROR = "Error"
    BUSY = "Busy"
    PAPER_JAM = "Paper Jam"
    PAPER_OUT = "Paper Out"
    MANUAL_FEED = "Manual Feed"
    WARMING_UP = "Warming Up"


class PrintJobStatus(Enum):
    """Print job status values"""
    SPOOLING = "Spooling"
    PRINTING = "Printing"
    PRINTED = "Printed"
    PAUSED = "Paused"
    DELETING = "Deleting"
    ERROR = "Error"
    OFFLINE = "Offline"


@dataclass
class PrinterInfo:
    """Printer information"""
    name: str
    driver_name: str
    port_name: str
    shared: bool
    share_name: Optional[str]
    is_default: bool
    status: PrinterStatus
    location: Optional[str]
    comment: Optional[str]


@dataclass
class PrintJob:
    """Print job information"""
    job_id: int
    document_name: str
    printer_name: str
    user_name: str
    status: PrintJobStatus
    submitted_time: datetime
    total_pages: int
    pages_printed: int
    size_bytes: int
    priority: int


class WindowsPrintPlugin(IntegrationPlugin):
    """
    Comprehensive Windows Print Management plugin
    
    Provides:
    - Printer discovery and listing
    - Printer installation and removal
    - Print queue management
    - Print job control (pause, resume, cancel)
    - Default printer management
    - Print spooler service control
    - Port and driver management
    - Print configuration
    - Network printer management
    - Print history and statistics
    """
    
    def __init__(self):
        metadata = PluginMetadata(
            id="windows-print",
            name="Windows Print Management",
            description="Printer and print job management",
            version="2.0.0",
            author="Windows AI Team"
        )
        super().__init__(metadata)
    

    async def connect(self, credentials: Dict[str, str]) -> bool:
        """Connect to the service"""
        return True

    async def disconnect(self) -> bool:
        """Disconnect from the service"""
        return True

    async def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """Execute print management actions"""
        actions = {
            # Printer Management
            "list_printers": self._list_printers,
            "get_printer": self._get_printer,
            "add_printer": self._add_printer,
            "remove_printer": self._remove_printer,
            "rename_printer": self._rename_printer,
            "set_default_printer": self._set_default_printer,
            "get_default_printer": self._get_default_printer,
            
            # Printer Configuration
            "get_printer_properties": self._get_printer_properties,
            "set_printer_property": self._set_printer_property,
            "share_printer": self._share_printer,
            "unshare_printer": self._unshare_printer,
            
            # Print Queue Management
            "get_print_queue": self._get_print_queue,
            "clear_print_queue": self._clear_print_queue,
            "pause_printer": self._pause_printer,
            "resume_printer": self._resume_printer,
            
            # Print Job Management
            "list_print_jobs": self._list_print_jobs,
            "get_print_job": self._get_print_job,
            "pause_print_job": self._pause_print_job,
            "resume_print_job": self._resume_print_job,
            "cancel_print_job": self._cancel_print_job,
            "restart_print_job": self._restart_print_job,
            
            # Print Spooler
            "get_spooler_status": self._get_spooler_status,
            "start_spooler": self._start_spooler,
            "stop_spooler": self._stop_spooler,
            "restart_spooler": self._restart_spooler,
            "clear_spooler": self._clear_spooler,
            
            # Drivers
            "list_printer_drivers": self._list_printer_drivers,
            "get_printer_driver": self._get_printer_driver,
            "add_printer_driver": self._add_printer_driver,
            "remove_printer_driver": self._remove_printer_driver,
            
            # Ports
            "list_printer_ports": self._list_printer_ports,
            "add_printer_port": self._add_printer_port,
            "remove_printer_port": self._remove_printer_port,
            
            # Network Printers
            "add_network_printer": self._add_network_printer,
            "discover_network_printers": self._discover_network_printers,
            
            # Print Test
            "print_test_page": self._print_test_page,
            
            # Statistics
            "get_print_statistics": self._get_print_statistics,
        }
        
        if action not in actions:
            return {"error": f"Unknown action: {action}", "available_actions": list(actions.keys())}
        
        try:
            return await actions[action](**kwargs)
        except Exception as e:
            logger.error(f"Print action '{action}' failed: {e}")
            return {"error": str(e), "action": action}
    
    # ========== Printer Management ==========
    
    async def _list_printers(self, **kwargs) -> Dict[str, Any]:
        """List all installed printers"""
        script = """
Get-Printer | ForEach-Object {
    @{
        name = $_.Name
        driver_name = $_.DriverName
        port_name = $_.PortName
        shared = $_.Shared
        share_name = $_.ShareName
        printer_status = $_.PrinterStatus.ToString()
        job_count = $_.JobCount
        location = $_.Location
        comment = $_.Comment
        type = $_.Type.ToString()
        device_type = $_.DeviceType.ToString()
    }
} | ConvertTo-Json -AsArray
"""
        result = await self._run_powershell(script)
        try:
            return {"printers": json.loads(result) if result.strip() else []}
        except json.JSONDecodeError:
            return {"printers": [], "raw": result}
    
    async def _get_printer(self, name: str, **kwargs) -> Dict[str, Any]:
        """Get detailed information about a specific printer"""
        script = f"""
$printer = Get-Printer -Name '{name}' -ErrorAction SilentlyContinue
if ($printer) {{
    $config = Get-PrintConfiguration -PrinterName '{name}' -ErrorAction SilentlyContinue
    @{{
        name = $printer.Name
        driver_name = $printer.DriverName
        port_name = $printer.PortName
        shared = $printer.Shared
        share_name = $printer.ShareName
        printer_status = $printer.PrinterStatus.ToString()
        job_count = $printer.JobCount
        location = $printer.Location
        comment = $printer.Comment
        type = $printer.Type.ToString()
        device_type = $printer.DeviceType.ToString()
        published = $printer.Published
        render_mode = $printer.RenderingMode.ToString()
        configuration = if ($config) {{
            @{{
                color = $config.Color
                duplex = $config.DuplexingMode.ToString()
                paper_size = $config.PaperSize.ToString()
                collate = $config.Collate
            }}
        }} else {{ $null }}
    }} | ConvertTo-Json -Depth 3
}} else {{
    @{{ error = "Printer not found"; name = '{name}' }} | ConvertTo-Json
}}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to get printer", "raw": result}
    
    async def _add_printer(
        self,
        name: str,
        driver_name: str,
        port_name: str,
        shared: bool = False,
        share_name: Optional[str] = None,
        location: Optional[str] = None,
        comment: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Add a new local printer"""
        share_params = ""
        if shared:
            share_params = f"-Shared"
            if share_name:
                share_params += f" -ShareName '{share_name}'"
        
        location_param = f"-Location '{location}'" if location else ""
        comment_param = f"-Comment '{comment}'" if comment else ""
        
        script = f"""
try {{
    Add-Printer -Name '{name}' -DriverName '{driver_name}' -PortName '{port_name}' {share_params} {location_param} {comment_param}
    @{{
        success = $true
        message = "Printer '{name}' added successfully"
        printer = (Get-Printer -Name '{name}').Name
    }} | ConvertTo-Json
}} catch {{
    @{{ success = $false; error = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to add printer", "raw": result}
    
    async def _remove_printer(self, name: str, **kwargs) -> Dict[str, Any]:
        """Remove a printer"""
        script = f"""
try {{
    Remove-Printer -Name '{name}' -ErrorAction Stop
    @{{ success = $true; message = "Printer '{name}' removed" }} | ConvertTo-Json
}} catch {{
    @{{ success = $false; error = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"success": True}
    
    async def _rename_printer(self, name: str, new_name: str, **kwargs) -> Dict[str, Any]:
        """Rename a printer"""
        script = f"""
try {{
    Rename-Printer -Name '{name}' -NewName '{new_name}' -ErrorAction Stop
    @{{ success = $true; message = "Printer renamed to '{new_name}'" }} | ConvertTo-Json
}} catch {{
    @{{ success = $false; error = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to rename printer", "raw": result}
    
    async def _set_default_printer(self, name: str, **kwargs) -> Dict[str, Any]:
        """Set the default printer"""
        script = f"""
try {{
    $printer = Get-CimInstance -ClassName Win32_Printer -Filter "Name='{name}'"
    if ($printer) {{
        Invoke-CimMethod -InputObject $printer -MethodName SetDefaultPrinter | Out-Null
        @{{ success = $true; message = "'{name}' set as default printer" }} | ConvertTo-Json
    }} else {{
        @{{ success = $false; error = "Printer not found" }} | ConvertTo-Json
    }}
}} catch {{
    @{{ success = $false; error = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to set default printer", "raw": result}
    
    async def _get_default_printer(self, **kwargs) -> Dict[str, Any]:
        """Get the default printer"""
        script = """
$default = Get-CimInstance -ClassName Win32_Printer -Filter "Default=True"
if ($default) {
    @{
        name = $default.Name
        driver_name = $default.DriverName
        port_name = $default.PortName
        status = $default.Status
    } | ConvertTo-Json
} else {
    @{ error = "No default printer set" } | ConvertTo-Json
}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to get default printer", "raw": result}
    
    # ========== Printer Configuration ==========
    
    async def _get_printer_properties(self, name: str, **kwargs) -> Dict[str, Any]:
        """Get printer properties and configuration"""
        script = f"""
$printer = Get-Printer -Name '{name}' -Full -ErrorAction SilentlyContinue
$config = Get-PrintConfiguration -PrinterName '{name}' -ErrorAction SilentlyContinue

if ($printer) {{
    @{{
        name = $printer.Name
        properties = @{{
            driver = $printer.DriverName
            port = $printer.PortName
            shared = $printer.Shared
            share_name = $printer.ShareName
            location = $printer.Location
            comment = $printer.Comment
            separator_page = $printer.SeparatorPageFile
            print_processor = $printer.PrintProcessor
            data_type = $printer.Datatype
            permissions_sddl = $printer.PermissionSDDL
            priority = $printer.Priority
            default_priority = $printer.DefaultJobPriority
        }}
        configuration = if ($config) {{
            @{{
                color = $config.Color
                duplex = $config.DuplexingMode.ToString()
                paper_size = $config.PaperSize.ToString()
                collate = $config.Collate
            }}
        }} else {{ $null }}
    }} | ConvertTo-Json -Depth 3
}} else {{
    @{{ error = "Printer not found" }} | ConvertTo-Json
}}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to get printer properties", "raw": result}
    
    async def _set_printer_property(self, name: str, property_name: str, value: Any, **kwargs) -> Dict[str, Any]:
        """Set a printer property"""
        script = f"""
try {{
    Set-Printer -Name '{name}' -{property_name} '{value}' -ErrorAction Stop
    @{{ success = $true; message = "Property '{property_name}' set to '{value}'" }} | ConvertTo-Json
}} catch {{
    @{{ success = $false; error = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to set property", "raw": result}
    
    async def _share_printer(self, name: str, share_name: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Share a printer on the network"""
        share_param = f"-ShareName '{share_name}'" if share_name else ""
        script = f"""
try {{
    Set-Printer -Name '{name}' -Shared $true {share_param} -ErrorAction Stop
    @{{ success = $true; message = "Printer '{name}' shared" }} | ConvertTo-Json
}} catch {{
    @{{ success = $false; error = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to share printer", "raw": result}
    
    async def _unshare_printer(self, name: str, **kwargs) -> Dict[str, Any]:
        """Stop sharing a printer"""
        script = f"""
try {{
    Set-Printer -Name '{name}' -Shared $false -ErrorAction Stop
    @{{ success = $true; message = "Printer '{name}' unshared" }} | ConvertTo-Json
}} catch {{
    @{{ success = $false; error = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to unshare printer", "raw": result}
    
    # ========== Print Queue Management ==========
    
    async def _get_print_queue(self, name: str, **kwargs) -> Dict[str, Any]:
        """Get print queue for a printer"""
        script = f"""
$jobs = Get-PrintJob -PrinterName '{name}' -ErrorAction SilentlyContinue
$printer = Get-Printer -Name '{name}' -ErrorAction SilentlyContinue

@{{
    printer = $printer.Name
    status = $printer.PrinterStatus.ToString()
    job_count = $printer.JobCount
    jobs = @($jobs | ForEach-Object {{
        @{{
            id = $_.Id
            document_name = $_.DocumentName
            user_name = $_.UserName
            submitted = $_.SubmittedTime.ToString('o')
            status = $_.JobStatus.ToString()
            size = $_.Size
            total_pages = $_.TotalPages
            pages_printed = $_.PagesPrinted
            priority = $_.Priority
        }}
    }})
}} | ConvertTo-Json -Depth 3
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to get print queue", "raw": result}
    
    async def _clear_print_queue(self, name: str, **kwargs) -> Dict[str, Any]:
        """Clear all jobs from a print queue"""
        script = f"""
try {{
    Get-PrintJob -PrinterName '{name}' | Remove-PrintJob
    @{{ success = $true; message = "Print queue cleared for '{name}'" }} | ConvertTo-Json
}} catch {{
    @{{ success = $false; error = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"success": True}
    
    async def _pause_printer(self, name: str, **kwargs) -> Dict[str, Any]:
        """Pause a printer"""
        script = f"""
try {{
    $printer = Get-CimInstance -ClassName Win32_Printer -Filter "Name='{name}'"
    Invoke-CimMethod -InputObject $printer -MethodName Pause | Out-Null
    @{{ success = $true; message = "Printer '{name}' paused" }} | ConvertTo-Json
}} catch {{
    @{{ success = $false; error = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to pause printer", "raw": result}
    
    async def _resume_printer(self, name: str, **kwargs) -> Dict[str, Any]:
        """Resume a paused printer"""
        script = f"""
try {{
    $printer = Get-CimInstance -ClassName Win32_Printer -Filter "Name='{name}'"
    Invoke-CimMethod -InputObject $printer -MethodName Resume | Out-Null
    @{{ success = $true; message = "Printer '{name}' resumed" }} | ConvertTo-Json
}} catch {{
    @{{ success = $false; error = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to resume printer", "raw": result}
    
    # ========== Print Job Management ==========
    
    async def _list_print_jobs(self, printer_name: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """List print jobs"""
        if printer_name:
            filter_param = f"-PrinterName '{printer_name}'"
        else:
            filter_param = ""
        
        script = f"""
$jobs = Get-PrintJob {filter_param} -ErrorAction SilentlyContinue
$jobs | ForEach-Object {{
    @{{
        id = $_.Id
        printer_name = $_.PrinterName
        document_name = $_.DocumentName
        user_name = $_.UserName
        submitted = $_.SubmittedTime.ToString('o')
        status = $_.JobStatus.ToString()
        size = $_.Size
        total_pages = $_.TotalPages
        pages_printed = $_.PagesPrinted
        priority = $_.Priority
    }}
}} | ConvertTo-Json -AsArray
"""
        result = await self._run_powershell(script)
        try:
            return {"jobs": json.loads(result) if result.strip() else []}
        except json.JSONDecodeError:
            return {"jobs": [], "raw": result}
    
    async def _get_print_job(self, printer_name: str, job_id: int, **kwargs) -> Dict[str, Any]:
        """Get details of a specific print job"""
        script = f"""
$job = Get-PrintJob -PrinterName '{printer_name}' -ID {job_id} -ErrorAction SilentlyContinue
if ($job) {{
    @{{
        id = $job.Id
        printer_name = $job.PrinterName
        document_name = $job.DocumentName
        user_name = $job.UserName
        submitted = $job.SubmittedTime.ToString('o')
        status = $job.JobStatus.ToString()
        size = $job.Size
        total_pages = $job.TotalPages
        pages_printed = $job.PagesPrinted
        priority = $job.Priority
        position = $job.Position
    }} | ConvertTo-Json
}} else {{
    @{{ error = "Print job not found" }} | ConvertTo-Json
}}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to get print job", "raw": result}
    
    async def _pause_print_job(self, printer_name: str, job_id: int, **kwargs) -> Dict[str, Any]:
        """Pause a print job"""
        script = f"""
try {{
    Suspend-PrintJob -PrinterName '{printer_name}' -ID {job_id} -ErrorAction Stop
    @{{ success = $true; message = "Print job {job_id} paused" }} | ConvertTo-Json
}} catch {{
    @{{ success = $false; error = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to pause job", "raw": result}
    
    async def _resume_print_job(self, printer_name: str, job_id: int, **kwargs) -> Dict[str, Any]:
        """Resume a paused print job"""
        script = f"""
try {{
    Resume-PrintJob -PrinterName '{printer_name}' -ID {job_id} -ErrorAction Stop
    @{{ success = $true; message = "Print job {job_id} resumed" }} | ConvertTo-Json
}} catch {{
    @{{ success = $false; error = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to resume job", "raw": result}
    
    async def _cancel_print_job(self, printer_name: str, job_id: int, **kwargs) -> Dict[str, Any]:
        """Cancel a print job"""
        script = f"""
try {{
    Remove-PrintJob -PrinterName '{printer_name}' -ID {job_id} -ErrorAction Stop
    @{{ success = $true; message = "Print job {job_id} cancelled" }} | ConvertTo-Json
}} catch {{
    @{{ success = $false; error = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"success": True}
    
    async def _restart_print_job(self, printer_name: str, job_id: int, **kwargs) -> Dict[str, Any]:
        """Restart a print job"""
        script = f"""
try {{
    Restart-PrintJob -PrinterName '{printer_name}' -ID {job_id} -ErrorAction Stop
    @{{ success = $true; message = "Print job {job_id} restarted" }} | ConvertTo-Json
}} catch {{
    @{{ success = $false; error = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to restart job", "raw": result}
    
    # ========== Print Spooler ==========
    
    async def _get_spooler_status(self, **kwargs) -> Dict[str, Any]:
        """Get print spooler service status"""
        script = """
$service = Get-Service Spooler
$spool_path = "$env:SystemRoot\\System32\\spool\\PRINTERS"
$pending_files = (Get-ChildItem $spool_path -ErrorAction SilentlyContinue | Measure-Object).Count

@{
    service_name = $service.Name
    display_name = $service.DisplayName
    status = $service.Status.ToString()
    start_type = $service.StartType.ToString()
    spool_directory = $spool_path
    pending_files = $pending_files
} | ConvertTo-Json
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to get spooler status", "raw": result}
    
    async def _start_spooler(self, **kwargs) -> Dict[str, Any]:
        """Start the print spooler service"""
        script = """
try {
    Start-Service Spooler -ErrorAction Stop
    @{ success = $true; status = (Get-Service Spooler).Status.ToString() } | ConvertTo-Json
} catch {
    @{ success = $false; error = $_.Exception.Message } | ConvertTo-Json
}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to start spooler", "raw": result}
    
    async def _stop_spooler(self, **kwargs) -> Dict[str, Any]:
        """Stop the print spooler service"""
        script = """
try {
    Stop-Service Spooler -Force -ErrorAction Stop
    @{ success = $true; status = (Get-Service Spooler).Status.ToString() } | ConvertTo-Json
} catch {
    @{ success = $false; error = $_.Exception.Message } | ConvertTo-Json
}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to stop spooler", "raw": result}
    
    async def _restart_spooler(self, **kwargs) -> Dict[str, Any]:
        """Restart the print spooler service"""
        script = """
try {
    Restart-Service Spooler -Force -ErrorAction Stop
    Start-Sleep -Seconds 2
    @{ success = $true; status = (Get-Service Spooler).Status.ToString() } | ConvertTo-Json
} catch {
    @{ success = $false; error = $_.Exception.Message } | ConvertTo-Json
}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to restart spooler", "raw": result}
    
    async def _clear_spooler(self, **kwargs) -> Dict[str, Any]:
        """Clear the print spooler (stops spooler, deletes pending jobs, restarts)"""
        script = """
try {
    Stop-Service Spooler -Force -ErrorAction Stop
    Start-Sleep -Seconds 1
    
    $spool_path = "$env:SystemRoot\\System32\\spool\\PRINTERS"
    Remove-Item "$spool_path\\*" -Force -ErrorAction SilentlyContinue
    
    Start-Service Spooler -ErrorAction Stop
    Start-Sleep -Seconds 2
    
    @{
        success = $true
        message = "Print spooler cleared"
        status = (Get-Service Spooler).Status.ToString()
    } | ConvertTo-Json
} catch {
    # Try to restart spooler even if clearing failed
    Start-Service Spooler -ErrorAction SilentlyContinue
    @{ success = $false; error = $_.Exception.Message } | ConvertTo-Json
}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to clear spooler", "raw": result}
    
    # ========== Drivers ==========
    
    async def _list_printer_drivers(self, **kwargs) -> Dict[str, Any]:
        """List installed printer drivers"""
        script = """
Get-PrinterDriver | ForEach-Object {
    @{
        name = $_.Name
        manufacturer = $_.Manufacturer
        driver_version = $_.DriverVersion
        print_processor = $_.PrintProcessor
        config_file = $_.ConfigFile
        provider_name = $_.ProviderName
        major_version = $_.MajorVersion
        print_environment = $_.PrinterEnvironment
    }
} | ConvertTo-Json -AsArray
"""
        result = await self._run_powershell(script)
        try:
            return {"drivers": json.loads(result) if result.strip() else []}
        except json.JSONDecodeError:
            return {"drivers": [], "raw": result}
    
    async def _get_printer_driver(self, name: str, **kwargs) -> Dict[str, Any]:
        """Get details of a specific printer driver"""
        script = f"""
$driver = Get-PrinterDriver -Name '{name}' -ErrorAction SilentlyContinue
if ($driver) {{
    @{{
        name = $driver.Name
        manufacturer = $driver.Manufacturer
        driver_version = $driver.DriverVersion
        print_processor = $driver.PrintProcessor
        config_file = $driver.ConfigFile
        data_file = $driver.DataFile
        driver_path = $driver.Path
        help_file = $driver.HelpFile
        provider_name = $driver.ProviderName
        major_version = $driver.MajorVersion
    }} | ConvertTo-Json
}} else {{
    @{{ error = "Driver not found" }} | ConvertTo-Json
}}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to get driver", "raw": result}
    
    async def _add_printer_driver(self, name: str, inf_path: str, **kwargs) -> Dict[str, Any]:
        """Add a printer driver from INF file"""
        script = f"""
try {{
    pnputil /add-driver '{inf_path}' /install
    Add-PrinterDriver -Name '{name}' -ErrorAction Stop
    @{{ success = $true; message = "Driver '{name}' installed" }} | ConvertTo-Json
}} catch {{
    @{{ success = $false; error = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to add driver", "raw": result}
    
    async def _remove_printer_driver(self, name: str, **kwargs) -> Dict[str, Any]:
        """Remove a printer driver"""
        script = f"""
try {{
    Remove-PrinterDriver -Name '{name}' -ErrorAction Stop
    @{{ success = $true; message = "Driver '{name}' removed" }} | ConvertTo-Json
}} catch {{
    @{{ success = $false; error = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to remove driver", "raw": result}
    
    # ========== Ports ==========
    
    async def _list_printer_ports(self, **kwargs) -> Dict[str, Any]:
        """List printer ports"""
        script = """
Get-PrinterPort | ForEach-Object {
    @{
        name = $_.Name
        description = $_.Description
        port_monitor = $_.PortMonitor
        printer_host_address = $_.PrinterHostAddress
        snmp_community = $_.SNMPCommunity
        snmp_enabled = $_.SNMPEnabled
    }
} | ConvertTo-Json -AsArray
"""
        result = await self._run_powershell(script)
        try:
            return {"ports": json.loads(result) if result.strip() else []}
        except json.JSONDecodeError:
            return {"ports": [], "raw": result}
    
    async def _add_printer_port(
        self,
        name: str,
        printer_host_address: Optional[str] = None,
        port_number: int = 9100,
        **kwargs
    ) -> Dict[str, Any]:
        """Add a printer port"""
        if printer_host_address:
            # TCP/IP port
            script = f"""
try {{
    Add-PrinterPort -Name '{name}' -PrinterHostAddress '{printer_host_address}' -PortNumber {port_number} -ErrorAction Stop
    @{{ success = $true; message = "TCP/IP port '{name}' created" }} | ConvertTo-Json
}} catch {{
    @{{ success = $false; error = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        else:
            # Local port
            script = f"""
try {{
    Add-PrinterPort -Name '{name}' -ErrorAction Stop
    @{{ success = $true; message = "Local port '{name}' created" }} | ConvertTo-Json
}} catch {{
    @{{ success = $false; error = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to add port", "raw": result}
    
    async def _remove_printer_port(self, name: str, **kwargs) -> Dict[str, Any]:
        """Remove a printer port"""
        script = f"""
try {{
    Remove-PrinterPort -Name '{name}' -ErrorAction Stop
    @{{ success = $true; message = "Port '{name}' removed" }} | ConvertTo-Json
}} catch {{
    @{{ success = $false; error = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to remove port", "raw": result}
    
    # ========== Network Printers ==========
    
    async def _add_network_printer(self, connection_name: str, **kwargs) -> Dict[str, Any]:
        """Add a network printer by UNC path"""
        script = f"""
try {{
    Add-Printer -ConnectionName '{connection_name}' -ErrorAction Stop
    @{{ success = $true; message = "Network printer '{connection_name}' added" }} | ConvertTo-Json
}} catch {{
    @{{ success = $false; error = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to add network printer", "raw": result}
    
    async def _discover_network_printers(self, subnet: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Discover network printers (searches for shared printers)"""
        script = """
$printers = @()

# Search local network for shared printers
$computers = Get-ADComputer -Filter * -ErrorAction SilentlyContinue
if (-not $computers) {
    # Fallback: try to find printers on broadcast
    $printers = Get-CimInstance -ClassName Win32_Printer -Filter "Network=True" -ErrorAction SilentlyContinue |
        Select-Object Name, ServerName, ShareName, PortName
}

@{
    discovered_printers = @($printers | ForEach-Object {
        @{
            name = $_.Name
            server = $_.ServerName
            share_name = $_.ShareName
            port = $_.PortName
        }
    })
    note = "Discovery limited to visible network printers. Use add_network_printer with specific UNC path for known printers."
} | ConvertTo-Json -Depth 3
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"discovered_printers": [], "raw": result}
    
    # ========== Print Test ==========
    
    async def _print_test_page(self, name: str, **kwargs) -> Dict[str, Any]:
        """Print a test page"""
        script = f"""
try {{
    $printer = Get-CimInstance -ClassName Win32_Printer -Filter "Name='{name}'"
    if ($printer) {{
        Invoke-CimMethod -InputObject $printer -MethodName PrintTestPage | Out-Null
        @{{ success = $true; message = "Test page sent to '{name}'" }} | ConvertTo-Json
    }} else {{
        @{{ success = $false; error = "Printer not found" }} | ConvertTo-Json
    }}
}} catch {{
    @{{ success = $false; error = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to print test page", "raw": result}
    
    # ========== Statistics ==========
    
    async def _get_print_statistics(self, **kwargs) -> Dict[str, Any]:
        """Get print statistics"""
        script = """
$printers = Get-Printer
$totalJobs = 0
$printers | ForEach-Object { $totalJobs += $_.JobCount }

$spooler = Get-Service Spooler
$spool_path = "$env:SystemRoot\\System32\\spool\\PRINTERS"
$spoolFiles = Get-ChildItem $spool_path -ErrorAction SilentlyContinue

@{
    total_printers = $printers.Count
    local_printers = ($printers | Where-Object { $_.Type -eq 'Local' }).Count
    network_printers = ($printers | Where-Object { $_.Type -eq 'Connection' }).Count
    shared_printers = ($printers | Where-Object { $_.Shared }).Count
    total_pending_jobs = $totalJobs
    spooler_status = $spooler.Status.ToString()
    spool_files = $spoolFiles.Count
    spool_size_bytes = ($spoolFiles | Measure-Object -Sum Length).Sum
} | ConvertTo-Json
"""
        result = await self._run_powershell(script)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to get statistics", "raw": result}
    
    async def _run_powershell(self, script: str) -> str:
        """Execute PowerShell script and return output"""
        try:
            process = await asyncio.create_subprocess_exec(
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy", "Bypass",
                "-Command", script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if stderr:
                logger.warning(f"PowerShell stderr: {stderr.decode()}")
            
            return stdout.decode().strip()
        except Exception as e:
            logger.error(f"PowerShell execution failed: {e}")
            raise
