"""
Dalai Integration Plugin

Production-grade interface for Dalai's local HTTP API.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

import httpx

from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class DalaiPlugin(IntegrationPlugin):
    @staticmethod
    def get_metadata() -> PluginMetadata:
        return PluginMetadata(
            id='dalai_local',
            name='Dalai Local Models',
            description='Interact with a running Dalai server',
            version='1.0.0',
            author='Windows AI Team',
            plugin_type=PluginType.INTEGRATION,
            tags=['local-llm', 'dalai'],
            requirements=['httpx'],
        )

    def __init__(self, metadata: PluginMetadata):
        super().__init__(metadata)
        self.base_url = os.getenv('DALAI_API_BASE', 'http://127.0.0.1:3000').rstrip('/')
        self.timeout = float(os.getenv('DALAI_TIMEOUT', '120'))
        self.client: Optional[httpx.AsyncClient] = None

    async def initialize(self) -> bool:
        await self._ensure_client()
        self._initialized = True
        return True

    async def connect(self, credentials: Dict[str, str]) -> bool:
        base_url = credentials.get('base_url')
        if base_url:
            self.base_url = base_url.rstrip('/')
        await self._ensure_client(force=True)
        health = await self._health({})
        return health.get('success', False)

    async def disconnect(self) -> bool:
        if self.client:
            await self.client.aclose()
            self.client = None
        return True

    def get_schema(self) -> Dict[str, Any]:
        return {
            'actions': [
                {'name': 'health', 'description': 'Check Dalai availability.'},
                {'name': 'list_models', 'description': 'List installed Dalai models.'},
                {
                    'name': 'generate',
                    'description': 'Generate text via Dalai',
                    'parameters': {
                        'prompt': {'type': 'string', 'required': True},
                        'model': {'type': 'string'},
                        'temperature': {'type': 'number'},
                        'max_tokens': {'type': 'number'},
                        'top_p': {'type': 'number'},
                    },
                },
                {
                    'name': 'install_model',
                    'description': 'Trigger Dalai to download a model',
                    'parameters': {
                        'family': {'type': 'string', 'required': True},
                        'size': {'type': 'string', 'required': True},
                    },
                },
            ]
        }

    async def execute(
        self,
        action: str,
        parameters: Optional[Dict[str, Any]] = None,
        **_: Any,
    ) -> Dict[str, Any]:
        params = parameters or {}
        action = action or 'health'
        handlers = {
            'health': self._health,
            'list_models': self._list_models,
            'generate': self._generate,
            'install_model': self._install,
        }
        handler = handlers.get(action)
        if not handler:
            return {
                'success': False,
                'error': f"Unsupported action '{action}'. Options: {', '.join(sorted(handlers))}",
            }
        try:
            return await handler(params)
        except Exception as exc:
            logger.error('Dalai action %s failed: %s', action, exc, exc_info=True)
            return {'success': False, 'error': str(exc)}

    async def _ensure_client(self, force: bool = False):
        if self.client and not force:
            return
        if self.client:
            await self.client.aclose()
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={'Content-Type': 'application/json'},
        )

    async def _request(
        self,
        method: str,
        path: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        await self._ensure_client()
        assert self.client is not None
        response = await self.client.request(method, path, json=payload)
        response.raise_for_status()
        return response.json() if response.content else {}

    async def _health(self, _: Dict[str, Any]) -> Dict[str, Any]:
        try:
            data = await self._request('GET', '/api/health')
            return {'success': True, 'server': self.base_url, 'details': data}
        except Exception as exc:
            return {'success': False, 'error': str(exc), 'server': self.base_url}

    async def _list_models(self, _: Dict[str, Any]) -> Dict[str, Any]:
        data = await self._request('GET', '/api/models')
        raw = data.get('models') or data.get('data') or []
        normalized = []
        for entry in raw:
            if isinstance(entry, dict):
                normalized.append(
                    {
                        'id': entry.get('id') or entry.get('name'),
                        'family': entry.get('family'),
                        'size': entry.get('size'),
                        'installed': entry.get('installed', True),
                    }
                )
            else:
                normalized.append({'id': str(entry)})
        return {'success': True, 'models': normalized}

    async def _generate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        prompt = params.get('prompt')
        if not prompt:
            return {'success': False, 'error': 'Parameter  is required.'}
        payload = {
            'model': params.get('model', 'llama-7B'),
            'prompt': prompt,
            'temperature': params.get('temperature', 0.7),
            'maxTokens': params.get('max_tokens', 256),
            'topP': params.get('top_p', 0.9),
        }
        data = await self._request('POST', '/api/generate', payload=payload)
        return {
            'success': True,
            'response': data.get('output') or data.get('response', ''),
            'raw': data,
        }

    async def _install(self, params: Dict[str, Any]) -> Dict[str, Any]:
        family = params.get('family')
        size = params.get('size')
        if not family or not size:
            return {'success': False, 'error': 'Parameters  and  are required.'}
        payload = {'family': family, 'size': size}
        data = await self._request('POST', '/api/install', payload=payload)
        return {'success': True, 'message': data.get('message', 'Install triggered'), 'raw': data}
