"""
Mistral AI Plugin - Production Grade
Full integration with Mistral 7B, Mixtral 8x7B, Mistral Medium/Large
"""
from typing import Dict, Any, List, Optional
import os
import logging
import json
from datetime import datetime

try:
    from mistralai.client import MistralClient
    from mistralai.models.chat_completion import ChatMessage
    MISTRAL_AVAILABLE = True
except ImportError:
    MISTRAL_AVAILABLE = False

logger = logging.getLogger(__name__)

class Plugin:
    """
    Production-grade Mistral AI Plugin

    Supports:
    - Mistral Large, Mistral Medium, Mistral Small
    - Mixtral 8x7B, Mixtral 8x22B
    - Mistral 7B
    - Streaming responses
    - Function calling
    - Token counting
    - Cost tracking
    """

    def __init__(self):
        self.name = "Mistral AI"
        self.version = "2.0.0"
        self.description = "Production Mistral AI integration with Mistral, Mixtral models"

        # Configuration
        self.api_key = os.getenv("MISTRAL_API_KEY", "")
        self.endpoint = os.getenv("MISTRAL_ENDPOINT", "https://api.mistral.ai")

        # Initialize client if available
        self.client = None
        if MISTRAL_AVAILABLE and self.api_key:
            self.client = MistralClient(
                api_key=self.api_key,
                endpoint=self.endpoint
            )

        # Model pricing (per 1M tokens) - as of 2025
        self.pricing = {
            "mistral-large-latest": {"input": 4.00, "output": 12.00},
            "mistral-medium-latest": {"input": 2.70, "output": 8.10},
            "mistral-small-latest": {"input": 1.00, "output": 3.00},
            "mixtral-8x7b-instruct": {"input": 0.70, "output": 0.70},
            "mixtral-8x22b-instruct": {"input": 2.00, "output": 6.00},
            "mistral-7b-instruct": {"input": 0.25, "output": 0.25},
            "mistral-embed": {"input": 0.10, "output": 0},
        }

        # Usage tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute Mistral AI request

        Args:
            action (str): Action to perform
                - "chat": Chat completion
                - "embed": Generate embeddings
                - "models": List available models
                - "stats": Get usage statistics
            **kwargs: Additional parameters

        Returns:
            Dict with status and results
        """
        if not MISTRAL_AVAILABLE:
            return {
                "status": "error",
                "message": "Mistral AI SDK not installed. Install with: pip install mistralai"
            }

        if not self.client:
            return {
                "status": "error",
                "message": "Mistral API key not configured. Set MISTRAL_API_KEY environment variable."
            }

        try:
            action = kwargs.get("action", "chat")

            # Route to appropriate handler
            if action == "chat":
                return await self._chat(**kwargs)
            elif action == "embed":
                return await self._embed(**kwargs)
            elif action == "models":
                return self._list_models()
            elif action == "stats":
                return self._get_stats()
            else:
                return {"status": "error", "message": f"Unknown action: {action}"}

        except Exception as e:
            logger.error(f"Mistral AI plugin error: {str(e)}", exc_info=True)
            return {"status": "error", "message": str(e)}

    async def _chat(self, **kwargs) -> Dict[str, Any]:
        """
        Chat completion with Mistral

        Args:
            messages (List[Dict]): Conversation messages
            model (str): Model to use (default: mistral-small-latest)
            temperature (float): Sampling temperature 0-1
            max_tokens (int): Maximum tokens to generate
            top_p (float): Nucleus sampling parameter
            stream (bool): Enable streaming responses
            safe_mode (bool): Enable content moderation
            tools (List[Dict]): Function calling tools
        """
        messages = kwargs.get("messages", [])
        model = kwargs.get("model", "mistral-small-latest")
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", None)
        top_p = kwargs.get("top_p", 1.0)
        stream = kwargs.get("stream", False)
        safe_mode = kwargs.get("safe_mode", False)
        tools = kwargs.get("tools", None)

        if not messages:
            return {"status": "error", "message": "No messages provided"}

        try:
            # Convert messages to Mistral format
            chat_messages = [
                ChatMessage(role=msg["role"], content=msg["content"])
                for msg in messages
            ]

            # Prepare request parameters
            request_params = {
                "model": model,
                "messages": chat_messages,
                "temperature": temperature,
                "top_p": top_p,
                "safe_mode": safe_mode
            }

            if max_tokens:
                request_params["max_tokens"] = max_tokens
            if tools:
                request_params["tools"] = tools

            if stream:
                # Streaming response
                stream_response = self.client.chat_stream(**request_params)

                collected_text = []
                for chunk in stream_response:
                    if chunk.choices[0].delta.content:
                        collected_text.append(chunk.choices[0].delta.content)

                full_response = "".join(collected_text)

                return {
                    "status": "success",
                    "response": full_response,
                    "model": model,
                    "streaming": True
                }
            else:
                # Standard response
                response = self.client.chat(**request_params)

                # Track usage
                if response.usage:
                    self.total_input_tokens += response.usage.prompt_tokens
                    self.total_output_tokens += response.usage.completion_tokens

                    # Calculate cost
                    if model in self.pricing:
                        input_cost = (response.usage.prompt_tokens / 1_000_000) * self.pricing[model]["input"]
                        output_cost = (response.usage.completion_tokens / 1_000_000) * self.pricing[model]["output"]
                        self.total_cost += (input_cost + output_cost)

                return {
                    "status": "success",
                    "response": response.choices[0].message.content,
                    "model": model,
                    "finish_reason": response.choices[0].finish_reason,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                        "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                        "total_tokens": response.usage.total_tokens if response.usage else 0,
                    },
                    "tool_calls": response.choices[0].message.tool_calls if hasattr(response.choices[0].message, 'tool_calls') else None
                }

        except Exception as e:
            logger.error(f"Chat completion error: {str(e)}")
            raise

    async def _embed(self, **kwargs) -> Dict[str, Any]:
        """
        Generate embeddings

        Args:
            input (str|List[str]): Text(s) to embed
            model (str): Embedding model
        """
        input_text = kwargs.get("input", "")
        model = kwargs.get("model", "mistral-embed")

        if not input_text:
            return {"status": "error", "message": "No input text provided"}

        try:
            # Convert to list if string
            texts = [input_text] if isinstance(input_text, str) else input_text

            response = self.client.embeddings(
                model=model,
                input=texts
            )

            # Track usage
            estimated_tokens = sum(len(text.split()) * 1.3 for text in texts)
            self.total_input_tokens += int(estimated_tokens)

            if model in self.pricing:
                cost = (estimated_tokens / 1_000_000) * self.pricing[model]["input"]
                self.total_cost += cost

            embeddings = [item.embedding for item in response.data]

            return {
                "status": "success",
                "embeddings": embeddings,
                "model": model,
                "dimensions": len(embeddings[0]) if embeddings else 0
            }

        except Exception as e:
            logger.error(f"Embedding generation error: {str(e)}")
            raise

    def _list_models(self) -> Dict[str, Any]:
        """List available Mistral models"""
        models = [
            {
                "id": "mistral-large-latest",
                "name": "Mistral Large",
                "description": "Most capable Mistral model for complex tasks",
                "context_window": 32000
            },
            {
                "id": "mistral-medium-latest",
                "name": "Mistral Medium",
                "description": "Balanced performance and cost",
                "context_window": 32000
            },
            {
                "id": "mistral-small-latest",
                "name": "Mistral Small",
                "description": "Fast and cost-effective model",
                "context_window": 32000
            },
            {
                "id": "mixtral-8x7b-instruct",
                "name": "Mixtral 8x7B",
                "description": "High-quality sparse mixture of experts model",
                "context_window": 32000
            },
            {
                "id": "mixtral-8x22b-instruct",
                "name": "Mixtral 8x22B",
                "description": "Larger sparse mixture of experts model",
                "context_window": 64000
            },
            {
                "id": "mistral-7b-instruct",
                "name": "Mistral 7B",
                "description": "Compact and efficient model",
                "context_window": 32000
            },
            {
                "id": "mistral-embed",
                "name": "Mistral Embed",
                "description": "Embedding model with 1024 dimensions",
                "type": "embedding"
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
