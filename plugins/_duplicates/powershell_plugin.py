"""
PowerShell Automation Plugin
Supports script execution and cmdlet invocation on Windows
"""

from typing import Dict, Any, Optional
import subprocess
import os


class PowerShellPlugin:
    """Plugin for PowerShell automation"""

    name = "powershell"
    version = "1.0.0"
    description = "PowerShell script execution and cmdlet invocation"
    author = "Windows AI Team"

    def __init__(self):
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the PowerShell plugin"""
        try:
            # Check if PowerShell is available
            result = subprocess.run(
                ["powershell", "-Command", "Write-Host 'PowerShell available'"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                self._initialized = True
                return True
            else:
                print("PowerShell not available or not working")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            print(f"Error initializing PowerShell plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a PowerShell action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. PowerShell may not be available."}

        try:
            if action == "execute_script":
                return self._execute_script(params)
            elif action == "invoke_cmdlet":
                return self._invoke_cmdlet(params)
            else:
                return {"error": f"Unknown action: {action}"}
        except Exception as e:
            return {"error": str(e)}

    def _execute_script(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a PowerShell script file"""
        script_path = params.get("script_path")
        if not script_path:
            return {"error": "script_path parameter required"}

        if not os.path.exists(script_path):
            return {"error": f"Script file not found: {script_path}"}

        try:
            # Execute the script
            result = subprocess.run(
                ["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path],
                capture_output=True,
                text=True,
                timeout=params.get("timeout", 30)
            )

            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "success": result.returncode == 0
            }
        except subprocess.TimeoutExpired:
            return {"error": "Script execution timed out"}
        except Exception as e:
            return {"error": f"Failed to execute script: {str(e)}"}

    def _invoke_cmdlet(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke a PowerShell cmdlet"""
        cmdlet = params.get("cmdlet")
        if not cmdlet:
            return {"error": "cmdlet parameter required"}

        # Build the command
        command = [cmdlet]
        args = params.get("args", [])
        if args:
            command.extend(args)

        try:
            # Run the cmdlet
            result = subprocess.run(
                ["powershell", "-Command", " ".join(command)],
                capture_output=True,
                text=True,
                timeout=params.get("timeout", 30)
            )

            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "success": result.returncode == 0
            }
        except subprocess.TimeoutExpired:
            return {"error": "Cmdlet execution timed out"}
        except Exception as e:
            return {"error": f"Failed to invoke cmdlet: {str(e)}"}

    def cleanup(self):
        """Cleanup resources"""
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = PowerShellPlugin
PLUGIN_NAME = "powershell"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "PowerShell script execution and cmdlet invocation"
PLUGIN_ACTIONS = ["execute_script", "invoke_cmdlet"]