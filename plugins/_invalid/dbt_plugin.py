"""
dbt (Data Build Tool) Plugin
Supports dbt project management, model execution, and data transformation workflows
"""

from typing import Dict, Any, Optional, List
import os
import json
import subprocess
import sys
from pathlib import Path


class DBTPlugin:
    """Plugin for dbt (Data Build Tool) integration"""

    name = "dbt"
    version = "1.0.0"
    description = "Integration with dbt for data transformation and analytics engineering"
    author = "Windows AI Team"

    def __init__(self):
        self.project_path: Optional[str] = None
        self.profiles_path: Optional[str] = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the dbt plugin"""
        try:
            if config:
                self.project_path = config.get("project_path")
                self.profiles_path = config.get("profiles_path")
            
            # Check if dbt is installed
            try:
                subprocess.run(["dbt", "--version"], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("dbt not found. Install with: pip install dbt-core")
                return False

            # Validate project path if provided
            if self.project_path and not os.path.exists(os.path.join(self.project_path, "dbt_project.yml")):
                print(f"Invalid dbt project path: {self.project_path}")
                return False

            self._initialized = True
            return True

        except Exception as e:
            print(f"Error initializing dbt plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a dbt action"""
        if not self._initialized:
            return {"error": "Plugin not initialized"}

        try:
            if action == "run":
                return self._run_models(params)
            elif action == "test":
                return self._test_models(params)
            elif action == "build":
                return self._build_project(params)
            elif action == "seed":
                return self._run_seeds(params)
            elif action == "snapshot":
                return self._run_snapshots(params)
            elif action == "compile":
                return self._compile_models(params)
            elif action == "docs_generate":
                return self._generate_docs(params)
            elif action == "docs_serve":
                return self._serve_docs(params)
            elif action == "list":
                return self._list_resources(params)
            elif action == "parse":
                return self._parse_project(params)
            elif action == "freshness":
                return self._check_freshness(params)
            elif action == "debug":
                return self._debug_connection(params)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {"error": str(e)}

    def _run_models(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run dbt models"""
        models = params.get("models", "")
        select = params.get("select", "")
        exclude = params.get("exclude", "")
        full_refresh = params.get("full_refresh", False)
        threads = params.get("threads", 1)

        cmd = ["dbt", "run"]
        
        if models:
            cmd.extend(["--models", models])
        if select:
            cmd.extend(["--select", select])
        if exclude:
            cmd.extend(["--exclude", exclude])
        if full_refresh:
            cmd.append("--full-refresh")
        if threads > 1:
            cmd.extend(["--threads", str(threads)])

        result = self._execute_dbt_command(cmd)
        return {"command": " ".join(cmd), "result": result}

    def _test_models(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run dbt tests"""
        models = params.get("models", "")
        select = params.get("select", "")
        exclude = params.get("exclude", "")
        threads = params.get("threads", 1)

        cmd = ["dbt", "test"]
        
        if models:
            cmd.extend(["--models", models])
        if select:
            cmd.extend(["--select", select])
        if exclude:
            cmd.extend(["--exclude", exclude])
        if threads > 1:
            cmd.extend(["--threads", str(threads)])

        result = self._execute_dbt_command(cmd)
        return {"command": " ".join(cmd), "result": result}

    def _build_project(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Build dbt project (run + test)"""
        select = params.get("select", "")
        exclude = params.get("exclude", "")
        full_refresh = params.get("full_refresh", False)
        threads = params.get("threads", 1)

        cmd = ["dbt", "build"]
        
        if select:
            cmd.extend(["--select", select])
        if exclude:
            cmd.extend(["--exclude", exclude])
        if full_refresh:
            cmd.append("--full-refresh")
        if threads > 1:
            cmd.extend(["--threads", str(threads)])

        result = self._execute_dbt_command(cmd)
        return {"command": " ".join(cmd), "result": result}

    def _run_seeds(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run dbt seeds"""
        select = params.get("select", "")
        show = params.get("show", False)
        threads = params.get("threads", 1)

        cmd = ["dbt", "seed"]
        
        if select:
            cmd.extend(["--select", select])
        if show:
            cmd.append("--show")
        if threads > 1:
            cmd.extend(["--threads", str(threads)])

        result = self._execute_dbt_command(cmd)
        return {"command": " ".join(cmd), "result": result}

    def _run_snapshots(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run dbt snapshots"""
        select = params.get("select", "")
        threads = params.get("threads", 1)

        cmd = ["dbt", "snapshot"]
        
        if select:
            cmd.extend(["--select", select])
        if threads > 1:
            cmd.extend(["--threads", str(threads)])

        result = self._execute_dbt_command(cmd)
        return {"command": " ".join(cmd), "result": result}

    def _compile_models(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Compile dbt models"""
        models = params.get("models", "")
        select = params.get("select", "")
        exclude = params.get("exclude", "")
        threads = params.get("threads", 1)

        cmd = ["dbt", "compile"]
        
        if models:
            cmd.extend(["--models", models])
        if select:
            cmd.extend(["--select", select])
        if exclude:
            cmd.extend(["--exclude", exclude])
        if threads > 1:
            cmd.extend(["--threads", str(threads)])

        result = self._execute_dbt_command(cmd)
        return {"command": " ".join(cmd), "result": result}

    def _generate_docs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate dbt documentation"""
        threads = params.get("threads", 1)

        cmd = ["dbt", "docs", "generate"]
        
        if threads > 1:
            cmd.extend(["--threads", str(threads)])

        result = self._execute_dbt_command(cmd)
        return {"command": " ".join(cmd), "result": result}

    def _serve_docs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Serve dbt documentation"""
        port = params.get("port", 8080)
        browser = params.get("browser", True)

        cmd = ["dbt", "docs", "serve", "--port", str(port)]
        
        if not browser:
            cmd.append("--no-browser")

        result = self._execute_dbt_command(cmd)
        return {"command": " ".join(cmd), "result": result}

    def _list_resources(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List dbt resources"""
        resource_type = params.get("resource_type", "")
        select = params.get("select", "")
        exclude = params.get("exclude", "")

        cmd = ["dbt", "list"]
        
        if resource_type:
            cmd.extend(["--resource-type", resource_type])
        if select:
            cmd.extend(["--select", select])
        if exclude:
            cmd.extend(["--exclude", exclude])

        result = self._execute_dbt_command(cmd)
        return {"command": " ".join(cmd), "result": result}

    def _parse_project(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Parse dbt project"""
        threads = params.get("threads", 1)

        cmd = ["dbt", "parse"]
        
        if threads > 1:
            cmd.extend(["--threads", str(threads)])

        result = self._execute_dbt_command(cmd)
        return {"command": " ".join(cmd), "result": result}

    def _check_freshness(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Check source freshness"""
        select = params.get("select", "")
        threads = params.get("threads", 1)

        cmd = ["dbt", "source", "freshness"]
        
        if select:
            cmd.extend(["--select", select])
        if threads > 1:
            cmd.extend(["--threads", str(threads)])

        result = self._execute_dbt_command(cmd)
        return {"command": " ".join(cmd), "result": result}

    def _debug_connection(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Debug dbt connection"""
        threads = params.get("threads", 1)

        cmd = ["dbt", "debug"]
        
        if threads > 1:
            cmd.extend(["--threads", str(threads)])

        result = self._execute_dbt_command(cmd)
        return {"command": " ".join(cmd), "result": result}

    def _execute_dbt_command(self, cmd: List[str]) -> Dict[str, Any]:
        """Execute a dbt command and return the result"""
        try:
            # Set working directory if project path is specified
            cwd = self.project_path if self.project_path else None
            
            # Set environment variables
            env = os.environ.copy()
            if self.profiles_path:
                env["DBT_PROFILES_DIR"] = self.profiles_path

            # Execute the command
            process = subprocess.run(
                cmd,
                cwd=cwd,
                env=env,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            return {
                "returncode": process.returncode,
                "stdout": process.stdout,
                "stderr": process.stderr,
                "success": process.returncode == 0
            }

        except subprocess.TimeoutExpired:
            return {
                "error": "Command timed out after 5 minutes",
                "success": False
            }
        except Exception as e:
            return {
                "error": str(e),
                "success": False
            }

    def get_project_info(self) -> Dict[str, Any]:
        """Get information about the current dbt project"""
        if not self._initialized:
            return {"error": "Plugin not initialized"}

        try:
            if not self.project_path:
                return {"error": "No project path configured"}

            project_file = os.path.join(self.project_path, "dbt_project.yml")
            if not os.path.exists(project_file):
                return {"error": "dbt_project.yml not found"}

            with open(project_file, 'r') as f:
                project_config = yaml.safe_load(f)

            return {
                "project_name": project_config.get("name"),
                "version": project_config.get("version"),
                "profile": project_config.get("profile"),
                "model_paths": project_config.get("model-paths", []),
                "seed_paths": project_config.get("seed-paths", []),
                "test_paths": project_config.get("test-paths", []),
                "config": project_config
            }

        except Exception as e:
            return {"error": str(e)}

    def cleanup(self):
        """Cleanup resources"""
        self.project_path = None
        self.profiles_path = None
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = DBTPlugin
PLUGIN_NAME = "dbt"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with dbt for data transformation and analytics engineering"
PLUGIN_ACTIONS = [
    "run", "test", "build", "seed", "snapshot", "compile",
    "docs_generate", "docs_serve", "list", "parse", "freshness", "debug"
]