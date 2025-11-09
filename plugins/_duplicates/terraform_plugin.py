"""
Terraform DevOps Plugin
Plugin for managing Terraform infrastructure as code
"""

from typing import Dict, Any, Optional, List
import os
import subprocess
import logging
from pathlib import Path


class TerraformPlugin:
    """Plugin for Terraform infrastructure management"""

    name = "terraform"
    version = "1.0.0"
    description = "Plugin for managing Terraform infrastructure as code"
    author = "Windows AI Team"

    def __init__(self):
        self.terraform_path: Optional[str] = None
        self.working_dir: Optional[str] = None
        self._initialized = False
        self.logger = logging.getLogger(__name__)

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Terraform plugin"""
        try:
            # Check if terraform is installed
            self.terraform_path = self._find_terraform()
            if not self.terraform_path:
                self.logger.error("Terraform not found. Please install Terraform and ensure it's in PATH")
                return False

            # Set working directory
            self.working_dir = config.get("working_dir", os.getcwd()) if config else os.getcwd()
            if not Path(self.working_dir).exists():
                self.logger.error(f"Working directory does not exist: {self.working_dir}")
                return False

            self._initialized = True
            self.logger.info("Terraform plugin initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error initializing Terraform plugin: {e}")
            return False

    def _find_terraform(self) -> Optional[str]:
        """Find terraform executable"""
        # Check PATH
        try:
            result = subprocess.run(["terraform", "version"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return "terraform"
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        # Check common locations
        common_paths = [
            "/usr/local/bin/terraform",
            "/usr/bin/terraform",
            "C:\\Program Files\\Terraform\\terraform.exe",
            "C:\\Terraform\\terraform.exe"
        ]

        for path in common_paths:
            if Path(path).exists():
                return path

        return None

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Terraform action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please check Terraform installation."}

        try:
            if action == "init":
                return self._terraform_init(params)
            elif action == "plan":
                return self._terraform_plan(params)
            elif action == "apply":
                return self._terraform_apply(params)
            elif action == "destroy":
                return self._terraform_destroy(params)
            elif action == "validate":
                return self._terraform_validate(params)
            elif action == "fmt":
                return self._terraform_fmt(params)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            self.logger.error(f"Error executing action {action}: {e}")
            return {"error": str(e)}

    def _run_terraform_command(self, args: List[str], cwd: Optional[str] = None) -> Dict[str, Any]:
        """Run a terraform command"""
        try:
            cmd = [self.terraform_path] + args
            working_dir = cwd or self.working_dir

            result = subprocess.run(
                cmd,
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )

            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": " ".join(cmd)
            }

        except subprocess.TimeoutExpired:
            return {"error": "Command timed out"}
        except Exception as e:
            return {"error": f"Failed to run command: {e}"}

    def _terraform_init(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize Terraform working directory"""
        args = ["init"]
        if params.get("upgrade"):
            args.append("-upgrade")
        if params.get("reconfigure"):
            args.append("-reconfigure")

        return self._run_terraform_command(args)

    def _terraform_plan(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a Terraform plan"""
        args = ["plan"]
        if params.get("out"):
            args.extend(["-out", params["out"]])
        if params.get("var_file"):
            args.extend(["-var-file", params["var_file"]])
        if params.get("vars"):
            for key, value in params["vars"].items():
                args.extend(["-var", f"{key}={value}"])

        return self._run_terraform_command(args)

    def _terraform_apply(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Apply Terraform changes"""
        args = ["apply"]
        if params.get("auto_approve"):
            args.append("-auto-approve")
        if params.get("plan_file"):
            args.append(params["plan_file"])
        if params.get("var_file"):
            args.extend(["-var-file", params["var_file"]])
        if params.get("vars"):
            for key, value in params["vars"].items():
                args.extend(["-var", f"{key}={value}"])

        return self._run_terraform_command(args)

    def _terraform_destroy(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Destroy Terraform-managed infrastructure"""
        args = ["destroy"]
        if params.get("auto_approve"):
            args.append("-auto-approve")
        if params.get("var_file"):
            args.extend(["-var-file", params["var_file"]])
        if params.get("vars"):
            for key, value in params["vars"].items():
                args.extend(["-var", f"{key}={value}"])

        return self._run_terraform_command(args)

    def _terraform_validate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Terraform configuration"""
        args = ["validate"]
        return self._run_terraform_command(args)

    def _terraform_fmt(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Format Terraform configuration files"""
        args = ["fmt"]
        if params.get("check"):
            args.append("-check")
        if params.get("diff"):
            args.append("-diff")

        return self._run_terraform_command(args)

    def cleanup(self):
        """Cleanup resources"""
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = TerraformPlugin
PLUGIN_NAME = "terraform"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Plugin for managing Terraform infrastructure as code"
PLUGIN_ACTIONS = ["init", "plan", "apply", "destroy", "validate", "fmt"]