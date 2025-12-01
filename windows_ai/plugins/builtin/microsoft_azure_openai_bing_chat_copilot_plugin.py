"""
Microsoft Azure OpenAI Plugin - Production Grade
Full integration with Azure OpenAI Service including GPT-4, GPT-3.5, DALL-E
"""
from typing import Dict, Any, List, Optional
import os
import logging
import json
from datetime import datetime

try:
    from openai import AsyncAzureOpenAI
    AZURE_OPENAI_AVAILABLE = True
except ImportError:
    AZURE_OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)

class Plugin:
    """
    Production-grade Microsoft Azure OpenAI Plugin

    Supports:
    - GPT-4, GPT-4 Turbo, GPT-3.5 Turbo (via Azure)
    - DALL-E 3 image generation (via Azure)
    - Text embeddings (via Azure)
    - Streaming responses
    - Function calling
    - Token counting
    - Cost tracking
    - Azure-specific features (content filtering, etc.)
    """

    def __init__(self):
        self.name = "Microsoft Azure OpenAI"
        self.version = "2.0.0"
        self.description = "Production Microsoft Azure OpenAI integration with GPT-4, GPT-3.5, DALL-E 3"

        # Configuration - Azure OpenAI requires endpoint, key, and deployment names
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
        self.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        self.timeout = int(os.getenv("AZURE_OPENAI_TIMEOUT", "120"))
        self.max_retries = int(os.getenv("AZURE_OPENAI_MAX_RETRIES", "3"))

        # Deployment names (Azure uses deployments instead of model names)
        self.chat_deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4")
        self.embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002")
        self.dalle_deployment = os.getenv("AZURE_OPENAI_DALLE_DEPLOYMENT", "dall-e-3")

        # Initialize client if available
        self.client = None
        if AZURE_OPENAI_AVAILABLE and self.api_key and self.azure_endpoint:
            self.client = AsyncAzureOpenAI(
                api_key=self.api_key,
                azure_endpoint=self.azure_endpoint,
                api_version=self.api_version,
                timeout=self.timeout,
                max_retries=self.max_retries
            )

        # Model pricing (per 1K tokens) - Azure pricing as of 2025
        # Note: Azure pricing varies by region, these are approximate US East prices
        self.pricing = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-32k": {"input": 0.06, "output": 0.12},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-35-turbo": {"input": 0.0005, "output": 0.0015},
            "gpt-35-turbo-16k": {"input": 0.001, "output": 0.002},
            "text-embedding-ada-002": {"input": 0.0001, "output": 0},
            "dall-e-3": {"1024x1024": 0.04, "1024x1792": 0.08, "1792x1024": 0.08}
        }

        # Usage tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute Azure OpenAI request

        Args:
            action (str): Action to perform
                - "chat": Chat completion
                - "image": Generate image with DALL-E
                - "embed": Generate embeddings
                - "models": List available deployments
                - "stats": Get usage statistics
            **kwargs: Additional parameters

        Returns:
            Dict with status and results
        """
        if not AZURE_OPENAI_AVAILABLE:
            return {
                "status": "error",
                "message": "Azure OpenAI SDK not installed. Install with: pip install openai"
            }

        if not self.client:
            return {
                "status": "error",
                "message": "Azure OpenAI not configured. Set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT environment variables."
            }

        try:
            action = kwargs.get("action", "chat")

            # Route to appropriate handler
            if action == "chat":
                return await self._chat(**kwargs)
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

        except Exception as e:
            logger.error(f"Azure OpenAI plugin error: {str(e)}", exc_info=True)
            return {"status": "error", "message": str(e)}

    async def _chat(self, **kwargs) -> Dict[str, Any]:
        """
        Chat completion with Azure OpenAI

        Args:
            messages (List[Dict]): Conversation messages
            deployment (str): Azure deployment name (overrides default)
            temperature (float): Sampling temperature 0-2
            max_tokens (int): Maximum tokens to generate
            stream (bool): Enable streaming responses
            functions (List[Dict]): Function definitions for function calling
            function_call (str|Dict): Function call behavior
            **kwargs: Additional OpenAI parameters
        """
        messages = kwargs.get("messages", [])
        deployment = kwargs.get("deployment", self.chat_deployment)
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", None)
        stream = kwargs.get("stream", False)
        functions = kwargs.get("functions", None)
        function_call = kwargs.get("function_call", None)

        if not messages:
            return {"status": "error", "message": "No messages provided"}

        # Prepare request parameters
        request_params = {
            "model": deployment,  # In Azure, this is the deployment name
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
                    "deployment": deployment,
                    "streaming": True
                }
            else:
                # Standard response
                response = await self.client.chat.completions.create(**request_params)

                # Track usage
                if response.usage:
                    self.total_input_tokens += response.usage.prompt_tokens
                    self.total_output_tokens += response.usage.completion_tokens

                    # Determine model type for pricing (Azure deployments map to OpenAI models)
                    model_type = self._get_model_type(deployment)
                    if model_type in self.pricing:
                        input_cost = (response.usage.prompt_tokens / 1000) * self.pricing[model_type]["input"]
                        output_cost = (response.usage.completion_tokens / 1000) * self.pricing[model_type]["output"]
                        self.total_cost += (input_cost + output_cost)

                return {
                    "status": "success",
                    "response": response.choices[0].message.content,
                    "deployment": deployment,
                    "finish_reason": response.choices[0].finish_reason,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                        "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                        "total_tokens": response.usage.total_tokens if response.usage else 0,
                    },
                    "function_call": response.choices[0].message.function_call if hasattr(response.choices[0].message, 'function_call') else None,
                    "content_filter_results": response.choices[0].content_filter_results if hasattr(response.choices[0], 'content_filter_results') else None
                }

        except Exception as e:
            logger.error(f"Chat completion error: {str(e)}")
            raise

    async def _generate_image(self, **kwargs) -> Dict[str, Any]:
        """
        Generate image with DALL-E 3 on Azure

        Args:
            prompt (str): Image description
            deployment (str): Azure DALL-E deployment name
            size (str): Image size (1024x1024, 1024x1792, 1792x1024)
            quality (str): Quality (standard, hd)
            style (str): Style (vivid, natural)
            n (int): Number of images (1 for dall-e-3)
        """
        prompt = kwargs.get("prompt", "")
        deployment = kwargs.get("deployment", self.dalle_deployment)
        size = kwargs.get("size", "1024x1024")
        quality = kwargs.get("quality", "standard")
        style = kwargs.get("style", "vivid")
        n = kwargs.get("n", 1)

        if not prompt:
            return {"status": "error", "message": "No prompt provided"}

        try:
            response = await self.client.images.generate(
                model=deployment,
                prompt=prompt,
                size=size,
                quality=quality,
                style=style,
                n=n
            )

            # Track cost
            if size in self.pricing["dall-e-3"]:
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
                "deployment": deployment,
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
            deployment (str): Azure embedding deployment name
        """
        input_text = kwargs.get("input", "")
        deployment = kwargs.get("deployment", self.embedding_deployment)

        if not input_text:
            return {"status": "error", "message": "No input text provided"}

        try:
            response = await self.client.embeddings.create(
                model=deployment,
                input=input_text
            )

            # Track usage
            if response.usage:
                self.total_input_tokens += response.usage.prompt_tokens

                model_type = self._get_model_type(deployment)
                if model_type in self.pricing:
                    cost = (response.usage.prompt_tokens / 1000) * self.pricing[model_type]["input"]
                    self.total_cost += cost

            embeddings = [item.embedding for item in response.data]

            return {
                "status": "success",
                "embeddings": embeddings,
                "deployment": deployment,
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
        """List available Azure OpenAI deployments"""
        # Note: Azure doesn't have a public API to list deployments
        # Return configured deployments
        deployments = [
            {
                "name": self.chat_deployment,
                "type": "chat",
                "description": "Chat completion deployment"
            },
            {
                "name": self.embedding_deployment,
                "type": "embedding",
                "description": "Text embedding deployment"
            },
            {
                "name": self.dalle_deployment,
                "type": "image",
                "description": "DALL-E 3 image generation deployment"
            }
        ]

        return {
            "status": "success",
            "deployments": deployments,
            "endpoint": self.azure_endpoint,
            "api_version": self.api_version
        }

    def _get_model_type(self, deployment_name: str) -> str:
        """Map Azure deployment name to model type for pricing"""
        deployment_lower = deployment_name.lower()

        if "gpt-4-turbo" in deployment_lower or "gpt4-turbo" in deployment_lower:
            return "gpt-4-turbo"
        elif "gpt-4-32k" in deployment_lower or "gpt4-32k" in deployment_lower:
            return "gpt-4-32k"
        elif "gpt-4" in deployment_lower or "gpt4" in deployment_lower:
            return "gpt-4"
        elif "gpt-35-turbo-16k" in deployment_lower or "gpt35-turbo-16k" in deployment_lower:
            return "gpt-35-turbo-16k"
        elif "gpt-35" in deployment_lower or "gpt35" in deployment_lower:
            return "gpt-35-turbo"
        elif "embedding" in deployment_lower or "ada" in deployment_lower:
            return "text-embedding-ada-002"
        elif "dall-e" in deployment_lower or "dalle" in deployment_lower:
            return "dall-e-3"
        else:
            return "gpt-35-turbo"  # Default fallback

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
