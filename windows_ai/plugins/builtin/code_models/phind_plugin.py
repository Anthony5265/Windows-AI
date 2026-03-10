"""
Phind Plugin
Provides developer-focused AI search and code generation using Phind
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
    Phind plugin for developer-focused AI search and coding assistance

    Capabilities:
    - Semantic code search across the web
    - Technical question answering with citations
    - Code generation from descriptions
    - Error explanation and debugging help

    Actions:
    - search_code: Search for code solutions and documentation
    - answer_question: Answer technical programming questions
    - generate_code: Generate code from a description
    - explain_error: Explain and fix error messages
    """

    def __init__(self):
        metadata = PluginMetadata(
            id="phind",
            name="Phind",
            description="Developer-focused AI search engine and code generation assistant",
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["code", "ai", "phind", "search", "developer"]
        )
        super().__init__(metadata)

        self.session = None
        self._api_key = None
        self._api_base = "https://https.extension.phind.com/agent"
        self._model = "Phind Model"
        self._initialized = False
        self._supported_languages = [
            "python", "javascript", "typescript", "java", "go", "rust",
            "cpp", "csharp", "ruby", "php", "swift", "kotlin", "bash", "sql"
        ]

    async def initialize(self) -> bool:
        if self._initialized:
            logger.warning("Phind plugin already initialized")
            return True

        try:
            self._api_key = os.environ.get("PHIND_API_KEY")

            if AIOHTTP_AVAILABLE:
                self.session = aiohttp.ClientSession()

            self._initialized = True
            logger.info("Phind plugin initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Phind plugin initialization failed: {e}")
            return False

    async def connect(self, credentials: Optional[Dict[str, Any]] = None) -> bool:
        try:
            if credentials:
                self._api_key = credentials.get("api_key", self._api_key)
                self._model = credentials.get("model", self._model)
            logger.info("Phind plugin connected")
            return True
        except Exception as e:
            logger.error(f"Phind connection failed: {e}")
            return False

    async def disconnect(self) -> bool:
        try:
            if self.session:
                await self.session.close()
                self.session = None
            logger.info("Phind plugin disconnected")
            return True
        except Exception as e:
            logger.error(f"Phind disconnection failed: {e}")
            return False

    async def execute(self, action: str, parameters: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        if not self._initialized:
            await self.initialize()

        try:
            if action == "search_code":
                return await self._search_code(parameters)
            elif action == "answer_question":
                return await self._answer_question(parameters)
            elif action == "generate_code" or action == "complete_code":
                return await self._generate_code(parameters)
            elif action == "explain_error":
                return await self._explain_error(parameters)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            logger.error(f"Phind execution failed: {e}")
            return {"success": False, "error": str(e)}

    async def _search_code(self, params: Dict[str, Any]) -> Dict[str, Any]:
        query = params.get("query", "")
        language = params.get("language", "python")

        if not self._api_key:
            return {
                "success": True,
                "result": {
                    "results": [
                        {
                            "title": f"How to: {query}",
                            "url": "https://docs.python.org",
                            "snippet": f"# {language} solution for: {query}\n# Example implementation\nresult = None",
                            "score": 0.92
                        }
                    ],
                    "query": query,
                    "language": language,
                    "total_results": 1,
                    "model": self._model
                },
                "mode": "offline_simulation"
            }

        headers = {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}
        try:
            async with self.session.post(
                f"{self._api_base}/search",
                headers=headers,
                json={"query": query, "language": language}
            ) as resp:
                data = await resp.json()
                return {"success": True, "result": data}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _answer_question(self, params: Dict[str, Any]) -> Dict[str, Any]:
        question = params.get("question", "")
        language = params.get("language", "python")
        code_context = params.get("code_context", "")

        if not self._api_key:
            return {
                "success": True,
                "result": {
                    "answer": (
                        f"To solve this {language} programming question: {question}\n\n"
                        "The recommended approach is to use built-in language features. "
                        "Here is a concise explanation with an example implementation that follows best practices."
                    ),
                    "code_examples": [f"# Example for: {question}\nresult = None  # implement here"],
                    "sources": ["https://docs.python.org", "https://stackoverflow.com"],
                    "model": self._model
                },
                "mode": "offline_simulation"
            }

        headers = {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}
        try:
            async with self.session.post(
                f"{self._api_base}/answer",
                headers=headers,
                json={"question": question, "language": language, "context": code_context}
            ) as resp:
                data = await resp.json()
                return {"success": True, "result": data}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _generate_code(self, params: Dict[str, Any]) -> Dict[str, Any]:
        description = params.get("description", "")
        language = params.get("language", "python")

        if not self._api_key:
            code = (
                f"# Phind generated {language} code\n"
                f"# {description}\n\n"
                f"def phind_solution():\n"
                f'    \"\"\"\n'
                f"    {description}\n"
                f'    \"\"\"\n'
                f"    # Implementation based on Phind search\n"
                f"    return None\n"
            )
            return {
                "success": True,
                "result": {
                    "code": code,
                    "language": language,
                    "description": description,
                    "model": self._model
                },
                "mode": "offline_simulation"
            }

        headers = {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}
        try:
            async with self.session.post(
                f"{self._api_base}/generate",
                headers=headers,
                json={"description": description, "language": language}
            ) as resp:
                data = await resp.json()
                return {"success": True, "result": data}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _explain_error(self, params: Dict[str, Any]) -> Dict[str, Any]:
        error_message = params.get("error", "")
        code = params.get("code", "")
        language = params.get("language", "python")

        if not self._api_key:
            return {
                "success": True,
                "result": {
                    "explanation": (
                        f"The error \"{error_message}\" occurs when the program attempts "
                        "an operation on an invalid or unexpected value. Common causes include "
                        "incorrect variable types, missing None checks, or out-of-bounds access."
                    ),
                    "fixes": [
                        "Add input validation before the failing operation",
                        "Check for None/null values before dereferencing",
                        "Verify array indices are within bounds"
                    ],
                    "fixed_code": code if code else f"# Fixed {language} code\npass",
                    "model": self._model
                },
                "mode": "offline_simulation"
            }

        headers = {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}
        try:
            async with self.session.post(
                f"{self._api_base}/explain-error",
                headers=headers,
                json={"error": error_message, "code": code, "language": language}
            ) as resp:
                data = await resp.json()
                return {"success": True, "result": data}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def shutdown(self) -> bool:
        await self.disconnect()
        self._initialized = False
        logger.info("Phind plugin shutdown")
        return True

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["search_code", "answer_question", "generate_code", "explain_error"],
                    "description": "Action to perform"
                },
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "question": {"type": "string", "description": "Technical question"},
                        "description": {"type": "string", "description": "Code generation description"},
                        "error": {"type": "string", "description": "Error message to explain"},
                        "code": {"type": "string", "description": "Code context"},
                        "code_context": {"type": "string", "description": "Additional code context"},
                        "language": {"type": "string", "enum": self._supported_languages, "description": "Programming language"}
                    }
                }
            },
            "required": ["action", "parameters"]
        }


plugin = Plugin()
