"""
Visual Studio IDE Plugin
Supports project automation for Visual Studio projects
"""

from typing import Dict, Any, Optional
import os
import subprocess


class VisualStudioPlugin:
    """Plugin for Visual Studio IDE integration"""

    name = "visualstudio"
    version = "1.0.0"
    description = "Integration with Visual Studio for project automation"
    author = "Windows AI Team"

    def __init__(self):
        self.devenv_path: Optional[str] = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Visual Studio plugin"""
        try:
            # Find Visual Studio installation using vswhere
            vswhere_path = r"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe"
            if not os.path.exists(vswhere_path):
                return False

            result = subprocess.run([
                vswhere_path,
                "-latest",
                "-property",
                "installationPath"
            ], capture_output=True, text=True, check=True)

            install_path = result.stdout.strip()
            self.devenv_path = os.path.join(install_path, "Common7", "IDE", "devenv.exe")

            if not os.path.exists(self.devenv_path):
                return False

            self._initialized = True
            return True

        except Exception as e:
            print(f"Error initializing Visual Studio plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Visual Studio action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Visual Studio not found."}

        try:
            if action == "open_project":
                return self._open_project(params)
            elif action == "build_project":
                return self._build_project(params)
            elif action == "clean_project":
                return self._clean_project(params)
            elif action == "run_project":
                return self._run_project(params)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {"error": str(e)}

    def _open_project(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Open a Visual Studio project"""
        project_path = params.get("project_path")
        if not project_path:
            return {"error": "project_path parameter is required"}

        if not os.path.exists(project_path):
            return {"error": f"Project file not found: {project_path}"}

        try:
            subprocess.Popen([self.devenv_path, project_path])
            return {"success": True, "message": "Project opened in Visual Studio"}
        except Exception as e:
            return {"error": f"Failed to open project: {str(e)}"}

    def _build_project(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Build a Visual Studio project"""
        project_path = params.get("project_path")
        configuration = params.get("configuration", "Release")

        if not project_path:
            return {"error": "project_path parameter is required"}

        if not os.path.exists(project_path):
            return {"error": f"Project file not found: {project_path}"}

        try:
            result = subprocess.run([
                self.devenv_path,
                project_path,
                "/build",
                configuration
            ], capture_output=True, text=True)

            if result.returncode == 0:
                return {"success": True, "output": result.stdout.strip()}
            else:
                return {"error": result.stderr.strip()}

        except Exception as e:
            return {"error": f"Failed to build project: {str(e)}"}

    def _clean_project(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Clean a Visual Studio project"""
        project_path = params.get("project_path")
        configuration = params.get("configuration", "Release")

        if not project_path:
            return {"error": "project_path parameter is required"}

        if not os.path.exists(project_path):
            return {"error": f"Project file not found: {project_path}"}

        try:
            result = subprocess.run([
                self.devenv_path,
                project_path,
                "/clean",
                configuration
            ], capture_output=True, text=True)

            if result.returncode == 0:
                return {"success": True, "output": result.stdout.strip()}
            else:
                return {"error": result.stderr.strip()}

        except Exception as e:
            return {"error": f"Failed to clean project: {str(e)}"}

    def _run_project(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run a Visual Studio project"""
        project_path = params.get("project_path")
        if not project_path:
            return {"error": "project_path parameter is required"}

        if not os.path.exists(project_path):
            return {"error": f"Project file not found: {project_path}"}

        try:
            subprocess.Popen([self.devenv_path, project_path, "/run"])
            return {"success": True, "message": "Project started"}
        except Exception as e:
            return {"error": f"Failed to run project: {str(e)}"}

    def cleanup(self):
        """Cleanup resources"""
        self._initialized = False


# Plugin metadata for registration
PLUGIN_CLASS = VisualStudioPlugin
PLUGIN_NAME = "visualstudio"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with Visual Studio for project automation"
PLUGIN_ACTIONS = ["open_project", "build_project", "clean_project", "run_project"]