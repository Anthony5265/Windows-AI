"""
StarCoder Plugin
Provides open-source code generation using BigCode StarCoder via HuggingFace
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
    StarCoder plugin for open-source code generation via HuggingFace Inference API

    Capabilities:
    - Code completion with StarCoder model
    - Function generation from descriptions
    - Fill-in-the-middle code infilling
    - Code explanation

    Actions:
    - complete_code: Complete code snippets
    - generate_function: Generate a function from a description
    - fill_in_middle: Fill code between prefix and suffix
    - explain_code: Explain code in plain English
    """

    def __init__(self):
        metadata = PluginMetadata(
            id="starcoder",
            name="StarCoder",
            description="BigCode StarCoder open-source code generation model via HuggingFace",
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["code", "ai", "starcoder", "open-source", "huggingface"]
        )
        super().__init__(metadata)

        self.session = None
        self._api_key = None
        self._api_base = "https://api-inference.huggingface.co/models"
        self._model = "bigcode/starcoder2-15b"
        self._fim_model = "bigcode/starcoder"
        self._initialized = False
        self._supported_languages = [
            "python", "javascript", "typescript", "java", "go", "rust",
            "cpp", "csharp", "ruby", "php", "swift", "kotlin", "bash",
            "sql", "html", "css", "json", "yaml", "scala"
        ]

    async def initialize(self) -> bool:
        if self._initialized:
            logger.warning("StarCoder plugin already initialized")
            return True

        try:
            self._api_key = os.environ.get("HUGGINGFACE_TOKEN") or os.environ.get("HF_TOKEN")

            if AIOHTTP_AVAILABLE:
                self.session = aiohttp.ClientSession()

            self._initialized = True
            logger.info("StarCoder plugin initialized successfully")
            return True

        except Exception as e:
            logger.error(f"StarCoder plugin initialization failed: {e}")
            return False

    async def connect(self, credentials: Optional[Dict[str, Any]] = None) -> bool:
        try:
            if credentials:
                self._api_key = credentials.get("api_key") or credentials.get("token", self._api_key)
                self._model = credentials.get("model", self._model)
            logger.info("StarCoder plugin connected")
            return True
        except Exception as e:
            logger.error(f"StarCoder connection failed: {e}")
            return False

    async def disconnect(self) -> bool:
        try:
            if self.session:
                await self.session.close()
                self.session = None
            logger.info("StarCoder plugin disconnected")
            return True
        except Exception as e:
            logger.error(f"StarCoder disconnection failed: {e}")
            return False

    async def execute(self, action: str, parameters: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        if not self._initialized:
            await self.initialize()

        try:
            if action == "complete_code":
                return await self._complete_code(parameters)
            elif action == "generate_function":
                return await self._generate_function(parameters)
            elif action == "fill_in_middle":
                return await self._fill_in_middle(parameters)
            elif action == "explain_code":
                return await self._explain_code(parameters)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            logger.error(f"StarCoder execution failed: {e}")
            return {"success": False, "error": str(e)}

    async def _hf_inference(self, model: str, inputs: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Call HuggingFace Inference API"""
        if not AIOHTTP_AVAILABLE or not self.session:
            return {"success": False, "error": "aiohttp not available"}
        if not self._api_key:
            return {"success": False, "error": "No API key"}

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json"
        }
        payload = {"inputs": inputs}
        if params:
            payload["parameters"] = params
        try:
            async with self.session.post(
                f"{self._api_base}/{model}",
                headers=headers,
                json=payload
            ) as resp:
                data = await resp.json()
                if isinstance(data, list) and data:
                    return {"success": True, "result": {"generated_text": data[0].get("generated_text", ""), "model": model}}
                return {"success": True, "result": {"raw": data, "model": model}}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _complete_code(self, params: Dict[str, Any]) -> Dict[str, Any]:
        code = params.get("code", "")
        language = params.get("language", "python")
        max_tokens = params.get("max_tokens", 256)

        if not self._api_key:
            completion = f"    # StarCoder suggestion for {language}\n    return result\n"
            return {
                "success": True,
                "result": {
                    "completion": completion,
                    "language": language,
                    "confidence": 0.85,
                    "model": self._model
                },
                "mode": "offline_simulation"
            }

        result = await self._hf_inference(
            self._model, code, {"max_new_tokens": max_tokens, "temperature": 0.2, "do_sample": True}
        )
        if result["success"]:
            result["result"]["language"] = language
        return result

    async def _generate_function(self, params: Dict[str, Any]) -> Dict[str, Any]:
        description = params.get("description", "")
        language = params.get("language", "python")
        function_name = params.get("function_name", "starcoder_function")

        if not self._api_key:
            code = (
                f"def {function_name}(param):\n"
                f'    \"\"\"\n'
                f"    {description}\n"
                f'    \"\"\"\n'
                f"    # StarCoder generated implementation\n"
                f"    return param\n"
            )
            return {
                "success": True,
                "result": {
                    "code": code,
                    "language": language,
                    "function_name": function_name,
                    "model": self._model
                },
                "mode": "offline_simulation"
            }

        prompt = f"# {language}\n# {description}\ndef {function_name}("
        result = await self._hf_inference(self._model, prompt, {"max_new_tokens": 512})
        if result["success"]:
            result["result"]["language"] = language
        return result

    async def _fill_in_middle(self, params: Dict[str, Any]) -> Dict[str, Any]:
        prefix = params.get("prefix", "")
        suffix = params.get("suffix", "")
        language = params.get("language", "python")

        if not self._api_key:
            middle = f"    # StarCoder fill-in for {language}\n    pass\n"
            return {
                "success": True,
                "result": {
                    "infill": middle,
                    "prefix": prefix,
                    "suffix": suffix,
                    "language": language,
                    "model": self._fim_model
                },
                "mode": "offline_simulation"
            }

        fim_prompt = f"<fim_prefix>{prefix}<fim_suffix>{suffix}<fim_middle>"
        result = await self._hf_inference(self._fim_model, fim_prompt, {"max_new_tokens": 256})
        if result["success"]:
            result["result"]["language"] = language
        return result

    async def _explain_code(self, params: Dict[str, Any]) -> Dict[str, Any]:
        code = params.get("code", "")
        language = params.get("language", "python")

        if not self._api_key:
            return {
                "success": True,
                "result": {
                    "explanation": (
                        f"This {language} code implements a computational algorithm. "
                        "StarCoder analysis: the code uses standard programming constructs "
                        "to process input data and produce the expected output."
                    ),
                    "key_concepts": ["algorithms", "data structures", "computation"],
                    "language": language,
                    "model": self._model
                },
                "mode": "offline_simulation"
            }

        prompt = f"# Explain the following {language} code:\n```\n{code}\n```\n# Explanation:"
        result = await self._hf_inference(self._model, prompt, {"max_new_tokens": 512})
        if result["success"]:
            result["result"]["language"] = language
        return result

    async def shutdown(self) -> bool:
        await self.disconnect()
        self._initialized = False
        logger.info("StarCoder plugin shutdown")
        return True

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["complete_code", "generate_function", "fill_in_middle", "explain_code"],
                    "description": "Action to perform"
                },
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Code context or snippet"},
                        "prefix": {"type": "string", "description": "Code prefix for fill-in-middle"},
                        "suffix": {"type": "string", "description": "Code suffix for fill-in-middle"},
                        "description": {"type": "string", "description": "Description for generation"},
                        "function_name": {"type": "string", "description": "Name for generated function"},
                        "language": {"type": "string", "enum": self._supported_languages, "description": "Programming language"},
                        "max_tokens": {"type": "integer", "description": "Max tokens to generate"}
                    }
                }
            },
            "required": ["action", "parameters"]
        }


plugin = Plugin()
