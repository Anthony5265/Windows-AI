"""
System Information Plugin

Provides system information and monitoring capabilities.
"""

from typing import Dict, Any, Optional
import psutil
import platform
import logging
from datetime import datetime

from windows_ai.plugins.base import ToolPlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class SystemInfoPlugin(ToolPlugin):
    """
    Provides detailed system information and monitoring.
    """

    def __init__(self):
        super().__init__(self.get_metadata())

    @staticmethod
    def get_metadata() -> PluginMetadata:
        return PluginMetadata(
            id="system_info",
            name="System Information",
            description="Get detailed system information and resource usage",
            version="1.0.0",
            author="Windows AI",
            plugin_type=PluginType.TOOL,
            icon="💻",
            tags=["system", "monitoring", "hardware"]
        )

    async def initialize(self) -> bool:
        """Initialize the system info plugin"""
        self._initialized = True
        logger.info("System Info plugin initialized")
        return True

    async def execute(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get system information.

        Args:
            query: Type of info to get: "all", "cpu", "memory", "disk", "network"
            parameters: Optional parameters

        Returns:
            System information
        """
        try:
            info_type = query.lower() if query else "all"

            result = {}

            if info_type in ["all", "basic"]:
                result["basic"] = {
                    "platform": platform.system(),
                    "platform_release": platform.release(),
                    "platform_version": platform.version(),
                    "architecture": platform.machine(),
                    "processor": platform.processor(),
                    "hostname": platform.node(),
                    "python_version": platform.python_version()
                }

            if info_type in ["all", "cpu"]:
                result["cpu"] = {
                    "physical_cores": psutil.cpu_count(logical=False),
                    "total_cores": psutil.cpu_count(logical=True),
                    "max_frequency": psutil.cpu_freq().max if psutil.cpu_freq() else None,
                    "current_frequency": psutil.cpu_freq().current if psutil.cpu_freq() else None,
                    "cpu_usage_percent": psutil.cpu_percent(interval=1),
                    "cpu_usage_per_core": psutil.cpu_percent(interval=1, percpu=True)
                }

            if info_type in ["all", "memory"]:
                memory = psutil.virtual_memory()
                swap = psutil.swap_memory()

                result["memory"] = {
                    "total": memory.total,
                    "total_gb": round(memory.total / (1024 ** 3), 2),
                    "available": memory.available,
                    "available_gb": round(memory.available / (1024 ** 3), 2),
                    "used": memory.used,
                    "used_gb": round(memory.used / (1024 ** 3), 2),
                    "percent": memory.percent,
                    "swap_total_gb": round(swap.total / (1024 ** 3), 2),
                    "swap_used_gb": round(swap.used / (1024 ** 3), 2),
                    "swap_percent": swap.percent
                }

            if info_type in ["all", "disk"]:
                partitions = psutil.disk_partitions()
                disk_info = []

                for partition in partitions:
                    try:
                        usage = psutil.disk_usage(partition.mountpoint)
                        disk_info.append({
                            "device": partition.device,
                            "mountpoint": partition.mountpoint,
                            "fstype": partition.fstype,
                            "total_gb": round(usage.total / (1024 ** 3), 2),
                            "used_gb": round(usage.used / (1024 ** 3), 2),
                            "free_gb": round(usage.free / (1024 ** 3), 2),
                            "percent": usage.percent
                        })
                    except PermissionError:
                        continue

                result["disk"] = disk_info

            if info_type in ["all", "network"]:
                net_io = psutil.net_io_counters()
                interfaces = psutil.net_if_addrs()

                result["network"] = {
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_sent_mb": round(net_io.bytes_sent / (1024 ** 2), 2),
                    "bytes_recv": net_io.bytes_recv,
                    "bytes_recv_mb": round(net_io.bytes_recv / (1024 ** 2), 2),
                    "packets_sent": net_io.packets_sent,
                    "packets_recv": net_io.packets_recv,
                    "interfaces": list(interfaces.keys())
                }

            if info_type in ["all", "processes"]:
                # Get top processes by CPU usage
                processes = []
                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                    try:
                        proc_info = proc.info
                        processes.append({
                            "pid": proc_info['pid'],
                            "name": proc_info['name'],
                            "cpu_percent": proc_info['cpu_percent'],
                            "memory_percent": round(proc_info['memory_percent'], 2)
                        })
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

                # Sort by CPU usage and get top 10
                processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
                result["top_processes"] = processes[:10]

            return {
                "success": True,
                "result": result,
                "message": f"Retrieved {info_type} system information",
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "info_type": info_type
                }
            }

        except Exception as e:
            logger.error(f"System info error: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Error retrieving system information"
            }

    def get_schema(self) -> Dict[str, Any]:
        """Return parameter schema"""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Type of system information to retrieve",
                    "enum": ["all", "basic", "cpu", "memory", "disk", "network", "processes"],
                    "default": "all"
                }
            }
        }

    def get_function_definition(self) -> Dict[str, Any]:
        """Return OpenAI function definition"""
        return {
            "name": "get_system_info",
            "description": "Get detailed system information including CPU, memory, disk, network status, and running processes. Use this when the user asks about system resources, performance, or hardware.",
            "parameters": self.get_schema()
        }


plugin = SystemInfoPlugin()
