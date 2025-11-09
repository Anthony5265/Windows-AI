"""
Eclipse IDE Plugin
Supports project automation for Eclipse projects
"""

from typing import Dict, Any, Optional
import os
import subprocess
import glob


class EclipsePlugin:
    """Plugin for Eclipse IDE integration"""

    name = "eclipse"
    version = "1.0.0"
    description = "Integration with Eclipse for project automation"
    author = "Windows AI Team"

    def __init__(self):
        self.eclipse_path: Optional[str] = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Eclipse plugin"""
        try:
            # Common Eclipse installation paths
            possible_paths = [
                r"C:\Program Files\Eclipse\eclipse.exe",
                r"C:\Program Files (x86)\Eclipse\eclipse.exe",
                r"C:\eclipse\eclipse.exe",
                # Add more paths if needed
            ]

            for path in possible_paths:
                if os.path.exists(path):
                    self.eclipse_path = path
                    break

            # If not found in common paths, try to find in PATH
            if not self.eclipse_path:
                try:
                    result = subprocess.run(["where", "eclipse"], capture_output=True, text=True, check=True)
                    self.eclipse_path = result.stdout.strip().split('\n')[0]
                except subprocess.CalledProcessError:
                    pass

            if not self.eclipse_path or not os.path.exists(self.eclipse_path):
                return False

            self._initialized = True
            return True

        except Exception as e:
            print(f"Error initializing Eclipse plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an Eclipse action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Eclipse not found."}

        try:
            if action == "open_workspace":
                return self._open_workspace(params)
            elif action == "open_project":
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

    def _open_workspace(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Open an Eclipse workspace"""
        workspace_path = params.get("workspace_path")
        if not workspace_path:
            return {"error": "workspace_path parameter is required"}

        if not os.path.exists(workspace_path):
            return {"error": f"Workspace directory not found: {workspace_path}"}

        try:
            subprocess.Popen([self.eclipse_path, "-data", workspace_path])
            return {"success": True, "message": "Workspace opened in Eclipse"}
        except Exception as e:
            return {"error": f"Failed to open workspace: {str(e)}"}

    def _open_project(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Open an Eclipse project"""
        project_path = params.get("project_path")
        workspace_path = params.get("workspace_path")

        if not project_path:
            return {"error": "project_path parameter is required"}

        if not os.path.exists(project_path):
            return {"error": f"Project directory not found: {project_path}"}

        # Check if it's a valid Eclipse project
        if not os.path.exists(os.path.join(project_path, ".project")):
            return {"error": f"Not a valid Eclipse project: {project_path}"}

        try:
            cmd = [self.eclipse_path]
            if workspace_path:
                cmd.extend(["-data", workspace_path])
            cmd.extend(["-import", project_path])
            subprocess.Popen(cmd)
            return {"success": True, "message": "Project opened in Eclipse"}
        except Exception as e:
            return {"error": f"Failed to open project: {str(e)}"}

    def _build_project(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Build an Eclipse project"""
        project_path = params.get("project_path")
        if not project_path:
            return {"error": "project_path parameter is required"}

        if not os.path.exists(project_path):
            return {"error": f"Project directory not found: {project_path}"}

        # For Eclipse builds, we might need to use command line build tools
        # This is a simplified version - in practice, Eclipse projects often use Maven/Gradle
        try:
            # Check for Maven
            if os.path.exists(os.path.join(project_path, "pom.xml")):
                if self._run_command(["mvn", "clean", "compile"], cwd=project_path):
                    return {"success": True, "message": "Project built successfully with Maven"}
                else:
                    return {"error": "Maven build failed"}

            # Check for Gradle
            elif os.path.exists(os.path.join(project_path, "build.gradle")):
                if self._run_command(["gradle", "build"], cwd=project_path):
                    return {"success": True, "message": "Project built successfully with Gradle"}
                else:
                    return {"error": "Gradle build failed"}

            else:
                return {"error": "No supported build system found (Maven or Gradle)"}

        except Exception as e:
            return {"error": f"Failed to build project: {str(e)}"}

    def _clean_project(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Clean an Eclipse project"""
        project_path = params.get("project_path")
        if not project_path:
            return {"error": "project_path parameter is required"}

        if not os.path.exists(project_path):
            return {"error": f"Project directory not found: {project_path}"}

        try:
            # Check for Maven
            if os.path.exists(os.path.join(project_path, "pom.xml")):
                if self._run_command(["mvn", "clean"], cwd=project_path):
                    return {"success": True, "message": "Project cleaned successfully with Maven"}
                else:
                    return {"error": "Maven clean failed"}

            # Check for Gradle
            elif os.path.exists(os.path.join(project_path, "build.gradle")):
                if self._run_command(["gradle", "clean"], cwd=project_path):
                    return {"success": True, "message": "Project cleaned successfully with Gradle"}
                else:
                    return {"error": "Gradle clean failed"}

            else:
                return {"error": "No supported build system found (Maven or Gradle)"}

        except Exception as e:
            return {"error": f"Failed to clean project: {str(e)}"}

    def _run_project(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run an Eclipse project"""
        project_path = params.get("project_path")
        main_class = params.get("main_class")

        if not project_path:
            return {"error": "project_path parameter is required"}

        if not os.path.exists(project_path):
            return {"error": f"Project directory not found: {project_path}"}

        try:
            # For Java projects, try to run with Maven or Gradle
            if os.path.exists(os.path.join(project_path, "pom.xml")):
                cmd = ["mvn", "exec:java"]
                if main_class:
                    cmd.extend(["-Dexec.mainClass=" + main_class])
                if self._run_command(cmd, cwd=project_path):
                    return {"success": True, "message": "Project executed successfully"}
                else:
                    return {"error": "Failed to run project"}

            elif os.path.exists(os.path.join(project_path, "build.gradle")):
                cmd = ["gradle", "run"]
                if self._run_command(cmd, cwd=project_path):
                    return {"success": True, "message": "Project executed successfully"}
                else:
                    return {"error": "Failed to run project"}

            else:
                return {"error": "No supported run configuration found"}

        except Exception as e:
            return {"error": f"Failed to run project: {str(e)}"}

    def _run_command(self, cmd: list, cwd: Optional[str] = None) -> bool:
        """Run a command and return success status"""
        try:
            result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False

    def cleanup(self):
        """Cleanup resources"""
        self._initialized = False


# Plugin metadata for registration
PLUGIN_CLASS = EclipsePlugin
PLUGIN_NAME = "eclipse"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with Eclipse for project automation"
PLUGIN_ACTIONS = ["open_workspace", "open_project", "build_project", "clean_project", "run_project"]