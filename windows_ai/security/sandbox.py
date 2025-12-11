"""
Sandbox Manager for Windows AI
Provides isolation and containment for AI operations
"""

import asyncio
import logging
import os
import sys
import tempfile
import subprocess
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)

class SandboxLevel(Enum):
    NONE = "none"  # No sandboxing - full system access
    MINIMAL = "minimal"  # Basic restrictions
    STANDARD = "standard"  # Balanced security/functionality
    STRICT = "strict"  # High security, limited functionality
    MAXIMUM = "maximum"  # Maximum isolation

@dataclass
class SandboxConfig:
    level: SandboxLevel = SandboxLevel.STANDARD
    allowed_paths: List[str] = field(default_factory=list)
    blocked_paths: List[str] = field(default_factory=list)
    allowed_commands: List[str] = field(default_factory=list)
    blocked_commands: List[str] = field(default_factory=list)
    network_access: bool = True
    max_memory_mb: int = 4096
    max_cpu_percent: int = 80
    timeout_seconds: int = 300
    allow_file_write: bool = True
    allow_file_delete: bool = False
    allow_registry_access: bool = False
    allow_process_spawn: bool = True

class SandboxManager:
    """Manages sandboxed execution environments"""

    def __init__(self):
        self.config = SandboxConfig()
        self.active_sandboxes: Dict[str, Any] = {}
        self._initialized = False

    async def initialize(self, config: Optional[Dict[str, Any]] = None):
        """Initialize sandbox manager"""
        if self._initialized:
            return

        if config:
            level = config.get("level", "standard")
            self.config.level = SandboxLevel(level)
            self._apply_level_defaults()

        self._initialized = True
        logger.info(f"Sandbox manager initialized with level: {self.config.level.value}")

    def _apply_level_defaults(self):
        """Apply default settings based on sandbox level"""
        if self.config.level == SandboxLevel.NONE:
            self.config.network_access = True
            self.config.allow_file_write = True
            self.config.allow_file_delete = True
            self.config.allow_registry_access = True
            self.config.allow_process_spawn = True
            self.config.blocked_commands = []

        elif self.config.level == SandboxLevel.MINIMAL:
            self.config.network_access = True
            self.config.allow_file_write = True
            self.config.allow_file_delete = True
            self.config.allow_registry_access = False
            self.config.blocked_commands = ["format", "del /s", "rm -rf /"]

        elif self.config.level == SandboxLevel.STANDARD:
            self.config.network_access = True
            self.config.allow_file_write = True
            self.config.allow_file_delete = False
            self.config.allow_registry_access = False
            self.config.blocked_commands = [
                "format", "del", "rmdir", "rm -rf",
                "shutdown", "restart", "regedit"
            ]
            self.config.blocked_paths = [
                "C:\\Windows\\System32",
                "C:\\Program Files",
                "/usr/bin", "/etc", "/var"
            ]

        elif self.config.level == SandboxLevel.STRICT:
            self.config.network_access = True
            self.config.allow_file_write = False
            self.config.allow_file_delete = False
            self.config.allow_registry_access = False
            self.config.allow_process_spawn = False
            self.config.max_memory_mb = 2048
            self.config.timeout_seconds = 60

        elif self.config.level == SandboxLevel.MAXIMUM:
            self.config.network_access = False
            self.config.allow_file_write = False
            self.config.allow_file_delete = False
            self.config.allow_registry_access = False
            self.config.allow_process_spawn = False
            self.config.max_memory_mb = 1024
            self.config.max_cpu_percent = 50
            self.config.timeout_seconds = 30

    def set_level(self, level: SandboxLevel):
        """Set sandbox level"""
        self.config.level = level
        self._apply_level_defaults()
        logger.info(f"Sandbox level set to: {level.value}")

    def is_path_allowed(self, path: str) -> bool:
        """Check if a path is allowed"""
        path = os.path.abspath(path)

        # Check blocked paths
        for blocked in self.config.blocked_paths:
            if path.startswith(blocked):
                return False

        # Check allowed paths if specified
        if self.config.allowed_paths:
            for allowed in self.config.allowed_paths:
                if path.startswith(allowed):
                    return True
            return False

        return True

    def is_command_allowed(self, command: str) -> bool:
        """Check if a command is allowed"""
        command_lower = command.lower()

        # Check blocked commands
        for blocked in self.config.blocked_commands:
            if blocked.lower() in command_lower:
                return False

        # Check allowed commands if specified
        if self.config.allowed_commands:
            for allowed in self.config.allowed_commands:
                if allowed.lower() in command_lower:
                    return True
            return False

        return True

    async def execute_sandboxed(
        self,
        command: str,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Execute a command in sandboxed environment"""
        # Check if command is allowed
        if not self.is_command_allowed(command):
            return {
                "success": False,
                "error": f"Command blocked by sandbox policy: {command}",
                "stdout": "",
                "stderr": ""
            }

        # Check working directory
        if cwd and not self.is_path_allowed(cwd):
            return {
                "success": False,
                "error": f"Working directory blocked by sandbox policy: {cwd}",
                "stdout": "",
                "stderr": ""
            }

        try:
            # Create sandboxed environment
            sandbox_env = os.environ.copy()
            if env:
                sandbox_env.update(env)

            # Add sandbox indicators
            sandbox_env["WINDOWS_AI_SANDBOX"] = "1"
            sandbox_env["WINDOWS_AI_SANDBOX_LEVEL"] = self.config.level.value

            # Execute with timeout and resource limits
            process = await asyncio.create_subprocess_shell(
                command,
                cwd=cwd,
                env=sandbox_env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.config.timeout_seconds
                )
            except asyncio.TimeoutError:
                process.kill()
                return {
                    "success": False,
                    "error": f"Command timed out after {self.config.timeout_seconds}s",
                    "stdout": "",
                    "stderr": ""
                }

            return {
                "success": process.returncode == 0,
                "return_code": process.returncode,
                "stdout": stdout.decode() if stdout else "",
                "stderr": stderr.decode() if stderr else ""
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "stdout": "",
                "stderr": ""
            }

    async def create_isolated_workspace(self) -> str:
        """Create an isolated temporary workspace"""
        workspace = tempfile.mkdtemp(prefix="windowsai_sandbox_")
        self.config.allowed_paths.append(workspace)
        return workspace

    def get_config(self) -> Dict[str, Any]:
        """Get current sandbox configuration"""
        return {
            "level": self.config.level.value,
            "network_access": self.config.network_access,
            "allow_file_write": self.config.allow_file_write,
            "allow_file_delete": self.config.allow_file_delete,
            "allow_registry_access": self.config.allow_registry_access,
            "allow_process_spawn": self.config.allow_process_spawn,
            "max_memory_mb": self.config.max_memory_mb,
            "max_cpu_percent": self.config.max_cpu_percent,
            "timeout_seconds": self.config.timeout_seconds,
            "allowed_paths": self.config.allowed_paths,
            "blocked_paths": self.config.blocked_paths,
            "allowed_commands": self.config.allowed_commands,
            "blocked_commands": self.config.blocked_commands
        }

    def update_config(self, **kwargs):
        """Update sandbox configuration"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        logger.info(f"Sandbox config updated: {kwargs}")

    async def execute_file_operation(
        self,
        operation: str,
        path: str,
        data: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute a file operation within sandbox constraints
        
        Args:
            operation: One of "read", "write", "delete", "exists"
            path: File path to operate on
            data: Data to write (for write operation)
            
        Returns:
            Dictionary with result status and data
            
        Raises:
            PermissionError: If operation is blocked by sandbox policy
        """
        # Check if path is allowed
        if not self.is_path_allowed(path):
            raise PermissionError(f"Path blocked by sandbox policy: {path}")
        
        # Check operation-specific permissions
        if operation == "write":
            if not self.config.allow_file_write:
                raise PermissionError("File write operations blocked by sandbox policy")
            
            try:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'w') as f:
                    f.write(data or "")
                return {"success": True, "allowed": True, "operation": operation, "path": path}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        elif operation == "delete":
            if not self.config.allow_file_delete:
                raise PermissionError("File delete operations blocked by sandbox policy")
            
            try:
                if os.path.exists(path):
                    os.remove(path)
                return {"success": True, "allowed": True, "operation": operation, "path": path}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        elif operation == "read":
            try:
                with open(path, 'r') as f:
                    content = f.read()
                return {"success": True, "allowed": True, "data": content}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        elif operation == "exists":
            exists = os.path.exists(path)
            return {"success": True, "allowed": True, "exists": exists}
        
        else:
            return {"success": False, "error": f"Unknown operation: {operation}"}
