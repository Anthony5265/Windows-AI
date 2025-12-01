"""
Process and System Monitoring Module
Cross-platform process monitoring using psutil
"""
from typing import Dict, Any, List, Optional
import logging
import platform

logger = logging.getLogger(__name__)

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil not available. Install with: pip install psutil")


class ProcessMonitor:
    """Production process and system monitoring"""

    def __init__(self):
        self.is_available = PSUTIL_AVAILABLE

    def get_system_stats(self) -> Dict[str, Any]:
        """Get overall system statistics"""
        if not self.is_available:
            return {
                "status": "error",
                "message": "psutil not available"
            }

        try:
            cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            disk = psutil.disk_usage('/')

            return {
                "status": "success",
                "cpu": {
                    "percent": psutil.cpu_percent(interval=0.1),
                    "per_cpu": cpu_percent,
                    "count_logical": psutil.cpu_count(logical=True),
                    "count_physical": psutil.cpu_count(logical=False)
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "used": memory.used,
                    "percent": memory.percent
                },
                "swap": {
                    "total": swap.total,
                    "used": swap.used,
                    "free": swap.free,
                    "percent": swap.percent
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": disk.percent
                }
            }

        except Exception as e:
            logger.error(f"Get system stats error: {e}")
            return {"status": "error", "message": str(e)}

    def get_process_list(self, sort_by: str = "memory") -> Dict[str, Any]:
        """
        Get list of running processes

        Args:
            sort_by: Sort criterion (cpu, memory, pid, name)

        Returns:
            Dict with process list
        """
        if not self.is_available:
            return {
                "status": "error",
                "message": "psutil not available"
            }

        try:
            processes = []

            for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'status']):
                try:
                    pinfo = proc.info
                    processes.append({
                        "pid": pinfo['pid'],
                        "name": pinfo['name'],
                        "username": pinfo['username'],
                        "cpu_percent": pinfo['cpu_percent'],
                        "memory_percent": pinfo['memory_percent'],
                        "status": pinfo['status']
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            # Sort processes
            if sort_by == "cpu":
                processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
            elif sort_by == "memory":
                processes.sort(key=lambda x: x['memory_percent'] or 0, reverse=True)
            elif sort_by == "pid":
                processes.sort(key=lambda x: x['pid'])
            elif sort_by == "name":
                processes.sort(key=lambda x: x['name'] or "")

            return {
                "status": "success",
                "processes": processes,
                "count": len(processes)
            }

        except Exception as e:
            logger.error(f"Get process list error: {e}")
            return {"status": "error", "message": str(e)}

    def get_process_info(self, pid: int) -> Dict[str, Any]:
        """Get detailed information about a specific process"""
        if not self.is_available:
            return {
                "status": "error",
                "message": "psutil not available"
            }

        try:
            proc = psutil.Process(pid)

            with proc.oneshot():
                return {
                    "status": "success",
                    "pid": proc.pid,
                    "name": proc.name(),
                    "exe": proc.exe(),
                    "cwd": proc.cwd(),
                    "cmdline": proc.cmdline(),
                    "status": proc.status(),
                    "username": proc.username(),
                    "create_time": proc.create_time(),
                    "cpu_percent": proc.cpu_percent(interval=0.1),
                    "cpu_times": proc.cpu_times()._asdict(),
                    "memory_info": proc.memory_info()._asdict(),
                    "memory_percent": proc.memory_percent(),
                    "num_threads": proc.num_threads(),
                    "num_fds": proc.num_fds() if hasattr(proc, 'num_fds') else None,
                    "open_files": [f._asdict() for f in proc.open_files()],
                    "connections": [c._asdict() for c in proc.connections()],
                    "nice": proc.nice()
                }

        except psutil.NoSuchProcess:
            return {
                "status": "error",
                "message": f"Process {pid} not found"
            }
        except psutil.AccessDenied:
            return {
                "status": "error",
                "message": f"Access denied to process {pid}"
            }
        except Exception as e:
            logger.error(f"Get process info error: {e}")
            return {"status": "error", "message": str(e)}

    def kill_process(self, pid: int, force: bool = False) -> Dict[str, Any]:
        """
        Kill a process

        Args:
            pid: Process ID
            force: Use SIGKILL instead of SIGTERM (Unix) or TerminateProcess (Windows)

        Returns:
            Dict with operation result
        """
        if not self.is_available:
            return {
                "status": "error",
                "message": "psutil not available"
            }

        try:
            proc = psutil.Process(pid)
            proc_name = proc.name()

            if force:
                proc.kill()
            else:
                proc.terminate()

            return {
                "status": "success",
                "message": f"Process {pid} ({proc_name}) {'killed' if force else 'terminated'}"
            }

        except psutil.NoSuchProcess:
            return {
                "status": "error",
                "message": f"Process {pid} not found"
            }
        except psutil.AccessDenied:
            return {
                "status": "error",
                "message": f"Access denied to process {pid}"
            }
        except Exception as e:
            logger.error(f"Kill process error: {e}")
            return {"status": "error", "message": str(e)}

    def find_processes_by_name(self, name: str) -> Dict[str, Any]:
        """Find processes by name"""
        if not self.is_available:
            return {
                "status": "error",
                "message": "psutil not available"
            }

        try:
            matching = []

            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if name.lower() in proc.info['name'].lower():
                        matching.append({
                            "pid": proc.info['pid'],
                            "name": proc.info['name']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            return {
                "status": "success",
                "processes": matching,
                "count": len(matching)
            }

        except Exception as e:
            logger.error(f"Find processes error: {e}")
            return {"status": "error", "message": str(e)}

    def get_network_connections(self, kind: str = "inet") -> Dict[str, Any]:
        """
        Get network connections

        Args:
            kind: Connection kind (inet, inet4, inet6, tcp, tcp4, tcp6, udp, udp4, udp6, unix, all)

        Returns:
            Dict with connection list
        """
        if not self.is_available:
            return {
                "status": "error",
                "message": "psutil not available"
            }

        try:
            connections = []

            for conn in psutil.net_connections(kind=kind):
                connections.append({
                    "fd": conn.fd,
                    "family": conn.family,
                    "type": conn.type,
                    "local_address": f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None,
                    "remote_address": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                    "status": conn.status,
                    "pid": conn.pid
                })

            return {
                "status": "success",
                "connections": connections,
                "count": len(connections)
            }

        except psutil.AccessDenied:
            return {
                "status": "error",
                "message": "Access denied. Administrator/root privileges required."
            }
        except Exception as e:
            logger.error(f"Get network connections error: {e}")
            return {"status": "error", "message": str(e)}

    def get_disk_partitions(self) -> Dict[str, Any]:
        """Get disk partition information"""
        if not self.is_available:
            return {
                "status": "error",
                "message": "psutil not available"
            }

        try:
            partitions = []

            for part in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    partitions.append({
                        "device": part.device,
                        "mountpoint": part.mountpoint,
                        "fstype": part.fstype,
                        "opts": part.opts,
                        "total": usage.total,
                        "used": usage.used,
                        "free": usage.free,
                        "percent": usage.percent
                    })
                except PermissionError:
                    partitions.append({
                        "device": part.device,
                        "mountpoint": part.mountpoint,
                        "fstype": part.fstype,
                        "opts": part.opts,
                        "error": "Permission denied"
                    })

            return {
                "status": "success",
                "partitions": partitions,
                "count": len(partitions)
            }

        except Exception as e:
            logger.error(f"Get disk partitions error: {e}")
            return {"status": "error", "message": str(e)}

    def get_network_stats(self) -> Dict[str, Any]:
        """Get network I/O statistics"""
        if not self.is_available:
            return {
                "status": "error",
                "message": "psutil not available"
            }

        try:
            net_io = psutil.net_io_counters()

            return {
                "status": "success",
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv,
                "errin": net_io.errin,
                "errout": net_io.errout,
                "dropin": net_io.dropin,
                "dropout": net_io.dropout
            }

        except Exception as e:
            logger.error(f"Get network stats error: {e}")
            return {"status": "error", "message": str(e)}

    def monitor_process_resource_usage(self, pid: int, duration: int = 10,
                                      interval: float = 1.0) -> Dict[str, Any]:
        """
        Monitor process resource usage over time

        Args:
            pid: Process ID
            duration: Monitoring duration in seconds
            interval: Sampling interval in seconds

        Returns:
            Dict with time series data
        """
        if not self.is_available:
            return {
                "status": "error",
                "message": "psutil not available"
            }

        try:
            import time

            proc = psutil.Process(pid)
            samples = []

            for _ in range(int(duration / interval)):
                try:
                    with proc.oneshot():
                        samples.append({
                            "timestamp": time.time(),
                            "cpu_percent": proc.cpu_percent(interval=interval),
                            "memory_percent": proc.memory_percent(),
                            "memory_mb": proc.memory_info().rss / (1024 * 1024),
                            "num_threads": proc.num_threads()
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    break

            return {
                "status": "success",
                "pid": pid,
                "samples": samples,
                "count": len(samples)
            }

        except psutil.NoSuchProcess:
            return {
                "status": "error",
                "message": f"Process {pid} not found"
            }
        except Exception as e:
            logger.error(f"Monitor process error: {e}")
            return {"status": "error", "message": str(e)}
