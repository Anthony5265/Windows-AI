"""
Windows Performance Recorder Plugin for Windows AI
Comprehensive ETW tracing and performance recording capabilities
"""

import asyncio
import logging
import subprocess
from typing import Any, Dict, Optional, List
from datetime import datetime

from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType


class PerformanceRecorderPlugin(IntegrationPlugin):
    """Plugin for Windows Performance Recorder and ETW tracing"""

    def __init__(self):
        metadata = PluginMetadata(
            id="performance-recorder",
            name="Performance Recorder",
            description="Windows Performance Recorder (WPR) and ETW tracing management",
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["windows", "performance", "wpr", "etw", "tracing", "profiling"],
        )
        super().__init__(metadata)
        self.logger = logging.getLogger(__name__)
        self._actions = {
            # WPR Recording
            "start_recording": self._start_recording,
            "stop_recording": self._stop_recording,
            "cancel_recording": self._cancel_recording,
            "get_recording_status": self._get_recording_status,
            "list_profiles": self._list_profiles,
            "get_profile_info": self._get_profile_info,
            # Built-in profiles
            "record_cpu": self._record_cpu,
            "record_disk_io": self._record_disk_io,
            "record_file_io": self._record_file_io,
            "record_network": self._record_network,
            "record_memory": self._record_memory,
            "record_gpu": self._record_gpu,
            "record_general": self._record_general,
            # Performance counters
            "list_counter_sets": self._list_counter_sets,
            "get_counter_set": self._get_counter_set,
            "get_counter_value": self._get_counter_value,
            "collect_counters": self._collect_counters,
            "start_counter_collection": self._start_counter_collection,
            "stop_counter_collection": self._stop_counter_collection,
            # Data collector sets
            "list_collectors": self._list_collectors,
            "create_collector": self._create_collector,
            "start_collector": self._start_collector,
            "stop_collector": self._stop_collector,
            "delete_collector": self._delete_collector,
            "get_collector_status": self._get_collector_status,
            # System diagnostics
            "get_system_performance": self._get_system_performance,
            "get_process_performance": self._get_process_performance,
            "get_disk_performance": self._get_disk_performance,
            "get_network_performance": self._get_network_performance,
            "get_memory_performance": self._get_memory_performance,
            # ETW Sessions
            "list_etw_sessions": self._list_etw_sessions,
            "start_etw_session": self._start_etw_session,
            "stop_etw_session": self._stop_etw_session,
            "get_etw_providers": self._get_etw_providers,
            "enable_etw_provider": self._enable_etw_provider,
            # Analysis
            "analyze_trace": self._analyze_trace,
            "get_trace_info": self._get_trace_info,
            "export_trace_summary": self._export_trace_summary,
            # Reliability
            "get_reliability_history": self._get_reliability_history,
            "get_stability_index": self._get_stability_index,
            # Boot trace
            "start_boot_trace": self._start_boot_trace,
            "get_boot_trace_status": self._get_boot_trace_status,
        }

    async def initialize(self) -> bool:
        """Initialize the plugin"""
        self.logger.info("Initializing Performance Recorder plugin")
        return True

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute performance recording operations"""
        action = kwargs.get("action", "get_recording_status")
        params = kwargs.get("params", {})
        
        if action in self._actions:
            try:
                return await self._actions[action](**params)
            except Exception as e:
                self.logger.error(f"Error executing {action}: {e}")
                return {"success": False, "error": str(e)}
        else:
            return {"success": False, "error": f"Unknown action: {action}", "available_actions": list(self._actions.keys())}

    async def _run_powershell(self, command: str) -> Dict[str, Any]:
        """Run a PowerShell command and return results"""
        try:
            process = await asyncio.create_subprocess_exec(
                "powershell", "-NoProfile", "-Command", command,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return {"success": True, "output": stdout.decode("utf-8", errors="replace").strip()}
            else:
                return {"success": False, "error": stderr.decode("utf-8", errors="replace").strip()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _run_command(self, command: str, args: List[str]) -> Dict[str, Any]:
        """Run a command directly"""
        try:
            process = await asyncio.create_subprocess_exec(
                command, *args,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            return {
                "success": process.returncode == 0,
                "output": stdout.decode("utf-8", errors="replace").strip(),
                "error": stderr.decode("utf-8", errors="replace").strip() if stderr else None
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # WPR Recording
    async def _start_recording(self, profile: str = "GeneralProfile", output_path: str = None, 
                               duration: int = None, **kwargs) -> Dict[str, Any]:
        """Start WPR recording"""
        args = ["-start", profile]
        if output_path:
            args.extend(["-recordtempuserdir", output_path])
        
        result = await self._run_command("wpr", args)
        if result["success"]:
            return {
                "success": True,
                "message": f"Recording started with profile: {profile}",
                "profile": profile,
                "duration": duration
            }
        return result

    async def _stop_recording(self, output_file: str = None, **kwargs) -> Dict[str, Any]:
        """Stop WPR recording and save trace"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"C:\\PerfLogs\\trace_{timestamp}.etl"
        
        args = ["-stop", output_file]
        result = await self._run_command("wpr", args)
        if result["success"]:
            return {
                "success": True,
                "message": "Recording stopped",
                "output_file": output_file
            }
        return result

    async def _cancel_recording(self, **kwargs) -> Dict[str, Any]:
        """Cancel current WPR recording"""
        return await self._run_command("wpr", ["-cancel"])

    async def _get_recording_status(self, **kwargs) -> Dict[str, Any]:
        """Get current WPR recording status"""
        result = await self._run_command("wpr", ["-status"])
        is_recording = "WPR is recording" in result.get("output", "") if result.get("output") else False
        return {
            "success": True,
            "is_recording": is_recording,
            "details": result.get("output", "")
        }

    async def _list_profiles(self, **kwargs) -> Dict[str, Any]:
        """List available WPR profiles"""
        return await self._run_command("wpr", ["-profiles"])

    async def _get_profile_info(self, profile: str, **kwargs) -> Dict[str, Any]:
        """Get information about a WPR profile"""
        return await self._run_command("wpr", ["-profiledetails", profile])

    # Built-in profile recordings
    async def _record_cpu(self, duration: int = 30, output_file: str = None, **kwargs) -> Dict[str, Any]:
        """Record CPU performance"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"C:\\PerfLogs\\cpu_trace_{timestamp}.etl"
        
        start_result = await self._run_command("wpr", ["-start", "CPU"])
        if not start_result.get("success", True):  # WPR may return success without output
            pass  # Continue anyway as WPR may have started
        
        await asyncio.sleep(duration)
        return await self._stop_recording(output_file=output_file)

    async def _record_disk_io(self, duration: int = 30, output_file: str = None, **kwargs) -> Dict[str, Any]:
        """Record disk I/O performance"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"C:\\PerfLogs\\disk_trace_{timestamp}.etl"
        
        await self._run_command("wpr", ["-start", "DiskIO"])
        await asyncio.sleep(duration)
        return await self._stop_recording(output_file=output_file)

    async def _record_file_io(self, duration: int = 30, output_file: str = None, **kwargs) -> Dict[str, Any]:
        """Record file I/O performance"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"C:\\PerfLogs\\fileio_trace_{timestamp}.etl"
        
        await self._run_command("wpr", ["-start", "FileIO"])
        await asyncio.sleep(duration)
        return await self._stop_recording(output_file=output_file)

    async def _record_network(self, duration: int = 30, output_file: str = None, **kwargs) -> Dict[str, Any]:
        """Record network performance"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"C:\\PerfLogs\\network_trace_{timestamp}.etl"
        
        await self._run_command("wpr", ["-start", "Network"])
        await asyncio.sleep(duration)
        return await self._stop_recording(output_file=output_file)

    async def _record_memory(self, duration: int = 30, output_file: str = None, **kwargs) -> Dict[str, Any]:
        """Record memory performance"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"C:\\PerfLogs\\memory_trace_{timestamp}.etl"
        
        await self._run_command("wpr", ["-start", "Heap"])
        await asyncio.sleep(duration)
        return await self._stop_recording(output_file=output_file)

    async def _record_gpu(self, duration: int = 30, output_file: str = None, **kwargs) -> Dict[str, Any]:
        """Record GPU performance"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"C:\\PerfLogs\\gpu_trace_{timestamp}.etl"
        
        await self._run_command("wpr", ["-start", "GPU"])
        await asyncio.sleep(duration)
        return await self._stop_recording(output_file=output_file)

    async def _record_general(self, duration: int = 30, output_file: str = None, **kwargs) -> Dict[str, Any]:
        """Record general system performance"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"C:\\PerfLogs\\general_trace_{timestamp}.etl"
        
        await self._run_command("wpr", ["-start", "GeneralProfile"])
        await asyncio.sleep(duration)
        return await self._stop_recording(output_file=output_file)

    # Performance counters
    async def _list_counter_sets(self, **kwargs) -> Dict[str, Any]:
        """List available performance counter sets"""
        cmd = """
        Get-Counter -ListSet * | 
        Select-Object CounterSetName, Description, CounterSetType |
        Sort-Object CounterSetName |
        ConvertTo-Json -Depth 2
        """
        return await self._run_powershell(cmd)

    async def _get_counter_set(self, counter_set: str, **kwargs) -> Dict[str, Any]:
        """Get counters in a specific counter set"""
        cmd = f"""
        $set = Get-Counter -ListSet '{counter_set}' -ErrorAction Stop
        [PSCustomObject]@{{
            CounterSetName = $set.CounterSetName
            Description = $set.Description
            Paths = $set.Paths
            PathsWithInstances = $set.PathsWithInstances
        }} | ConvertTo-Json -Depth 3
        """
        return await self._run_powershell(cmd)

    async def _get_counter_value(self, counter_path: str, **kwargs) -> Dict[str, Any]:
        """Get current value of a performance counter"""
        cmd = f"""
        $counter = Get-Counter -Counter '{counter_path}' -ErrorAction Stop
        [PSCustomObject]@{{
            Timestamp = $counter.Timestamp
            CounterPath = $counter.CounterSamples[0].Path
            InstanceName = $counter.CounterSamples[0].InstanceName
            CookedValue = $counter.CounterSamples[0].CookedValue
        }} | ConvertTo-Json
        """
        return await self._run_powershell(cmd)

    async def _collect_counters(self, counters: List[str], samples: int = 5, 
                                interval: int = 1, **kwargs) -> Dict[str, Any]:
        """Collect performance counter samples"""
        counter_list = "', '".join(counters)
        cmd = f"""
        $counters = Get-Counter -Counter @('{counter_list}') -SampleInterval {interval} -MaxSamples {samples}
        $results = $counters | ForEach-Object {{
            [PSCustomObject]@{{
                Timestamp = $_.Timestamp
                Samples = @($_.CounterSamples | ForEach-Object {{
                    [PSCustomObject]@{{
                        Path = $_.Path
                        Instance = $_.InstanceName
                        Value = $_.CookedValue
                    }}
                }})
            }}
        }}
        $results | ConvertTo-Json -Depth 4
        """
        return await self._run_powershell(cmd)

    async def _start_counter_collection(self, name: str, counters: List[str], 
                                        output_path: str = None, interval: int = 15, **kwargs) -> Dict[str, Any]:
        """Start a performance counter data collector"""
        if not output_path:
            output_path = f"C:\\PerfLogs\\{name}"
        
        counter_list = '", "'.join(counters)
        cmd = f"""
        $null = New-Item -Path '{output_path}' -ItemType Directory -Force
        $counters = @("{counter_list}")
        $name = "{name}"
        $collector = New-Object -ComObject Pla.DataCollectorSet
        $collector.DisplayName = $name
        $collector.Duration = 0
        $collector.RootPath = "{output_path}"
        $collector.Segment = $false
        
        $perfCounter = $collector.DataCollectors.CreateDataCollector(0)
        $perfCounter.FileName = "perfdata"
        $perfCounter.FileNameFormat = 1
        $perfCounter.FileNameFormatPattern = "yyyyMMdd-HHmmss"
        $perfCounter.SampleInterval = {interval}
        $perfCounter.PerformanceCounters = $counters
        
        $collector.DataCollectors.Add($perfCounter)
        $collector.Commit("{name}", $null, 0x0003)
        $collector.Start($false)
        
        @{{ success = $true; name = "{name}"; output_path = "{output_path}" }} | ConvertTo-Json
        """
        return await self._run_powershell(cmd)

    async def _stop_counter_collection(self, name: str, **kwargs) -> Dict[str, Any]:
        """Stop a performance counter data collector"""
        cmd = f"""
        $collector = New-Object -ComObject Pla.DataCollectorSet
        $collector.Query("{name}", $null)
        $collector.Stop($false)
        @{{ success = $true; message = "Collector '{name}' stopped" }} | ConvertTo-Json
        """
        return await self._run_powershell(cmd)

    # Data collector sets
    async def _list_collectors(self, **kwargs) -> Dict[str, Any]:
        """List all data collector sets"""
        cmd = """
        $dcs = New-Object -ComObject Pla.DataCollectorSet
        $setNames = @()
        foreach ($name in @("System", "Event Trace Sessions", "Startup Event Trace Sessions")) {
            try {
                $dcs.Query($name, $null)
                $setNames += [PSCustomObject]@{
                    Name = $name
                    Status = $dcs.Status
                }
            } catch {}
        }
        # Also get user-defined collectors
        Get-ChildItem "C:\\PerfLogs\\Admin" -ErrorAction SilentlyContinue | ForEach-Object {
            $setNames += [PSCustomObject]@{
                Name = $_.Name
                Path = $_.FullName
            }
        }
        $setNames | ConvertTo-Json -Depth 2
        """
        return await self._run_powershell(cmd)

    async def _create_collector(self, name: str, counters: List[str] = None, 
                                trace_providers: List[str] = None, **kwargs) -> Dict[str, Any]:
        """Create a new data collector set"""
        counter_list = '", "'.join(counters) if counters else ""
        provider_list = '", "'.join(trace_providers) if trace_providers else ""
        
        cmd = f"""
        $dcs = New-Object -ComObject Pla.DataCollectorSet
        $dcs.DisplayName = "{name}"
        $dcs.RootPath = "C:\\PerfLogs\\{name}"
        
        {"# Add performance counters" if counters else ""}
        {f'''
        $perfCounter = $dcs.DataCollectors.CreateDataCollector(0)
        $perfCounter.Name = "PerfCounter"
        $perfCounter.PerformanceCounters = @("{counter_list}")
        $perfCounter.SampleInterval = 15
        $dcs.DataCollectors.Add($perfCounter)
        ''' if counters else ""}
        
        $dcs.Commit("{name}", $null, 0x0003)
        @{{ success = $true; name = "{name}" }} | ConvertTo-Json
        """
        return await self._run_powershell(cmd)

    async def _start_collector(self, name: str, **kwargs) -> Dict[str, Any]:
        """Start a data collector set"""
        cmd = f"""
        $dcs = New-Object -ComObject Pla.DataCollectorSet
        $dcs.Query("{name}", $null)
        $dcs.Start($false)
        @{{ success = $true; message = "Collector started" }} | ConvertTo-Json
        """
        return await self._run_powershell(cmd)

    async def _stop_collector(self, name: str, **kwargs) -> Dict[str, Any]:
        """Stop a data collector set"""
        cmd = f"""
        $dcs = New-Object -ComObject Pla.DataCollectorSet
        $dcs.Query("{name}", $null)
        $dcs.Stop($false)
        @{{ success = $true; message = "Collector stopped" }} | ConvertTo-Json
        """
        return await self._run_powershell(cmd)

    async def _delete_collector(self, name: str, **kwargs) -> Dict[str, Any]:
        """Delete a data collector set"""
        cmd = f"""
        $dcs = New-Object -ComObject Pla.DataCollectorSet
        $dcs.Query("{name}", $null)
        $dcs.Delete()
        @{{ success = $true; message = "Collector deleted" }} | ConvertTo-Json
        """
        return await self._run_powershell(cmd)

    async def _get_collector_status(self, name: str, **kwargs) -> Dict[str, Any]:
        """Get status of a data collector set"""
        cmd = f"""
        $dcs = New-Object -ComObject Pla.DataCollectorSet
        $dcs.Query("{name}", $null)
        [PSCustomObject]@{{
            Name = $dcs.Name
            Status = switch ($dcs.Status) {{
                0 {{ "Stopped" }}
                1 {{ "Running" }}
                2 {{ "Compiling" }}
                3 {{ "Pending" }}
                default {{ "Unknown" }}
            }}
            RootPath = $dcs.RootPath
            Duration = $dcs.Duration
        }} | ConvertTo-Json
        """
        return await self._run_powershell(cmd)

    # System diagnostics
    async def _get_system_performance(self, **kwargs) -> Dict[str, Any]:
        """Get overall system performance metrics"""
        cmd = """
        $cpu = (Get-Counter '\\Processor(_Total)\\% Processor Time' -ErrorAction SilentlyContinue).CounterSamples[0].CookedValue
        $mem = Get-CimInstance Win32_OperatingSystem
        $disk = Get-Counter '\\PhysicalDisk(_Total)\\% Disk Time' -ErrorAction SilentlyContinue
        
        [PSCustomObject]@{
            Timestamp = (Get-Date -Format "o")
            CPU = @{
                UsagePercent = [math]::Round($cpu, 2)
                ProcessorCount = (Get-CimInstance Win32_ComputerSystem).NumberOfLogicalProcessors
            }
            Memory = @{
                TotalGB = [math]::Round($mem.TotalVisibleMemorySize / 1MB, 2)
                FreeGB = [math]::Round($mem.FreePhysicalMemory / 1MB, 2)
                UsedPercent = [math]::Round((1 - $mem.FreePhysicalMemory / $mem.TotalVisibleMemorySize) * 100, 2)
            }
            Disk = @{
                UsagePercent = if ($disk) { [math]::Round($disk.CounterSamples[0].CookedValue, 2) } else { 0 }
            }
        } | ConvertTo-Json -Depth 3
        """
        return await self._run_powershell(cmd)

    async def _get_process_performance(self, process_name: str = None, top_n: int = 10, **kwargs) -> Dict[str, Any]:
        """Get process performance metrics"""
        filter_cmd = f"Where-Object {{ $_.Name -like '*{process_name}*' }} |" if process_name else ""
        cmd = f"""
        Get-Process | {filter_cmd}
        Sort-Object CPU -Descending |
        Select-Object -First {top_n} Name, Id, CPU, 
            @{{N='WorkingSetMB';E={{[math]::Round($_.WorkingSet64/1MB,2)}}}},
            @{{N='PrivateMemoryMB';E={{[math]::Round($_.PrivateMemorySize64/1MB,2)}}}},
            @{{N='Threads';E={{$_.Threads.Count}}}},
            @{{N='Handles';E={{$_.HandleCount}}}} |
        ConvertTo-Json -Depth 2
        """
        return await self._run_powershell(cmd)

    async def _get_disk_performance(self, **kwargs) -> Dict[str, Any]:
        """Get disk performance metrics"""
        cmd = """
        $counters = @(
            '\\PhysicalDisk(*)\\% Disk Time',
            '\\PhysicalDisk(*)\\Disk Reads/sec',
            '\\PhysicalDisk(*)\\Disk Writes/sec',
            '\\PhysicalDisk(*)\\Avg. Disk Queue Length'
        )
        $samples = Get-Counter -Counter $counters -ErrorAction SilentlyContinue
        $results = @{}
        foreach ($sample in $samples.CounterSamples) {
            $instance = $sample.InstanceName
            if (-not $results[$instance]) {
                $results[$instance] = @{}
            }
            $counterName = $sample.Path -replace '.*\\\\', ''
            $results[$instance][$counterName] = [math]::Round($sample.CookedValue, 2)
        }
        $results | ConvertTo-Json -Depth 3
        """
        return await self._run_powershell(cmd)

    async def _get_network_performance(self, **kwargs) -> Dict[str, Any]:
        """Get network performance metrics"""
        cmd = """
        $counters = @(
            '\\Network Interface(*)\\Bytes Total/sec',
            '\\Network Interface(*)\\Bytes Received/sec',
            '\\Network Interface(*)\\Bytes Sent/sec',
            '\\Network Interface(*)\\Packets/sec'
        )
        $samples = Get-Counter -Counter $counters -ErrorAction SilentlyContinue
        $results = @{}
        foreach ($sample in $samples.CounterSamples) {
            $instance = $sample.InstanceName
            if ($instance -and $instance -ne '_Total') {
                if (-not $results[$instance]) {
                    $results[$instance] = @{}
                }
                $counterName = $sample.Path -replace '.*\\\\', ''
                $results[$instance][$counterName] = [math]::Round($sample.CookedValue, 2)
            }
        }
        $results | ConvertTo-Json -Depth 3
        """
        return await self._run_powershell(cmd)

    async def _get_memory_performance(self, **kwargs) -> Dict[str, Any]:
        """Get memory performance metrics"""
        cmd = """
        $counters = @(
            '\\Memory\\Available MBytes',
            '\\Memory\\% Committed Bytes In Use',
            '\\Memory\\Cache Bytes',
            '\\Memory\\Pool Paged Bytes',
            '\\Memory\\Pool Nonpaged Bytes',
            '\\Memory\\Pages/sec',
            '\\Memory\\Page Faults/sec'
        )
        $samples = Get-Counter -Counter $counters -ErrorAction SilentlyContinue
        $results = @{}
        foreach ($sample in $samples.CounterSamples) {
            $counterName = $sample.Path -replace '.*\\\\Memory\\\\', ''
            $results[$counterName] = [math]::Round($sample.CookedValue, 2)
        }
        $results | ConvertTo-Json -Depth 2
        """
        return await self._run_powershell(cmd)

    # ETW Sessions
    async def _list_etw_sessions(self, **kwargs) -> Dict[str, Any]:
        """List active ETW sessions"""
        result = await self._run_command("logman", ["query", "-ets"])
        return result

    async def _start_etw_session(self, name: str, providers: List[str], 
                                  output_file: str = None, **kwargs) -> Dict[str, Any]:
        """Start an ETW session"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"C:\\PerfLogs\\{name}_{timestamp}.etl"
        
        args = ["start", name, "-o", output_file, "-ets"]
        for provider in providers:
            args.extend(["-p", provider])
        
        return await self._run_command("logman", args)

    async def _stop_etw_session(self, name: str, **kwargs) -> Dict[str, Any]:
        """Stop an ETW session"""
        return await self._run_command("logman", ["stop", name, "-ets"])

    async def _get_etw_providers(self, filter_name: str = None, **kwargs) -> Dict[str, Any]:
        """List available ETW providers"""
        cmd = """
        $providers = logman query providers
        $providers
        """
        if filter_name:
            cmd = f"""
            logman query providers | Select-String -Pattern '{filter_name}'
            """
        return await self._run_powershell(cmd)

    async def _enable_etw_provider(self, session_name: str, provider: str, 
                                    level: int = 5, **kwargs) -> Dict[str, Any]:
        """Enable an ETW provider in a session"""
        return await self._run_command("logman", [
            "update", session_name, "-p", provider, f"0x{level:x}", "-ets"
        ])

    # Analysis
    async def _analyze_trace(self, trace_file: str, **kwargs) -> Dict[str, Any]:
        """Analyze an ETL trace file"""
        cmd = f"""
        $trace = Get-WinEvent -Path '{trace_file}' -Oldest -MaxEvents 1000 -ErrorAction SilentlyContinue
        [PSCustomObject]@{{
            TraceFile = '{trace_file}'
            EventCount = $trace.Count
            FirstEvent = $trace[0].TimeCreated
            LastEvent = $trace[-1].TimeCreated
            ProviderNames = @($trace | Group-Object ProviderName | Select-Object Name, Count)
        }} | ConvertTo-Json -Depth 3
        """
        return await self._run_powershell(cmd)

    async def _get_trace_info(self, trace_file: str, **kwargs) -> Dict[str, Any]:
        """Get information about a trace file"""
        cmd = f"""
        $file = Get-Item '{trace_file}'
        [PSCustomObject]@{{
            Path = $file.FullName
            SizeBytes = $file.Length
            SizeMB = [math]::Round($file.Length / 1MB, 2)
            Created = $file.CreationTime
            Modified = $file.LastWriteTime
        }} | ConvertTo-Json
        """
        return await self._run_powershell(cmd)

    async def _export_trace_summary(self, trace_file: str, output_file: str = None, **kwargs) -> Dict[str, Any]:
        """Export trace summary to file"""
        if not output_file:
            output_file = trace_file.replace('.etl', '_summary.txt')
        
        return await self._run_command("xperf", ["-i", trace_file, "-o", output_file, "-a", "summary"])

    # Reliability
    async def _get_reliability_history(self, days: int = 7, **kwargs) -> Dict[str, Any]:
        """Get system reliability history"""
        cmd = f"""
        $startDate = (Get-Date).AddDays(-{days})
        Get-CimInstance -ClassName Win32_ReliabilityRecords -ErrorAction SilentlyContinue |
        Where-Object {{ $_.TimeGenerated -gt $startDate }} |
        Select-Object TimeGenerated, EventIdentifier, SourceName, Message, RecordNumber |
        Sort-Object TimeGenerated -Descending |
        ConvertTo-Json -Depth 2
        """
        return await self._run_powershell(cmd)

    async def _get_stability_index(self, **kwargs) -> Dict[str, Any]:
        """Get system stability index"""
        cmd = """
        $stabilityData = Get-CimInstance -ClassName Win32_ReliabilityStabilityMetrics -ErrorAction SilentlyContinue |
        Select-Object -First 10 SystemStabilityIndex, TimeGenerated |
        Sort-Object TimeGenerated -Descending
        
        if ($stabilityData) {
            [PSCustomObject]@{
                CurrentIndex = $stabilityData[0].SystemStabilityIndex
                History = @($stabilityData | ForEach-Object {
                    [PSCustomObject]@{
                        Index = $_.SystemStabilityIndex
                        Date = $_.TimeGenerated
                    }
                })
            } | ConvertTo-Json -Depth 3
        } else {
            @{ error = "Stability data not available" } | ConvertTo-Json
        }
        """
        return await self._run_powershell(cmd)

    # Boot trace
    async def _start_boot_trace(self, **kwargs) -> Dict[str, Any]:
        """Start a boot trace for next restart"""
        return await self._run_command("wpr", ["-boottrace", "-addboot", "GeneralProfile"])

    async def _get_boot_trace_status(self, **kwargs) -> Dict[str, Any]:
        """Get boot trace status"""
        return await self._run_command("wpr", ["-boottrace", "-status"])

    async def cleanup(self):
        """Cleanup plugin resources"""
        self.logger.info("Cleaning up Performance Recorder plugin")
