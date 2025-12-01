"""
Unified LLM Provider for Windows AI
Single interface to all LLM providers
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, AsyncGenerator, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class LLMProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    MISTRAL = "mistral"
    COHERE = "cohere"
    GROQ = "groq"
    TOGETHER = "together"
    REPLICATE = "replicate"
    OLLAMA = "ollama"
    AZURE = "azure"
    LITELLM = "litellm"

@dataclass
class LLMConfig:
    provider: LLMProvider
    model: str
    temperature: float = 0.7
    max_tokens: int = 4096
    api_key: Optional[str] = None
    base_url: Optional[str] = None

@dataclass
class Message:
    role: str  # system, user, assistant
    content: str

@dataclass
class LLMResponse:
    content: str
    model: str
    provider: str
    usage: Optional[Dict[str, int]] = None
    raw_response: Optional[Any] = None

class UnifiedLLMProvider:
    """Unified interface to all LLM providers"""

    def __init__(self):
        self.configs: Dict[str, LLMConfig] = {}
        self.default_provider: Optional[str] = None
        self._clients: Dict[str, Any] = {}
        self._initialized = False

    async def initialize(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the unified LLM provider"""
        if self._initialized:
            return

        # Register default configurations
        self._register_defaults()

        self._initialized = True
        logger.info("Unified LLM provider initialized")

    def _register_defaults(self):
        """Register default provider configurations"""
        # OpenAI
        self.register_config("gpt-4-turbo", LLMConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-4-turbo-preview"
        ))
        self.register_config("gpt-4o", LLMConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-4o"
        ))
        self.register_config("gpt-4o-mini", LLMConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-4o-mini"
        ))

        # Anthropic
        self.register_config("claude-3-opus", LLMConfig(
            provider=LLMProvider.ANTHROPIC,
            model="claude-3-opus-20240229"
        ))
        self.register_config("claude-3-sonnet", LLMConfig(
            provider=LLMProvider.ANTHROPIC,
            model="claude-3-sonnet-20240229"
        ))
        self.register_config("claude-3.5-sonnet", LLMConfig(
            provider=LLMProvider.ANTHROPIC,
            model="claude-3-5-sonnet-20241022"
        ))

        # Google
        self.register_config("gemini-pro", LLMConfig(
            provider=LLMProvider.GOOGLE,
            model="gemini-pro"
        ))
        self.register_config("gemini-1.5-pro", LLMConfig(
            provider=LLMProvider.GOOGLE,
            model="gemini-1.5-pro"
        ))

        # Mistral
        self.register_config("mistral-large", LLMConfig(
            provider=LLMProvider.MISTRAL,
            model="mistral-large-latest"
        ))

        # Groq (fast inference)
        self.register_config("groq-llama", LLMConfig(
            provider=LLMProvider.GROQ,
            model="llama-3.1-70b-versatile"
        ))
        self.register_config("groq-mixtral", LLMConfig(
            provider=LLMProvider.GROQ,
            model="mixtral-8x7b-32768"
        ))

        # Local (Ollama)
        self.register_config("local-llama", LLMConfig(
            provider=LLMProvider.OLLAMA,
            model="llama3.2",
            base_url="http://localhost:11434"
        ))

        self.default_provider = "gpt-4o-mini"

    def register_config(self, name: str, config: LLMConfig):
        """Register a provider configuration"""
        self.configs[name] = config

    def set_default(self, name: str):
        """Set the default provider"""
        if name not in self.configs:
            raise ValueError(f"Config '{name}' not found")
        self.default_provider = name

    async def _get_client(self, provider: LLMProvider) -> Any:
        """Get or create a client for a provider"""
        if provider.value in self._clients:
            return self._clients[provider.value]

        if provider == LLMProvider.OPENAI:
            from openai import AsyncOpenAI
            client = AsyncOpenAI()
        elif provider == LLMProvider.ANTHROPIC:
            from anthropic import AsyncAnthropic
            client = AsyncAnthropic()
        elif provider == LLMProvider.GOOGLE:
            import google.generativeai as genai
            client = genai
        elif provider == LLMProvider.MISTRAL:
            from mistralai.async_client import MistralAsyncClient
            client = MistralAsyncClient()
        elif provider == LLMProvider.GROQ:
            from groq import AsyncGroq
            client = AsyncGroq()
        elif provider == LLMProvider.LITELLM:
            import litellm
            client = litellm
        else:
            client = None

        self._clients[provider.value] = client
        return client

    async def complete(
        self,
        prompt: str,
        config_name: Optional[str] = None,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate a completion"""
        messages = []
        if system:
            messages.append(Message(role="system", content=system))
        messages.append(Message(role="user", content=prompt))

        return await self.chat(
            messages=messages,
            config_name=config_name,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

    async def chat(
        self,
        messages: List[Union[Message, Dict[str, str]]],
        config_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Union[LLMResponse, AsyncGenerator[str, None]]:
        """Send a chat request"""
        config_name = config_name or self.default_provider
        config = self.configs.get(config_name)

        if not config:
            raise ValueError(f"Config '{config_name}' not found")

        # Normalize messages
        normalized_messages = []
        for msg in messages:
            if isinstance(msg, Message):
                normalized_messages.append({"role": msg.role, "content": msg.content})
            else:
                normalized_messages.append(msg)

        temp = temperature if temperature is not None else config.temperature
        tokens = max_tokens if max_tokens is not None else config.max_tokens

        # Route to appropriate provider
        if config.provider == LLMProvider.OPENAI:
            return await self._openai_chat(config, normalized_messages, temp, tokens, stream)
        elif config.provider == LLMProvider.ANTHROPIC:
            return await self._anthropic_chat(config, normalized_messages, temp, tokens, stream)
        elif config.provider == LLMProvider.GOOGLE:
            return await self._google_chat(config, normalized_messages, temp, tokens, stream)
        elif config.provider == LLMProvider.GROQ:
            return await self._groq_chat(config, normalized_messages, temp, tokens, stream)
        elif config.provider == LLMProvider.OLLAMA:
            return await self._ollama_chat(config, normalized_messages, temp, tokens, stream)
        else:
            # Fallback to LiteLLM
            return await self._litellm_chat(config, normalized_messages, temp, tokens, stream)

    async def _openai_chat(self, config, messages, temperature, max_tokens, stream):
        client = await self._get_client(LLMProvider.OPENAI)

        response = await client.chat.completions.create(
            model=config.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream
        )

        if stream:
            async def generator():
                async for chunk in response:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            return generator()

        return LLMResponse(
            content=response.choices[0].message.content,
            model=config.model,
            provider="openai",
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens
            },
            raw_response=response
        )

    async def _anthropic_chat(self, config, messages, temperature, max_tokens, stream):
        client = await self._get_client(LLMProvider.ANTHROPIC)

        # Extract system message
        system = None
        filtered_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                filtered_messages.append(msg)

        response = await client.messages.create(
            model=config.model,
            messages=filtered_messages,
            system=system or "",
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream
        )

        if stream:
            async def generator():
                async for event in response:
                    if hasattr(event, 'delta') and hasattr(event.delta, 'text'):
                        yield event.delta.text
            return generator()

        return LLMResponse(
            content=response.content[0].text,
            model=config.model,
            provider="anthropic",
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens
            },
            raw_response=response
        )

    async def _google_chat(self, config, messages, temperature, max_tokens, stream):
        import google.generativeai as genai

        model = genai.GenerativeModel(config.model)

        # Convert messages format
        history = []
        for msg in messages[:-1]:
            role = "user" if msg["role"] == "user" else "model"
            history.append({"role": role, "parts": [msg["content"]]})

        chat = model.start_chat(history=history)
        response = await asyncio.get_event_loop().run_in_executor(
            None, lambda: chat.send_message(messages[-1]["content"])
        )

        return LLMResponse(
            content=response.text,
            model=config.model,
            provider="google",
            raw_response=response
        )

    async def _groq_chat(self, config, messages, temperature, max_tokens, stream):
        client = await self._get_client(LLMProvider.GROQ)

        response = await client.chat.completions.create(
            model=config.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream
        )

        if stream:
            async def generator():
                async for chunk in response:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            return generator()

        return LLMResponse(
            content=response.choices[0].message.content,
            model=config.model,
            provider="groq",
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens
            },
            raw_response=response
        )

    async def _ollama_chat(self, config, messages, temperature, max_tokens, stream):
        from .ollama_integration import OllamaManager

        ollama = OllamaManager(host=config.base_url or "http://localhost:11434")
        await ollama.initialize()

        response = await ollama.chat(
            model=config.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        return LLMResponse(
            content=response,
            model=config.model,
            provider="ollama"
        )

    async def _litellm_chat(self, config, messages, temperature, max_tokens, stream):
        import litellm

        response = await litellm.acompletion(
            model=f"{config.provider.value}/{config.model}",
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream
        )

        if stream:
            async def generator():
                async for chunk in response:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            return generator()

        return LLMResponse(
            content=response.choices[0].message.content,
            model=config.model,
            provider=config.provider.value,
            raw_response=response
        )

    def list_providers(self) -> List[str]:
        """List all available provider configurations"""
        return list(self.configs.keys())

    def get_config(self, name: str) -> Optional[LLMConfig]:
        """Get a provider configuration"""
        return self.configs.get(name)
