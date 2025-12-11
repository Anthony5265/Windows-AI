"""
Ollama Integration for Windows AI
Local LLM support via Ollama
"""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional, AsyncGenerator
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class OllamaModel:
    name: str
    size: str
    modified: str
    digest: str

class OllamaManager:
    """Manages Ollama local LLM integration"""

    def __init__(self, host: str = "http://localhost:11434"):
        self.host = host
        self.models: Dict[str, OllamaModel] = {}
        self.conversations: Dict[str, List[Dict]] = {}
        self._initialized = False

    async def initialize(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Ollama connection"""
        if self._initialized:
            return

        if config:
            self.host = config.get("host", self.host)

        try:
            # Check if Ollama is running
            await self.list_models()
            self._initialized = True
            logger.info(f"Ollama integration initialized at {self.host}")
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
            self._initialized = False

    async def _request(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict] = None,
    ) -> Any:
        """Make HTTP request to Ollama API (non-streaming)"""
        import aiohttp

        url = f"{self.host}/api/{endpoint}"

        async with aiohttp.ClientSession() as session:
            if method == "GET":
                async with session.get(url) as response:
                    return await response.json()
            elif method == "POST":
                async with session.post(url, json=data) as response:
                    return await response.json()
            elif method == "DELETE":
                async with session.delete(url, json=data) as response:
                    return await response.json()

    async def _request_stream(
        self,
        endpoint: str,
        data: Optional[Dict] = None,
    ):
        """Make streaming HTTP request to Ollama API"""
        import aiohttp

        url = f"{self.host}/api/{endpoint}"

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                async for line in response.content:
                    if line:
                        yield json.loads(line.decode())

    async def list_models(self) -> List[OllamaModel]:
        """List available Ollama models"""
        response = await self._request("tags")
        models = []

        for model_data in response.get("models", []):
            model = OllamaModel(
                name=model_data["name"],
                size=model_data.get("size", "unknown"),
                modified=model_data.get("modified_at", ""),
                digest=model_data.get("digest", "")
            )
            self.models[model.name] = model
            models.append(model)

        return models

    async def pull_model(self, model_name: str) -> AsyncGenerator[Dict, None]:
        """Pull/download a model"""
        async for chunk in self._request_stream("pull", {"name": model_name}):
            yield chunk

    async def delete_model(self, model_name: str) -> bool:
        """Delete a model"""
        try:
            await self._request("delete", "DELETE", {"name": model_name})
            if model_name in self.models:
                del self.models[model_name]
            return True
        except Exception as e:
            logger.error(f"Failed to delete model: {e}")
            return False

    async def generate(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """Generate text completion (non-streaming)"""
        data = {
            "model": model,
            "prompt": prompt,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            },
            "stream": False
        }

        if system:
            data["system"] = system

        response = await self._request("generate", "POST", data)
        return response.get("response", "")

    async def generate_stream(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[Dict, None]:
        """Generate text completion (streaming)"""
        data = {
            "model": model,
            "prompt": prompt,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            },
            "stream": True
        }

        if system:
            data["system"] = system

        async for chunk in self._request_stream("generate", data):
            yield chunk

    async def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """Chat with a model (non-streaming)"""
        data = {
            "model": model,
            "messages": messages,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            },
            "stream": False
        }

        response = await self._request("chat", "POST", data)
        return response.get("message", {}).get("content", "")

    async def chat_stream(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[Dict, None]:
        """Chat with a model (streaming)"""
        data = {
            "model": model,
            "messages": messages,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            },
            "stream": True
        }

        async for chunk in self._request_stream("chat", data):
            yield chunk

    async def chat_with_history(
        self,
        conversation_id: str,
        model: str,
        user_message: str,
        system: Optional[str] = None,
        temperature: float = 0.7
    ) -> str:
        """Chat with conversation history"""
        # Initialize conversation if needed
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
            if system:
                self.conversations[conversation_id].append({
                    "role": "system",
                    "content": system
                })

        # Add user message
        self.conversations[conversation_id].append({
            "role": "user",
            "content": user_message
        })

        # Get response
        response = await self.chat(
            model=model,
            messages=self.conversations[conversation_id],
            temperature=temperature
        )

        # Add assistant response to history
        self.conversations[conversation_id].append({
            "role": "assistant",
            "content": response
        })

        return response

    async def embeddings(self, model: str, text: str) -> List[float]:
        """Generate embeddings for text"""
        response = await self._request("embeddings", "POST", {
            "model": model,
            "prompt": text
        })
        return response.get("embedding", [])

    async def show_model_info(self, model_name: str) -> Dict[str, Any]:
        """Show model information"""
        response = await self._request("show", "POST", {"name": model_name})
        return response

    def clear_conversation(self, conversation_id: str):
        """Clear a conversation history"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]

    def get_available_models(self) -> List[str]:
        """Get list of available model names"""
        return list(self.models.keys())

    def get_conversations(self) -> List[str]:
        """Get list of active conversation IDs"""
        return list(self.conversations.keys())

    # Pre-configured model shortcuts
    RECOMMENDED_MODELS = {
        "llama3.2": "Latest Llama 3.2 - Great general purpose",
        "llama3.2:1b": "Llama 3.2 1B - Fast, lightweight",
        "llama3.2:3b": "Llama 3.2 3B - Balanced performance",
        "mistral": "Mistral 7B - Fast and capable",
        "mixtral": "Mixtral 8x7B - High quality MoE",
        "phi3": "Microsoft Phi-3 - Efficient",
        "gemma2": "Google Gemma 2 - Modern architecture",
        "qwen2.5": "Qwen 2.5 - Multilingual",
        "codellama": "Code Llama - For programming",
        "deepseek-coder": "DeepSeek Coder - Code specialist",
        "llava": "LLaVA - Vision + Language",
        "nomic-embed-text": "Embedding model",
    }

    async def ensure_model(self, model_name: str) -> bool:
        """Ensure a model is available, pull if needed"""
        models = await self.list_models()
        model_names = [m.name for m in models]

        if model_name not in model_names:
            logger.info(f"Pulling model: {model_name}")
            async for status in self.pull_model(model_name):
                if "status" in status:
                    logger.debug(status["status"])
            return True

        return True

    async def auto_setup(self, preferred_models: Optional[List[str]] = None):
        """Auto-setup with recommended models"""
        models_to_pull = preferred_models or ["llama3.2:3b", "nomic-embed-text"]

        for model in models_to_pull:
            try:
                await self.ensure_model(model)
                logger.info(f"Model ready: {model}")
            except Exception as e:
                logger.error(f"Failed to setup {model}: {e}")
