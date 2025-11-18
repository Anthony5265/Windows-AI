"""
Metabase - Production Implementation
Open-source BI
"""
from typing import Dict, Any, Optional
import os
import logging
import aiohttp
from datetime import datetime

from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class MetabasePlugin(IntegrationPlugin):
    def __init__(self):
        metadata = PluginMetadata(
            id="metabase",
            name="Metabase",
            description="Open-source BI",
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["metabase", "production"]
        )
        super().__init__(metadata)
        self.api_key = os.getenv("METABASE_API_KEY", "")
        self.base_url = os.getenv("METABASE_URL", "https://api.metabase.com")
        self.session: Optional[aiohttp.ClientSession] = None
        self.connected = False

    async def initialize(self) -> bool:
        try:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=60)
            )
            self._initialized = True
            return True
        except Exception as e:
            logger.error(f"Init failed: {e}")
            return False

    async def connect(self, credentials: Dict[str, str]) -> bool:
        try:
            if "api_key" in credentials:
                self.api_key = credentials["api_key"]
            self.connected = True
            return True
        except Exception as e:
            logger.error(f"Connect failed: {e}")
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
            "query": self._query,
            "dashboard": self._dashboard,
            "share": self._share,
        }

        handler = action_map.get(action)
        if not handler:
            return {"success": False, "error": f"Unknown action: {action}"}

        try:
            result = await handler(parameters)
            return {"success": True, "result": result, "timestamp": datetime.now().isoformat()}
        except Exception as e:
            logger.error(f"Action failed: {e}")
            return {"success": False, "error": str(e)}

    async def _query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute query action"""
        async with self.session.post(
            f"{self.base_url}/query",
            json=params,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=60
        ) as response:
            if response.status == 200:
                return await response.json()
            raise Exception(f"query failed: {response.status}")

    async def _dashboard(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute dashboard action"""
        async with self.session.post(
            f"{self.base_url}/dashboard",
            json=params,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=60
        ) as response:
            if response.status == 200:
                return await response.json()
            raise Exception(f"dashboard failed: {response.status}")

    async def _share(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute share action"""
        async with self.session.post(
            f"{self.base_url}/share",
            json=params,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=60
        ) as response:
            if response.status == 200:
                return await response.json()
            raise Exception(f"share failed: {response.status}")

    async def shutdown(self):
        await self.disconnect()

    def get_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {"action": {"type": "string"}, "parameters": {"type": "object"}}, "required": ["action"]}


plugin = MetabasePlugin()
