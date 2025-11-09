"""
VS Code Remote Plugin
Supports integration with VS Code Remote for remote development
"""

from typing import Dict, Any, Optional
import os
import subprocess
import shutil


class VSCodeRemotePlugin:
    """Plugin for VS Code Remote integration"""

    name = "vscode_remote"
    version = "1.0.0"
    description = "Integration with VS Code Remote for remote development"
    author = "Windows AI Team"

    def __init__(self):
        self.code_path: Optional[str] = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the VS Code Remote plugin"""
        try:
            # Find VS Code installation
            self.code_path = shutil.which("code")
            if not self.code_path:
                # Try common Windows installation paths
                common_paths = [
                    r"C:\Program Files\Microsoft VS Code\bin\code.cmd",
                    r"C:\Program Files\Microsoft VS Code\Code.exe",
                    r"C:\Users\{}\AppData\Local\Programs\Microsoft VS Code\bin\code.cmd".format(os.getenv("USERNAME", "")),
                    r"C:\Users\{}\AppData\Local\Programs\Microsoft VS Code\Code.exe".format(os.getenv("USERNAME", ""))
                ]
                for path in common_paths:
                    if os.path.exists(path):
                        self.code_path = path
                        break

            if not self.code_path:
                return False

            # Test if VS Code responds
            result = subprocess.run([
                self.code_path, "--version"
            ], capture_output=True, text=True, timeout=10)

            if result.returncode != 0:
                return False

            self._initialized = True
            return True

        except Exception as e:
            print(f"Error initializing VS Code Remote plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a VS Code Remote action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. VS Code not found."}

        try:
            if action == "connect_ssh":
                return self._connect_ssh(params)
            elif action == "open_remote_folder":
                return self._open_remote_folder(params)
            elif action == "install_remote_extension":
                return self._install_remote_extension(params)
            elif action == "run_remote_command":
                return self._run_remote_command(params)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {"error": str(e)}

    def _connect_ssh(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Connect to SSH remote host"""
        host = params.get("host")
        user = params.get("user")
        if not host:
            return {"error": "host parameter is required"}

        try:
            # Build SSH remote URI
            remote_uri = f"vscode-remote://ssh-remote+{user}@{host}" if user else f"vscode-remote://ssh-remote+{host}"

            # Use --folder-uri to open remote connection
            subprocess.Popen([self.code_path, "--folder-uri", remote_uri])
            return {"success": True, "message": f"Connecting to SSH remote: {host}"}

        except Exception as e:
            return {"error": f"Failed to connect to SSH remote: {str(e)}"}

    def _open_remote_folder(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Open a folder on remote host"""
        host = params.get("host")
        user = params.get("user")
        folder_path = params.get("folder_path")

        if not host:
            return {"error": "host parameter is required"}
        if not folder_path:
            return {"error": "folder_path parameter is required"}

        try:
            # Build SSH remote URI with folder
            remote_uri = f"vscode-remote://ssh-remote+{user}@{host}{folder_path}" if user else f"vscode-remote://ssh-remote+{host}{folder_path}"

            subprocess.Popen([self.code_path, "--folder-uri", remote_uri])
            return {"success": True, "message": f"Opening remote folder: {folder_path} on {host}"}

        except Exception as e:
            return {"error": f"Failed to open remote folder: {str(e)}"}

    def _install_remote_extension(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Install extension on remote host"""
        host = params.get("host")
        user = params.get("user")
        extension_id = params.get("extension_id")

        if not host:
            return {"error": "host parameter is required"}
        if not extension_id:
            return {"error": "extension_id parameter is required"}

        try:
            # Build remote command
            remote_target = f"{user}@{host}" if user else host

            result = subprocess.run([
                self.code_path,
                "--remote", f"ssh-remote+{remote_target}",
                "--install-extension", extension_id
            ], capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                return {"success": True, "output": result.stdout.strip()}
            else:
                return {"error": result.stderr.strip() or "Failed to install extension"}

        except subprocess.TimeoutExpired:
            return {"error": "Extension installation timed out"}
        except Exception as e:
            return {"error": f"Failed to install remote extension: {str(e)}"}

    def _run_remote_command(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run command on remote host"""
        host = params.get("host")
        user = params.get("user")
        command = params.get("command")

        if not host:
            return {"error": "host parameter is required"}
        if not command:
            return {"error": "command parameter is required"}

        try:
            # For running commands, we might need to use SSH directly
            # since VS Code CLI doesn't have a direct command execution feature
            ssh_command = ["ssh"]
            if user:
                ssh_command.extend(["-l", user])
            ssh_command.append(host)
            ssh_command.extend(command.split())  # Simple split, could be improved

            result = subprocess.run(
                ssh_command,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                return {"success": True, "output": result.stdout.strip()}
            else:
                return {"error": result.stderr.strip() or "Command failed"}

        except subprocess.TimeoutExpired:
            return {"error": "Remote command timed out"}
        except Exception as e:
            return {"error": f"Failed to run remote command: {str(e)}"}

    def cleanup(self):
        """Cleanup resources"""
        self._initialized = False


# Plugin metadata for registration
PLUGIN_CLASS = VSCodeRemotePlugin
PLUGIN_NAME = "vscode_remote"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with VS Code Remote for remote development"
PLUGIN_ACTIONS = ["connect_ssh", "open_remote_folder", "install_remote_extension", "run_remote_command"]