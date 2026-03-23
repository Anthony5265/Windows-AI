"""
Process Management Plugin - Monitor and control Windows processes
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class ProcessManagementPlugin(IntegrationPlugin):
    """Plugin for comprehensive Windows process management"""

    def __init__(self):
        metadata = PluginMetadata(
            id="windows.process-management",
            name="Process Management",
            description="Monitor, control, and analyze Windows processes",
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["process", "task", "management", "monitoring", "windows"],
        )
        super().__init__(metadata)

    async def initialize(self) -> bool:
        """Initialize process management plugin"""
        try:
            result = await self._run_powershell("Get-Process | Select-Object -First 1 | ConvertTo-Json")
            logger.info("Process Management plugin initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Process Management: {e}")
            return False

    async def _run_powershell(self, script: str, timeout: int = 60) -> Dict[str, Any]:
        """Execute a PowerShell command"""
        try:
            process = await asyncio.create_subprocess_exec(
                "powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            return {
                "success": process.returncode == 0,
                "output": stdout.decode("utf-8", errors="replace").strip(),
                "error": stderr.decode("utf-8", errors="replace").strip() if stderr else None
            }
        except asyncio.TimeoutError:
            return {"success": False, "error": f"Command timed out after {timeout} seconds"}
        except Exception as e:
            return {"success": False, "error": str(e)}


    async def connect(self, credentials: Dict[str, str]) -> bool:
        """Connect to the service"""
        return True

    async def disconnect(self) -> bool:
        """Disconnect from the service"""
        return True

    async def execute(self, action: str = "list_processes", params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute process management actions"""
        params = params or {}
        
        actions = {
            # Process listing
            "status": self._get_status,
            "list_processes": self._list_processes,
            "get_process": self._get_process,
            "get_process_by_name": self._get_process_by_name,
            "get_process_by_id": self._get_process_by_id,
            
            # Process control
            "start_process": self._start_process,
            "stop_process": self._stop_process,
            "kill_process": self._kill_process,
            "restart_process": self._restart_process,
            
            # Process priority
            "get_priority": self._get_priority,
            "set_priority": self._set_priority,
            
            # Process affinity
            "get_affinity": self._get_affinity,
            "set_affinity": self._set_affinity,
            
            # Process details
            "get_modules": self._get_modules,
            "get_threads": self._get_threads,
            "get_handles": self._get_handles,
            "get_memory_info": self._get_memory_info,
            "get_cpu_usage": self._get_cpu_usage,
            
            # Process tree
            "get_parent": self._get_parent,
            "get_children": self._get_children,
            "get_process_tree": self._get_process_tree,
            
            # Process search
            "find_by_window": self._find_by_window,
            "find_by_port": self._find_by_port,
            "find_by_path": self._find_by_path,
            
            # System info
            "get_top_cpu": self._get_top_cpu,
            "get_top_memory": self._get_top_memory,
            "get_process_count": self._get_process_count,
            
            # Wait operations
            "wait_for_exit": self._wait_for_exit,
            "wait_for_idle": self._wait_for_idle
        }
        
        if action not in actions:
            return {"success": False, "error": f"Unknown action: {action}. Available: {list(actions.keys())}"}
        
        try:
            return await actions[action](params)
        except Exception as e:
            logger.error(f"Process action '{action}' failed: {e}")
            return {"success": False, "error": str(e)}

    async def _get_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get process management status"""
        script = """
        $procs = Get-Process
        @{
            TotalProcesses = $procs.Count
            TotalThreads = ($procs | Measure-Object -Property Threads -Sum).Sum
            TotalMemoryMB = [math]::Round(($procs | Measure-Object -Property WorkingSet64 -Sum).Sum / 1MB, 2)
            TopCPU = ($procs | Sort-Object CPU -Descending | Select-Object -First 5 | Select-Object Name, Id, CPU)
        } | ConvertTo-Json -Depth 5
        """
        return await self._run_powershell(script)

    async def _list_processes(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List all running processes"""
        sort_by = params.get("sort_by", "Name")
        limit = params.get("limit", 100)
        
        script = f"""
        Get-Process | Sort-Object {sort_by} | Select-Object -First {limit} |
        Select-Object Name, Id, CPU, 
            @{{N='MemoryMB';E={{[math]::Round($_.WorkingSet64/1MB,2)}}}},
            @{{N='Threads';E={{$_.Threads.Count}}}},
            StartTime, Path |
        ConvertTo-Json -Depth 3
        """
        return await self._run_powershell(script)

    async def _get_process(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get process by name or ID"""
        name = params.get("name")
        pid = params.get("pid")
        
        if pid:
            filter_param = f"-Id {pid}"
        elif name:
            filter_param = f"-Name '{name}'"
        else:
            return {"success": False, "error": "Process name or PID required"}
        
        script = f"""
        Get-Process {filter_param} -ErrorAction SilentlyContinue |
        Select-Object Name, Id, CPU,
            @{{N='MemoryMB';E={{[math]::Round($_.WorkingSet64/1MB,2)}}}},
            @{{N='VirtualMemoryMB';E={{[math]::Round($_.VirtualMemorySize64/1MB,2)}}}},
            @{{N='Threads';E={{$_.Threads.Count}}}},
            @{{N='Handles';E={{$_.HandleCount}}}},
            StartTime, Path, Company, Description,
            @{{N='Priority';E={{$_.PriorityClass}}}},
            Responding |
        ConvertTo-Json -Depth 3
        """
        return await self._run_powershell(script)

    async def _get_process_by_name(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get all processes matching a name"""
        name = params.get("name")
        if not name:
            return {"success": False, "error": "Process name required"}
        
        script = f"""
        Get-Process -Name '*{name}*' -ErrorAction SilentlyContinue |
        Select-Object Name, Id, CPU, @{{N='MemoryMB';E={{[math]::Round($_.WorkingSet64/1MB,2)}}}}, Path |
        ConvertTo-Json -Depth 3
        """
        return await self._run_powershell(script)

    async def _get_process_by_id(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get process by ID with full details"""
        pid = params.get("pid")
        if not pid:
            return {"success": False, "error": "Process ID required"}
        
        params["pid"] = pid
        return await self._get_process(params)

    async def _start_process(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Start a new process"""
        path = params.get("path") or params.get("file_path")
        args = params.get("arguments", "")
        working_dir = params.get("working_directory", "")
        window_style = params.get("window_style", "Normal")  # Normal, Hidden, Minimized, Maximized
        wait = params.get("wait", False)
        
        if not path:
            return {"success": False, "error": "Path or file_path required"}
        
        wd_param = f"-WorkingDirectory '{working_dir}'" if working_dir else ""
        wait_param = "-Wait" if wait else ""
        
        script = f"""
        $proc = Start-Process -FilePath '{path}' -ArgumentList '{args}' {wd_param} -WindowStyle {window_style} {wait_param} -PassThru
        @{{
            Success = $true
            ProcessId = $proc.Id
            ProcessName = $proc.ProcessName
            StartTime = $proc.StartTime
        }} | ConvertTo-Json
        """
        return await self._run_powershell(script)

    async def _stop_process(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Stop a process gracefully"""
        name = params.get("name")
        pid = params.get("pid")
        
        if pid:
            filter_param = f"-Id {pid}"
        elif name:
            filter_param = f"-Name '{name}'"
        else:
            return {"success": False, "error": "Process name or PID required"}
        
        script = f"""
        $proc = Get-Process {filter_param} -ErrorAction SilentlyContinue
        if ($proc) {{
            $proc | ForEach-Object {{
                $_.CloseMainWindow() | Out-Null
                @{{ Name = $_.Name; Id = $_.Id; Stopped = $true }}
            }} | ConvertTo-Json
        }} else {{
            @{{ success = $false; error = "Process not found" }} | ConvertTo-Json
        }}
        """
        return await self._run_powershell(script)

    async def _kill_process(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Forcefully kill a process"""
        name = params.get("name")
        pid = params.get("pid")
        force = "-Force" if params.get("force", True) else ""
        
        if pid:
            filter_param = f"-Id {pid}"
        elif name:
            filter_param = f"-Name '{name}'"
        else:
            return {"success": False, "error": "Process name or PID required"}
        
        script = f"""
        Stop-Process {filter_param} {force} -ErrorAction SilentlyContinue
        @{{ success = $true; message = "Process terminated" }} | ConvertTo-Json
        """
        return await self._run_powershell(script)

    async def _restart_process(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Restart a process"""
        pid = params.get("pid")
        if not pid:
            return {"success": False, "error": "Process ID required"}
        
        script = f"""
        $proc = Get-Process -Id {pid} -ErrorAction SilentlyContinue
        if ($proc -and $proc.Path) {{
            $path = $proc.Path
            Stop-Process -Id {pid} -Force
            Start-Sleep -Milliseconds 500
            $newProc = Start-Process -FilePath $path -PassThru
            @{{
                success = $true
                OldPid = {pid}
                NewPid = $newProc.Id
                Path = $path
            }} | ConvertTo-Json
        }} else {{
            @{{ success = $false; error = "Cannot restart - process not found or no path" }} | ConvertTo-Json
        }}
        """
        return await self._run_powershell(script)

    async def _get_priority(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get process priority"""
        pid = params.get("pid")
        if not pid:
            return {"success": False, "error": "Process ID required"}
        
        script = f"""
        $proc = Get-Process -Id {pid} -ErrorAction SilentlyContinue
        @{{
            ProcessId = $proc.Id
            ProcessName = $proc.Name
            PriorityClass = $proc.PriorityClass.ToString()
            BasePriority = $proc.BasePriority
        }} | ConvertTo-Json
        """
        return await self._run_powershell(script)

    async def _set_priority(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set process priority"""
        pid = params.get("pid")
        priority = params.get("priority")  # Idle, BelowNormal, Normal, AboveNormal, High, RealTime
        
        if not pid or not priority:
            return {"success": False, "error": "Process ID and priority required"}
        
        script = f"""
        $proc = Get-Process -Id {pid}
        $proc.PriorityClass = [System.Diagnostics.ProcessPriorityClass]::'{priority}'
        @{{
            success = $true
            ProcessId = $proc.Id
            NewPriority = $proc.PriorityClass.ToString()
        }} | ConvertTo-Json
        """
        return await self._run_powershell(script)

    async def _get_affinity(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get processor affinity mask"""
        pid = params.get("pid")
        if not pid:
            return {"success": False, "error": "Process ID required"}
        
        script = f"""
        $proc = Get-Process -Id {pid}
        @{{
            ProcessId = $proc.Id
            ProcessName = $proc.Name
            AffinityMask = $proc.ProcessorAffinity.ToInt64()
            AffinityBinary = [Convert]::ToString($proc.ProcessorAffinity.ToInt64(), 2)
        }} | ConvertTo-Json
        """
        return await self._run_powershell(script)

    async def _set_affinity(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set processor affinity mask"""
        pid = params.get("pid")
        mask = params.get("mask")  # Bitmask for CPUs (e.g., 3 for CPU 0 and 1)
        
        if not pid or mask is None:
            return {"success": False, "error": "Process ID and affinity mask required"}
        
        script = f"""
        $proc = Get-Process -Id {pid}
        $proc.ProcessorAffinity = {mask}
        @{{
            success = $true
            ProcessId = $proc.Id
            NewAffinityMask = $proc.ProcessorAffinity.ToInt64()
        }} | ConvertTo-Json
        """
        return await self._run_powershell(script)

    async def _get_modules(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get loaded modules for a process"""
        pid = params.get("pid")
        if not pid:
            return {"success": False, "error": "Process ID required"}
        
        script = f"""
        Get-Process -Id {pid} -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty Modules -ErrorAction SilentlyContinue |
        Select-Object ModuleName, FileName, @{{N='SizeMB';E={{[math]::Round($_.ModuleMemorySize/1MB,2)}}}}, FileVersion, Company |
        ConvertTo-Json -Depth 3
        """
        return await self._run_powershell(script)

    async def _get_threads(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get threads for a process"""
        pid = params.get("pid")
        if not pid:
            return {"success": False, "error": "Process ID required"}
        
        script = f"""
        Get-Process -Id {pid} -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty Threads |
        Select-Object Id, ThreadState, WaitReason, 
            @{{N='CPUTime';E={{$_.TotalProcessorTime}}}},
            StartTime, PriorityLevel |
        ConvertTo-Json -Depth 3
        """
        return await self._run_powershell(script)

    async def _get_handles(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get handle count for a process"""
        pid = params.get("pid")
        if not pid:
            return {"success": False, "error": "Process ID required"}
        
        script = f"""
        $proc = Get-Process -Id {pid} -ErrorAction SilentlyContinue
        @{{
            ProcessId = $proc.Id
            ProcessName = $proc.Name
            HandleCount = $proc.HandleCount
        }} | ConvertTo-Json
        """
        return await self._run_powershell(script)

    async def _get_memory_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed memory info for a process"""
        pid = params.get("pid")
        if not pid:
            return {"success": False, "error": "Process ID required"}
        
        script = f"""
        $proc = Get-Process -Id {pid} -ErrorAction SilentlyContinue
        @{{
            ProcessId = $proc.Id
            ProcessName = $proc.Name
            WorkingSetMB = [math]::Round($proc.WorkingSet64/1MB, 2)
            PeakWorkingSetMB = [math]::Round($proc.PeakWorkingSet64/1MB, 2)
            PrivateMemoryMB = [math]::Round($proc.PrivateMemorySize64/1MB, 2)
            VirtualMemoryMB = [math]::Round($proc.VirtualMemorySize64/1MB, 2)
            PagedMemoryMB = [math]::Round($proc.PagedMemorySize64/1MB, 2)
            NonpagedSystemMemoryKB = [math]::Round($proc.NonpagedSystemMemorySize64/1KB, 2)
        }} | ConvertTo-Json
        """
        return await self._run_powershell(script)

    async def _get_cpu_usage(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get CPU usage for a process"""
        pid = params.get("pid")
        if not pid:
            return {"success": False, "error": "Process ID required"}
        
        script = f"""
        $proc = Get-Process -Id {pid} -ErrorAction SilentlyContinue
        @{{
            ProcessId = $proc.Id
            ProcessName = $proc.Name
            CPUSeconds = $proc.CPU
            TotalProcessorTime = $proc.TotalProcessorTime.ToString()
            UserProcessorTime = $proc.UserProcessorTime.ToString()
            PrivilegedProcessorTime = $proc.PrivilegedProcessorTime.ToString()
        }} | ConvertTo-Json
        """
        return await self._run_powershell(script)

    async def _get_parent(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get parent process"""
        pid = params.get("pid")
        if not pid:
            return {"success": False, "error": "Process ID required"}
        
        script = f"""
        $proc = Get-CimInstance Win32_Process -Filter "ProcessId = {pid}"
        if ($proc) {{
            $parent = Get-Process -Id $proc.ParentProcessId -ErrorAction SilentlyContinue
            @{{
                ChildPid = {pid}
                ParentPid = $proc.ParentProcessId
                ParentName = $parent.Name
                ParentPath = $parent.Path
            }} | ConvertTo-Json
        }}
        """
        return await self._run_powershell(script)

    async def _get_children(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get child processes"""
        pid = params.get("pid")
        if not pid:
            return {"success": False, "error": "Process ID required"}
        
        script = f"""
        Get-CimInstance Win32_Process -Filter "ParentProcessId = {pid}" |
        ForEach-Object {{
            $p = Get-Process -Id $_.ProcessId -ErrorAction SilentlyContinue
            @{{
                ProcessId = $_.ProcessId
                ProcessName = $_.Name
                CommandLine = $_.CommandLine
                MemoryMB = if($p){{[math]::Round($p.WorkingSet64/1MB,2)}}else{{0}}
            }}
        }} | ConvertTo-Json -Depth 3
        """
        return await self._run_powershell(script)

    async def _get_process_tree(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get full process tree"""
        pid = params.get("pid")
        if not pid:
            return {"success": False, "error": "Process ID required"}
        
        script = f"""
        function Get-ProcessTree {{
            param($ParentId, $Depth = 0)
            Get-CimInstance Win32_Process -Filter "ParentProcessId = $ParentId" | ForEach-Object {{
                @{{
                    Depth = $Depth
                    ProcessId = $_.ProcessId
                    ProcessName = $_.Name
                    Children = @(Get-ProcessTree -ParentId $_.ProcessId -Depth ($Depth + 1))
                }}
            }}
        }}
        Get-ProcessTree -ParentId {pid} | ConvertTo-Json -Depth 10
        """
        return await self._run_powershell(script)

    async def _find_by_window(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Find process by window title"""
        title = params.get("title")
        if not title:
            return {"success": False, "error": "Window title required"}
        
        script = f"""
        Get-Process | Where-Object {{ $_.MainWindowTitle -like '*{title}*' }} |
        Select-Object Name, Id, MainWindowTitle, Path |
        ConvertTo-Json -Depth 3
        """
        return await self._run_powershell(script)

    async def _find_by_port(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Find process using a specific port"""
        port = params.get("port")
        if not port:
            return {"success": False, "error": "Port number required"}
        
        script = f"""
        Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue |
        ForEach-Object {{
            $proc = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue
            @{{
                Port = $_.LocalPort
                State = $_.State
                ProcessId = $_.OwningProcess
                ProcessName = $proc.Name
                ProcessPath = $proc.Path
            }}
        }} | ConvertTo-Json -Depth 3
        """
        return await self._run_powershell(script)

    async def _find_by_path(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Find process by executable path"""
        path = params.get("path")
        if not path:
            return {"success": False, "error": "Path required"}
        
        script = f"""
        Get-Process | Where-Object {{ $_.Path -like '*{path}*' }} |
        Select-Object Name, Id, Path, @{{N='MemoryMB';E={{[math]::Round($_.WorkingSet64/1MB,2)}}}} |
        ConvertTo-Json -Depth 3
        """
        return await self._run_powershell(script)

    async def _get_top_cpu(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get top CPU consuming processes"""
        count = params.get("count", 10)
        script = f"""
        Get-Process | Sort-Object CPU -Descending | Select-Object -First {count} |
        Select-Object Name, Id, CPU, @{{N='MemoryMB';E={{[math]::Round($_.WorkingSet64/1MB,2)}}}} |
        ConvertTo-Json -Depth 3
        """
        return await self._run_powershell(script)

    async def _get_top_memory(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get top memory consuming processes"""
        count = params.get("count", 10)
        script = f"""
        Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First {count} |
        Select-Object Name, Id, @{{N='MemoryMB';E={{[math]::Round($_.WorkingSet64/1MB,2)}}}}, CPU |
        ConvertTo-Json -Depth 3
        """
        return await self._run_powershell(script)

    async def _get_process_count(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get process count statistics"""
        script = """
        $procs = Get-Process
        @{
            TotalCount = $procs.Count
            RespondingCount = ($procs | Where-Object { $_.Responding }).Count
            NotRespondingCount = ($procs | Where-Object { -not $_.Responding }).Count
            WithWindowCount = ($procs | Where-Object { $_.MainWindowHandle -ne 0 }).Count
        } | ConvertTo-Json
        """
        return await self._run_powershell(script)

    async def _wait_for_exit(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Wait for a process to exit"""
        pid = params.get("pid")
        timeout = params.get("timeout", 60)
        
        if not pid:
            return {"success": False, "error": "Process ID required"}
        
        script = f"""
        $proc = Get-Process -Id {pid} -ErrorAction SilentlyContinue
        if ($proc) {{
            $exited = $proc.WaitForExit({timeout * 1000})
            @{{ success = $exited; message = if($exited){{"Process exited"}}else{{"Timeout waiting for exit"}} }} | ConvertTo-Json
        }} else {{
            @{{ success = $true; message = "Process not running" }} | ConvertTo-Json
        }}
        """
        return await self._run_powershell(script, timeout=timeout + 10)

    async def _wait_for_idle(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Wait for a process to become idle"""
        pid = params.get("pid")
        timeout = params.get("timeout", 30)
        
        if not pid:
            return {"success": False, "error": "Process ID required"}
        
        script = f"""
        $proc = Get-Process -Id {pid} -ErrorAction SilentlyContinue
        if ($proc) {{
            $idle = $proc.WaitForInputIdle({timeout * 1000})
            @{{ success = $idle; message = if($idle){{"Process is idle"}}else{{"Timeout waiting for idle"}} }} | ConvertTo-Json
        }} else {{
            @{{ success = $false; error = "Process not found" }} | ConvertTo-Json
        }}
        """
        return await self._run_powershell(script, timeout=timeout + 10)

    async def cleanup(self) -> None:
        """Cleanup plugin resources"""
        logger.info("Process Management plugin cleaned up")


plugin = ProcessManagementPlugin()
