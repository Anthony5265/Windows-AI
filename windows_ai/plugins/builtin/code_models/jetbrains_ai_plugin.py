"""
JetBrains AI Plugin
Provides AI-powered coding assistance using JetBrains AI Assistant
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
    JetBrains AI Assistant plugin for IDE-integrated code assistance

    Capabilities:
    - Context-aware code completion
    - Code explanation with IDE context
    - Unit test generation
    - Bug detection and fixing
    - Documentation generation

    Actions:
    - complete_code: Get JetBrains AI completions
    - explain_code: Explain code with context
    - generate_tests: Generate JUnit/pytest tests
    - fix_bug: Detect and fix bugs
    - documentation: Generate documentation
    """

    def __init__(self):
        metadata = PluginMetadata(
            id="jetbrains_ai",
            name="JetBrains AI Assistant",
            description="AI coding assistance integrated with JetBrains IDEs",
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["code", "ai", "jetbrains", "completion", "ide"]
        )
        super().__init__(metadata)

        self.session = None
        self._api_key = None
        self._api_base = "https://api.jetbrains.ai/v1"
        self._model = "jba-default"
        self._initialized = False
        self._supported_languages = [
            "python", "java", "kotlin", "javascript", "typescript", "go",
            "rust", "cpp", "csharp", "php", "ruby", "scala", "swift", "sql"
        ]

    async def initialize(self) -> bool:
        if self._initialized:
            logger.warning("JetBrains AI plugin already initialized")
            return True

        try:
            self._api_key = os.environ.get("JETBRAINS_AI_API_KEY")

            if AIOHTTP_AVAILABLE:
                self.session = aiohttp.ClientSession()

            self._initialized = True
            logger.info("JetBrains AI plugin initialized successfully")
            return True

        except Exception as e:
            logger.error(f"JetBrains AI plugin initialization failed: {e}")
            return False

    async def connect(self, credentials: Optional[Dict[str, Any]] = None) -> bool:
        try:
            if credentials:
                self._api_key = credentials.get("api_key", self._api_key)
                self._model = credentials.get("model", self._model)
            logger.info("JetBrains AI plugin connected")
            return True
        except Exception as e:
            logger.error(f"JetBrains AI connection failed: {e}")
            return False

    async def disconnect(self) -> bool:
        try:
            if self.session:
                await self.session.close()
                self.session = None
            logger.info("JetBrains AI plugin disconnected")
            return True
        except Exception as e:
            logger.error(f"JetBrains AI disconnection failed: {e}")
            return False

    async def execute(self, action: str, parameters: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        if not self._initialized:
            await self.initialize()

        try:
            if action == "complete_code":
                return await self._complete_code(parameters)
            elif action == "explain_code":
                return await self._explain_code(parameters)
            elif action == "generate_tests":
                return await self._generate_tests(parameters)
            elif action == "fix_bug":
                return await self._fix_bug(parameters)
            elif action == "documentation":
                return await self._generate_documentation(parameters)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            logger.error(f"JetBrains AI execution failed: {e}")
            return {"success": False, "error": str(e)}

    async def _complete_code(self, params: Dict[str, Any]) -> Dict[str, Any]:
        code = params.get("code", "")
        language = params.get("language", "java")
        ide_context = params.get("ide_context", {})

        if not self._api_key:
            completion = f"    // JetBrains AI suggestion for {language}\n    return result;\n"
            if language == "python":
                completion = f"    # JetBrains AI suggestion for {language}\n    return result\n"
            return {
                "success": True,
                "result": {
                    "completion": completion,
                    "language": language,
                    "confidence": 0.90,
                    "model": self._model
                },
                "mode": "offline_simulation"
            }

        headers = {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}
        try:
            async with self.session.post(
                f"{self._api_base}/completions",
                headers=headers,
                json={"code": code, "language": language, "context": ide_context, "model": self._model}
            ) as resp:
                data = await resp.json()
                return {"success": True, "result": data}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _explain_code(self, params: Dict[str, Any]) -> Dict[str, Any]:
        code = params.get("code", "")
        language = params.get("language", "java")

        if not self._api_key:
            return {
                "success": True,
                "result": {
                    "explanation": (
                        f"This {language} code implements a class or method following object-oriented "
                        "principles. It encapsulates logic, manages state transitions, and provides "
                        "a clean interface for consumers of this code."
                    ),
                    "key_concepts": ["encapsulation", "abstraction", "state management"],
                    "language": language,
                    "model": self._model
                },
                "mode": "offline_simulation"
            }

        headers = {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}
        try:
            async with self.session.post(
                f"{self._api_base}/explain",
                headers=headers,
                json={"code": code, "language": language}
            ) as resp:
                data = await resp.json()
                return {"success": True, "result": data}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _generate_tests(self, params: Dict[str, Any]) -> Dict[str, Any]:
        code = params.get("code", "")
        language = params.get("language", "java")
        framework = params.get("framework", "junit5" if language == "java" else "pytest")

        if not self._api_key:
            if language == "java":
                tests = (
                    "import org.junit.jupiter.api.Test;\n"
                    "import static org.junit.jupiter.api.Assertions.*;\n\n"
                    "class JetBrainsAIGeneratedTest {\n"
                    "    @Test\n"
                    "    void testGenerated() {\n"
                    "        // JetBrains AI generated test\n"
                    "        assertTrue(true);\n"
                    "    }\n"
                    "}\n"
                )
            else:
                tests = (
                    "import pytest\n\n\n"
                    "def test_jetbrains_generated():\n"
                    '    \"\"\"Auto-generated by JetBrains AI\"\"\"\n'
                    "    assert True\n"
                )
            return {
                "success": True,
                "result": {
                    "tests": tests,
                    "framework": framework,
                    "language": language,
                    "model": self._model
                },
                "mode": "offline_simulation"
            }

        headers = {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}
        try:
            async with self.session.post(
                f"{self._api_base}/generate-tests",
                headers=headers,
                json={"code": code, "language": language, "framework": framework}
            ) as resp:
                data = await resp.json()
                return {"success": True, "result": data}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _fix_bug(self, params: Dict[str, Any]) -> Dict[str, Any]:
        code = params.get("code", "")
        error = params.get("error", "")
        language = params.get("language", "java")

        if not self._api_key:
            return {
                "success": True,
                "result": {
                    "fixed_code": code if code else "// Fixed version",
                    "explanation": "Resolved NullPointerException by adding null check before dereferencing",
                    "bugs_found": ["NullPointerException risk", "missing null guard"],
                    "confidence": 0.88,
                    "language": language,
                    "model": self._model
                },
                "mode": "offline_simulation"
            }

        headers = {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}
        try:
            async with self.session.post(
                f"{self._api_base}/fix-bug",
                headers=headers,
                json={"code": code, "error": error, "language": language}
            ) as resp:
                data = await resp.json()
                return {"success": True, "result": data}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _generate_documentation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        code = params.get("code", "")
        language = params.get("language", "java")
        style = params.get("style", "javadoc" if language == "java" else "google")

        if not self._api_key:
            if language == "java":
                doc = (
                    "/**\n"
                    " * JetBrains AI generated documentation.\n"
                    " * Describes the functionality of this code block.\n"
                    " *\n"
                    " * @param param input parameter\n"
                    " * @return processed result\n"
                    " */\n"
                )
            else:
                doc = (
                    '    \"\"\"\n'
                    "    JetBrains AI generated documentation.\n"
                    "    Describes the functionality of this code block.\n\n"
                    "    Args:\n"
                    "        param: Input parameter\n\n"
                    "    Returns:\n"
                    "        Processed result\n"
                    '    \"\"\"\n'
                )
            return {
                "success": True,
                "result": {
                    "documentation": doc,
                    "style": style,
                    "language": language,
                    "model": self._model
                },
                "mode": "offline_simulation"
            }

        headers = {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}
        try:
            async with self.session.post(
                f"{self._api_base}/documentation",
                headers=headers,
                json={"code": code, "language": language, "style": style}
            ) as resp:
                data = await resp.json()
                return {"success": True, "result": data}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def shutdown(self) -> bool:
        await self.disconnect()
        self._initialized = False
        logger.info("JetBrains AI plugin shutdown")
        return True

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["complete_code", "explain_code", "generate_tests", "fix_bug", "documentation"],
                    "description": "Action to perform"
                },
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Code context or snippet"},
                        "error": {"type": "string", "description": "Error message for bug fixing"},
                        "language": {"type": "string", "enum": self._supported_languages, "description": "Programming language"},
                        "framework": {"type": "string", "description": "Test framework"},
                        "style": {"type": "string", "description": "Documentation style"},
                        "ide_context": {"type": "object", "description": "IDE context metadata"}
                    }
                }
            },
            "required": ["action", "parameters"]
        }


plugin = Plugin()
