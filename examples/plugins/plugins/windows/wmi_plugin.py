"""
Windows WMI (Windows Management Instrumentation) Plugin
"""

from typing import Dict, Any, Optional, List
import subprocess


class WMIPlugin:
    """Plugin for Windows WMI"""
    
    name = "wmi"
    version = "1.0.0"
    description = "Integration with Windows Management Instrumentation (WMI)"
    author = "Windows AI Team"
    
    def __init__(self):
        self._initialized = False
        
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the WMI plugin"""
        self._initialized = True
        return True
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a WMI action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}
            
        try:
            if action == "query":
                return self._query_wmi(params)
            elif action == "get_system_info":
                return self._get_system_info()
            elif action == "get_processes":
                return self._get_processes()
            elif action == "get_services":
                return self._get_services()
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _query_wmi(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute WMI query"""
        query = params.get("query", "")
        
        cmd = f"Get-WmiObject -Query '{query}' | ConvertTo-Json"
        
        result = subprocess.run(
            ["powershell", "-Command", cmd],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            import json
            try:
                data = json.loads(result.stdout)
                return {
                    "success": True,
                    "data": data if isinstance(data, list) else [data]
                }
            except json.JSONDecodeError:
                return {"success": False, "error": "Failed to parse WMI data"}
        return {"success": False, "error": result.stderr}
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        cmd = "Get-WmiObject Win32_OperatingSystem | Select-Object Caption, Version, BuildNumber, OSArchitecture, TotalVisibleMemorySize | ConvertTo-Json"
        
        result = subprocess.run(
            ["powershell", "-Command", cmd],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            import json
            try:
                return {
                    "success": True,
                    "system_info": json.loads(result.stdout)
                }
            except json.JSONDecodeError:
                return {"success": False, "error": "Failed to parse system info"}
        return {"success": False, "error": result.stderr}
    
    def _get_processes(self) -> Dict[str, Any]:
        """Get running processes"""
        cmd = "Get-WmiObject Win32_Process | Select-Object Name, ProcessId, WorkingSetSize | ConvertTo-Json"
        
        result = subprocess.run(
            ["powershell", "-Command", cmd],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            import json
            try:
                processes = json.loads(result.stdout)
                return {
                    "success": True,
                    "processes": processes if isinstance(processes, list) else [processes]
                }
            except json.JSONDecodeError:
                return {"success": False, "error": "Failed to parse processes"}
        return {"success": False, "error": result.stderr}
    
    def _get_services(self) -> Dict[str, Any]:
        """Get Windows services"""
        cmd = "Get-WmiObject Win32_Service | Select-Object Name, DisplayName, State, StartMode | ConvertTo-Json"
        
        result = subprocess.run(
            ["powershell", "-Command", cmd],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            import json
            try:
                services = json.loads(result.stdout)
                return {
                    "success": True,
                    "services": services if isinstance(services, list) else [services]
                }
            except json.JSONDecodeError:
                return {"success": False, "error": "Failed to parse services"}
        return {"success": False, "error": result.stderr}
    
    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        return True
