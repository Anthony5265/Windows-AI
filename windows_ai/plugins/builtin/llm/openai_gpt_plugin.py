"""
OpenAI GPT Plugin
OpenAI GPT-3.5, GPT-4, GPT-4-Turbo integration
"""
from typing import Dict, Any, List
import os
import logging
import aiohttp
from windows_ai.plugins.base import Plugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)

class OpenAIPlugin(Plugin):
    """Plugin for OpenAI GPT integration"""
    
    def __init__(self):
        metadata = PluginMetadata(
            id="openai-gpt",
            name="OpenAI GPT",
            version="1.0.0",
            description="OpenAI GPT-3.5, GPT-4, GPT-4-Turbo integration",
            author="Windows AI",
            plugin_type=PluginType.INTEGRATION
        )
        super().__init__(metadata)
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.base_url = "https://api.openai.com/v1"
        self.timeout = 30
    
    async def initialize(self) -> None:
        """Initialize the plugin"""
        if not self.api_key:
            logger.warning("OpenAI API key not found. Plugin functionality will be limited.")

    async def shutdown(self) -> None:
        """Shutdown the plugin"""
        pass

    def get_supported_models(self) -> List[Dict[str, Any]]:
        """Get list of supported models"""
        return [
            {
                "id": "gpt-4-turbo-preview",
                "name": "GPT-4 Turbo",
                "provider": "OpenAI",
                "description": "Latest GPT-4 model with improved capabilities",
                "context_window": 128000
            },
            {
                "id": "gpt-4",
                "name": "GPT-4",
                "provider": "OpenAI",
                "description": "High-intelligence model",
                "context_window": 8192
            },
            {
                "id": "gpt-3.5-turbo",
                "name": "GPT-3.5 Turbo",
                "provider": "OpenAI",
                "description": "Fast and cost-effective model",
                "context_window": 16385
            }
        ]

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute OpenAI GPT request
        
        Args:
            action (str): Action to perform (generate, analyze, etc.)
            **kwargs: Additional parameters
        
        Returns:
            Dict with status and results
        """
        try:
            # Validate API key
            if not self.api_key:
                return {
                    "status": "error",
                    "message": f"{self.metadata.name} API key not configured. Set OPENAI_API_KEY environment variable."
                }
            
            action = kwargs.get("action", "generate")
            
            # Route to appropriate handler
            if action == "generate":
                return await self._generate(**kwargs)
            elif action == "analyze":
                return await self._analyze(**kwargs)
            elif action == "list_models":
                return {
                    "status": "success",
                    "models": self.get_supported_models()
                }
            else:
                return {"status": "error", "message": f"Unknown action: {action}"}
                
        except Exception as e:
            logger.error(f"{self.metadata.name} error: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _generate(self, **kwargs) -> Dict[str, Any]:
        """Generate content using OpenAI GPT"""
        prompt = kwargs.get("prompt", "")
        model = kwargs.get("model", "gpt-3.5-turbo")
        max_tokens = kwargs.get("max_tokens", 1000)
        temperature = kwargs.get("temperature", 0.7)
        
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Use chat completions for modern models
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            try:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data['choices'][0]['message']['content']
                        return {"status": "success", "result": content, "raw": data}
                    else:
                        error = await response.text()
                        return {"status": "error", "message": error, "status_code": response.status}
            except aiohttp.ClientError as e:
                return {"status": "error", "message": f"API request failed: {str(e)}"}
    
    async def _analyze(self, **kwargs) -> Dict[str, Any]:
        """Analyze content using OpenAI GPT"""
        text = kwargs.get("text", "")
        prompt = f"Analyze the following text and provide a summary and key points:\n\n{text}"
        return await self._generate(prompt=prompt, **kwargs)

# Instantiate the plugin
plugin = OpenAIPlugin()
