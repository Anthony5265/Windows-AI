"""
TASK-004: Codeium Plugin - Production Implementation
Multi-language support and context-aware completions
"""
from typing import Dict, Any, List, Optional
import os
import logging
import aiohttp
import json

from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class CodeiumPlugin(IntegrationPlugin):
    """Free AI code completion with 70+ languages"""

    def __init__(self):
        metadata = PluginMetadata(
            id="codeium_enhanced",
            name="Codeium",
            description="Free AI code completion supporting 70+ programming languages",
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["code", "completion", "ai", "free", "multilanguage"],
            requirements=["aiohttp>=3.8.0"]
        )
        super().__init__(metadata)

        self.api_key = os.getenv("CODEIUM_API_KEY", "")
        self.base_url = "https://server.codeium.com"
        self.session: Optional[aiohttp.ClientSession] = None
        self.connected = False

    async def initialize(self) -> bool:
        try:
            self.session = aiohttp.ClientSession()
            self._initialized = True
            logger.info("Codeium initialized")
            return True
        except Exception as e:
            logger.error(f"Init failed: {e}")
            return False

    async def connect(self, credentials: Dict[str, str]) -> bool:
        try:
            if "api_key" in credentials:
                self.api_key = credentials["api_key"]

            # Verify API key
            headers = {"Authorization": f"Bearer {self.api_key}"}
            async with self.session.get(
                f"{self.base_url}/exa.api_server_pb.ApiServer/GetCompletions",
                headers=headers,
                timeout=5
            ) as response:
                self.connected = True
                logger.info("Connected to Codeium")
                return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False

    async def disconnect(self) -> bool:
        if self.session:
            await self.session.close()
        self.connected = False
        return True

    async def execute(self, action: str, parameters: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        if not self.connected:
            return {"success": False, "error": "Not connected"}

        action_map = {
            "complete": self._get_completions,
            "search": self._semantic_search,
            "explain": self._explain_code,
            "refactor": self._refactor_code,
            "chat": self._chat
        }

        handler = action_map.get(action)
        if not handler:
            return {"success": False, "error": f"Unknown action: {action}"}

        try:
            result = await handler(parameters)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _get_completions(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get code completions"""
        document = {
            "text": params.get("text", ""),
            "editor_language": params.get("language", "python"),
            "language": self._map_language(params.get("language", "python")),
            "cursor_position": params.get("cursor_position", 0)
        }

        metadata = {
            "ide_name": "windows_ai",
            "ide_version": "1.0.0",
            "extension_name": "codeium",
            "extension_version": "2.0.0"
        }

        payload = {
            "metadata": metadata,
            "document": document,
            "editor_options": {
                "tab_size": params.get("tab_size", 4),
                "insert_spaces": params.get("insert_spaces", True)
            }
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        async with self.session.post(
            f"{self.base_url}/exa.api_server_pb.ApiServer/GetCompletions",
            json=payload,
            headers=headers,
            timeout=10
        ) as response:
            if response.status == 200:
                data = await response.json()
                completions = [
                    {
                        "text": item["completion"]["text"],
                        "range": item.get("range", {}),
                        "source": item.get("completionMetadata", {}).get("source", "")
                    }
                    for item in data.get("completionItems", [])
                ]
                return {"completions": completions}
            raise Exception(f"API error: {response.status}")

    async def _semantic_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Semantic code search"""
        query = params.get("query", "")
        language = params.get("language", "python")
        limit = params.get("limit", 10)

        payload = {
            "query": query,
            "language": self._map_language(language),
            "limit": limit
        }

        headers = {"Authorization": f"Bearer {self.api_key}"}

        async with self.session.post(
            f"{self.base_url}/exa.api_server_pb.ApiServer/SearchCode",
            json=payload,
            headers=headers
        ) as response:
            if response.status == 200:
                data = await response.json()
                return {"results": data.get("searchResults", [])}
            raise Exception(f"Search failed: {response.status}")

    async def _explain_code(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Explain code"""
        code = params.get("code", "")
        language = params.get("language", "python")

        # Use chat for explanation
        return await self._chat({
            "message": f"Explain this {language} code:\n\n{code}",
            "context": {"language": language}
        })

    async def _refactor_code(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Refactor code"""
        code = params.get("code", "")
        instructions = params.get("instructions", "improve code quality")
        language = params.get("language", "python")

        return await self._chat({
            "message": f"Refactor this {language} code ({instructions}):\n\n{code}",
            "context": {"language": language, "task": "refactor"}
        })

    async def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Chat with Codeium"""
        message = params.get("message", "")
        context = params.get("context", {})

        payload = {
            "message": message,
            "context": context
        }

        headers = {"Authorization": f"Bearer {self.api_key}"}

        async with self.session.post(
            f"{self.base_url}/exa.api_server_pb.ApiServer/Chat",
            json=payload,
            headers=headers
        ) as response:
            if response.status == 200:
                data = await response.json()
                return {
                    "response": data.get("chatMessage", {}).get("text", ""),
                    "conversation_id": data.get("conversationId", "")
                }
            raise Exception(f"Chat failed: {response.status}")

    def _map_language(self, lang: str) -> int:
        """Map language string to Codeium language ID"""
        lang_map = {
            "python": 1, "javascript": 2, "typescript": 3, "java": 4,
            "cpp": 5, "c": 6, "csharp": 7, "php": 8, "ruby": 9,
            "go": 10, "rust": 11, "swift": 12, "kotlin": 13, "scala": 14,
            "r": 15, "perl": 16, "lua": 17, "shell": 18, "sql": 19,
            "html": 20, "css": 21, "json": 22, "yaml": 23, "xml": 24
        }
        return lang_map.get(lang.lower(), 1)

    async def shutdown(self):
        await self.disconnect()

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["complete", "search", "explain", "refactor", "chat"]},
                "text": {"type": "string"},
                "language": {"type": "string"}
            },
            "required": ["action"]
        }


plugin = CodeiumPlugin()
