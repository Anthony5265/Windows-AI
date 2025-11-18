"""
Llamafile Local Platform Integration - PRODUCTION
"""
from typing import Dict, Any, Optional
import os
import logging
import aiohttp
import asyncio

from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class LlamafilePlugin(IntegrationPlugin):
    """Llamafile local model platform"""

    def __init__(self):
        metadata = PluginMetadata(
            id="llamafile_local",
            name="Llamafile",
            description="Llamafile local AI platform with full model management",
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["local", "ai", "llm", "llamafile"],
            requirements=["aiohttp>=3.8.0", "psutil>=5.9.0"]
        )
        super().__init__(metadata)

        self.base_url = os.getenv("LLAMAFILE_URL", "http://localhost:8000")
        self.model_path = os.getenv("LLAMAFILE_MODELS", "./models")
        self.session: Optional[aiohttp.ClientSession] = None
        self.connected = False
        self.loaded_models = []

    async def initialize(self) -> bool:
        """Initialize local platform"""
        try:
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=120))

            # Ensure models directory exists
            os.makedirs(self.model_path, exist_ok=True)

            self._initialized = True
            logger.info(f"{self.metadata.name} initialized")
            return True
        except Exception as e:
            logger.error(f"Init failed: {e}")
            return False

    async def connect(self, credentials: Dict[str, str]) -> bool:
        """Connect to local platform"""
        try:
            # Check if local server is running
            async with self.session.get(f"{self.base_url}/health", timeout=5) as response:
                self.connected = response.status == 200
                if self.connected:
                    logger.info(f"Connected to {self.metadata.name}")
                return self.connected
        except:
            logger.warning(f"{self.metadata.name} server not running, starting...")
            await self._start_server()
            self.connected = True
            return True

    async def disconnect(self) -> bool:
        """Disconnect"""
        if self.session:
            await self.session.close()
        self.connected = False
        return True

    async def execute(self, action: str, parameters: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Execute action"""
        if not self.connected:
            return {"success": False, "error": "Not connected"}

        action_map = {
            "load_model": self._load_model,
            "unload_model": self._unload_model,
            "list_models": self._list_models,
            "generate": self._generate,
            "chat": self._chat,
            "embed": self._embed,
            "download_model": self._download_model,
        }

        handler = action_map.get(action)
        if not handler:
            return {"success": False, "error": f"Unknown action: {action}"}

        try:
            result = await handler(parameters)
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"Action failed: {e}")
            return {"success": False, "error": str(e)}

    async def _start_server(self):
        """Start local server"""
        cmd = ["llamafile", "--port", "8000", "--models-path", self.model_path]
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await asyncio.sleep(3)  # Wait for startup

    async def _load_model(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Load model into memory"""
        model_name = params.get("model_name", "")

        async with self.session.post(
            f"{self.base_url}/load",
            json={"model": model_name},
            timeout=60
        ) as response:
            if response.status == 200:
                self.loaded_models.append(model_name)
                return {"loaded": model_name, "status": "ready"}
            raise Exception(f"Failed to load model: {response.status}")

    async def _unload_model(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Unload model from memory"""
        model_name = params.get("model_name", "")

        async with self.session.post(
            f"{self.base_url}/unload",
            json={"model": model_name}
        ) as response:
            if response.status == 200:
                if model_name in self.loaded_models:
                    self.loaded_models.remove(model_name)
                return {"unloaded": model_name}
            raise Exception("Unload failed")

    async def _list_models(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List available models"""
        async with self.session.get(f"{self.base_url}/models") as response:
            if response.status == 200:
                data = await response.json()
                return {"models": data.get("models", []), "loaded": self.loaded_models}
            raise Exception("Failed to list models")

    async def _generate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate text"""
        prompt = params.get("prompt", "")
        model = params.get("model", self.loaded_models[0] if self.loaded_models else "default")
        max_tokens = params.get("max_tokens", 256)

        payload = {
            "prompt": prompt,
            "model": model,
            "max_tokens": max_tokens,
            "temperature": params.get("temperature", 0.7),
            "top_p": params.get("top_p", 0.9)
        }

        async with self.session.post(
            f"{self.base_url}/generate",
            json=payload,
            timeout=120
        ) as response:
            if response.status == 200:
                data = await response.json()
                return {"text": data.get("text", ""), "model": model}
            raise Exception(f"Generation failed: {response.status}")

    async def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Chat completion"""
        messages = params.get("messages", [])
        model = params.get("model", self.loaded_models[0] if self.loaded_models else "default")

        async with self.session.post(
            f"{self.base_url}/chat",
            json={"messages": messages, "model": model},
            timeout=120
        ) as response:
            if response.status == 200:
                data = await response.json()
                return data
            raise Exception("Chat failed")

    async def _embed(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate embeddings"""
        text = params.get("text", "")

        async with self.session.post(
            f"{self.base_url}/embed",
            json={"text": text},
            timeout=30
        ) as response:
            if response.status == 200:
                data = await response.json()
                return {"embedding": data.get("embedding", [])}
            raise Exception("Embedding failed")

    async def _download_model(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Download model"""
        model_name = params.get("model_name", "")

        async with self.session.post(
            f"{self.base_url}/download",
            json={"model": model_name},
            timeout=3600
        ) as response:
            if response.status == 200:
                return {"downloaded": model_name, "path": self.model_path}
            raise Exception("Download failed")

    async def shutdown(self):
        """Shutdown"""
        await self.disconnect()
        self._initialized = False

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {"type": "string"},
                "parameters": {"type": "object"}
            },
            "required": ["action"]
        }


plugin = LlamafilePlugin()
