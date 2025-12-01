"""
Perplexity AI Plugin - Production Grade
Online LLMs with internet search and up-to-date information
"""
from typing import Dict, Any, List, Optional
import httpx
import logging
import json
import os

logger = logging.getLogger(__name__)


class PerplexityAIPlugin:
    """Production Perplexity AI integration"""

    def __init__(self):
        self.api_key = os.getenv("PERPLEXITY_API_KEY", "")
        self.base_url = "https://api.perplexity.ai"
        self.available_models = [
            "llama-3.1-sonar-small-128k-online",
            "llama-3.1-sonar-large-128k-online",
            "llama-3.1-sonar-huge-128k-online",
            "llama-3.1-8b-instruct",
            "llama-3.1-70b-instruct",
            "llama-3.1-405b-instruct"
        ]
        self.total_requests = 0
        self.total_tokens = 0

    async def complete(self, **kwargs) -> Dict[str, Any]:
        """
        Generate text completion with Perplexity AI

        Supported parameters:
            prompt: Text prompt
            model: Model to use (default: llama-3.1-sonar-small-128k-online)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Top-p sampling
            stream: Enable streaming

        Returns:
            Dict with completion results
        """
        if not self.api_key:
            return {
                "status": "error",
                "message": "PERPLEXITY_API_KEY not configured"
            }

        prompt = kwargs.get("prompt", "")
        model = kwargs.get("model", "llama-3.1-sonar-small-128k-online")
        max_tokens = kwargs.get("max_tokens", 1024)
        temperature = kwargs.get("temperature", 0.7)
        top_p = kwargs.get("top_p", 1.0)
        stream = kwargs.get("stream", False)

        if not prompt:
            return {"status": "error", "message": "Prompt is required"}

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
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        "top_p": top_p,
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
                    "text": result["choices"][0]["message"]["content"],
                    "model": model,
                    "usage": result.get("usage", {}),
                    "citations": result.get("citations", [])
                }

        except Exception as e:
            logger.error(f"Perplexity completion error: {e}")
            return {"status": "error", "message": str(e)}

    async def chat(self, **kwargs) -> Dict[str, Any]:
        """
        Chat completion with conversation history

        Supported parameters:
            messages: List of message dicts with role and content
            model: Model to use
            max_tokens: Maximum tokens
            temperature: Sampling temperature
            top_p: Top-p sampling

        Returns:
            Dict with chat response
        """
        if not self.api_key:
            return {
                "status": "error",
                "message": "PERPLEXITY_API_KEY not configured"
            }

        messages = kwargs.get("messages", [])
        model = kwargs.get("model", "llama-3.1-sonar-small-128k-online")
        max_tokens = kwargs.get("max_tokens", 1024)
        temperature = kwargs.get("temperature", 0.7)
        top_p = kwargs.get("top_p", 1.0)

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
                        "top_p": top_p
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
                    "citations": result.get("citations", []),
                    "finish_reason": result["choices"][0].get("finish_reason")
                }

        except Exception as e:
            logger.error(f"Perplexity chat error: {e}")
            return {"status": "error", "message": str(e)}

    async def search(self, **kwargs) -> Dict[str, Any]:
        """
        Search-augmented generation

        Uses online models to search the internet and provide up-to-date answers

        Supported parameters:
            query: Search query
            model: Online model (default: llama-3.1-sonar-small-128k-online)
            max_tokens: Maximum tokens

        Returns:
            Dict with search results and answer
        """
        if not self.api_key:
            return {
                "status": "error",
                "message": "PERPLEXITY_API_KEY not configured"
            }

        query = kwargs.get("query", "")
        model = kwargs.get("model", "llama-3.1-sonar-small-128k-online")
        max_tokens = kwargs.get("max_tokens", 1024)

        if not query:
            return {"status": "error", "message": "Query is required"}

        # Ensure using an online model
        if "online" not in model:
            model = "llama-3.1-sonar-small-128k-online"

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
                        "messages": [
                            {
                                "role": "system",
                                "content": "Be precise and concise. Provide up-to-date information."
                            },
                            {
                                "role": "user",
                                "content": query
                            }
                        ],
                        "max_tokens": max_tokens,
                        "temperature": 0.2  # Lower temperature for factual queries
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
                    "answer": result["choices"][0]["message"]["content"],
                    "citations": result.get("citations", []),
                    "model": model,
                    "usage": result.get("usage", {})
                }

        except Exception as e:
            logger.error(f"Perplexity search error: {e}")
            return {"status": "error", "message": str(e)}

    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        return self.available_models

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return {
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens
        }


# Plugin metadata
PLUGIN_METADATA = {
    "name": "Perplexity AI",
    "version": "1.0.0",
    "description": "Online LLMs with internet search and up-to-date information",
    "author": "Windows-AI",
    "capabilities": [
        "text_completion",
        "chat",
        "search_augmented_generation",
        "online_information"
    ],
    "models": [
        "llama-3.1-sonar-small-128k-online",
        "llama-3.1-sonar-large-128k-online",
        "llama-3.1-sonar-huge-128k-online",
        "llama-3.1-8b-instruct",
        "llama-3.1-70b-instruct",
        "llama-3.1-405b-instruct"
    ],
    "documentation": "https://docs.perplexity.ai/"
}


def create_plugin():
    """Factory function to create plugin instance"""
    return PerplexityAIPlugin()
