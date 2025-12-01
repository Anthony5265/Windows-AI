"""
Anyscale Endpoints Plugin - Production Grade
Scalable inference for Llama, Mistral, and other open-source models
"""
from typing import Dict, Any, List, Optional
import httpx
import logging
import os

logger = logging.getLogger(__name__)


class AnyscalePlugin:
    """Production Anyscale Endpoints integration"""

    def __init__(self):
        self.api_key = os.getenv("ANYSCALE_API_KEY", "")
        self.base_url = "https://api.endpoints.anyscale.com/v1"

        # Popular models on Anyscale
        self.available_models = [
            "meta-llama/Meta-Llama-3.1-70B-Instruct",
            "meta-llama/Meta-Llama-3.1-8B-Instruct",
            "meta-llama/Llama-3-70b-chat-hf",
            "meta-llama/Llama-3-8b-chat-hf",
            "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "mistralai/Mistral-7B-Instruct-v0.1",
            "codellama/CodeLlama-70b-Instruct-hf",
            "google/gemma-7b-it"
        ]

        self.total_requests = 0
        self.total_tokens = 0

    async def chat(self, **kwargs) -> Dict[str, Any]:
        """
        Chat completion using Anyscale Endpoints

        Supported parameters:
            messages: List of message dicts
            model: Model to use
            max_tokens: Maximum tokens
            temperature: Sampling temperature
            top_p: Top-p sampling
            frequency_penalty: Frequency penalty
            presence_penalty: Presence penalty
            stream: Enable streaming

        Returns:
            Dict with chat response
        """
        if not self.api_key:
            return {
                "status": "error",
                "message": "ANYSCALE_API_KEY not configured"
            }

        messages = kwargs.get("messages", [])
        model = kwargs.get("model", "meta-llama/Meta-Llama-3.1-70B-Instruct")
        max_tokens = kwargs.get("max_tokens", 512)
        temperature = kwargs.get("temperature", 0.7)
        top_p = kwargs.get("top_p", 1.0)
        frequency_penalty = kwargs.get("frequency_penalty", 0.0)
        presence_penalty = kwargs.get("presence_penalty", 0.0)
        stream = kwargs.get("stream", False)

        if not messages:
            return {"status": "error", "message": "Messages are required"}

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        "top_p": top_p,
                        "frequency_penalty": frequency_penalty,
                        "presence_penalty": presence_penalty,
                        "stream": stream
                    }
                )

                if response.status_code != 200:
                    return {
                        "status": "error",
                        "message": f"API error: {response.status_code}",
                        "details": response.text
                    }

                result = response.json()
                self.total_requests += 1

                if "usage" in result:
                    self.total_tokens += result["usage"].get("total_tokens", 0)

                return {
                    "status": "success",
                    "message": result["choices"][0]["message"],
                    "model": model,
                    "usage": result.get("usage", {}),
                    "finish_reason": result["choices"][0].get("finish_reason")
                }

        except Exception as e:
            logger.error(f"Anyscale chat error: {e}")
            return {"status": "error", "message": str(e)}

    async def complete(self, **kwargs) -> Dict[str, Any]:
        """
        Text completion using Anyscale Endpoints

        Supported parameters:
            prompt: Text prompt
            model: Model to use
            max_tokens: Maximum tokens
            temperature: Sampling temperature
            top_p: Top-p sampling
            frequency_penalty: Frequency penalty
            presence_penalty: Presence penalty
            stop: Stop sequences

        Returns:
            Dict with completion
        """
        if not self.api_key:
            return {
                "status": "error",
                "message": "ANYSCALE_API_KEY not configured"
            }

        prompt = kwargs.get("prompt", "")
        model = kwargs.get("model", "meta-llama/Meta-Llama-3.1-70B-Instruct")
        max_tokens = kwargs.get("max_tokens", 512)
        temperature = kwargs.get("temperature", 0.7)
        top_p = kwargs.get("top_p", 1.0)
        frequency_penalty = kwargs.get("frequency_penalty", 0.0)
        presence_penalty = kwargs.get("presence_penalty", 0.0)
        stop = kwargs.get("stop", None)

        if not prompt:
            return {"status": "error", "message": "Prompt is required"}

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "prompt": prompt,
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        "top_p": top_p,
                        "frequency_penalty": frequency_penalty,
                        "presence_penalty": presence_penalty,
                        "stop": stop
                    }
                )

                if response.status_code != 200:
                    return {
                        "status": "error",
                        "message": f"API error: {response.status_code}",
                        "details": response.text
                    }

                result = response.json()
                self.total_requests += 1

                if "usage" in result:
                    self.total_tokens += result["usage"].get("total_tokens", 0)

                return {
                    "status": "success",
                    "text": result["choices"][0]["text"],
                    "model": model,
                    "usage": result.get("usage", {}),
                    "finish_reason": result["choices"][0].get("finish_reason")
                }

        except Exception as e:
            logger.error(f"Anyscale completion error: {e}")
            return {"status": "error", "message": str(e)}

    async def generate_embeddings(self, **kwargs) -> Dict[str, Any]:
        """
        Generate embeddings using Anyscale

        Supported parameters:
            input: Text or list of texts
            model: Embedding model

        Returns:
            Dict with embeddings
        """
        if not self.api_key:
            return {
                "status": "error",
                "message": "ANYSCALE_API_KEY not configured"
            }

        input_text = kwargs.get("input", "")
        model = kwargs.get("model", "thenlper/gte-large")

        if not input_text:
            return {"status": "error", "message": "Input text is required"}

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/embeddings",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "input": input_text,
                        "model": model
                    }
                )

                if response.status_code != 200:
                    return {
                        "status": "error",
                        "message": f"API error: {response.status_code}",
                        "details": response.text
                    }

                result = response.json()
                self.total_requests += 1

                return {
                    "status": "success",
                    "embeddings": [item["embedding"] for item in result["data"]],
                    "model": model,
                    "usage": result.get("usage", {})
                }

        except Exception as e:
            logger.error(f"Anyscale embeddings error: {e}")
            return {"status": "error", "message": str(e)}

    async def list_models(self) -> Dict[str, Any]:
        """List available models"""
        if not self.api_key:
            return {
                "status": "error",
                "message": "ANYSCALE_API_KEY not configured"
            }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers={
                        "Authorization": f"Bearer {self.api_key}"
                    }
                )

                if response.status_code != 200:
                    return {
                        "status": "error",
                        "message": f"API error: {response.status_code}"
                    }

                result = response.json()

                return {
                    "status": "success",
                    "models": [
                        {
                            "id": model["id"],
                            "created": model.get("created"),
                            "owned_by": model.get("owned_by")
                        }
                        for model in result.get("data", [])
                    ]
                }

        except Exception as e:
            logger.error(f"Anyscale list models error: {e}")
            return {"status": "error", "message": str(e)}

    def get_available_models(self) -> List[str]:
        """Get list of popular models"""
        return self.available_models

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return {
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens
        }


# Plugin metadata
PLUGIN_METADATA = {
    "name": "Anyscale Endpoints",
    "version": "1.0.0",
    "description": "Scalable inference for Llama, Mistral, and other open-source models",
    "author": "Windows-AI",
    "capabilities": [
        "chat",
        "text_completion",
        "embeddings",
        "code_generation"
    ],
    "models": [
        "meta-llama/Meta-Llama-3.1-70B-Instruct",
        "meta-llama/Meta-Llama-3.1-8B-Instruct",
        "meta-llama/Llama-3-70b-chat-hf",
        "meta-llama/Llama-3-8b-chat-hf",
        "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "mistralai/Mistral-7B-Instruct-v0.1",
        "codellama/CodeLlama-70b-Instruct-hf",
        "google/gemma-7b-it"
    ],
    "documentation": "https://docs.anyscale.com/"
}


def create_plugin():
    """Factory function to create plugin instance"""
    return AnyscalePlugin()
