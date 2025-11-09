"""
Emacs IDE Plugin
Supports integration with Emacs for file editing and code evaluation
"""

from typing import Dict, Any, Optional
import os
import subprocess
import shutil


class EmacsPlugin:
    """Plugin for Emacs IDE integration"""

    name = "emacs"
    version = "1.0.0"
    description = "Integration with Emacs for file editing and code evaluation"
    author = "Windows AI Team"

    def __init__(self):
        self.emacsclient_path: Optional[str] = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Emacs plugin"""
        try:
            # Check if emacsclient is in PATH
            self.emacsclient_path = shutil.which("emacsclient")
            if not self.emacsclient_path:
                # Try common Windows installation paths
                common_paths = [
                    r"C:\Program Files\Emacs\bin\emacsclient.exe",
                    r"C:\Program Files (x86)\Emacs\bin\emacsclient.exe",
                    r"C:\emacs\bin\emacsclient.exe"
                ]
                for path in common_paths:
                    if os.path.exists(path):
                        self.emacsclient_path = path
                        break

            if not self.emacsclient_path:
                return False

            # Test if emacsclient can connect (assuming Emacs server is running)
            result = subprocess.run([
                self.emacsclient_path, "--eval", "(+ 1 1)"
            ], capture_output=True, text=True, timeout=5)

            # Even if it fails, we consider initialized if path exists
            self._initialized = True
            return True

        except Exception as e:
            print(f"Error initializing Emacs plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an Emacs action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Emacs client not found or not running."}

        try:
            if action == "open_file":
                return self._open_file(params)
            elif action == "eval_code":
                return self._eval_code(params)
            elif action == "load_elisp":
                return self._load_elisp(params)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {"error": str(e)}

    def _open_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Open a file in Emacs"""
        file_path = params.get("file_path")
        if not file_path:
            return {"error": "file_path parameter is required"}

        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}

        try:
            # Use Popen to not block
            subprocess.Popen([self.emacsclient_path, file_path])
            return {"success": True, "message": "File opened in Emacs"}
        except Exception as e:
            return {"error": f"Failed to open file: {str(e)}"}

    def _eval_code(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate Emacs Lisp code"""
        code = params.get("code")
        if not code:
            return {"error": "code parameter is required"}

        try:
            result = subprocess.run([
                self.emacsclient_path, "--eval", code
            ], capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                return {"success": True, "output": result.stdout.strip()}
            else:
                return {"error": result.stderr.strip() or "Evaluation failed"}

        except subprocess.TimeoutExpired:
            return {"error": "Evaluation timed out"}
        except Exception as e:
            return {"error": f"Failed to evaluate code: {str(e)}"}

    def _load_elisp(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Load an Emacs Lisp file"""
        file_path = params.get("file_path")
        if not file_path:
            return {"error": "file_path parameter is required"}

        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}

        try:
            # Load the file by evaluating (load "path")
            load_expr = f'(load "{file_path}")'
            result = subprocess.run([
                self.emacsclient_path, "--eval", load_expr
            ], capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                return {"success": True, "output": result.stdout.strip()}
            else:
                return {"error": result.stderr.strip() or "Load failed"}

        except subprocess.TimeoutExpired:
            return {"error": "Load timed out"}
        except Exception as e:
            return {"error": f"Failed to load file: {str(e)}"}

    def cleanup(self):
        """Cleanup resources"""
        self._initialized = False


# Plugin metadata for registration
PLUGIN_CLASS = EmacsPlugin
PLUGIN_NAME = "emacs"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with Emacs for file editing and code evaluation"
PLUGIN_ACTIONS = ["open_file", "eval_code", "load_elisp"]