"""
TASK-146: OWASP ZAP Plugin - Production Implementation
OWASP ZAP testing integration
"""
from typing import Dict, Any, List, Optional
import os
import logging
import aiohttp
import json
from datetime import datetime

from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class OWASPZAPPlugin(IntegrationPlugin):
    """OWASP ZAP integration plugin"""

    def __init__(self):
        metadata = PluginMetadata(
            id="task-146_owasp_zap",
            name="OWASP ZAP",
            description="OWASP ZAP testing integration",
            version="1.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["testing", "ai", "integration"],
            requirements=["aiohttp>=3.8.0"]
        )
        super().__init__(metadata)

        self.api_key = os.getenv("OWASP_ZAP_API_KEY", "")
        self.base_url = "http://localhost:8080"
        self.session: Optional[aiohttp.ClientSession] = None
        self.connected = False

    async def initialize(self) -> bool:
        """Initialize plugin"""
        try:
            self.session = aiohttp.ClientSession()
            self._initialized = True
            logger.info("OWASP ZAP plugin initialized")
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
            logger.info("Connected to OWASP ZAP")
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
            return {"success": False, "error": "Not connected to OWASP ZAP"}

        # Map actions
        action_map = {
            "scan": self._scan,
            "attack": self._attack,
            "analyze": self._analyze,
            "report": self._report,
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


    async def _scan(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Scan action"""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}

            async with self.session.post(
                f"{self.base_url}/scan",
                json=params,
                headers=headers,
                timeout=30
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return {"result": data, "action": "scan"}
                else:
                    error = await response.text()
                    raise Exception(f"OWASP ZAP API error {response.status}: {error}")
        except Exception as e:
            raise Exception(f"scan failed: {e}")


    async def _attack(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Attack action"""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}

            async with self.session.post(
                f"{self.base_url}/attack",
                json=params,
                headers=headers,
                timeout=30
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return {"result": data, "action": "attack"}
                else:
                    error = await response.text()
                    raise Exception(f"OWASP ZAP API error {response.status}: {error}")
        except Exception as e:
            raise Exception(f"attack failed: {e}")


    async def _analyze(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze action"""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}

            async with self.session.post(
                f"{self.base_url}/analyze",
                json=params,
                headers=headers,
                timeout=30
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return {"result": data, "action": "analyze"}
                else:
                    error = await response.text()
                    raise Exception(f"OWASP ZAP API error {response.status}: {error}")
        except Exception as e:
            raise Exception(f"analyze failed: {e}")


    async def _report(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Report action"""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}

            async with self.session.post(
                f"{self.base_url}/report",
                json=params,
                headers=headers,
                timeout=30
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return {"result": data, "action": "report"}
                else:
                    error = await response.text()
                    raise Exception(f"OWASP ZAP API error {response.status}: {error}")
        except Exception as e:
            raise Exception(f"report failed: {e}")


    async def shutdown(self):
        """Cleanup"""
        await self.disconnect()
        self._initialized = False

    def get_schema(self) -> Dict[str, Any]:
        """Return schema"""
        return {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ['scan', 'attack', 'analyze', 'report']},
                "parameters": {"type": "object"}
            },
            "required": ["action"]
        }


plugin = OWASPZAPPlugin()
