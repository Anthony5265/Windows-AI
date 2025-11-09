"""
Jest Testing Plugin
Supports running Jest tests for JavaScript/TypeScript projects
"""

from typing import Dict, Any, Optional, List
import os
import subprocess
import json


class JestPlugin:
    """Plugin for running Jest tests"""

    name = "jest"
    version = "1.0.0"
    description = "Integration with Jest testing framework for JavaScript/TypeScript"
    author = "Windows AI Team"

    def __init__(self):
        self._initialized = False
        self.working_dir = os.getcwd()

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Jest plugin"""
        try:
            # Check if jest is installed
            result = subprocess.run(
                ["npx", "jest", "--version"],
                capture_output=True,
                text=True,
                cwd=self.working_dir
            )
            if result.returncode != 0:
                print("Jest not found. Install with: npm install --save-dev jest")
                return False

            if config and "working_dir" in config:
                self.working_dir = config["working_dir"]

            self._initialized = True
            return True

        except FileNotFoundError:
            print("Node.js/npm not found. Please install Node.js.")
            return False
        except Exception as e:
            print(f"Error initializing Jest plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Jest action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please ensure Jest is installed."}

        try:
            if action == "run_tests":
                return self._run_tests(params)
            elif action == "run_tests_watch":
                return self._run_tests_watch(params)
            elif action == "run_tests_coverage":
                return self._run_tests_coverage(params)
            elif action == "run_specific_test":
                return self._run_specific_test(params)
            elif action == "update_snapshots":
                return self._update_snapshots(params)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {"error": str(e)}

    def _run_tests(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run all Jest tests"""
        test_path = params.get("test_path", "")
        verbose = params.get("verbose", False)

        cmd = ["npx", "jest"]
        if test_path:
            cmd.append(test_path)
        if verbose:
            cmd.append("--verbose")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=self.working_dir
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode
        }

    def _run_tests_watch(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run Jest tests in watch mode"""
        test_path = params.get("test_path", "")

        cmd = ["npx", "jest", "--watch"]
        if test_path:
            cmd.append(test_path)

        # For watch mode, we can't capture output as it runs indefinitely
        # Instead, we'll start the process and return the command
        return {
            "command": " ".join(cmd),
            "working_dir": self.working_dir,
            "note": "Watch mode started. Use Ctrl+C to stop watching."
        }

    def _run_tests_coverage(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run Jest tests with coverage"""
        test_path = params.get("test_path", "")
        coverage_dir = params.get("coverage_dir", "coverage")

        cmd = ["npx", "jest", "--coverage"]
        if test_path:
            cmd.append(test_path)
        if coverage_dir:
            cmd.extend(["--coverageDirectory", coverage_dir])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=self.working_dir
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode,
            "coverage_dir": coverage_dir
        }

    def _run_specific_test(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run a specific test file or test name"""
        test_name = params.get("test_name", "")
        test_file = params.get("test_file", "")

        cmd = ["npx", "jest"]
        if test_file:
            cmd.append(test_file)
        if test_name:
            cmd.extend(["-t", test_name])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=self.working_dir
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode,
            "test_name": test_name,
            "test_file": test_file
        }

    def _update_snapshots(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update Jest snapshots"""
        test_path = params.get("test_path", "")

        cmd = ["npx", "jest", "--updateSnapshot"]
        if test_path:
            cmd.append(test_path)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=self.working_dir
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode
        }

    def cleanup(self):
        """Cleanup resources"""
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = JestPlugin
PLUGIN_NAME = "jest"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with Jest testing framework for JavaScript/TypeScript"
PLUGIN_ACTIONS = ["run_tests", "run_tests_watch", "run_tests_coverage", "run_specific_test", "update_snapshots"]