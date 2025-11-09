"""
Windows Management Instrumentation (WMI) Module
System monitoring, hardware info, process management via WMI
"""
from typing import Dict, Any, List, Optional
import logging
import platform

logger = logging.getLogger(__name__)

# Try to import Windows-specific WMI module
IS_WINDOWS = platform.system() == "Windows"
if IS_WINDOWS:
    try:
        import wmi
        WMI_AVAILABLE = True
    except ImportError:
        WMI_AVAILABLE = False
        logger.warning("WMI module not available. Install with: pip install WMI")
else:
    WMI_AVAILABLE = False


class WMIManager:
    """Production WMI access for Windows system management"""

    def __init__(self):
        self.is_available = WMI_AVAILABLE
        self.connection = None

        if self.is_available:
            try:
                self.connection = wmi.WMI()
            except Exception as e:
                logger.error(f"WMI connection error: {e}")
                self.is_available = False

    def get_computer_info(self) -> Dict[str, Any]:
        """Get computer system information"""
        if not self.is_available:
            return {
                "status": "error",
                "message": "WMI not available"
            }

        try:
            computer = self.connection.Win32_ComputerSystem()[0]

            return {
                "status": "success",
                "name": computer.Name,
                "manufacturer": computer.Manufacturer,
                "model": computer.Model,
                "domain": computer.Domain,
                "total_physical_memory": computer.TotalPhysicalMemory,
                "number_of_processors": computer.NumberOfProcessors,
                "system_type": computer.SystemType,
                "username": computer.UserName
            }

        except Exception as e:
            logger.error(f"WMI get computer info error: {e}")
            return {"status": "error", "message": str(e)}

    def get_os_info(self) -> Dict[str, Any]:
        """Get operating system information"""
        if not self.is_available:
            return {
                "status": "error",
                "message": "WMI not available"
            }

        try:
            os_info = self.connection.Win32_OperatingSystem()[0]

            return {
                "status": "success",
                "caption": os_info.Caption,
                "version": os_info.Version,
                "build_number": os_info.BuildNumber,
                "os_architecture": os_info.OSArchitecture,
                "install_date": str(os_info.InstallDate) if os_info.InstallDate else None,
                "last_boot_up_time": str(os_info.LastBootUpTime) if os_info.LastBootUpTime else None,
                "system_directory": os_info.SystemDirectory,
                "windows_directory": os_info.WindowsDirectory,
                "free_physical_memory": os_info.FreePhysicalMemory,
                "total_visible_memory_size": os_info.TotalVisibleMemorySize
            }

        except Exception as e:
            logger.error(f"WMI get OS info error: {e}")
            return {"status": "error", "message": str(e)}

    def get_processor_info(self) -> Dict[str, Any]:
        """Get processor information"""
        if not self.is_available:
            return {
                "status": "error",
                "message": "WMI not available"
            }

        try:
            processors = []
            for proc in self.connection.Win32_Processor():
                processors.append({
                    "name": proc.Name,
                    "manufacturer": proc.Manufacturer,
                    "max_clock_speed": proc.MaxClockSpeed,
                    "number_of_cores": proc.NumberOfCores,
                    "number_of_logical_processors": proc.NumberOfLogicalProcessors,
                    "processor_id": proc.ProcessorId,
                    "architecture": proc.Architecture,
                    "l2_cache_size": proc.L2CacheSize,
                    "l3_cache_size": proc.L3CacheSize
                })

            return {
                "status": "success",
                "processors": processors,
                "count": len(processors)
            }

        except Exception as e:
            logger.error(f"WMI get processor info error: {e}")
            return {"status": "error", "message": str(e)}

    def get_memory_info(self) -> Dict[str, Any]:
        """Get physical memory information"""
        if not self.is_available:
            return {
                "status": "error",
                "message": "WMI not available"
            }

        try:
            memory_modules = []
            for mem in self.connection.Win32_PhysicalMemory():
                memory_modules.append({
                    "capacity": mem.Capacity,
                    "speed": mem.Speed,
                    "manufacturer": mem.Manufacturer,
                    "part_number": mem.PartNumber,
                    "serial_number": mem.SerialNumber,
                    "device_locator": mem.DeviceLocator,
                    "memory_type": mem.MemoryType,
                    "form_factor": mem.FormFactor
                })

            return {
                "status": "success",
                "memory_modules": memory_modules,
                "count": len(memory_modules),
                "total_capacity": sum(int(m["capacity"]) for m in memory_modules if m["capacity"])
            }

        except Exception as e:
            logger.error(f"WMI get memory info error: {e}")
            return {"status": "error", "message": str(e)}

    def get_disk_drives(self) -> Dict[str, Any]:
        """Get disk drive information"""
        if not self.is_available:
            return {
                "status": "error",
                "message": "WMI not available"
            }

        try:
            drives = []
            for drive in self.connection.Win32_DiskDrive():
                drives.append({
                    "model": drive.Model,
                    "size": drive.Size,
                    "interface_type": drive.InterfaceType,
                    "media_type": drive.MediaType,
                    "partitions": drive.Partitions,
                    "serial_number": drive.SerialNumber,
                    "device_id": drive.DeviceID
                })

            return {
                "status": "success",
                "drives": drives,
                "count": len(drives)
            }

        except Exception as e:
            logger.error(f"WMI get disk drives error: {e}")
            return {"status": "error", "message": str(e)}

    def get_logical_disks(self) -> Dict[str, Any]:
        """Get logical disk (partition) information"""
        if not self.is_available:
            return {
                "status": "error",
                "message": "WMI not available"
            }

        try:
            disks = []
            for disk in self.connection.Win32_LogicalDisk():
                disks.append({
                    "device_id": disk.DeviceID,
                    "volume_name": disk.VolumeName,
                    "file_system": disk.FileSystem,
                    "size": disk.Size,
                    "free_space": disk.FreeSpace,
                    "drive_type": disk.DriveType,
                    "volume_serial_number": disk.VolumeSerialNumber
                })

            return {
                "status": "success",
                "logical_disks": disks,
                "count": len(disks)
            }

        except Exception as e:
            logger.error(f"WMI get logical disks error: {e}")
            return {"status": "error", "message": str(e)}

    def get_network_adapters(self) -> Dict[str, Any]:
        """Get network adapter information"""
        if not self.is_available:
            return {
                "status": "error",
                "message": "WMI not available"
            }

        try:
            adapters = []
            for adapter in self.connection.Win32_NetworkAdapterConfiguration(IPEnabled=True):
                adapters.append({
                    "description": adapter.Description,
                    "mac_address": adapter.MACAddress,
                    "ip_addresses": adapter.IPAddress,
                    "ip_subnets": adapter.IPSubnet,
                    "default_gateway": adapter.DefaultIPGateway,
                    "dns_servers": adapter.DNSServerSearchOrder,
                    "dhcp_enabled": adapter.DHCPEnabled,
                    "dhcp_server": adapter.DHCPServer
                })

            return {
                "status": "success",
                "adapters": adapters,
                "count": len(adapters)
            }

        except Exception as e:
            logger.error(f"WMI get network adapters error: {e}")
            return {"status": "error", "message": str(e)}

    def get_running_processes(self, name_filter: str = None) -> Dict[str, Any]:
        """Get running process information"""
        if not self.is_available:
            return {
                "status": "error",
                "message": "WMI not available"
            }

        try:
            processes = []
            query = self.connection.Win32_Process()

            if name_filter:
                query = self.connection.Win32_Process(Name=name_filter)

            for process in query:
                processes.append({
                    "name": process.Name,
                    "process_id": process.ProcessId,
                    "parent_process_id": process.ParentProcessId,
                    "executable_path": process.ExecutablePath,
                    "command_line": process.CommandLine,
                    "creation_date": str(process.CreationDate) if process.CreationDate else None,
                    "working_set_size": process.WorkingSetSize,
                    "thread_count": process.ThreadCount
                })

            return {
                "status": "success",
                "processes": processes,
                "count": len(processes)
            }

        except Exception as e:
            logger.error(f"WMI get processes error: {e}")
            return {"status": "error", "message": str(e)}

    def get_services(self, state_filter: str = None) -> Dict[str, Any]:
        """Get Windows services information"""
        if not self.is_available:
            return {
                "status": "error",
                "message": "WMI not available"
            }

        try:
            services = []
            query = self.connection.Win32_Service()

            if state_filter:
                query = self.connection.Win32_Service(State=state_filter)

            for service in query:
                services.append({
                    "name": service.Name,
                    "display_name": service.DisplayName,
                    "state": service.State,
                    "status": service.Status,
                    "start_mode": service.StartMode,
                    "service_type": service.ServiceType,
                    "path_name": service.PathName,
                    "description": service.Description
                })

            return {
                "status": "success",
                "services": services,
                "count": len(services)
            }

        except Exception as e:
            logger.error(f"WMI get services error: {e}")
            return {"status": "error", "message": str(e)}

    def start_service(self, service_name: str) -> Dict[str, Any]:
        """Start a Windows service"""
        if not self.is_available:
            return {
                "status": "error",
                "message": "WMI not available"
            }

        try:
            service = self.connection.Win32_Service(Name=service_name)[0]
            result = service.StartService()

            return {
                "status": "success" if result[0] == 0 else "error",
                "return_code": result[0],
                "message": "Service started" if result[0] == 0 else f"Error code: {result[0]}"
            }

        except IndexError:
            return {
                "status": "error",
                "message": f"Service not found: {service_name}"
            }
        except Exception as e:
            logger.error(f"WMI start service error: {e}")
            return {"status": "error", "message": str(e)}

    def stop_service(self, service_name: str) -> Dict[str, Any]:
        """Stop a Windows service"""
        if not self.is_available:
            return {
                "status": "error",
                "message": "WMI not available"
            }

        try:
            service = self.connection.Win32_Service(Name=service_name)[0]
            result = service.StopService()

            return {
                "status": "success" if result[0] == 0 else "error",
                "return_code": result[0],
                "message": "Service stopped" if result[0] == 0 else f"Error code: {result[0]}"
            }

        except IndexError:
            return {
                "status": "error",
                "message": f"Service not found: {service_name}"
            }
        except Exception as e:
            logger.error(f"WMI stop service error: {e}")
            return {"status": "error", "message": str(e)}
