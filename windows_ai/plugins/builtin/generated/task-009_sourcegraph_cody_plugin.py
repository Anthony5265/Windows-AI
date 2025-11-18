"""
TASK-009: Sourcegraph Cody Plugin - Production Implementation
Cody with repository-wide context search
"""
from typing import Dict, Any, List, Optional
import os
import logging
import aiohttp
import json
from datetime import datetime

from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class SourcegraphCodyPlugin(IntegrationPlugin):
    """Sourcegraph Cody integration plugin"""

    def __init__(self):
        metadata = PluginMetadata(
            id="task-009_sourcegraph_cody",
            name="Sourcegraph Cody",
            description="Cody with repository-wide context search",
            version="1.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["", "ai", "integration"],
            requirements=["aiohttp>=3.8.0"]
        )
        super().__init__(metadata)

        self.api_key = os.getenv("SOURCEGRAPH_API_KEY", "")
        self.base_url = "https://sourcegraph.com/.api/completions"
        self.session: Optional[aiohttp.ClientSession] = None
        self.connected = False

    async def initialize(self) -> bool:
        """Initialize plugin"""
        try:
            self.session = aiohttp.ClientSession()
            self._initialized = True
            logger.info("Sourcegraph Cody plugin initialized")
            return True
        except Exception as e:
            logger.error(f"Init failed: {e}")
            return False

    async def connect(self, credentials: Dict[str, str]) -> bool:
        """Connect to service"""
        try:
            if "api_key" in credentials:
                self.api_key = credentials["api_key"]

            if not self.api_key:
                logger.warning("No API key provided")
                return False

            self.connected = True
            logger.info("Connected to Sourcegraph Cody")
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False

    async def disconnect(self) -> bool:
        """Disconnect"""
        if self.session:
            await self.session.close()
        self.connected = False
        return True

    async def execute(self, action: str, parameters: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Execute action"""
        if not self.connected:
            return {"success": False, "error": "Not connected to Sourcegraph Cody"}

        # Map actions
        action_map = {
            "complete": self._complete,
            "search_codebase": self._search_codebase,
            "explain": self._explain,
            "fix": self._fix,
        }

        handler = action_map.get(action)
        if not handler:
            return {"success": False, "error": f"Unknown action: {action}"}

        try:
            result = await handler(parameters)
            return {"success": True, "result": result, "timestamp": datetime.now().isoformat()}
        except Exception as e:
            logger.error(f"Action '{action}' failed: {e}")
            return {"success": False, "error": str(e)}


    async def _complete(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Complete action"""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}

            async with self.session.post(
                f"{self.base_url}/complete",
                json=params,
                headers=headers,
                timeout=30
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return {"result": data, "action": "complete"}
                else:
                    error = await response.text()
                    raise Exception(f"Sourcegraph Cody API error {response.status}: {error}")
        except Exception as e:
            raise Exception(f"complete failed: {e}")


    async def _search_codebase(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search Codebase action"""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}

            async with self.session.post(
                f"{self.base_url}/search_codebase",
                json=params,
                headers=headers,
                timeout=30
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return {"result": data, "action": "search_codebase"}
                else:
                    error = await response.text()
                    raise Exception(f"Sourcegraph Cody API error {response.status}: {error}")
        except Exception as e:
            raise Exception(f"search_codebase failed: {e}")


    async def _explain(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Explain action"""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}

            async with self.session.post(
                f"{self.base_url}/explain",
                json=params,
                headers=headers,
                timeout=30
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return {"result": data, "action": "explain"}
                else:
                    error = await response.text()
                    raise Exception(f"Sourcegraph Cody API error {response.status}: {error}")
        except Exception as e:
            raise Exception(f"explain failed: {e}")


    async def _fix(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Fix action"""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}

            async with self.session.post(
                f"{self.base_url}/fix",
                json=params,
                headers=headers,
                timeout=30
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return {"result": data, "action": "fix"}
                else:
                    error = await response.text()
                    raise Exception(f"Sourcegraph Cody API error {response.status}: {error}")
        except Exception as e:
            raise Exception(f"fix failed: {e}")


    async def shutdown(self):
        """Cleanup"""
        await self.disconnect()
        self._initialized = False

    def get_schema(self) -> Dict[str, Any]:
        """Return schema"""
        return {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ['complete', 'search_codebase', 'explain', 'fix']},
                "parameters": {"type": "object"}
            },
            "required": ["action"]
        }


plugin = SourcegraphCodyPlugin()
