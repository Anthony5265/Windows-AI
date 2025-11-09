"""
TestCafe Testing Framework Plugin
Supports running TestCafe tests for web applications
"""

from typing import Dict, Any, Optional
import os
import subprocess
import json


class TestCafePlugin:
    """Plugin for running TestCafe tests"""

    name = "testcafe"
    version = "1.0.0"
    description = "Integration with TestCafe testing framework"
    author = "Windows AI Team"

    def __init__(self):
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the TestCafe plugin"""
        try:
            # Check if Node.js is installed
            result = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                print("Node.js not found. Please install Node.js to use TestCafe plugin.")
                return False

            # Check if TestCafe is installed globally or locally
            try:
                result = subprocess.run(
                    ["npx", "testcafe", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode != 0:
                    print("TestCafe not found. Install with: npm install -g testcafe")
                    return False
            except FileNotFoundError:
                print("npx not found. Please ensure npm is installed.")
                return False

            self._initialized = True
            return True

        except Exception as e:
            print(f"Error initializing TestCafe plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a TestCafe action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please ensure Node.js and TestCafe are installed."}

        try:
            if action == "run":
                return self._run_tests(params)
            elif action == "list_browsers":
                return self._list_browsers(params)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {"error": str(e)}

    def _run_tests(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run TestCafe tests"""
        browsers = params.get("browsers", "chrome")
        test_files = params.get("test_files", "test/**/*.js")
        base_url = params.get("base_url", "")
        timeout = params.get("timeout", 3000)
        reporter = params.get("reporter", "spec")
        concurrency = params.get("concurrency", 1)

        # Build testcafe command
        cmd = [
            "npx", "testcafe",
            browsers,
            test_files,
            "--reporter", reporter,
            "--concurrency", str(concurrency),
            "--selector-timeout", str(timeout)
        ]

        if base_url:
            cmd.extend(["--base-url", base_url])

        # Add any additional flags
        if params.get("debug"):
            cmd.append("--debug-mode")
        if params.get("screenshots"):
            cmd.extend(["--screenshots", params.get("screenshots_path", "screenshots")])
        if params.get("videos"):
            cmd.extend(["--video", params.get("videos_path", "videos")])

        try:
            result = subprocess.run(
                cmd,
                cwd=os.getcwd(),
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "command": " ".join(cmd)
            }

        except subprocess.TimeoutExpired:
            return {"error": "Test execution timed out"}
        except Exception as e:
            return {"error": f"Failed to run tests: {str(e)}"}

    def _list_browsers(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List available browsers for TestCafe"""
        try:
            result = subprocess.run(
                ["npx", "testcafe", "--list-browsers"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                browsers = result.stdout.strip().split('\n')
                browsers = [b.strip() for b in browsers if b.strip()]
                return {
                    "browsers": browsers,
                    "count": len(browsers)
                }
            else:
                return {"error": "Failed to list browsers", "stderr": result.stderr}

        except Exception as e:
            return {"error": f"Failed to list browsers: {str(e)}"}

    def cleanup(self):
        """Cleanup resources"""
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = TestCafePlugin
PLUGIN_NAME = "testcafe"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with TestCafe testing framework"
PLUGIN_ACTIONS = ["run", "list_browsers"]