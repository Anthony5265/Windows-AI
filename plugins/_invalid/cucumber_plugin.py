"""
Cucumber Testing Framework Plugin
Supports running Cucumber tests for behavior-driven development (BDD)
"""

from typing import Dict, Any, Optional
import os
import subprocess
import json
import glob


class CucumberPlugin:
    """Plugin for running Cucumber BDD tests"""

    name = "cucumber"
    version = "1.0.0"
    description = "Integration with Cucumber testing framework for BDD"
    author = "Windows AI Team"

    def __init__(self):
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Cucumber plugin"""
        try:
            # Check if Node.js is installed
            result = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                print("Node.js not found. Please install Node.js to use Cucumber plugin.")
                return False

            # Check if Cucumber.js is installed
            try:
                result = subprocess.run(
                    ["npx", "cucumber-js", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode != 0:
                    print("Cucumber.js not found. Install with: npm install -g @cucumber/cucumber")
                    return False
            except FileNotFoundError:
                print("npx not found. Please ensure npm is installed.")
                return False

            self._initialized = True
            return True

        except Exception as e:
            print(f"Error initializing Cucumber plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Cucumber action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please ensure Node.js and Cucumber.js are installed."}

        try:
            if action == "run":
                return self._run_tests(params)
            elif action == "list_features":
                return self._list_features(params)
            elif action == "list_scenarios":
                return self._list_scenarios(params)
            elif action == "generate_report":
                return self._generate_report(params)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {"error": str(e)}

    def _run_tests(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run Cucumber tests"""
        features_dir = params.get("features_dir", "features")
        step_definitions = params.get("step_definitions", "features/step_definitions")
        format = params.get("format", "pretty")
        tags = params.get("tags", "")
        parallel = params.get("parallel", 0)

        # Ensure features directory exists
        if not os.path.exists(features_dir):
            return {"error": f"Features directory '{features_dir}' does not exist"}

        # Build cucumber command
        cmd = [
            "npx", "cucumber-js",
            "--format", format,
            features_dir
        ]

        if step_definitions and os.path.exists(step_definitions):
            cmd.extend(["--require", step_definitions])

        if tags:
            cmd.extend(["--tags", tags])

        if parallel > 0:
            cmd.extend(["--parallel", str(parallel)])

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
                "returncode": result.returncode
            }

        except subprocess.TimeoutExpired:
            return {"error": "Test execution timed out"}
        except Exception as e:
            return {"error": f"Failed to run tests: {str(e)}"}

    def _list_features(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List available feature files"""
        features_dir = params.get("features_dir", "features")

        if not os.path.exists(features_dir):
            return {"error": f"Features directory '{features_dir}' does not exist"}

        feature_files = []
        for root, dirs, files in os.walk(features_dir):
            for file in files:
                if file.endswith('.feature'):
                    feature_files.append(os.path.join(root, file))

        return {
            "feature_files": feature_files,
            "count": len(feature_files)
        }

    def _list_scenarios(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List scenarios from feature files"""
        features_dir = params.get("features_dir", "features")

        if not os.path.exists(features_dir):
            return {"error": f"Features directory '{features_dir}' does not exist"}

        scenarios = []

        # Use cucumber-js dry-run to list scenarios
        cmd = [
            "npx", "cucumber-js",
            "--dry-run",
            "--format", "json",
            features_dir
        ]

        try:
            result = subprocess.run(
                cmd,
                cwd=os.getcwd(),
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0 and result.stdout:
                try:
                    data = json.loads(result.stdout)
                    for feature in data:
                        feature_name = feature.get("name", "")
                        for element in feature.get("elements", []):
                            if element.get("type") == "scenario":
                                scenarios.append({
                                    "feature": feature_name,
                                    "scenario": element.get("name", ""),
                                    "tags": [tag["name"] for tag in element.get("tags", [])]
                                })
                except json.JSONDecodeError:
                    pass

        except Exception as e:
            return {"error": f"Failed to list scenarios: {str(e)}"}

        return {
            "scenarios": scenarios,
            "count": len(scenarios)
        }

    def _generate_report(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test report"""
        features_dir = params.get("features_dir", "features")
        output_file = params.get("output_file", "cucumber-report.json")
        format = params.get("format", "json")

        if not os.path.exists(features_dir):
            return {"error": f"Features directory '{features_dir}' does not exist"}

        cmd = [
            "npx", "cucumber-js",
            "--format", f"{format}:{output_file}",
            features_dir
        ]

        try:
            result = subprocess.run(
                cmd,
                cwd=os.getcwd(),
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0 and os.path.exists(output_file):
                return {
                    "success": True,
                    "report_file": output_file,
                    "stdout": result.stdout
                }
            else:
                return {
                    "success": False,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }

        except Exception as e:
            return {"error": f"Failed to generate report: {str(e)}"}

    def cleanup(self):
        """Cleanup resources"""
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = CucumberPlugin
PLUGIN_NAME = "cucumber"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with Cucumber testing framework for BDD"
PLUGIN_ACTIONS = ["run", "list_features", "list_scenarios", "generate_report"]