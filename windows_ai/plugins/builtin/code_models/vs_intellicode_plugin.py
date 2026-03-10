"""
Visual Studio IntelliCode Plugin
Provides AI-enhanced IntelliSense and code intelligence for Visual Studio and VS Code
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
    Visual Studio IntelliCode plugin for AI-enhanced code intelligence

    Capabilities:
    - AI-enhanced IntelliSense completions
    - Refactoring suggestions based on usage patterns
    - Code pattern detection and recommendations
    - Code explanation

    Actions:
    - complete_code: Get AI-enhanced IntelliSense completions
    - suggest_refactor: Suggest AI-driven refactoring
    - detect_patterns: Detect common code patterns and anti-patterns
    - explain_code: Explain code with Microsoft AI
    """

    def __init__(self):
        metadata = PluginMetadata(
            id="vs_intellicode",
            name="Visual Studio IntelliCode",
            description="AI-enhanced IntelliSense for Visual Studio and VS Code by Microsoft",
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["code", "ai", "intellicode", "vscode", "microsoft"]
        )
        super().__init__(metadata)

        self.session = None
        self._api_key = None
        self._azure_api_key = None
        self._api_base = "https://intellicode.westus2.cloudapp.azure.com/v1"
        self._azure_endpoint = "https://api.openai.azure.com"
        self._model = "intellicode-completions"
        self._initialized = False
        self._supported_languages = [
            "python", "javascript", "typescript", "java", "csharp", "cpp",
            "go", "rust", "php", "ruby", "sql", "html", "css", "json", "yaml"
        ]

    async def initialize(self) -> bool:
        if self._initialized:
            logger.warning("VS IntelliCode plugin already initialized")
            return True

        try:
            self._api_key = os.environ.get("VSCODE_EXTENSION_API_KEY")
            self._azure_api_key = os.environ.get("AZURE_OPENAI_API_KEY")

            if AIOHTTP_AVAILABLE:
                self.session = aiohttp.ClientSession()

            self._initialized = True
            logger.info("VS IntelliCode plugin initialized successfully")
            return True

        except Exception as e:
            logger.error(f"VS IntelliCode plugin initialization failed: {e}")
            return False

    async def connect(self, credentials: Optional[Dict[str, Any]] = None) -> bool:
        try:
            if credentials:
                self._api_key = credentials.get("api_key", self._api_key)
                self._azure_api_key = credentials.get("azure_api_key", self._azure_api_key)
                self._azure_endpoint = credentials.get("azure_endpoint", self._azure_endpoint)
            logger.info("VS IntelliCode plugin connected")
            return True
        except Exception as e:
            logger.error(f"VS IntelliCode connection failed: {e}")
            return False

    async def disconnect(self) -> bool:
        try:
            if self.session:
                await self.session.close()
                self.session = None
            logger.info("VS IntelliCode plugin disconnected")
            return True
        except Exception as e:
            logger.error(f"VS IntelliCode disconnection failed: {e}")
            return False

    def _has_credentials(self) -> bool:
        return bool(self._api_key or self._azure_api_key)

    async def execute(self, action: str, parameters: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        if not self._initialized:
            await self.initialize()

        try:
            if action == "complete_code":
                return await self._complete_code(parameters)
            elif action == "suggest_refactor":
                return await self._suggest_refactor(parameters)
            elif action == "detect_patterns":
                return await self._detect_patterns(parameters)
            elif action == "explain_code":
                return await self._explain_code(parameters)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            logger.error(f"VS IntelliCode execution failed: {e}")
            return {"success": False, "error": str(e)}

    async def _complete_code(self, params: Dict[str, Any]) -> Dict[str, Any]:
        code = params.get("code", "")
        language = params.get("language", "python")
        cursor_line = params.get("cursor_line", 0)
        cursor_col = params.get("cursor_col", 0)

        if not self._has_credentials():
            completion = f"    # IntelliCode AI suggestion for {language}\n    return result\n"
            return {
                "success": True,
                "result": {
                    "completions": [
                        {
                            "insertText": completion,
                            "sortText": "0001",
                            "detail": "IntelliCode suggestion",
                            "kind": "Method",
                            "score": 0.94
                        }
                    ],
                    "language": language,
                    "model": self._model
                },
                "mode": "offline_simulation"
            }

        effective_key = self._api_key or self._azure_api_key
        headers = {"Authorization": f"Bearer {effective_key}", "Content-Type": "application/json"}
        try:
            async with self.session.post(
                f"{self._api_base}/completions",
                headers=headers,
                json={
                    "code": code,
                    "language": language,
                    "cursorLine": cursor_line,
                    "cursorColumn": cursor_col
                }
            ) as resp:
                data = await resp.json()
                return {"success": True, "result": data}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _suggest_refactor(self, params: Dict[str, Any]) -> Dict[str, Any]:
        code = params.get("code", "")
        language = params.get("language", "python")

        if not self._has_credentials():
            return {
                "success": True,
                "result": {
                    "refactoring_suggestions": [
                        {
                            "type": "rename",
                            "description": "Rename variable to follow naming conventions",
                            "priority": "medium"
                        },
                        {
                            "type": "extract_method",
                            "description": "Extract repeated logic into a reusable method",
                            "priority": "high"
                        },
                        {
                            "type": "simplify_condition",
                            "description": "Simplify complex boolean conditions",
                            "priority": "low"
                        }
                    ],
                    "language": language,
                    "model": self._model
                },
                "mode": "offline_simulation"
            }

        effective_key = self._api_key or self._azure_api_key
        headers = {"Authorization": f"Bearer {effective_key}", "Content-Type": "application/json"}
        try:
            async with self.session.post(
                f"{self._api_base}/refactor-suggestions",
                headers=headers,
                json={"code": code, "language": language}
            ) as resp:
                data = await resp.json()
                return {"success": True, "result": data}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _detect_patterns(self, params: Dict[str, Any]) -> Dict[str, Any]:
        code = params.get("code", "")
        language = params.get("language", "python")

        if not self._has_credentials():
            return {
                "success": True,
                "result": {
                    "patterns_detected": [
                        {
                            "pattern": "singleton",
                            "confidence": 0.75,
                            "description": "Possible singleton pattern detected",
                            "is_anti_pattern": False
                        },
                        {
                            "pattern": "deep_nesting",
                            "confidence": 0.60,
                            "description": "Deeply nested conditionals reduce readability",
                            "is_anti_pattern": True
                        }
                    ],
                    "overall_quality": "good",
                    "language": language,
                    "model": self._model
                },
                "mode": "offline_simulation"
            }

        effective_key = self._api_key or self._azure_api_key
        headers = {"Authorization": f"Bearer {effective_key}", "Content-Type": "application/json"}
        try:
            async with self.session.post(
                f"{self._api_base}/detect-patterns",
                headers=headers,
                json={"code": code, "language": language}
            ) as resp:
                data = await resp.json()
                return {"success": True, "result": data}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _explain_code(self, params: Dict[str, Any]) -> Dict[str, Any]:
        code = params.get("code", "")
        language = params.get("language", "python")

        if not self._has_credentials():
            return {
                "success": True,
                "result": {
                    "explanation": (
                        f"This {language} code implements functionality using Microsoft-recommended "
                        "patterns. IntelliCode analysis indicates the code follows standard conventions "
                        "for the language and IDE environment."
                    ),
                    "key_concepts": ["code patterns", "best practices", "IDE integration"],
                    "language": language,
                    "model": self._model
                },
                "mode": "offline_simulation"
            }

        effective_key = self._api_key or self._azure_api_key
        headers = {"Authorization": f"Bearer {effective_key}", "Content-Type": "application/json"}
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

    async def shutdown(self) -> bool:
        await self.disconnect()
        self._initialized = False
        logger.info("VS IntelliCode plugin shutdown")
        return True

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["complete_code", "suggest_refactor", "detect_patterns", "explain_code"],
                    "description": "Action to perform"
                },
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Code context or snippet"},
                        "language": {"type": "string", "enum": self._supported_languages, "description": "Programming language"},
                        "cursor_line": {"type": "integer", "description": "Cursor line number"},
                        "cursor_col": {"type": "integer", "description": "Cursor column number"}
                    }
                }
            },
            "required": ["action", "parameters"]
        }


plugin = Plugin()
