"""
Mocha Testing Framework Plugin
Supports running Mocha tests for JavaScript/Node.js projects
"""

from typing import Dict, Any, Optional
import os
import subprocess
import json


class MochaPlugin:
    """Plugin for running Mocha tests"""

    name = "mocha"
    version = "1.0.0"
    description = "Integration with Mocha testing framework"
    author = "Windows AI Team"

    def __init__(self):
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Mocha plugin"""
        try:
            # Check if Node.js is installed
            result = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                print("Node.js not found. Please install Node.js to use Mocha plugin.")
                return False

            # Check if Mocha is installed globally or locally
            try:
                result = subprocess.run(
                    ["npx", "mocha", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode != 0:
                    print("Mocha not found. Install with: npm install -g mocha")
                    return False
            except FileNotFoundError:
                print("npx not found. Please ensure npm is installed.")
                return False

            self._initialized = True
            return True

        except Exception as e:
            print(f"Error initializing Mocha plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Mocha action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please ensure Node.js and Mocha are installed."}

        try:
            if action == "run":
                return self._run_tests(params)
            elif action == "list":
                return self._list_tests(params)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {"error": str(e)}

    def _run_tests(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run Mocha tests"""
        test_dir = params.get("test_dir", "test")
        pattern = params.get("pattern", "**/*.test.js")
        timeout = params.get("timeout", 2000)
        reporter = params.get("reporter", "spec")

        # Ensure test directory exists
        if not os.path.exists(test_dir):
            return {"error": f"Test directory '{test_dir}' does not exist"}

        # Build mocha command
        cmd = [
            "npx", "mocha",
            "--timeout", str(timeout),
            "--reporter", reporter,
            "--recursive",
            test_dir
        ]

        if pattern:
            cmd.extend(["--grep", pattern])

        try:
            result = subprocess.run(
                cmd,
                cwd=os.getcwd(),
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }

        except subprocess.TimeoutExpired:
            return {"error": "Test execution timed out"}
        except Exception as e:
            return {"error": f"Failed to run tests: {str(e)}"}

    def _list_tests(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List available test files"""
        test_dir = params.get("test_dir", "test")

        if not os.path.exists(test_dir):
            return {"error": f"Test directory '{test_dir}' does not exist"}

        test_files = []
        for root, dirs, files in os.walk(test_dir):
            for file in files:
                if file.endswith('.test.js') or file.endswith('.spec.js'):
                    test_files.append(os.path.join(root, file))

        return {
            "test_files": test_files,
            "count": len(test_files)
        }

    def cleanup(self):
        """Cleanup resources"""
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = MochaPlugin
PLUGIN_NAME = "mocha"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with Mocha testing framework"
PLUGIN_ACTIONS = ["run", "list"]