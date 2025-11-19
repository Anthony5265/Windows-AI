"""
TASK-003: Tabnine Plugin - Production Implementation
Offline model support, custom training, and enterprise features
"""
from typing import Dict, Any, List, Optional
import os
import logging
import aiohttp
import json
from pathlib import Path

from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class TabninePlugin(IntegrationPlugin):
    """Tabnine AI code completion with offline and custom model support"""

    def __init__(self):
        metadata = PluginMetadata(
            id="tabnine_enhanced",
            name="Tabnine",
            description="AI code completion with offline models and custom training",
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["code", "completion", "ai", "offline", "privacy"],
            requirements=["aiohttp>=3.8.0"]
        )
        super().__init__(metadata)

        self.api_key = os.getenv("TABNINE_API_KEY", "")
        self.use_local_model = os.getenv("TABNINE_LOCAL_MODE", "true").lower() == "true"
        self.local_port = int(os.getenv("TABNINE_LOCAL_PORT", "5555"))
        self.cloud_url = "https://cloud.tabnine.com/api/v1"
        self.session: Optional[aiohttp.ClientSession] = None
        self.connected = False

    async def initialize(self) -> bool:
        """Initialize Tabnine"""
        try:
            self.session = aiohttp.ClientSession()
            self._initialized = True
            logger.info("Tabnine plugin initialized")
            return True
        except Exception as e:
            logger.error(f"Init failed: {e}")
            return False

    async def connect(self, credentials: Dict[str, str]) -> bool:
        """Connect to Tabnine"""
        try:
            if "api_key" in credentials:
                self.api_key = credentials["api_key"]

            # Try local model first if enabled
            if self.use_local_model:
                try:
                    async with self.session.get(
                        f"http://localhost:{self.local_port}/health",
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        if response.status == 200:
                            self.connected = True
                            logger.info("Connected to local Tabnine model")
                            return True
                except:
                    logger.warning("Local Tabnine not available, falling back to cloud")

            # Fall back to cloud
            if self.api_key:
                self.connected = True
                logger.info("Using Tabnine cloud service")
                return True

            return False
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False

    async def disconnect(self) -> bool:
        """Disconnect"""
        if self.session:
            await self.session.close()
        self.connected = False
        return True

    async def execute(self, action: str, parameters: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Execute Tabnine actions"""
        if not self.connected:
            return {"success": False, "error": "Not connected"}

        action_map = {
            "complete": self._get_completion,
            "train": self._train_custom_model,
            "semantic": self._semantic_completion,
            "whole_line": self._whole_line_completion,
            "configure": self._configure_model
        }

        handler = action_map.get(action)
        if not handler:
            return {"success": False, "error": f"Unknown action: {action}"}

        try:
            result = await handler(parameters)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _get_completion(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get code completions"""
        code_before = params.get("before", "")
        code_after = params.get("after", "")
        filename = params.get("filename", "")
        language = params.get("language", "")
        max_results = params.get("max_results", 5)

        url = f"http://localhost:{self.local_port}/complete" if self.use_local_model else f"{self.cloud_url}/complete"

        payload = {
            "before": code_before,
            "after": code_after,
            "filename": filename,
            "language": language,
            "max_num_results": max_results,
            "region_includes_beginning": True,
            "region_includes_end": True
        }

        headers = {}
        if not self.use_local_model and self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        async with self.session.post(url, json=payload, headers=headers, timeout=10) as response:
            if response.status == 200:
                data = await response.json()
                completions = [
                    {
                        "text": item.get("new_prefix", ""),
                        "detail": item.get("detail", ""),
                        "kind": item.get("kind", ""),
                        "origin": item.get("origin", ""),
                        "deprecated": item.get("deprecated", False)
                    }
                    for item in data.get("results", [])
                ]
                return {"completions": completions, "old_prefix": data.get("old_prefix", "")}
            else:
                raise Exception(f"API error: {response.status}")

    async def _train_custom_model(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Train custom Tabnine model on codebase"""
        codebase_path = params.get("codebase_path", "")
        model_name = params.get("model_name", "custom_model")
        languages = params.get("languages", [])

        # Collect training data
        training_files = []
        path = Path(codebase_path)
        for lang in languages:
            extensions = self._get_extensions_for_language(lang)
            for ext in extensions:
                training_files.extend(list(path.rglob(f"*{ext}")))

        payload = {
            "model_name": model_name,
            "training_files": [str(f) for f in training_files],
            "languages": languages
        }

        if not self.use_local_model:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            async with self.session.post(
                f"{self.cloud_url}/train",
                json=payload,
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "model_id": data.get("model_id"),
                        "status": "training",
                        "files_count": len(training_files)
                    }
                raise Exception(f"Training failed: {response.status}")

        return {"status": "local_training_not_supported"}

    async def _semantic_completion(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get semantic code completions"""
        query = params.get("query", "")
        context = params.get("context", "")
        language = params.get("language", "python")

        # Use semantic search for completions
        completion_result = await self._get_completion({
            "before": f"{context}\n# {query}\n",
            "after": "",
            "language": language,
            "max_results": 3
        })

        return {
            "semantic_suggestions": completion_result.get("completions", []),
            "query": query
        }

    async def _whole_line_completion(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get whole line completions"""
        code = params.get("code", "")
        line_prefix = params.get("line_prefix", "")
        language = params.get("language", "python")

        result = await self._get_completion({
            "before": code + line_prefix,
            "after": "",
            "language": language,
            "max_results": 5
        })

        return {
            "line_completions": result.get("completions", [])
        }

    async def _configure_model(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Configure Tabnine model settings"""
        config = {
            "local_mode": params.get("local_mode", self.use_local_model),
            "local_port": params.get("local_port", self.local_port),
            "auto_import": params.get("auto_import", True),
            "semantic_status": params.get("semantic_status", True),
            "snippets_status": params.get("snippets_status", True)
        }

        self.use_local_model = config["local_mode"]
        self.local_port = config["local_port"]

        return {"configuration": config, "applied": True}

    def _get_extensions_for_language(self, language: str) -> List[str]:
        """Get file extensions for language"""
        ext_map = {
            "python": [".py"],
            "javascript": [".js", ".jsx"],
            "typescript": [".ts", ".tsx"],
            "java": [".java"],
            "csharp": [".cs"],
            "cpp": [".cpp", ".h"],
            "go": [".go"],
            "rust": [".rs"],
            "ruby": [".rb"],
            "php": [".php"]
        }
        return ext_map.get(language, [f".{language}"])

    async def shutdown(self):
        await self.disconnect()

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["complete", "train", "semantic", "whole_line", "configure"]},
                "code": {"type": "string"},
                "language": {"type": "string"}
            },
            "required": ["action"]
        }


plugin = TabninePlugin()
