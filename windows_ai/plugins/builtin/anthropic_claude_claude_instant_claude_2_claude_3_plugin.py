"""
Anthropic Claude Plugin - Production Grade
Full integration with Claude 3 Opus, Sonnet, Haiku, Claude 2, Claude Instant
"""
from typing import Dict, Any, List, Optional, AsyncIterator
import os
import logging
import json
from datetime import datetime

try:
    from anthropic import AsyncAnthropic, HUMAN_PROMPT, AI_PROMPT
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

logger = logging.getLogger(__name__)

class Plugin:
    """
    Production-grade Anthropic Claude Plugin

    Supports:
    - Claude 3 Opus, Sonnet, Haiku
    - Claude 2.1, Claude 2.0
    - Claude Instant
    - Vision support (Claude 3 models)
    - Streaming responses
    - System prompts (Constitutional AI)
    - Token counting
    - Cost tracking
    - Rate limiting handling
    """

    def __init__(self):
        self.name = "Anthropic Claude"
        self.version = "2.0.0"
        self.description = "Production Anthropic Claude integration with Claude 3 (Opus, Sonnet, Haiku), Claude 2, Claude Instant"

        # Configuration
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.timeout = int(os.getenv("ANTHROPIC_TIMEOUT", "120"))
        self.max_retries = int(os.getenv("ANTHROPIC_MAX_RETRIES", "3"))

        # Initialize client if available
        self.client = None
        if ANTHROPIC_AVAILABLE and self.api_key:
            self.client = AsyncAnthropic(
                api_key=self.api_key,
                timeout=self.timeout,
                max_retries=self.max_retries
            )

        # Model pricing (per 1M tokens) - as of 2025
        self.pricing = {
            "claude-3-opus-20240229": {"input": 15.00, "output": 75.00},
            "claude-3-sonnet-20240229": {"input": 3.00, "output": 15.00},
            "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
            "claude-2.1": {"input": 8.00, "output": 24.00},
            "claude-2.0": {"input": 8.00, "output": 24.00},
            "claude-instant-1.2": {"input": 0.80, "output": 2.40},
        }

        # Model capabilities
        self.vision_models = [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307"
        ]

        # Usage tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute Anthropic Claude request

        Args:
            action (str): Action to perform
                - "chat": Chat completion
                - "vision": Analyze image with Claude 3
                - "models": List available models
                - "stats": Get usage statistics
            **kwargs: Additional parameters

        Returns:
            Dict with status and results
        """
        if not ANTHROPIC_AVAILABLE:
            return {
                "status": "error",
                "message": "Anthropic SDK not installed. Install with: pip install anthropic"
            }

        if not self.client:
            return {
                "status": "error",
                "message": "Anthropic API key not configured. Set ANTHROPIC_API_KEY environment variable."
            }

        try:
            action = kwargs.get("action", "chat")

            # Route to appropriate handler
            if action == "chat":
                return await self._chat(**kwargs)
            elif action == "vision":
                return await self._vision(**kwargs)
            elif action == "models":
                return await self._list_models(**kwargs)
            elif action == "stats":
                return self._get_stats()
            else:
                return {"status": "error", "message": f"Unknown action: {action}"}

        except Exception as e:
            logger.error(f"Anthropic plugin error: {str(e)}", exc_info=True)
            return {"status": "error", "message": str(e)}

    async def _chat(self, **kwargs) -> Dict[str, Any]:
        """
        Chat completion with Claude

        Args:
            messages (List[Dict]): Conversation messages
            model (str): Model to use (default: claude-3-sonnet-20240229)
            system (str): System prompt for Constitutional AI
            temperature (float): Sampling temperature 0-1
            max_tokens (int): Maximum tokens to generate
            stream (bool): Enable streaming responses
            top_p (float): Nucleus sampling parameter
            top_k (int): Top-k sampling parameter
            **kwargs: Additional Anthropic parameters
        """
        messages = kwargs.get("messages", [])
        model = kwargs.get("model", "claude-3-sonnet-20240229")
        system = kwargs.get("system", None)
        temperature = kwargs.get("temperature", 1.0)
        max_tokens = kwargs.get("max_tokens", 4096)
        stream = kwargs.get("stream", False)
        top_p = kwargs.get("top_p", None)
        top_k = kwargs.get("top_k", None)

        if not messages:
            return {"status": "error", "message": "No messages provided"}

        # Prepare request parameters
        request_params = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if system:
            request_params["system"] = system
        if top_p is not None:
            request_params["top_p"] = top_p
        if top_k is not None:
            request_params["top_k"] = top_k

        try:
            if stream:
                # Streaming response
                stream_response = await self.client.messages.create(
                    **request_params,
                    stream=True
                )

                collected_text = []
                async for event in stream_response:
                    if event.type == "content_block_delta":
                        if hasattr(event.delta, 'text'):
                            collected_text.append(event.delta.text)

                full_response = "".join(collected_text)

                return {
                    "status": "success",
                    "response": full_response,
                    "model": model,
                    "streaming": True
                }
            else:
                # Standard response
                response = await self.client.messages.create(**request_params)

                # Track usage
                if response.usage:
                    self.total_input_tokens += response.usage.input_tokens
                    self.total_output_tokens += response.usage.output_tokens

                    # Calculate cost (pricing is per 1M tokens)
                    if model in self.pricing:
                        input_cost = (response.usage.input_tokens / 1_000_000) * self.pricing[model]["input"]
                        output_cost = (response.usage.output_tokens / 1_000_000) * self.pricing[model]["output"]
                        self.total_cost += (input_cost + output_cost)

                # Extract text from content blocks
                response_text = ""
                for block in response.content:
                    if block.type == "text":
                        response_text += block.text

                return {
                    "status": "success",
                    "response": response_text,
                    "model": response.model,
                    "stop_reason": response.stop_reason,
                    "usage": {
                        "input_tokens": response.usage.input_tokens if response.usage else 0,
                        "output_tokens": response.usage.output_tokens if response.usage else 0,
                        "total_tokens": (response.usage.input_tokens + response.usage.output_tokens) if response.usage else 0,
                    }
                }

        except Exception as e:
            logger.error(f"Chat completion error: {str(e)}")
            raise

    async def _vision(self, **kwargs) -> Dict[str, Any]:
        """
        Analyze image with Claude 3 Vision

        Args:
            image_url (str): URL of image to analyze
            image_data (str): Base64 encoded image data
            image_media_type (str): Media type (image/jpeg, image/png, image/gif, image/webp)
            prompt (str): Question about the image
            model (str): Model to use (default: claude-3-sonnet-20240229)
            max_tokens (int): Maximum tokens
        """
        image_url = kwargs.get("image_url")
        image_data = kwargs.get("image_data")
        image_media_type = kwargs.get("image_media_type", "image/jpeg")
        prompt = kwargs.get("prompt", "What's in this image?")
        model = kwargs.get("model", "claude-3-sonnet-20240229")
        max_tokens = kwargs.get("max_tokens", 4096)

        # Check if model supports vision
        if model not in self.vision_models:
            return {
                "status": "error",
                "message": f"Model {model} does not support vision. Use Claude 3 models."
            }

        if not image_url and not image_data:
            return {"status": "error", "message": "No image provided (image_url or image_data required)"}

        # Prepare image content
        if image_url:
            image_content = {
                "type": "image",
                "source": {
                    "type": "url",
                    "url": image_url
                }
            }
        else:
            image_content = {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": image_media_type,
                    "data": image_data
                }
            }

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    image_content
                ]
            }
        ]

        try:
            response = await self.client.messages.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens
            )

            # Track usage
            if response.usage:
                self.total_input_tokens += response.usage.input_tokens
                self.total_output_tokens += response.usage.output_tokens

                if model in self.pricing:
                    input_cost = (response.usage.input_tokens / 1_000_000) * self.pricing[model]["input"]
                    output_cost = (response.usage.output_tokens / 1_000_000) * self.pricing[model]["output"]
                    self.total_cost += (input_cost + output_cost)

            # Extract text from content blocks
            analysis_text = ""
            for block in response.content:
                if block.type == "text":
                    analysis_text += block.text

            return {
                "status": "success",
                "analysis": analysis_text,
                "model": response.model,
                "usage": {
                    "input_tokens": response.usage.input_tokens if response.usage else 0,
                    "output_tokens": response.usage.output_tokens if response.usage else 0,
                    "total_tokens": (response.usage.input_tokens + response.usage.output_tokens) if response.usage else 0,
                }
            }

        except Exception as e:
            logger.error(f"Vision analysis error: {str(e)}")
            raise

    async def _list_models(self, **kwargs) -> Dict[str, Any]:
        """List available Claude models"""
        models = [
            {
                "id": "claude-3-opus-20240229",
                "name": "Claude 3 Opus",
                "description": "Most capable Claude model for complex tasks",
                "context_window": 200000,
                "supports_vision": True
            },
            {
                "id": "claude-3-sonnet-20240229",
                "name": "Claude 3 Sonnet",
                "description": "Balanced performance and speed",
                "context_window": 200000,
                "supports_vision": True
            },
            {
                "id": "claude-3-haiku-20240307",
                "name": "Claude 3 Haiku",
                "description": "Fastest Claude model for quick responses",
                "context_window": 200000,
                "supports_vision": True
            },
            {
                "id": "claude-2.1",
                "name": "Claude 2.1",
                "description": "Previous generation Claude with improved accuracy",
                "context_window": 200000,
                "supports_vision": False
            },
            {
                "id": "claude-2.0",
                "name": "Claude 2.0",
                "description": "Previous generation Claude",
                "context_window": 100000,
                "supports_vision": False
            },
            {
                "id": "claude-instant-1.2",
                "name": "Claude Instant",
                "description": "Fast and affordable Claude model",
                "context_window": 100000,
                "supports_vision": False
            }
        ]

        return {
            "status": "success",
            "models": models,
            "count": len(models)
        }

    def _get_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return {
            "status": "success",
            "stats": {
                "total_input_tokens": self.total_input_tokens,
                "total_output_tokens": self.total_output_tokens,
                "total_tokens": self.total_input_tokens + self.total_output_tokens,
                "total_cost_usd": round(self.total_cost, 4),
                "timestamp": datetime.now().isoformat()
            }
        }
