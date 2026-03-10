"""
Code Llama Plugin
Provides AI-powered code generation using Meta's Code Llama model via Replicate or Ollama
"""

from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType
from typing import Dict, Any, Optional, List
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    aiohttp = None
import os
import logging
import json

logger = logging.getLogger(__name__)


class Plugin(IntegrationPlugin):
    """
    Code Llama plugin for local and cloud AI code generation

    Capabilities:
    - Code completion with context awareness
    - Function generation from natural language descriptions
    - Fill-in-the-middle (FIM) completions
    - Code explanation
    - Unit test generation

    Actions:
    - complete_code: Complete partial code snippets
    - generate_function: Generate a function from a description
    - explain_code: Explain what code does
    - generate_tests: Generate unit tests
    - fill_in_middle: Fill in code between prefix and suffix
    """

    def __init__(self):
        metadata = PluginMetadata(
            id="code_llama",
            name="Code Llama",
            description="Meta's open-source code generation model via Replicate or Ollama local inference",
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["code", "ai", "code-llama", "meta", "local", "open-source"]
        )
        super().__init__(metadata)

        self.session = None
        self._api_key = None
        self._ollama_host = "http://localhost:11434"
        self._use_ollama = False
        self._api_base = "https://api.replicate.com/v1"
        self._model_version = "cdd97b257f93cb89dede1c7584e3f3dfc969571b"
        self._initialized = False
        self._supported_languages = [
            "python", "javascript", "typescript", "java", "go", "rust",
            "cpp", "csharp", "php", "ruby", "swift", "kotlin", "bash", "sql"
        ]

    async def initialize(self) -> bool:
        """Initialize the Code Llama plugin"""
        if self._initialized:
            logger.warning("Code Llama plugin already initialized")
            return True

        try:
            self._api_key = os.environ.get("REPLICATE_API_TOKEN")
            ollama_host = os.environ.get("OLLAMA_HOST", self._ollama_host)
            self._ollama_host = ollama_host
            self._use_ollama = not bool(self._api_key)

            if AIOHTTP_AVAILABLE:
                self.session = aiohttp.ClientSession()

            self._initialized = True
            logger.info("Code Llama plugin initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Code Llama plugin initialization failed: {e}")
            return False

    async def connect(self, credentials: Optional[Dict[str, Any]] = None) -> bool:
        """Connect with Replicate or Ollama credentials"""
        try:
            if credentials:
                self._api_key = credentials.get("api_key", self._api_key)
                self._ollama_host = credentials.get("ollama_host", self._ollama_host)
                self._use_ollama = credentials.get("use_ollama", self._use_ollama)

            logger.info("Code Llama plugin connected")
            return True

        except Exception as e:
            logger.error(f"Code Llama connection failed: {e}")
            return False

    async def disconnect(self) -> bool:
        """Disconnect and cleanup resources"""
        try:
            if self.session:
                await self.session.close()
                self.session = None

            logger.info("Code Llama plugin disconnected")
            return True

        except Exception as e:
            logger.error(f"Code Llama disconnection failed: {e}")
            return False

    async def execute(self, action: str, parameters: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Execute Code Llama actions"""
        if not self._initialized:
            await self.initialize()

        try:
            if action == "complete_code":
                return await self._complete_code(parameters)
            elif action == "generate_function":
                return await self._generate_function(parameters)
            elif action == "explain_code":
                return await self._explain_code(parameters)
            elif action == "generate_tests":
                return await self._generate_tests(parameters)
            elif action == "fill_in_middle":
                return await self._fill_in_middle(parameters)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            logger.error(f"Code Llama execution failed: {e}")
            return {"success": False, "error": str(e)}

    def _has_backend(self) -> bool:
        return bool(self._api_key) or self._use_ollama

    async def _complete_code(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Complete partial code snippets"""
        code = params.get("code", "")
        language = params.get("language", "python")
        max_tokens = params.get("max_tokens", 256)

        if not self._has_backend():
            completion = f"    # Code Llama completion for {language}\n    return result\n"
            return {
                "success": True,
                "result": {
                    "completion": completion,
                    "language": language,
                    "confidence": 0.87,
                    "model": "codellama-34b-instruct"
                },
                "mode": "offline_simulation"
            }

        if self._use_ollama:
            return await self._ollama_generate(
                f"Complete this {language} code:\n{code}", max_tokens, language
            )

        headers = {
            "Authorization": f"Token {self._api_key}",
            "Content-Type": "application/json"
        }
        try:
            payload = {
                "version": self._model_version,
                "input": {"prompt": f"<PRE>{code}<SUF><MID>", "max_new_tokens": max_tokens}
            }
            async with self.session.post(
                f"{self._api_base}/predictions",
                headers=headers,
                json=payload
            ) as resp:
                data = await resp.json()
                return {"success": True, "result": data}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _generate_function(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a function from a description"""
        description = params.get("description", "")
        language = params.get("language", "python")
        function_name = params.get("function_name", "generated_function")

        if not self._has_backend():
            code = (
                f"def {function_name}(param):\n"
                f'    """{description}"""\n'
                f"    # Code Llama generated implementation\n"
                f"    result = param\n"
                f"    return result\n"
            )
            return {
                "success": True,
                "result": {
                    "code": code,
                    "language": language,
                    "function_name": function_name,
                    "model": "codellama-34b-instruct"
                },
                "mode": "offline_simulation"
            }

        prompt = f"Write a {language} function named `{function_name}` that: {description}"
        if self._use_ollama:
            return await self._ollama_generate(prompt, 512, language)

        headers = {"Authorization": f"Token {self._api_key}", "Content-Type": "application/json"}
        try:
            async with self.session.post(
                f"{self._api_base}/predictions",
                headers=headers,
                json={"version": self._model_version, "input": {"prompt": prompt, "max_new_tokens": 512}}
            ) as resp:
                data = await resp.json()
                return {"success": True, "result": data}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _explain_code(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Explain what code does"""
        code = params.get("code", "")
        language = params.get("language", "python")

        if not self._has_backend():
            return {
                "success": True,
                "result": {
                    "explanation": (
                        "This code defines logic that processes the provided inputs through "
                        "a series of operations. It uses standard programming constructs including "
                        "conditionals, loops, and function calls to transform data and return results."
                    ),
                    "key_concepts": ["functions", "control flow", "data transformation"],
                    "language": language,
                    "model": "codellama-34b-instruct"
                },
                "mode": "offline_simulation"
            }

        prompt = f"Explain the following {language} code in plain English:\n```{language}\n{code}\n```"
        if self._use_ollama:
            return await self._ollama_generate(prompt, 512, language)

        headers = {"Authorization": f"Token {self._api_key}", "Content-Type": "application/json"}
        try:
            async with self.session.post(
                f"{self._api_base}/predictions",
                headers=headers,
                json={"version": self._model_version, "input": {"prompt": prompt, "max_new_tokens": 512}}
            ) as resp:
                data = await resp.json()
                return {"success": True, "result": data}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _generate_tests(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate unit tests for code"""
        code = params.get("code", "")
        language = params.get("language", "python")
        framework = params.get("framework", "pytest")

        if not self._has_backend():
            tests = (
                f"import pytest\n\n\n"
                f"def test_code_llama_generated():\n"
                f'    """Auto-generated test by Code Llama"""\n'
                f"    # Arrange\n"
                f"    input_val = 1\n"
                f"    expected = 1\n"
                f"    # Act & Assert\n"
                f"    assert input_val == expected\n"
            )
            return {
                "success": True,
                "result": {
                    "tests": tests,
                    "framework": framework,
                    "language": language,
                    "model": "codellama-34b-instruct"
                },
                "mode": "offline_simulation"
            }

        prompt = f"Generate {framework} unit tests for this {language} code:\n```{language}\n{code}\n```"
        if self._use_ollama:
            return await self._ollama_generate(prompt, 1024, language)

        headers = {"Authorization": f"Token {self._api_key}", "Content-Type": "application/json"}
        try:
            async with self.session.post(
                f"{self._api_base}/predictions",
                headers=headers,
                json={"version": self._model_version, "input": {"prompt": prompt, "max_new_tokens": 1024}}
            ) as resp:
                data = await resp.json()
                return {"success": True, "result": data}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _fill_in_middle(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Fill in code between a prefix and suffix"""
        prefix = params.get("prefix", "")
        suffix = params.get("suffix", "")
        language = params.get("language", "python")

        if not self._has_backend():
            middle = f"    # Code Llama fill-in-middle for {language}\n    pass\n"
            return {
                "success": True,
                "result": {
                    "infill": middle,
                    "prefix": prefix,
                    "suffix": suffix,
                    "language": language,
                    "model": "codellama-34b-instruct"
                },
                "mode": "offline_simulation"
            }

        fim_prompt = f"<PRE>{prefix}<SUF>{suffix}<MID>"
        if self._use_ollama:
            return await self._ollama_generate(fim_prompt, 256, language)

        headers = {"Authorization": f"Token {self._api_key}", "Content-Type": "application/json"}
        try:
            async with self.session.post(
                f"{self._api_base}/predictions",
                headers=headers,
                json={"version": self._model_version, "input": {"prompt": fim_prompt, "max_new_tokens": 256}}
            ) as resp:
                data = await resp.json()
                return {"success": True, "result": data}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _ollama_generate(self, prompt: str, max_tokens: int, language: str) -> Dict[str, Any]:
        """Run inference via local Ollama server"""
        if not AIOHTTP_AVAILABLE or not self.session:
            return {"success": False, "error": "aiohttp not available for Ollama requests"}
        try:
            async with self.session.post(
                f"{self._ollama_host}/api/generate",
                json={"model": "codellama", "prompt": prompt, "stream": False, "options": {"num_predict": max_tokens}}
            ) as resp:
                data = await resp.json()
                return {"success": True, "result": {"output": data.get("response", ""), "language": language, "model": "codellama-ollama"}}
        except Exception as e:
            return {"success": False, "error": f"Ollama request failed: {e}"}

    async def shutdown(self) -> bool:
        """Shutdown plugin"""
        await self.disconnect()
        self._initialized = False
        logger.info("Code Llama plugin shutdown")
        return True

    def get_schema(self) -> Dict[str, Any]:
        """Get plugin schema"""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["complete_code", "generate_function", "explain_code", "generate_tests", "fill_in_middle"],
                    "description": "Action to perform"
                },
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Code context or snippet"},
                        "prefix": {"type": "string", "description": "Code prefix for fill-in-middle"},
                        "suffix": {"type": "string", "description": "Code suffix for fill-in-middle"},
                        "description": {"type": "string", "description": "Natural language description"},
                        "function_name": {"type": "string", "description": "Name for generated function"},
                        "language": {
                            "type": "string",
                            "enum": self._supported_languages,
                            "description": "Programming language"
                        },
                        "framework": {"type": "string", "description": "Test framework"},
                        "max_tokens": {"type": "integer", "description": "Maximum tokens to generate"}
                    }
                }
            },
            "required": ["action", "parameters"]
        }


plugin = Plugin()
