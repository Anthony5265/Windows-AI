"""
Text Generation WebUI (Oobabooga) Integration Plugin
====================================================

Provides a production-grade bridge between Windows AI and a locally running
Text Generation WebUI/Oobabooga server. The plugin exposes health checks,
model management, text generation, chat completions, and abort controls so
the orchestrator can treat the local stack similarly to hosted LLMs.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional, Sequence, Tuple

import httpx

from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class TextGenerationWebUIPlugin(IntegrationPlugin):
    """
    Integration plugin that talks to the Text Generation WebUI HTTP API.

    The connection can be configured through environment variables:
    - `TEXTGEN_WEBUI_URL`
    - `TEXTGEN_WEBUI_API_KEY`
    - `TEXTGEN_WEBUI_TIMEOUT`
    """

    @staticmethod
    def get_metadata() -> PluginMetadata:
        return PluginMetadata(
            id="text_generation_webui",
            name="Text Generation WebUI",
            description="Manage and query a local Oobabooga/Text Generation WebUI server",
            version="1.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["local-llm", "oobabooga", "text-generation", "offline"],
            requirements=["httpx"],
        )

    def __init__(self, metadata: PluginMetadata):
        super().__init__(metadata)
        self.base_url = (
            os.getenv("TEXTGEN_WEBUI_URL", "http://127.0.0.1:5000").rstrip("/")
        )
        self.api_key = os.getenv("TEXTGEN_WEBUI_API_KEY")
        self.timeout = float(os.getenv("TEXTGEN_WEBUI_TIMEOUT", "120"))
        self.client: Optional[httpx.AsyncClient] = None

        self.default_generation_params: Dict[str, Any] = {
            "max_new_tokens": 256,
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40,
            "typical_p": 1.0,
            "repetition_penalty": 1.1,
            "presence_penalty": 0.0,
            "frequency_penalty": 0.0,
            "seed": -1,
            "stream": False,
            "do_sample": True,
            "truncate": 2048,
            "ban_eos_token": False,
            "skip_special_tokens": True,
            "mode": "instruct",
        }

    async def initialize(self) -> bool:
        """Create the HTTP client and probe the server."""
        await self._reset_client()
        try:
            health = await self._health_check({})
            if not health.get("success"):
                logger.warning("Text Generation WebUI health check failed: %s", health)
        except Exception as exc:  # pragma: no cover - health is best effort
            logger.debug("Text Generation WebUI probe skipped: %s", exc)

        self._initialized = True
        return True

    async def connect(self, credentials: Dict[str, str]) -> bool:
        """Override connection details at runtime and verify connectivity."""
        base_url = credentials.get("base_url")
        api_key = credentials.get("api_key")

        if base_url:
            self.base_url = base_url.rstrip("/")
        if api_key is not None:
            self.api_key = api_key or None

        await self._reset_client()
        health = await self._health_check({})
        return bool(health.get("success"))

    async def disconnect(self) -> bool:
        """Close the HTTP session."""
        if self.client:
            await self.client.aclose()
            self.client = None
        return True

    async def execute(
        self,
        action: str,
        parameters: Optional[Dict[str, Any]] = None,
        **_: Any,
    ) -> Dict[str, Any]:
        """Dispatch user actions to the appropriate helper."""
        params = parameters or {}
        action = action or "health"

        handlers = {
            "health": self._health_check,
            "list_models": self._list_models,
            "load_model": self._load_model,
            "unload_model": self._unload_model,
            "generate": self._generate_text,
            "chat": self._chat_completion,
            "abort": self._abort_generation,
        }

        handler = handlers.get(action)
        if not handler:
            return {
                "success": False,
                "error": f"Unsupported action '{action}'. "
                f"Available actions: {', '.join(sorted(handlers))}",
            }

        return await handler(params)

    def get_schema(self) -> Dict[str, Any]:
        """Describe supported actions for the UI and API clients."""
        return {
            "actions": [
                {
                    "name": "health",
                    "description": "Check if the local Text Generation WebUI server is reachable.",
                    "parameters": {},
                },
                {
                    "name": "list_models",
                    "description": "List discovered models and the currently loaded default.",
                    "parameters": {},
                },
                {
                    "name": "load_model",
                    "description": "Load or switch the active model in the running server.",
                    "parameters": {
                        "model": {"type": "string", "required": True},
                        "lora": {"type": "string", "required": False},
                        "mode": {
                            "type": "string",
                            "required": False,
                            "description": "chat/instruct/etc.",
                        },
                    },
                },
                {
                    "name": "unload_model",
                    "description": "Free GPU/CPU memory by unloading the active model.",
                    "parameters": {
                        "model": {
                            "type": "string",
                            "required": False,
                            "description": "Optional specific model to unload.",
                        }
                    },
                },
                {
                    "name": "generate",
                    "description": "Run a prompt through the loaded model.",
                    "parameters": {
                        "prompt": {"type": "string", "required": True},
                        "max_new_tokens": {"type": "number", "required": False},
                        "temperature": {"type": "number", "required": False},
                        "top_p": {"type": "number", "required": False},
                        "stop": {"type": "array", "items": {"type": "string"}},
                        "model": {"type": "string", "required": False},
                    },
                },
                {
                    "name": "chat",
                    "description": "Send a conversational turn with optional history.",
                    "parameters": {
                        "user_input": {"type": "string", "required": False},
                        "messages": {
                            "type": "array",
                            "required": False,
                            "description": "OpenAI-style messages list.",
                        },
                        "history": {
                            "type": "object",
                            "required": False,
                            "description": "Raw history structure expected by WebUI.",
                        },
                        "max_new_tokens": {"type": "number", "required": False},
                    },
                },
                {
                    "name": "abort",
                    "description": "Abort the currently running generation job.",
                    "parameters": {},
                },
            ]
        }

    async def _reset_client(self):
        """Ensure the HTTP client reflects the latest settings."""
        if self.client:
            await self.client.aclose()

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers=headers,
        )

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an HTTP request and normalise errors."""
        if not self.client:
            await self._reset_client()
        assert self.client is not None

        try:
            response = await self.client.request(
                method=method,
                url=path,
                json=json_body,
            )
            response.raise_for_status()
            if response.content:
                return response.json()
            return {}
        except httpx.TimeoutException as exc:
            raise RuntimeError(
                f"Text Generation WebUI request timed out after {self.timeout:.1f}s"
            ) from exc
        except httpx.HTTPStatusError as exc:
            text = exc.response.text.strip()
            raise RuntimeError(
                f"Text Generation WebUI responded with {exc.response.status_code}: {text}"
            ) from exc
        except httpx.RequestError as exc:
            raise RuntimeError(f"Unable to reach Text Generation WebUI: {exc}") from exc

    async def _health_check(self, _: Dict[str, Any]) -> Dict[str, Any]:
        """Probe the server by listing models."""
        try:
            data = await self._request("GET", "/api/v1/models")
            models = self._normalise_models(data)
            return {
                "success": True,
                "server_url": self.base_url,
                "model_count": len(models),
                "default_model": data.get("default") or data.get("default_model"),
                "models": models,
            }
        except RuntimeError as exc:
            return {"success": False, "error": str(exc), "server_url": self.base_url}

    async def _list_models(self, _: Dict[str, Any]) -> Dict[str, Any]:
        """Return available models and metadata."""
        return await self._health_check({})

    async def _load_model(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Load or switch the active model."""
        model_name = params.get("model")
        if not model_name:
            return {"success": False, "error": "Parameter 'model' is required."}

        payload_keys = [
            "lora",
            "lora_dir",
            "prompt_template",
            "mode",
            "gpu_split",
            "auto_repeat",
            "stream",
        ]
        payload = {"model": model_name}
        for key in payload_keys:
            if key in params:
                payload[key] = params[key]

        try:
            data = await self._request("POST", "/api/v1/load", json_body=payload)
            return {
                "success": True,
                "message": data.get("result") or f"Load requested for {model_name}",
                "details": data,
            }
        except RuntimeError as exc:
            return {"success": False, "error": str(exc)}

    async def _unload_model(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Unload the active model."""
        payload = {}
        if params.get("model"):
            payload["model"] = params["model"]

        try:
            data = await self._request("POST", "/api/v1/unload", json_body=payload)
            return {
                "success": True,
                "message": data.get("result", "Model unload requested."),
                "details": data,
            }
        except RuntimeError as exc:
            return {"success": False, "error": str(exc)}

    async def _generate_text(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send a prompt to /api/v1/generate."""
        prompt = params.get("prompt")
        if not prompt:
            return {"success": False, "error": "Parameter 'prompt' is required."}

        payload = self._build_generation_payload(prompt, params)

        try:
            data = await self._request("POST", "/api/v1/generate", json_body=payload)
            results = data.get("results") or []
            text = results[0].get("text") if results else ""
            return {
                "success": True,
                "text": text,
                "finish_reason": results[0].get("finish_reason") if results else None,
                "seed": results[0].get("seed") if results else None,
                "raw": data,
            }
        except RuntimeError as exc:
            return {"success": False, "error": str(exc)}

    async def _chat_completion(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send a conversational turn to /api/v1/chat."""
        user_input = params.get("user_input")
        messages = params.get("messages") or []
        history = params.get("history")

        if not user_input:
            user_input, history = self._extract_user_input_from_messages(
                messages, history
            )

        if not user_input:
            return {
                "success": False,
                "error": "Provide 'user_input' or include a user message in 'messages'.",
            }

        payload = self._build_generation_payload(user_input, params)
        payload["user_input"] = user_input
        payload["stream"] = bool(params.get("stream", False))
        payload["history"] = history or {"internal": [], "visible": []}

        optional_keys = [
            "character",
            "instruction_template",
            "name1",
            "name2",
            "mode",
        ]
        for key in optional_keys:
            if key in params:
                payload[key] = params[key]

        try:
            data = await self._request("POST", "/api/v1/chat", json_body=payload)
            response = data.get("results", [{}])[0]
            history_visible = response.get("history_visible") or []
            reply_text = (
                history_visible[-1][-1]
                if history_visible and history_visible[-1]
                else response.get("text")
            )
            return {
                "success": True,
                "text": reply_text,
                "history": data.get("history") or response.get("history"),
                "raw": data,
            }
        except RuntimeError as exc:
            return {"success": False, "error": str(exc)}

    async def _abort_generation(self, _: Dict[str, Any]) -> Dict[str, Any]:
        """Abort the current inference job."""
        try:
            data = await self._request("POST", "/api/v1/abort", json_body={})
            return {
                "success": True,
                "message": data.get("result", "Abort signal sent."),
                "details": data,
            }
        except RuntimeError as exc:
            return {"success": False, "error": str(exc)}

    def _build_generation_payload(
        self, prompt: str, overrides: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge common generation parameters with user overrides."""
        payload = dict(self.default_generation_params)
        payload["prompt"] = prompt

        allowed_overrides = set(payload.keys()).union(
            {
                "stop",
                "negative_prompt",
                "grammar",
                "model",
                "preset",
                "memory",
                "min_p",
            }
        )

        for key, value in overrides.items():
            if value is None:
                continue
            if key in allowed_overrides:
                payload[key] = value

        if isinstance(payload.get("stop"), str):
            payload["stop"] = [payload["stop"]]

        return payload

    def _extract_user_input_from_messages(
        self,
        messages: Sequence[Dict[str, Any]],
        history: Optional[Dict[str, Any]],
    ) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """Convert OpenAI-style messages into WebUI history."""
        user_input: Optional[str] = None
        trimmed_messages: List[Dict[str, Any]] = list(messages)

        for index in range(len(trimmed_messages) - 1, -1, -1):
            if trimmed_messages[index].get("role") == "user":
                user_input = trimmed_messages[index].get("content", "")
                trimmed_messages = trimmed_messages[:index]
                break

        if not history:
            history = self._build_history(trimmed_messages)

        return user_input, history

    def _build_history(
        self, messages: Sequence[Dict[str, Any]]
    ) -> Dict[str, List[List[str]]]:
        """Transform OpenAI-style history into WebUI history format."""
        history: Dict[str, List[List[str]]] = {"internal": [], "visible": []}
        visible: List[List[str]] = []
        current_user: Optional[str] = None

        for message in messages:
            role = message.get("role")
            content = message.get("content", "")
            if role == "user":
                current_user = content
            elif role == "assistant":
                visible.append([current_user or "", content])
                current_user = None

        if current_user:
            visible.append([current_user, ""])

        history["visible"] = visible
        return history

    def _normalise_models(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Normalize the models payload from the WebUI server."""
        raw_models = data.get("data") or data.get("models") or []
        models: List[Dict[str, Any]] = []

        for entry in raw_models:
            if isinstance(entry, dict):
                models.append(
                    {
                        "name": entry.get("name") or entry.get("model"),
                        "path": entry.get("path"),
                        "size": entry.get("size") or entry.get("filesize"),
                        "last_modified": entry.get("last_modified"),
                        "metadata": {
                            key: value
                            for key, value in entry.items()
                            if key
                            not in {"name", "model", "path", "size", "filesize", "last_modified"}
                        },
                    }
                )
            else:
                models.append({"name": str(entry)})

        return models
