"""
Jupyter Notebook IDE Plugin
Supports automation for Jupyter notebooks
"""

from typing import Dict, Any, Optional
import os
import subprocess


class JupyterPlugin:
    """Plugin for Jupyter Notebook integration"""

    name = "jupyter"
    version = "1.0.0"
    description = "Integration with Jupyter for notebook automation"
    author = "Windows AI Team"

    def __init__(self):
        self.jupyter_path: Optional[str] = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Jupyter plugin"""
        try:
            # Check if jupyter is installed
            result = subprocess.run(
                ["jupyter", "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            self.jupyter_path = "jupyter"
            self._initialized = True
            return True

        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"Error initializing Jupyter plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Jupyter action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Jupyter not found."}

        try:
            if action == "open_notebook":
                return self._open_notebook(params)
            elif action == "run_notebook":
                return self._run_notebook(params)
            elif action == "export_notebook":
                return self._export_notebook(params)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {"error": str(e)}

    def _open_notebook(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Open a Jupyter notebook"""
        notebook_path = params.get("notebook_path")
        if not notebook_path:
            return {"error": "notebook_path parameter is required"}

        if not os.path.exists(notebook_path):
            return {"error": f"Notebook file not found: {notebook_path}"}

        try:
            subprocess.Popen([self.jupyter_path, "notebook", notebook_path])
            return {"success": True, "message": "Notebook opened in Jupyter"}
        except Exception as e:
            return {"error": f"Failed to open notebook: {str(e)}"}

    def _run_notebook(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run a Jupyter notebook"""
        notebook_path = params.get("notebook_path")
        output_path = params.get("output_path")

        if not notebook_path:
            return {"error": "notebook_path parameter is required"}

        if not os.path.exists(notebook_path):
            return {"error": f"Notebook file not found: {notebook_path}"}

        try:
            cmd = [self.jupyter_path, "nbconvert", "--execute", notebook_path]
            if output_path:
                cmd.extend(["--output", output_path])

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                return {"success": True, "output": result.stdout.strip()}
            else:
                return {"error": result.stderr.strip()}

        except Exception as e:
            return {"error": f"Failed to run notebook: {str(e)}"}

    def _export_notebook(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Export a Jupyter notebook"""
        notebook_path = params.get("notebook_path")
        export_format = params.get("format", "html")
        output_path = params.get("output_path")

        if not notebook_path:
            return {"error": "notebook_path parameter is required"}

        if not os.path.exists(notebook_path):
            return {"error": f"Notebook file not found: {notebook_path}"}

        supported_formats = ["html", "pdf", "markdown", "python", "script"]
        if export_format not in supported_formats:
            return {"error": f"Unsupported export format: {export_format}. Supported: {', '.join(supported_formats)}"}

        try:
            cmd = [self.jupyter_path, "nbconvert", "--to", export_format, notebook_path]
            if output_path:
                cmd.extend(["--output", output_path])

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                return {"success": True, "output": result.stdout.strip()}
            else:
                return {"error": result.stderr.strip()}

        except Exception as e:
            return {"error": f"Failed to export notebook: {str(e)}"}

    def cleanup(self):
        """Cleanup resources"""
        self._initialized = False


# Plugin metadata for registration
PLUGIN_CLASS = JupyterPlugin
PLUGIN_NAME = "jupyter"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with Jupyter for notebook automation"
PLUGIN_ACTIONS = ["open_notebook", "run_notebook", "export_notebook"]