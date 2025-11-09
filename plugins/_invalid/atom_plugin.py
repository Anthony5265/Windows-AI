"""
Atom Editor AI Model Plugin
Supports AI-assisted coding and integration with Atom editor
"""

from typing import Dict, Any, Optional, List
import os
import subprocess
import tempfile
import json


class AtomPlugin:
    """Plugin for Atom editor AI integration"""

    name = "atom"
    version = "1.0.0"
    description = "Integration with Atom editor for AI-assisted coding"
    author = "Windows AI Team"

    def __init__(self):
        self.atom_path: Optional[str] = None
        self.apm_path: Optional[str] = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Atom plugin"""
        try:
            # Find Atom installation
            possible_paths = [
                r"C:\Users\%USERNAME%\AppData\Local\atom\bin\atom.cmd",
                r"C:\Program Files\Atom\bin\atom.cmd",
                "/usr/bin/atom",
                "/usr/local/bin/atom",
                "/opt/atom/bin/atom"
            ]

            for path in possible_paths:
                expanded_path = os.path.expandvars(path)
                if os.path.exists(expanded_path):
                    self.atom_path = expanded_path
                    break

            if not self.atom_path:
                # Try to find atom in PATH
                try:
                    result = subprocess.run(["where", "atom"], capture_output=True, text=True, check=True)
                    self.atom_path = result.stdout.strip().split('\n')[0]
                except:
                    pass

            if not self.atom_path:
                return False

            # Find APM (Atom Package Manager)
            apm_paths = [
                self.atom_path.replace("atom.cmd", "apm.cmd").replace("atom", "apm"),
                os.path.join(os.path.dirname(self.atom_path), "apm.cmd"),
                os.path.join(os.path.dirname(self.atom_path), "apm")
            ]

            for path in apm_paths:
                if os.path.exists(path):
                    self.apm_path = path
                    break

            # Try to find apm in PATH
            if not self.apm_path:
                try:
                    result = subprocess.run(["where", "apm"], capture_output=True, text=True, check=True)
                    self.apm_path = result.stdout.strip().split('\n')[0]
                except:
                    pass

            self._initialized = True
            return True

        except Exception as e:
            print(f"Error initializing Atom plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an Atom action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Atom not found."}

        try:
            if action == "open_file":
                return self._open_file(params)
            elif action == "open_project":
                return self._open_project(params)
            elif action == "generate_and_open":
                return self._generate_and_open(params)
            elif action == "install_package":
                return self._install_package(params)
            elif action == "run_command":
                return self._run_command(params)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {"error": str(e)}

    def _open_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Open a file in Atom"""
        file_path = params.get("file_path")
        if not file_path:
            return {"error": "file_path parameter is required"}

        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}

        try:
            subprocess.Popen([self.atom_path, file_path])
            return {"success": True, "message": "File opened in Atom"}
        except Exception as e:
            return {"error": f"Failed to open file: {str(e)}"}

    def _open_project(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Open a project directory in Atom"""
        project_path = params.get("project_path")
        if not project_path:
            return {"error": "project_path parameter is required"}

        if not os.path.exists(project_path):
            return {"error": f"Project directory not found: {project_path}"}

        try:
            subprocess.Popen([self.atom_path, project_path])
            return {"success": True, "message": "Project opened in Atom"}
        except Exception as e:
            return {"error": f"Failed to open project: {str(e)}"}

    def _generate_and_open(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code and open in Atom"""
        code = params.get("code", "")
        language = params.get("language", "python")
        file_name = params.get("file_name", f"generated.{language}")

        if not code:
            return {"error": "code parameter is required"}

        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix=f".{language}", delete=False) as f:
                f.write(code)
                temp_file = f.name

            # Open in Atom
            subprocess.Popen([self.atom_path, temp_file])
            return {
                "success": True,
                "message": "Generated code opened in Atom",
                "temp_file": temp_file
            }
        except Exception as e:
            return {"error": f"Failed to generate and open code: {str(e)}"}

    def _install_package(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Install an Atom package"""
        package_name = params.get("package_name")
        if not package_name:
            return {"error": "package_name parameter is required"}

        if not self.apm_path:
            return {"error": "APM not found. Cannot install packages."}

        try:
            result = subprocess.run([
                self.apm_path, "install", package_name
            ], capture_output=True, text=True)

            if result.returncode == 0:
                return {"success": True, "output": result.stdout.strip()}
            else:
                return {"error": result.stderr.strip()}

        except Exception as e:
            return {"error": f"Failed to install package: {str(e)}"}

    def _run_command(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run an Atom command"""
        command = params.get("command")
        args = params.get("args", [])

        if not command:
            return {"error": "command parameter is required"}

        try:
            cmd_args = [self.atom_path, "--command", command] + args
            result = subprocess.run(cmd_args, capture_output=True, text=True)

            if result.returncode == 0:
                return {"success": True, "output": result.stdout.strip()}
            else:
                return {"error": result.stderr.strip()}

        except Exception as e:
            return {"error": f"Failed to run command: {str(e)}"}

    def cleanup(self):
        """Cleanup resources"""
        self.atom_path = None
        self.apm_path = None
        self._initialized = False


# Plugin metadata for registration
PLUGIN_CLASS = AtomPlugin
PLUGIN_NAME = "atom"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with Atom editor for AI-assisted coding"
PLUGIN_ACTIONS = ["open_file", "open_project", "generate_and_open", "install_package", "run_command"]</content>
<parameter name="filePath">plugins/ai_models/atom_plugin.py