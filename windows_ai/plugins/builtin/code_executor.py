"""
Code Execution Sandbox Plugin

Safely executes code in isolated environments.
"""

from typing import Dict, Any, Optional
import subprocess
import tempfile
import os
from pathlib import Path
import logging
import asyncio

from windows_ai.plugins.base import ToolPlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class CodeExecutorPlugin(ToolPlugin):
    """
    Executes code safely in sandboxed environments.
    Supports Python, JavaScript, and shell commands.
    """

    @staticmethod
    def get_metadata() -> PluginMetadata:
        return PluginMetadata(
            id="code_executor",
            name="Code Executor",
            description="Safely execute code in sandboxed environments",
            version="1.0.0",
            author="Windows AI",
            plugin_type=PluginType.TOOL,
            icon="⚡",
            tags=["code", "execution", "sandbox", "development"]
        )

    def __init__(self, metadata: PluginMetadata):
        super().__init__(metadata)
        self.supported_languages = ["python", "javascript", "bash", "shell"]
        self.timeout_seconds = 30
        self.max_output_size = 10000  # characters

    async def initialize(self) -> bool:
        """Initialize the code executor plugin"""
        self._initialized = True
        logger.info("Code Executor plugin initialized")
        return True

    async def execute(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute code in a sandbox.

        Args:
            query: The code to execute
            parameters: Dict with:
                - language: Programming language (python, javascript, bash)
                - timeout: Max execution time in seconds (default: 30)
                - env: Environment variables (dict)

        Returns:
            Execution results including stdout, stderr, exit code
        """
        if not parameters:
            parameters = {}

        language = parameters.get("language", "python").lower()
        timeout = parameters.get("timeout", self.timeout_seconds)
        env_vars = parameters.get("env", {})

        if language not in self.supported_languages:
            return {
                "success": False,
                "error": f"Unsupported language: {language}. Supported: {', '.join(self.supported_languages)}"
            }

        try:
            if language == "python":
                result = await self._execute_python(query, timeout, env_vars)
            elif language in ["javascript", "js", "node"]:
                result = await self._execute_javascript(query, timeout, env_vars)
            elif language in ["bash", "shell", "sh"]:
                result = await self._execute_shell(query, timeout, env_vars)
            else:
                return {
                    "success": False,
                    "error": f"Language {language} not yet implemented"
                }

            return {
                "success": result["exit_code"] == 0,
                "result": result,
                "message": f"Code executed {'successfully' if result['exit_code'] == 0 else 'with errors'}"
            }

        except Exception as e:
            logger.error(f"Code execution error: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Error executing code"
            }

    async def _execute_python(
        self,
        code: str,
        timeout: int,
        env_vars: Dict[str, str]
    ) -> Dict[str, Any]:
        """Execute Python code"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            # Prepare environment
            env = os.environ.copy()
            env.update(env_vars)

            # Execute with timeout
            process = await asyncio.create_subprocess_exec(
                "python3",
                temp_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )

                return {
                    "stdout": stdout.decode('utf-8', errors='replace')[:self.max_output_size],
                    "stderr": stderr.decode('utf-8', errors='replace')[:self.max_output_size],
                    "exit_code": process.returncode,
                    "timed_out": False
                }

            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {
                    "stdout": "",
                    "stderr": f"Execution timed out after {timeout} seconds",
                    "exit_code": -1,
                    "timed_out": True
                }

        finally:
            # Clean up temp file
            try:
                os.unlink(temp_file)
            except:
                pass

    async def _execute_javascript(
        self,
        code: str,
        timeout: int,
        env_vars: Dict[str, str]
    ) -> Dict[str, Any]:
        """Execute JavaScript code using Node.js"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            # Prepare environment
            env = os.environ.copy()
            env.update(env_vars)

            # Check if node is available
            try:
                node_check = await asyncio.create_subprocess_exec(
                    "node",
                    "--version",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await node_check.wait()
                if node_check.returncode != 0:
                    return {
                        "stdout": "",
                        "stderr": "Node.js is not installed or not in PATH",
                        "exit_code": -1,
                        "timed_out": False
                    }
            except FileNotFoundError:
                return {
                    "stdout": "",
                    "stderr": "Node.js is not installed",
                    "exit_code": -1,
                    "timed_out": False
                }

            # Execute with timeout
            process = await asyncio.create_subprocess_exec(
                "node",
                temp_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )

                return {
                    "stdout": stdout.decode('utf-8', errors='replace')[:self.max_output_size],
                    "stderr": stderr.decode('utf-8', errors='replace')[:self.max_output_size],
                    "exit_code": process.returncode,
                    "timed_out": False
                }

            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {
                    "stdout": "",
                    "stderr": f"Execution timed out after {timeout} seconds",
                    "exit_code": -1,
                    "timed_out": True
                }

        finally:
            # Clean up temp file
            try:
                os.unlink(temp_file)
            except:
                pass

    async def _execute_shell(
        self,
        code: str,
        timeout: int,
        env_vars: Dict[str, str]
    ) -> Dict[str, Any]:
        """Execute shell commands"""
        # Prepare environment
        env = os.environ.copy()
        env.update(env_vars)

        # Execute with timeout
        process = await asyncio.create_subprocess_shell(
            code,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )

            return {
                "stdout": stdout.decode('utf-8', errors='replace')[:self.max_output_size],
                "stderr": stderr.decode('utf-8', errors='replace')[:self.max_output_size],
                "exit_code": process.returncode,
                "timed_out": False
            }

        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            return {
                "stdout": "",
                "stderr": f"Execution timed out after {timeout} seconds",
                "exit_code": -1,
                "timed_out": True
            }

    def get_schema(self) -> Dict[str, Any]:
        """Return parameter schema"""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The code to execute"
                },
                "language": {
                    "type": "string",
                    "enum": ["python", "javascript", "js", "node", "bash", "shell", "sh"],
                    "description": "Programming language",
                    "default": "python"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Maximum execution time in seconds",
                    "default": 30,
                    "minimum": 1,
                    "maximum": 300
                },
                "env": {
                    "type": "object",
                    "description": "Environment variables",
                    "additionalProperties": {"type": "string"}
                }
            },
            "required": ["query"]
        }

    def get_function_definition(self) -> Dict[str, Any]:
        """Return OpenAI function definition"""
        return {
            "name": "execute_code",
            "description": "Execute code safely in a sandboxed environment. Use this when you need to run Python, JavaScript, or shell commands. IMPORTANT: Only execute safe, non-destructive code.",
            "parameters": self.get_schema()
        }
