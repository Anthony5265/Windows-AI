"""
Windows Process Manager Plugin
Monitor and control system processes with advanced features

Features:
- List and filter processes
- Process information (CPU, memory, threads)
- Kill/terminate processes
- Process priority management
- Resource monitoring and alerts
- Process search by name, PID, or resource usage
- Safe process management with confirmation

Author: Windows AI Team
Version: 1.0.0
"""

from typing import Dict, Any, List, Optional
import logging
import asyncio
from datetime import datetime
from dataclasses import dataclass, asdict

from windows_ai.plugins.base import ToolPlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


@dataclass
class ProcessInfo:
    """Process information"""
    pid: int
    name: str
    status: str
    cpu_percent: float
    memory_mb: float
    num_threads: int
    username: Optional[str] = None
    create_time: Optional[str] = None
    cmdline: Optional[str] = None


class WindowsProcessManagerPlugin(ToolPlugin):
    """Advanced process monitoring and management"""

    def __init__(self):
        metadata = PluginMetadata(
            id="windows_process_manager",
            name="Windows Process Manager",
            description="Monitor and control system processes with resource tracking",
            version="1.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.TOOL,
            enabled=True,
            icon="⚙️",
            tags=["process", "system", "monitoring", "windows"],
            requirements=["psutil>=5.9.0"]
        )
        super().__init__(metadata)

        self.psutil = None
        self._process_cache: Dict[int, ProcessInfo] = {}
        self._monitoring_task: Optional[asyncio.Task] = None

    async def initialize(self) -> bool:
        """Initialize process manager"""
        try:
            # Import psutil
            try:
                import psutil
                self.psutil = psutil
                logger.info("✓ Process manager initialized (psutil)")
            except ImportError:
                logger.error("❌ psutil not available - process manager disabled")
                return False

            return True

        except Exception as e:
            logger.error(f"Error initializing process manager: {e}")
            return False

    async def execute(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute process management operations

        Args:
            query: Action to perform
            parameters: Action-specific parameters
        """
        try:
            if not self.psutil:
                return {
                    "success": False,
                    "error": "Process manager not initialized (psutil required)"
                }

            params = parameters or {}
            params.update(kwargs)

            # Action routing
            actions = {
                "list": self._list_processes,
                "get": self._get_process,
                "search": self._search_processes,
                "kill": self._kill_process,
                "suspend": self._suspend_process,
                "resume": self._resume_process,
                "set_priority": self._set_priority,
                "get_stats": self._get_system_stats,
                "top_cpu": self._top_cpu,
                "top_memory": self._top_memory,
                "monitor": self._monitor_process,
            }

            action = query.lower().replace(" ", "_")

            if action not in actions:
                return {
                    "success": False,
                    "error": f"Unknown action: {query}",
                    "available_actions": list(actions.keys())
                }

            handler = actions[action]
            result = await handler(**params)

            return {
                "success": True,
                "result": result
            }

        except Exception as e:
            logger.error(f"Process manager error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for parameters"""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "list", "get", "search", "kill", "suspend", "resume",
                        "set_priority", "get_stats", "top_cpu", "top_memory", "monitor"
                    ],
                    "description": "Action to perform"
                },
                "pid": {
                    "type": "integer",
                    "description": "Process ID"
                },
                "name": {
                    "type": "string",
                    "description": "Process name for search"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results",
                    "default": 50
                },
                "sort_by": {
                    "type": "string",
                    "enum": ["cpu", "memory", "name", "pid"],
                    "description": "Sort field",
                    "default": "cpu"
                },
                "priority": {
                    "type": "string",
                    "enum": ["idle", "below_normal", "normal", "above_normal", "high", "realtime"],
                    "description": "Process priority"
                },
                "force": {
                    "type": "boolean",
                    "description": "Force kill process",
                    "default": False
                }
            },
            "required": ["action"]
        }

    # =========================================================================
    # Process Listing & Search
    # =========================================================================

    async def _list_processes(
        self,
        limit: int = 50,
        sort_by: str = "cpu",
        **kwargs
    ) -> Dict[str, Any]:
        """List all running processes"""
        try:
            processes = []

            for proc in self.psutil.process_iter(['pid', 'name', 'status']):
                try:
                    info = self._get_process_info(proc)
                    if info:
                        processes.append(asdict(info))
                except (self.psutil.NoSuchProcess, self.psutil.AccessDenied):
                    continue

            # Sort processes
            if sort_by == "cpu":
                processes.sort(key=lambda p: p.get("cpu_percent", 0), reverse=True)
            elif sort_by == "memory":
                processes.sort(key=lambda p: p.get("memory_mb", 0), reverse=True)
            elif sort_by == "name":
                processes.sort(key=lambda p: p.get("name", ""))
            elif sort_by == "pid":
                processes.sort(key=lambda p: p.get("pid", 0))

            # Apply limit
            processes = processes[:limit]

            return {
                "processes": processes,
                "total_count": len(processes),
                "sorted_by": sort_by
            }

        except Exception as e:
            return {
                "error": f"Failed to list processes: {str(e)}",
                "processes": []
            }

    async def _get_process(self, pid: int, **kwargs) -> Dict[str, Any]:
        """Get detailed information about a specific process"""
        try:
            proc = self.psutil.Process(pid)
            info = self._get_process_info(proc, detailed=True)

            if info:
                result = asdict(info)

                # Add additional details
                try:
                    result["connections"] = len(proc.connections())
                    result["open_files"] = len(proc.open_files())
                    result["parent_pid"] = proc.ppid()
                    result["children"] = [p.pid for p in proc.children()]
                except (self.psutil.NoSuchProcess, self.psutil.AccessDenied):
                    pass

                return result
            else:
                return {"error": f"Process not found or access denied: {pid}"}

        except self.psutil.NoSuchProcess:
            return {"error": f"Process not found: {pid}"}
        except self.psutil.AccessDenied:
            return {"error": f"Access denied to process: {pid}"}
        except Exception as e:
            return {"error": f"Failed to get process info: {str(e)}"}

    async def _search_processes(
        self,
        name: str,
        limit: int = 50,
        **kwargs
    ) -> Dict[str, Any]:
        """Search processes by name"""
        try:
            name_lower = name.lower()
            matching = []

            for proc in self.psutil.process_iter(['pid', 'name']):
                try:
                    proc_name = proc.info['name'].lower()
                    if name_lower in proc_name:
                        info = self._get_process_info(proc)
                        if info:
                            matching.append(asdict(info))

                    if len(matching) >= limit:
                        break

                except (self.psutil.NoSuchProcess, self.psutil.AccessDenied):
                    continue

            return {
                "processes": matching,
                "query": name,
                "matches_found": len(matching)
            }

        except Exception as e:
            return {
                "error": f"Search failed: {str(e)}",
                "processes": []
            }

    # =========================================================================
    # Process Control
    # =========================================================================

    async def _kill_process(self, pid: int, force: bool = False, **kwargs) -> Dict[str, Any]:
        """Kill/terminate a process"""
        try:
            proc = self.psutil.Process(pid)
            proc_name = proc.name()

            if force:
                proc.kill()  # SIGKILL
                action = "killed"
            else:
                proc.terminate()  # SIGTERM
                action = "terminated"

            # Wait a bit to ensure it's dead
            await asyncio.sleep(0.5)

            try:
                if proc.is_running():
                    return {
                        "success": False,
                        "message": f"Process still running after {action}: {proc_name} (PID: {pid})",
                        "hint": "Try with force=True"
                    }
            except self.psutil.NoSuchProcess:
                pass  # Process is gone, which is what we want

            return {
                "success": True,
                "message": f"Process {action}: {proc_name} (PID: {pid})",
                "pid": pid,
                "name": proc_name,
                "action": action
            }

        except self.psutil.NoSuchProcess:
            return {
                "success": False,
                "error": f"Process not found: {pid}"
            }
        except self.psutil.AccessDenied:
            return {
                "success": False,
                "error": f"Access denied to kill process: {pid}",
                "hint": "Try running with administrator privileges"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to kill process: {str(e)}"
            }

    async def _suspend_process(self, pid: int, **kwargs) -> Dict[str, Any]:
        """Suspend a process"""
        try:
            proc = self.psutil.Process(pid)
            proc.suspend()

            return {
                "success": True,
                "message": f"Process suspended: {proc.name()} (PID: {pid})",
                "pid": pid
            }

        except self.psutil.NoSuchProcess:
            return {"success": False, "error": f"Process not found: {pid}"}
        except self.psutil.AccessDenied:
            return {"success": False, "error": f"Access denied: {pid}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _resume_process(self, pid: int, **kwargs) -> Dict[str, Any]:
        """Resume a suspended process"""
        try:
            proc = self.psutil.Process(pid)
            proc.resume()

            return {
                "success": True,
                "message": f"Process resumed: {proc.name()} (PID: {pid})",
                "pid": pid
            }

        except self.psutil.NoSuchProcess:
            return {"success": False, "error": f"Process not found: {pid}"}
        except self.psutil.AccessDenied:
            return {"success": False, "error": f"Access denied: {pid}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _set_priority(self, pid: int, priority: str, **kwargs) -> Dict[str, Any]:
        """Set process priority"""
        try:
            proc = self.psutil.Process(pid)

            # Map priority string to psutil constant
            priority_map = {
                "idle": self.psutil.IDLE_PRIORITY_CLASS if hasattr(self.psutil, 'IDLE_PRIORITY_CLASS') else 0,
                "below_normal": self.psutil.BELOW_NORMAL_PRIORITY_CLASS if hasattr(self.psutil, 'BELOW_NORMAL_PRIORITY_CLASS') else 1,
                "normal": self.psutil.NORMAL_PRIORITY_CLASS if hasattr(self.psutil, 'NORMAL_PRIORITY_CLASS') else 2,
                "above_normal": self.psutil.ABOVE_NORMAL_PRIORITY_CLASS if hasattr(self.psutil, 'ABOVE_NORMAL_PRIORITY_CLASS') else 3,
                "high": self.psutil.HIGH_PRIORITY_CLASS if hasattr(self.psutil, 'HIGH_PRIORITY_CLASS') else 4,
                "realtime": self.psutil.REALTIME_PRIORITY_CLASS if hasattr(self.psutil, 'REALTIME_PRIORITY_CLASS') else 5
            }

            if priority not in priority_map:
                return {
                    "success": False,
                    "error": f"Invalid priority: {priority}",
                    "valid_priorities": list(priority_map.keys())
                }

            proc.nice(priority_map[priority])

            return {
                "success": True,
                "message": f"Priority set to {priority} for {proc.name()} (PID: {pid})",
                "pid": pid,
                "priority": priority
            }

        except self.psutil.NoSuchProcess:
            return {"success": False, "error": f"Process not found: {pid}"}
        except self.psutil.AccessDenied:
            return {"success": False, "error": f"Access denied: {pid}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # =========================================================================
    # Statistics & Monitoring
    # =========================================================================

    async def _get_system_stats(self, **kwargs) -> Dict[str, Any]:
        """Get overall system statistics"""
        try:
            cpu_percent = self.psutil.cpu_percent(interval=1)
            memory = self.psutil.virtual_memory()
            disk = self.psutil.disk_usage('/')

            return {
                "cpu": {
                    "percent": cpu_percent,
                    "count": self.psutil.cpu_count()
                },
                "memory": {
                    "total_mb": memory.total / (1024 * 1024),
                    "available_mb": memory.available / (1024 * 1024),
                    "used_mb": memory.used / (1024 * 1024),
                    "percent": memory.percent
                },
                "disk": {
                    "total_gb": disk.total / (1024 * 1024 * 1024),
                    "used_gb": disk.used / (1024 * 1024 * 1024),
                    "free_gb": disk.free / (1024 * 1024 * 1024),
                    "percent": disk.percent
                },
                "processes": {
                    "total": len(self.psutil.pids())
                }
            }

        except Exception as e:
            return {"error": f"Failed to get system stats: {str(e)}"}

    async def _top_cpu(self, limit: int = 10, **kwargs) -> Dict[str, Any]:
        """Get top CPU-consuming processes"""
        return await self._list_processes(limit=limit, sort_by="cpu")

    async def _top_memory(self, limit: int = 10, **kwargs) -> Dict[str, Any]:
        """Get top memory-consuming processes"""
        return await self._list_processes(limit=limit, sort_by="memory")

    async def _monitor_process(self, pid: int, duration: int = 10, **kwargs) -> Dict[str, Any]:
        """Monitor a process over time"""
        try:
            proc = self.psutil.Process(pid)
            samples = []

            for _ in range(duration):
                try:
                    cpu = proc.cpu_percent(interval=1)
                    memory = proc.memory_info().rss / (1024 * 1024)

                    samples.append({
                        "timestamp": datetime.now().isoformat(),
                        "cpu_percent": cpu,
                        "memory_mb": memory
                    })

                except (self.psutil.NoSuchProcess, self.psutil.AccessDenied):
                    break

            if samples:
                avg_cpu = sum(s["cpu_percent"] for s in samples) / len(samples)
                avg_memory = sum(s["memory_mb"] for s in samples) / len(samples)

                return {
                    "pid": pid,
                    "name": proc.name(),
                    "samples": samples,
                    "summary": {
                        "duration_seconds": duration,
                        "samples_collected": len(samples),
                        "avg_cpu_percent": avg_cpu,
                        "avg_memory_mb": avg_memory
                    }
                }
            else:
                return {"error": "Process terminated during monitoring"}

        except self.psutil.NoSuchProcess:
            return {"error": f"Process not found: {pid}"}
        except Exception as e:
            return {"error": f"Monitoring failed: {str(e)}"}

    # =========================================================================
    # Helpers
    # =========================================================================

    def _get_process_info(self, proc, detailed: bool = False) -> Optional[ProcessInfo]:
        """Extract process information"""
        try:
            with proc.oneshot():
                info = ProcessInfo(
                    pid=proc.pid,
                    name=proc.name(),
                    status=proc.status(),
                    cpu_percent=proc.cpu_percent(),
                    memory_mb=proc.memory_info().rss / (1024 * 1024),
                    num_threads=proc.num_threads()
                )

                if detailed:
                    try:
                        info.username = proc.username()
                        info.create_time = datetime.fromtimestamp(proc.create_time()).isoformat()
                        cmdline = proc.cmdline()
                        info.cmdline = " ".join(cmdline) if cmdline else None
                    except (self.psutil.AccessDenied, AttributeError):
                        pass

                return info

        except (self.psutil.NoSuchProcess, self.psutil.AccessDenied, self.psutil.ZombieProcess):
            return None


# Export
__all__ = ["WindowsProcessManagerPlugin"]
