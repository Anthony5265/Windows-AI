"""
PowerShell Integration Module
Execute PowerShell scripts and commands from Python
"""
from typing import Dict, Any, List, Optional
import logging
import subprocess
import platform
import json

logger = logging.getLogger(__name__)

IS_WINDOWS = platform.system() == "Windows"


class PowerShellManager:
    """Production PowerShell integration"""

    def __init__(self):
        self.is_available = IS_WINDOWS
        self.powershell_path = "powershell.exe" if IS_WINDOWS else None

    def execute(self, command: str, **kwargs) -> Dict[str, Any]:
        """
        Execute PowerShell command

        Args:
            command: PowerShell command to execute
            timeout: Command timeout in seconds
            encode_command: Base64 encode command (useful for complex scripts)

        Returns:
            Dict with stdout, stderr, and return code
        """
        if not self.is_available:
            return {
                "status": "error",
                "message": "PowerShell not available (not Windows)"
            }

        timeout = kwargs.get("timeout", 300)
        encode_command = kwargs.get("encode_command", False)

        try:
            if encode_command:
                import base64
                encoded = base64.b64encode(command.encode("utf-16le")).decode("ascii")
                ps_command = [self.powershell_path, "-EncodedCommand", encoded]
            else:
                ps_command = [
                    self.powershell_path,
                    "-NoProfile",
                    "-NonInteractive",
                    "-Command",
                    command
                ]

            result = subprocess.run(
                ps_command,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            return {
                "status": "success",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "success": result.returncode == 0
            }

        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "message": f"Command timed out after {timeout} seconds"
            }
        except Exception as e:
            logger.error(f"PowerShell execute error: {e}")
            return {"status": "error", "message": str(e)}

    def execute_script(self, script_path: str, **kwargs) -> Dict[str, Any]:
        """
        Execute PowerShell script file

        Args:
            script_path: Path to .ps1 script file
            parameters: Dict of parameters to pass to script
            timeout: Script timeout in seconds

        Returns:
            Dict with stdout, stderr, and return code
        """
        if not self.is_available:
            return {
                "status": "error",
                "message": "PowerShell not available"
            }

        parameters = kwargs.get("parameters", {})
        timeout = kwargs.get("timeout", 300)

        try:
            # Build command with parameters
            command_parts = [self.powershell_path, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script_path]

            for key, value in parameters.items():
                command_parts.extend([f"-{key}", str(value)])

            result = subprocess.run(
                command_parts,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            return {
                "status": "success",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "success": result.returncode == 0
            }

        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "message": f"Script timed out after {timeout} seconds"
            }
        except Exception as e:
            logger.error(f"PowerShell execute script error: {e}")
            return {"status": "error", "message": str(e)}

    def get_command_output(self, command: str, **kwargs) -> Dict[str, Any]:
        """
        Execute PowerShell command and return output as structured data

        Args:
            command: PowerShell command
            output_format: Format of output (json, text)

        Returns:
            Dict with parsed output
        """
        output_format = kwargs.get("output_format", "text")

        result = self.execute(command, **kwargs)

        if result["status"] != "success":
            return result

        if output_format == "json":
            try:
                parsed = json.loads(result["stdout"])
                result["parsed_output"] = parsed
            except json.JSONDecodeError as e:
                result["parse_error"] = str(e)

        return result

    def get_system_info_ps(self) -> Dict[str, Any]:
        """Get system information using PowerShell"""
        command = """
        Get-ComputerInfo | ConvertTo-Json -Depth 2
        """

        return self.get_command_output(command, output_format="json", timeout=60)

    def get_processes_ps(self, name_filter: str = None) -> Dict[str, Any]:
        """Get process information using PowerShell"""
        if name_filter:
            command = f"""
            Get-Process -Name '{name_filter}' | Select-Object Name, Id, CPU, WorkingSet, Path | ConvertTo-Json
            """
        else:
            command = """
            Get-Process | Select-Object Name, Id, CPU, WorkingSet, Path | ConvertTo-Json
            """

        return self.get_command_output(command, output_format="json", timeout=60)

    def get_services_ps(self, state_filter: str = None) -> Dict[str, Any]:
        """Get services information using PowerShell"""
        if state_filter:
            command = f"""
            Get-Service | Where-Object {{$_.Status -eq '{state_filter}'}} | Select-Object Name, DisplayName, Status, StartType | ConvertTo-Json
            """
        else:
            command = """
            Get-Service | Select-Object Name, DisplayName, Status, StartType | ConvertTo-Json
            """

        return self.get_command_output(command, output_format="json", timeout=60)

    def get_event_logs(self, log_name: str = "System", max_events: int = 100) -> Dict[str, Any]:
        """Get Windows event logs using PowerShell"""
        command = f"""
        Get-EventLog -LogName '{log_name}' -Newest {max_events} | Select-Object TimeGenerated, EntryType, Source, EventID, Message | ConvertTo-Json
        """

        return self.get_command_output(command, output_format="json", timeout=60)

    def get_installed_software(self) -> Dict[str, Any]:
        """Get installed software using PowerShell"""
        command = """
        Get-ItemProperty HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* |
        Select-Object DisplayName, DisplayVersion, Publisher, InstallDate |
        Where-Object {$_.DisplayName} |
        ConvertTo-Json
        """

        return self.get_command_output(command, output_format="json", timeout=120)

    def get_network_config(self) -> Dict[str, Any]:
        """Get network configuration using PowerShell"""
        command = """
        Get-NetIPConfiguration | Select-Object InterfaceAlias, InterfaceDescription, IPv4Address, IPv6Address, DNSServer | ConvertTo-Json
        """

        return self.get_command_output(command, output_format="json", timeout=60)

    def test_network_connection(self, target: str, count: int = 4) -> Dict[str, Any]:
        """Test network connection using PowerShell"""
        command = f"""
        Test-Connection -ComputerName '{target}' -Count {count} | Select-Object Address, ResponseTime, StatusCode | ConvertTo-Json
        """

        return self.get_command_output(command, output_format="json", timeout=30)

    def get_disk_space(self) -> Dict[str, Any]:
        """Get disk space information using PowerShell"""
        command = """
        Get-PSDrive -PSProvider FileSystem |
        Select-Object Name, @{Name='Used(GB)';Expression={[math]::Round($_.Used/1GB,2)}}, @{Name='Free(GB)';Expression={[math]::Round($_.Free/1GB,2)}} |
        ConvertTo-Json
        """

        return self.get_command_output(command, output_format="json", timeout=60)

    def manage_scheduled_task(self, action: str, task_name: str, **kwargs) -> Dict[str, Any]:
        """
        Manage Windows scheduled tasks

        Args:
            action: Action to perform (get, create, run, disable, enable, delete)
            task_name: Name of the task
            trigger: Task trigger for create action
            task_path: Script/program path for create action

        Returns:
            Dict with operation result
        """
        if action == "get":
            command = f"Get-ScheduledTask -TaskName '{task_name}' | ConvertTo-Json"
            return self.get_command_output(command, output_format="json")

        elif action == "run":
            command = f"Start-ScheduledTask -TaskName '{task_name}'"
            return self.execute(command)

        elif action == "disable":
            command = f"Disable-ScheduledTask -TaskName '{task_name}'"
            return self.execute(command)

        elif action == "enable":
            command = f"Enable-ScheduledTask -TaskName '{task_name}'"
            return self.execute(command)

        elif action == "delete":
            command = f"Unregister-ScheduledTask -TaskName '{task_name}' -Confirm:$false"
            return self.execute(command)

        else:
            return {
                "status": "error",
                "message": f"Unknown action: {action}"
            }
