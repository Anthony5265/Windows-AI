"""
NetBeans IDE Plugin
Supports project automation for Apache NetBeans IDE
"""

from typing import Dict, Any, Optional
import os
import subprocess
import platform


class NetBeansPlugin:
    """Plugin for Apache NetBeans IDE integration"""

    name = "netbeans"
    version = "1.0.0"
    description = "Integration with Apache NetBeans IDE for project automation"
    author = "Windows AI Team"

    def __init__(self):
        self.netbeans_path: Optional[str] = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the NetBeans plugin"""
        try:
            # Check for custom NetBeans path in config
            if config and config.get("netbeans_path"):
                self.netbeans_path = config["netbeans_path"]
                if os.path.exists(self.netbeans_path):
                    self._initialized = True
                    return True

            # Auto-detect NetBeans installation
            system = platform.system().lower()

            if system == "windows":
                # Common Windows installation paths
                possible_paths = [
                    r"C:\Program Files\NetBeans\bin\netbeans.exe",
                    r"C:\Program Files (x86)\NetBeans\bin\netbeans.exe",
                    r"C:\netbeans\bin\netbeans.exe",
                    os.path.expanduser(r"~\netbeans\bin\netbeans.exe")
                ]

                for path in possible_paths:
                    if os.path.exists(path):
                        self.netbeans_path = path
                        self._initialized = True
                        return True

                # Try to find via environment or registry (simplified)
                netbeans_home = os.getenv("NETBEANS_HOME")
                if netbeans_home:
                    exe_path = os.path.join(netbeans_home, "bin", "netbeans.exe")
                    if os.path.exists(exe_path):
                        self.netbeans_path = exe_path
                        self._initialized = True
                        return True

            elif system == "linux":
                # Common Linux installation paths
                possible_paths = [
                    "/usr/local/netbeans/bin/netbeans",
                    "/opt/netbeans/bin/netbeans",
                    os.path.expanduser("~/netbeans/bin/netbeans")
                ]

                for path in possible_paths:
                    if os.path.exists(path):
                        self.netbeans_path = path
                        self._initialized = True
                        return True

                # Try which command
                try:
                    result = subprocess.run(["which", "netbeans"],
                                          capture_output=True, text=True, check=True)
                    self.netbeans_path = result.stdout.strip()
                    self._initialized = True
                    return True
                except subprocess.CalledProcessError:
                    pass

            elif system == "darwin":  # macOS
                # Common macOS installation paths
                possible_paths = [
                    "/Applications/NetBeans/NetBeans.app/Contents/MacOS/netbeans",
                    os.path.expanduser("~/Applications/NetBeans/NetBeans.app/Contents/MacOS/netbeans")
                ]

                for path in possible_paths:
                    if os.path.exists(path):
                        self.netbeans_path = path
                        self._initialized = True
                        return True

            return False

        except Exception as e:
            print(f"Error initializing NetBeans plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a NetBeans action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. NetBeans installation not found."}

        try:
            if action == "open_project":
                return self._open_project(params)
            elif action == "build_project":
                return self._build_project(params)
            elif action == "clean_project":
                return self._clean_project(params)
            elif action == "run_project":
                return self._run_project(params)
            elif action == "create_project":
                return self._create_project(params)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {"error": str(e)}

    def _open_project(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Open a NetBeans project"""
        project_path = params.get("project_path")
        if not project_path:
            return {"error": "project_path parameter is required"}

        if not os.path.exists(project_path):
            return {"error": f"Project directory not found: {project_path}"}

        try:
            # NetBeans can open project directories directly
            subprocess.Popen([self.netbeans_path, "--open", project_path])
            return {"success": True, "message": "Project opened in NetBeans"}
        except Exception as e:
            return {"error": f"Failed to open project: {str(e)}"}

    def _build_project(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Build a NetBeans project"""
        project_path = params.get("project_path")
        if not project_path:
            return {"error": "project_path parameter is required"}

        if not os.path.exists(project_path):
            return {"error": f"Project directory not found: {project_path}"}

        try:
            # Use ant or maven depending on project type
            build_file = self._detect_build_system(project_path)
            if not build_file:
                return {"error": "Could not detect build system (ant or maven)"}

            if build_file.endswith("build.xml"):
                # Ant project
                result = subprocess.run(
                    ["ant", "-f", build_file],
                    cwd=project_path,
                    capture_output=True,
                    text=True
                )
            elif build_file.endswith("pom.xml"):
                # Maven project
                result = subprocess.run(
                    ["mvn", "compile"],
                    cwd=project_path,
                    capture_output=True,
                    text=True
                )
            else:
                return {"error": f"Unsupported build file: {build_file}"}

            if result.returncode == 0:
                return {"success": True, "output": result.stdout.strip()}
            else:
                return {"error": result.stderr.strip()}

        except FileNotFoundError:
            return {"error": "Build tool (ant/mvn) not found in PATH"}
        except Exception as e:
            return {"error": f"Failed to build project: {str(e)}"}

    def _clean_project(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Clean a NetBeans project"""
        project_path = params.get("project_path")
        if not project_path:
            return {"error": "project_path parameter is required"}

        if not os.path.exists(project_path):
            return {"error": f"Project directory not found: {project_path}"}

        try:
            build_file = self._detect_build_system(project_path)
            if not build_file:
                return {"error": "Could not detect build system (ant or maven)"}

            if build_file.endswith("build.xml"):
                # Ant project
                result = subprocess.run(
                    ["ant", "-f", build_file, "clean"],
                    cwd=project_path,
                    capture_output=True,
                    text=True
                )
            elif build_file.endswith("pom.xml"):
                # Maven project
                result = subprocess.run(
                    ["mvn", "clean"],
                    cwd=project_path,
                    capture_output=True,
                    text=True
                )
            else:
                return {"error": f"Unsupported build file: {build_file}"}

            if result.returncode == 0:
                return {"success": True, "output": result.stdout.strip()}
            else:
                return {"error": result.stderr.strip()}

        except FileNotFoundError:
            return {"error": "Build tool (ant/mvn) not found in PATH"}
        except Exception as e:
            return {"error": f"Failed to clean project: {str(e)}"}

    def _run_project(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run a NetBeans project"""
        project_path = params.get("project_path")
        if not project_path:
            return {"error": "project_path parameter is required"}

        if not os.path.exists(project_path):
            return {"error": f"Project directory not found: {project_path}"}

        try:
            build_file = self._detect_build_system(project_path)
            if not build_file:
                return {"error": "Could not detect build system (ant or maven)"}

            if build_file.endswith("build.xml"):
                # Ant project - try common run targets
                result = subprocess.run(
                    ["ant", "-f", build_file, "run"],
                    cwd=project_path,
                    capture_output=True,
                    text=True
                )
            elif build_file.endswith("pom.xml"):
                # Maven project
                result = subprocess.run(
                    ["mvn", "exec:java"],
                    cwd=project_path,
                    capture_output=True,
                    text=True
                )
            else:
                return {"error": f"Unsupported build file: {build_file}"}

            if result.returncode == 0:
                return {"success": True, "output": result.stdout.strip()}
            else:
                return {"error": result.stderr.strip()}

        except FileNotFoundError:
            return {"error": "Build tool (ant/mvn) not found in PATH"}
        except Exception as e:
            return {"error": f"Failed to run project: {str(e)}"}

    def _create_project(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new NetBeans project"""
        project_type = params.get("project_type", "java-application")
        project_name = params.get("project_name")
        project_path = params.get("project_path")

        if not project_name:
            return {"error": "project_name parameter is required"}
        if not project_path:
            return {"error": "project_path parameter is required"}

        if os.path.exists(project_path):
            return {"error": f"Project path already exists: {project_path}"}

        try:
            # Use NetBeans command line to create project
            # This is a simplified version - NetBeans CLI might vary
            cmd = [
                self.netbeans_path,
                "--create-project",
                f"--type={project_type}",
                f"--name={project_name}",
                project_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                return {"success": True, "message": f"Project created at {project_path}"}
            else:
                return {"error": result.stderr.strip()}

        except Exception as e:
            return {"error": f"Failed to create project: {str(e)}"}

    def _detect_build_system(self, project_path: str) -> Optional[str]:
        """Detect the build system used by the project"""
        # Check for Maven
        pom_xml = os.path.join(project_path, "pom.xml")
        if os.path.exists(pom_xml):
            return pom_xml

        # Check for Ant
        build_xml = os.path.join(project_path, "build.xml")
        if os.path.exists(build_xml):
            return build_xml

        # Check for Gradle
        build_gradle = os.path.join(project_path, "build.gradle")
        if os.path.exists(build_gradle):
            return build_gradle

        return None

    def cleanup(self):
        """Cleanup resources"""
        self._initialized = False


# Plugin metadata for registration
PLUGIN_CLASS = NetBeansPlugin
PLUGIN_NAME = "netbeans"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with Apache NetBeans IDE for project automation"
PLUGIN_ACTIONS = ["open_project", "build_project", "clean_project", "run_project", "create_project"]