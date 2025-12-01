"""
OpenAI GPT-3.5, GPT-4, GPT-4 Turbo, GPT-4V, DALL-E 3 Plugin
Production-grade OpenAI integration with full feature support
"""
from typing import Dict, Any, List, Optional, AsyncIterator
import os
import logging
import json
from datetime import datetime

try:
    import openai
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)

class Plugin:
    """
    Production-grade OpenAI Plugin

    Supports:
    - GPT-3.5-turbo, GPT-4, GPT-4-turbo, GPT-4V (Vision)
    - DALL-E 3 image generation
    - Text embeddings (ada-002)
    - Streaming responses
    - Function calling
    - Vision analysis
    - Token counting
    - Rate limiting handling
    - Cost tracking
    """

    def __init__(self):
        self.name = "OpenAI"
        self.version = "2.0.0"
        self.description = "Production OpenAI integration with GPT-3.5, GPT-4, GPT-4 Turbo, GPT-4V, DALL-E 3"

        # Configuration
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.organization = os.getenv("OPENAI_ORG_ID", None)
        self.timeout = int(os.getenv("OPENAI_TIMEOUT", "120"))
        self.max_retries = int(os.getenv("OPENAI_MAX_RETRIES", "3"))

        # Initialize client if available
        self.client = None
        if OPENAI_AVAILABLE and self.api_key:
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                organization=self.organization,
                timeout=self.timeout,
                max_retries=self.max_retries
            )

        # Model pricing (per 1K tokens) - as of 2025
        self.pricing = {
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
            "gpt-3.5-turbo-16k": {"input": 0.001, "output": 0.002},
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-32k": {"input": 0.06, "output": 0.12},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-4-turbo-preview": {"input": 0.01, "output": 0.03},
            "gpt-4-vision-preview": {"input": 0.01, "output": 0.03},
            "gpt-4o": {"input": 0.005, "output": 0.015},
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
            "text-embedding-ada-002": {"input": 0.0001, "output": 0},
            "dall-e-3": {"1024x1024": 0.04, "1024x1792": 0.08, "1792x1024": 0.08}
        }

        # Usage tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute OpenAI request

        Args:
            action (str): Action to perform
                - "chat": Chat completion
                - "vision": Analyze image with GPT-4V
                - "image": Generate image with DALL-E
                - "embed": Generate embeddings
                - "models": List available models
                - "stats": Get usage statistics
            **kwargs: Additional parameters

        Returns:
            Dict with status and results
        """
        if not OPENAI_AVAILABLE:
            return {
                "status": "error",
                "message": "OpenAI SDK not installed. Install with: pip install openai"
            }

        if not self.client:
            return {
                "status": "error",
                "message": "OpenAI API key not configured. Set OPENAI_API_KEY environment variable."
            }

        try:
            action = kwargs.get("action", "chat")

            # Route to appropriate handler
            if action == "chat":
                return await self._chat(**kwargs)
            elif action == "vision":
                return await self._vision(**kwargs)
            elif action == "image":
                return await self._generate_image(**kwargs)
            elif action == "embed":
                return await self._embed(**kwargs)
            elif action == "models":
                return await self._list_models(**kwargs)
            elif action == "stats":
                return self._get_stats()
            else:
                return {"status": "error", "message": f"Unknown action: {action}"}

        except openai.RateLimitError as e:
            logger.error(f"OpenAI rate limit: {str(e)}")
            return {
                "status": "error",
                "error_type": "rate_limit",
                "message": "Rate limit exceeded. Please try again later.",
                "details": str(e)
            }
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return {
                "status": "error",
                "error_type": "api_error",
                "message": str(e)
            }
        except Exception as e:
            logger.error(f"OpenAI plugin error: {str(e)}", exc_info=True)
            return {"status": "error", "message": str(e)}

    async def _chat(self, **kwargs) -> Dict[str, Any]:
        """
        Chat completion with OpenAI

        Args:
            messages (List[Dict]): Conversation messages
            model (str): Model to use (default: gpt-4-turbo)
            temperature (float): Sampling temperature 0-2
            max_tokens (int): Maximum tokens to generate
            stream (bool): Enable streaming responses
            functions (List[Dict]): Function definitions for function calling
            function_call (str|Dict): Function call behavior
            **kwargs: Additional OpenAI parameters
        """
        messages = kwargs.get("messages", [])
        model = kwargs.get("model", "gpt-4-turbo")
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", None)
        stream = kwargs.get("stream", False)
        functions = kwargs.get("functions", None)
        function_call = kwargs.get("function_call", None)

        if not messages:
            return {"status": "error", "message": "No messages provided"}

        # Prepare request parameters
        request_params = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }

        if max_tokens:
            request_params["max_tokens"] = max_tokens
        if functions:
            request_params["functions"] = functions
        if function_call:
            request_params["function_call"] = function_call

        try:
            if stream:
                # Streaming response
                stream_response = await self.client.chat.completions.create(
                    **request_params,
                    stream=True
                )

                collected_messages = []
                async for chunk in stream_response:
                    if chunk.choices[0].delta.content:
                        collected_messages.append(chunk.choices[0].delta.content)

                full_response = "".join(collected_messages)

                return {
                    "status": "success",
                    "response": full_response,
                    "model": model,
                    "streaming": True
                }
            else:
                # Standard response
                response = await self.client.chat.completions.create(**request_params)

                # Track usage
                if response.usage:
                    self.total_input_tokens += response.usage.prompt_tokens
                    self.total_output_tokens += response.usage.completion_tokens

                    # Calculate cost
                    if model in self.pricing:
                        input_cost = (response.usage.prompt_tokens / 1000) * self.pricing[model]["input"]
                        output_cost = (response.usage.completion_tokens / 1000) * self.pricing[model]["output"]
                        self.total_cost += (input_cost + output_cost)

                return {
                    "status": "success",
                    "response": response.choices[0].message.content,
                    "model": response.model,
                    "finish_reason": response.choices[0].finish_reason,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                        "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                        "total_tokens": response.usage.total_tokens if response.usage else 0,
                    },
                    "function_call": response.choices[0].message.function_call if hasattr(response.choices[0].message, 'function_call') else None
                }

        except Exception as e:
            logger.error(f"Chat completion error: {str(e)}")
            raise

    async def _vision(self, **kwargs) -> Dict[str, Any]:
        """
        Analyze image with GPT-4 Vision

        Args:
            image_url (str): URL of image to analyze
            image_data (str): Base64 encoded image data
            prompt (str): Question about the image
            model (str): Model to use (default: gpt-4-vision-preview)
            max_tokens (int): Maximum tokens
        """
        image_url = kwargs.get("image_url")
        image_data = kwargs.get("image_data")
        prompt = kwargs.get("prompt", "What's in this image?")
        model = kwargs.get("model", "gpt-4-vision-preview")
        max_tokens = kwargs.get("max_tokens", 300)

        if not image_url and not image_data:
            return {"status": "error", "message": "No image provided (image_url or image_data required)"}

        # Prepare image content
        image_content = {
            "type": "image_url",
            "image_url": {
                "url": image_url if image_url else f"data:image/jpeg;base64,{image_data}"
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
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens
            )

            # Track usage
            if response.usage:
                self.total_input_tokens += response.usage.prompt_tokens
                self.total_output_tokens += response.usage.completion_tokens

                if model in self.pricing:
                    input_cost = (response.usage.prompt_tokens / 1000) * self.pricing[model]["input"]
                    output_cost = (response.usage.completion_tokens / 1000) * self.pricing[model]["output"]
                    self.total_cost += (input_cost + output_cost)

            return {
                "status": "success",
                "analysis": response.choices[0].message.content,
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0,
                }
            }

        except Exception as e:
            logger.error(f"Vision analysis error: {str(e)}")
            raise

    async def _generate_image(self, **kwargs) -> Dict[str, Any]:
        """
        Generate image with DALL-E 3

        Args:
            prompt (str): Image description
            model (str): Model to use (default: dall-e-3)
            size (str): Image size (1024x1024, 1024x1792, 1792x1024)
            quality (str): Quality (standard, hd)
            style (str): Style (vivid, natural)
            n (int): Number of images (1 for dall-e-3)
        """
        prompt = kwargs.get("prompt", "")
        model = kwargs.get("model", "dall-e-3")
        size = kwargs.get("size", "1024x1024")
        quality = kwargs.get("quality", "standard")
        style = kwargs.get("style", "vivid")
        n = kwargs.get("n", 1)

        if not prompt:
            return {"status": "error", "message": "No prompt provided"}

        try:
            response = await self.client.images.generate(
                model=model,
                prompt=prompt,
                size=size,
                quality=quality,
                style=style,
                n=n
            )

            # Track cost
            if model == "dall-e-3" and size in self.pricing["dall-e-3"]:
                self.total_cost += self.pricing["dall-e-3"][size] * n

            images = []
            for image in response.data:
                images.append({
                    "url": image.url,
                    "revised_prompt": image.revised_prompt if hasattr(image, 'revised_prompt') else None
                })

            return {
                "status": "success",
                "images": images,
                "model": model,
                "size": size,
                "quality": quality,
                "style": style
            }

        except Exception as e:
            logger.error(f"Image generation error: {str(e)}")
            raise

    async def _embed(self, **kwargs) -> Dict[str, Any]:
        """
        Generate text embeddings

        Args:
            input (str|List[str]): Text(s) to embed
            model (str): Model to use (default: text-embedding-ada-002)
        """
        input_text = kwargs.get("input", "")
        model = kwargs.get("model", "text-embedding-ada-002")

        if not input_text:
            return {"status": "error", "message": "No input text provided"}

        try:
            response = await self.client.embeddings.create(
                model=model,
                input=input_text
            )

            # Track usage
            if response.usage:
                self.total_input_tokens += response.usage.prompt_tokens

                if model in self.pricing:
                    cost = (response.usage.prompt_tokens / 1000) * self.pricing[model]["input"]
                    self.total_cost += cost

            embeddings = [item.embedding for item in response.data]

            return {
                "status": "success",
                "embeddings": embeddings,
                "model": response.model,
                "dimensions": len(embeddings[0]) if embeddings else 0,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0,
                }
            }

        except Exception as e:
            logger.error(f"Embedding generation error: {str(e)}")
            raise

    async def _list_models(self, **kwargs) -> Dict[str, Any]:
        """List available OpenAI models"""
        try:
            models_response = await self.client.models.list()

            models = []
            for model in models_response.data:
                models.append({
                    "id": model.id,
                    "created": model.created,
                    "owned_by": model.owned_by
                })

            return {
                "status": "success",
                "models": models,
                "count": len(models)
            }

        except Exception as e:
            logger.error(f"List models error: {str(e)}")
            raise

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
