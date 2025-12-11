"""
Windows Task Scheduler Integration - PRODUCTION

Provides comprehensive Windows Task Scheduler management capabilities including:
- Creating scheduled tasks (one-time, daily, weekly, monthly)
- Managing existing tasks (enable, disable, run, delete)
- Listing and querying tasks
- Task history and status monitoring
"""
import asyncio
import json
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType
import logging

logger = logging.getLogger(__name__)


class WindowsTaskSchedulerPlugin(IntegrationPlugin):
    """Windows Task Scheduler plugin with comprehensive task management."""
    
    def __init__(self):
        metadata = PluginMetadata(
            id="windows_task_scheduler",
            name="Windows Task Scheduler",
            description="Comprehensive Windows Task Scheduler management - create, modify, run, and delete scheduled tasks",
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["windows", "task_scheduler", "automation", "scheduling"]
        )
        super().__init__(metadata)
        self.connected = False

    async def initialize(self) -> bool:
        """Initialize the task scheduler plugin."""
        self._initialized = True
        return True

    async def connect(self, credentials: Dict[str, str]) -> bool:
        """Connect to Task Scheduler (local access)."""
        self.connected = True
        return True

    async def disconnect(self) -> bool:
        """Disconnect from Task Scheduler."""
        self.connected = False
        return True

    async def _run_powershell(self, command: str) -> Dict[str, Any]:
        """Execute a PowerShell command and return results."""
        try:
            process = await asyncio.create_subprocess_exec(
                "powershell", "-NoProfile", "-NonInteractive", "-Command", command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            return {
                "success": process.returncode == 0,
                "output": stdout.decode('utf-8', errors='replace').strip(),
                "error": stderr.decode('utf-8', errors='replace').strip() if stderr else None,
                "return_code": process.returncode
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def execute(self, action: str, parameters: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Execute a task scheduler operation."""
        if not self.connected:
            return {"success": False, "error": "Not connected"}

        actions = {
            "list_tasks": self._list_tasks,
            "get_task": self._get_task,
            "create_task": self._create_task,
            "delete_task": self._delete_task,
            "enable_task": self._enable_task,
            "disable_task": self._disable_task,
            "run_task": self._run_task,
            "stop_task": self._stop_task,
            "get_task_history": self._get_task_history,
            "list_running_tasks": self._list_running_tasks,
            "export_task": self._export_task,
            "import_task": self._import_task,
        }

        if action not in actions:
            return {"success": False, "error": f"Unknown action: {action}. Available: {list(actions.keys())}"}

        try:
            return await actions[action](parameters)
        except Exception as e:
            logger.error(f"Task scheduler operation failed: {e}")
            return {"success": False, "error": str(e)}

    async def _list_tasks(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List all scheduled tasks or tasks in a specific folder."""
        folder = params.get("folder", "\\")
        include_hidden = params.get("include_hidden", False)
        
        cmd = f"""
        $tasks = Get-ScheduledTask -TaskPath '{folder}*' | Select-Object TaskName, TaskPath, State, Description
        $tasks | ConvertTo-Json -Depth 3
        """
        
        result = await self._run_powershell(cmd)
        if result["success"] and result["output"]:
            try:
                tasks = json.loads(result["output"]) if result["output"] else []
                if isinstance(tasks, dict):
                    tasks = [tasks]
                return {"success": True, "tasks": tasks, "count": len(tasks)}
            except json.JSONDecodeError:
                return {"success": True, "tasks": [], "raw_output": result["output"]}
        return result

    async def _get_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed information about a specific task."""
        task_name = params.get("task_name", "")
        task_path = params.get("task_path", "\\")
        
        if not task_name:
            return {"success": False, "error": "task_name is required"}
        
        cmd = f"""
        $task = Get-ScheduledTask -TaskName '{task_name}' -TaskPath '{task_path}' -ErrorAction SilentlyContinue
        if ($task) {{
            $info = Get-ScheduledTaskInfo -TaskName '{task_name}' -TaskPath '{task_path}'
            @{{
                TaskName = $task.TaskName
                TaskPath = $task.TaskPath
                State = $task.State.ToString()
                Description = $task.Description
                Author = $task.Author
                LastRunTime = $info.LastRunTime
                LastTaskResult = $info.LastTaskResult
                NextRunTime = $info.NextRunTime
                NumberOfMissedRuns = $info.NumberOfMissedRuns
            }} | ConvertTo-Json
        }} else {{
            @{{ error = "Task not found" }} | ConvertTo-Json
        }}
        """
        
        result = await self._run_powershell(cmd)
        if result["success"] and result["output"]:
            try:
                task_info = json.loads(result["output"])
                if "error" in task_info:
                    return {"success": False, "error": task_info["error"]}
                return {"success": True, "task": task_info}
            except json.JSONDecodeError:
                return {"success": False, "error": "Failed to parse task info"}
        return result

    async def _create_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new scheduled task."""
        task_name = params.get("task_name", "")
        action_path = params.get("action_path", "")  # Program to run
        action_args = params.get("action_args", "")  # Arguments
        trigger_type = params.get("trigger_type", "once")  # once, daily, weekly, monthly, startup, logon
        start_time = params.get("start_time", "")  # HH:mm format
        start_date = params.get("start_date", "")  # yyyy-MM-dd format
        description = params.get("description", "")
        run_as_user = params.get("run_as_user", "SYSTEM")
        task_path = params.get("task_path", "\\WindowsAI\\")
        
        if not task_name or not action_path:
            return {"success": False, "error": "task_name and action_path are required"}
        
        # Build trigger based on type
        trigger_cmd = ""
        if trigger_type == "once":
            if start_time and start_date:
                trigger_cmd = f"$trigger = New-ScheduledTaskTrigger -Once -At '{start_date} {start_time}'"
            else:
                trigger_cmd = "$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(5)"
        elif trigger_type == "daily":
            trigger_cmd = f"$trigger = New-ScheduledTaskTrigger -Daily -At '{start_time or '09:00'}'"
        elif trigger_type == "weekly":
            days = params.get("days_of_week", "Monday")
            trigger_cmd = f"$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek {days} -At '{start_time or '09:00'}'"
        elif trigger_type == "startup":
            trigger_cmd = "$trigger = New-ScheduledTaskTrigger -AtStartup"
        elif trigger_type == "logon":
            trigger_cmd = "$trigger = New-ScheduledTaskTrigger -AtLogOn"
        else:
            return {"success": False, "error": f"Unknown trigger_type: {trigger_type}"}
        
        cmd = f"""
        $action = New-ScheduledTaskAction -Execute '{action_path}' -Argument '{action_args}'
        {trigger_cmd}
        $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
        Register-ScheduledTask -TaskName '{task_name}' -TaskPath '{task_path}' -Action $action -Trigger $trigger -Settings $settings -Description '{description}' -User '{run_as_user}' -Force
        @{{ success = $true; task_name = '{task_name}' }} | ConvertTo-Json
        """
        
        result = await self._run_powershell(cmd)
        if result["success"]:
            return {"success": True, "message": f"Task '{task_name}' created successfully", "task_path": task_path}
        return result

    async def _delete_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a scheduled task."""
        task_name = params.get("task_name", "")
        task_path = params.get("task_path", "\\")
        
        if not task_name:
            return {"success": False, "error": "task_name is required"}
        
        cmd = f"Unregister-ScheduledTask -TaskName '{task_name}' -TaskPath '{task_path}' -Confirm:$false"
        result = await self._run_powershell(cmd)
        if result["success"]:
            return {"success": True, "message": f"Task '{task_name}' deleted successfully"}
        return result

    async def _enable_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Enable a disabled task."""
        task_name = params.get("task_name", "")
        task_path = params.get("task_path", "\\")
        
        if not task_name:
            return {"success": False, "error": "task_name is required"}
        
        cmd = f"Enable-ScheduledTask -TaskName '{task_name}' -TaskPath '{task_path}'"
        result = await self._run_powershell(cmd)
        if result["success"]:
            return {"success": True, "message": f"Task '{task_name}' enabled"}
        return result

    async def _disable_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Disable a task."""
        task_name = params.get("task_name", "")
        task_path = params.get("task_path", "\\")
        
        if not task_name:
            return {"success": False, "error": "task_name is required"}
        
        cmd = f"Disable-ScheduledTask -TaskName '{task_name}' -TaskPath '{task_path}'"
        result = await self._run_powershell(cmd)
        if result["success"]:
            return {"success": True, "message": f"Task '{task_name}' disabled"}
        return result

    async def _run_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run a task immediately."""
        task_name = params.get("task_name", "")
        task_path = params.get("task_path", "\\")
        
        if not task_name:
            return {"success": False, "error": "task_name is required"}
        
        cmd = f"Start-ScheduledTask -TaskName '{task_name}' -TaskPath '{task_path}'"
        result = await self._run_powershell(cmd)
        if result["success"]:
            return {"success": True, "message": f"Task '{task_name}' started"}
        return result

    async def _stop_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Stop a running task."""
        task_name = params.get("task_name", "")
        task_path = params.get("task_path", "\\")
        
        if not task_name:
            return {"success": False, "error": "task_name is required"}
        
        cmd = f"Stop-ScheduledTask -TaskName '{task_name}' -TaskPath '{task_path}'"
        result = await self._run_powershell(cmd)
        if result["success"]:
            return {"success": True, "message": f"Task '{task_name}' stopped"}
        return result

    async def _get_task_history(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get task execution history."""
        task_name = params.get("task_name", "")
        max_events = params.get("max_events", 10)
        
        if not task_name:
            return {"success": False, "error": "task_name is required"}
        
        cmd = f"""
        $history = Get-WinEvent -FilterHashtable @{{LogName='Microsoft-Windows-TaskScheduler/Operational'; ID=102,201}} -MaxEvents {max_events} -ErrorAction SilentlyContinue | 
            Where-Object {{ $_.Message -like '*{task_name}*' }} |
            Select-Object TimeCreated, Id, Message
        $history | ConvertTo-Json -Depth 2
        """
        
        result = await self._run_powershell(cmd)
        if result["success"] and result["output"]:
            try:
                history = json.loads(result["output"]) if result["output"] else []
                if isinstance(history, dict):
                    history = [history]
                return {"success": True, "history": history}
            except json.JSONDecodeError:
                return {"success": True, "history": [], "raw_output": result["output"]}
        return {"success": True, "history": []}

    async def _list_running_tasks(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List currently running tasks."""
        cmd = """
        Get-ScheduledTask | Where-Object {$_.State -eq 'Running'} | 
        Select-Object TaskName, TaskPath, State | ConvertTo-Json
        """
        
        result = await self._run_powershell(cmd)
        if result["success"] and result["output"]:
            try:
                tasks = json.loads(result["output"]) if result["output"] else []
                if isinstance(tasks, dict):
                    tasks = [tasks]
                return {"success": True, "running_tasks": tasks}
            except json.JSONDecodeError:
                return {"success": True, "running_tasks": []}
        return {"success": True, "running_tasks": []}

    async def _export_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Export a task to XML."""
        task_name = params.get("task_name", "")
        task_path = params.get("task_path", "\\")
        output_path = params.get("output_path", "")
        
        if not task_name:
            return {"success": False, "error": "task_name is required"}
        
        cmd = f"Export-ScheduledTask -TaskName '{task_name}' -TaskPath '{task_path}'"
        result = await self._run_powershell(cmd)
        
        if result["success"] and result["output"]:
            if output_path:
                try:
                    with open(output_path, 'w') as f:
                        f.write(result["output"])
                    return {"success": True, "message": f"Task exported to {output_path}"}
                except Exception as e:
                    return {"success": False, "error": f"Failed to write file: {e}"}
            return {"success": True, "xml": result["output"]}
        return result

    async def _import_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Import a task from XML."""
        task_name = params.get("task_name", "")
        task_path = params.get("task_path", "\\WindowsAI\\")
        xml_path = params.get("xml_path", "")
        xml_content = params.get("xml_content", "")
        
        if not task_name:
            return {"success": False, "error": "task_name is required"}
        
        if xml_path:
            cmd = f"Register-ScheduledTask -TaskName '{task_name}' -TaskPath '{task_path}' -Xml (Get-Content '{xml_path}' -Raw)"
        elif xml_content:
            # Escape the XML for PowerShell
            escaped_xml = xml_content.replace("'", "''")
            cmd = f"Register-ScheduledTask -TaskName '{task_name}' -TaskPath '{task_path}' -Xml '{escaped_xml}'"
        else:
            return {"success": False, "error": "xml_path or xml_content is required"}
        
        result = await self._run_powershell(cmd)
        if result["success"]:
            return {"success": True, "message": f"Task '{task_name}' imported successfully"}
        return result

    async def shutdown(self):
        """Shutdown the plugin."""
        self._initialized = False

    def get_schema(self) -> Dict[str, Any]:
        """Return the plugin schema."""
        return {
            "type": "object",
            "actions": {
                "list_tasks": {"params": {"folder": "string (optional)"}},
                "get_task": {"params": {"task_name": "string", "task_path": "string (optional)"}},
                "create_task": {"params": {
                    "task_name": "string",
                    "action_path": "string (program to run)",
                    "action_args": "string (optional)",
                    "trigger_type": "once|daily|weekly|startup|logon",
                    "start_time": "HH:mm (optional)",
                    "start_date": "yyyy-MM-dd (optional)",
                    "description": "string (optional)"
                }},
                "delete_task": {"params": {"task_name": "string"}},
                "enable_task": {"params": {"task_name": "string"}},
                "disable_task": {"params": {"task_name": "string"}},
                "run_task": {"params": {"task_name": "string"}},
                "stop_task": {"params": {"task_name": "string"}},
                "get_task_history": {"params": {"task_name": "string", "max_events": "int (optional)"}},
                "list_running_tasks": {"params": {}},
                "export_task": {"params": {"task_name": "string", "output_path": "string (optional)"}},
                "import_task": {"params": {"task_name": "string", "xml_path": "string"}}
            }
        }


plugin = WindowsTaskSchedulerPlugin()
