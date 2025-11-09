"""
Together AI Plugin - Production Grade
Access to 100+ open-source models including Llama, Mistral, Qwen, DeepSeek
"""
from typing import Dict, Any, List, Optional, AsyncIterator
import logging
import os

logger = logging.getLogger(__name__)

try:
    from together import AsyncTogether
    TOGETHER_AVAILABLE = True
except ImportError:
    TOGETHER_AVAILABLE = False


class TogetherAIPlugin:
    """Production Together AI integration"""

    def __init__(self):
        self.api_key = os.getenv("TOGETHER_API_KEY", "")
        self.client = None

        if TOGETHER_AVAILABLE and self.api_key:
            self.client = AsyncTogether(api_key=self.api_key)

        # Popular models
        self.popular_models = {
            "chat": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
            "code": "deepseek-ai/deepseek-coder-33b-instruct",
            "fast": "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "large": "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
            "vision": "meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo"
        }

        self.total_requests = 0
        self.total_tokens = 0

    async def chat(self, **kwargs) -> Dict[str, Any]:
        """
        Chat completion

        Supported parameters:
            messages: List of message dicts
            model: Model to use
            max_tokens: Maximum tokens
            temperature: Sampling temperature
            top_p: Top-p sampling
            top_k: Top-k sampling
            repetition_penalty: Repetition penalty
            stream: Enable streaming

        Returns:
            Dict with chat response
        """
        if not TOGETHER_AVAILABLE:
            return {
                "status": "error",
                "message": "together package not installed. Install with: pip install together"
            }

        if not self.api_key:
            return {
                "status": "error",
                "message": "TOGETHER_API_KEY not configured"
            }

        messages = kwargs.get("messages", [])
        model = kwargs.get("model", self.popular_models["chat"])
        max_tokens = kwargs.get("max_tokens", 512)
        temperature = kwargs.get("temperature", 0.7)
        top_p = kwargs.get("top_p", 0.7)
        top_k = kwargs.get("top_k", 50)
        repetition_penalty = kwargs.get("repetition_penalty", 1.0)
        stream = kwargs.get("stream", False)

        if not messages:
            return {"status": "error", "message": "Messages are required"}

        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                repetition_penalty=repetition_penalty,
                stream=stream
            )

            self.total_requests += 1

            if stream:
                return {
                    "status": "success",
                    "stream": response,
                    "model": model
                }

            if hasattr(response, 'usage'):
                self.total_tokens += response.usage.total_tokens

            return {
                "status": "success",
                "message": {
                    "role": response.choices[0].message.role,
                    "content": response.choices[0].message.content
                },
                "model": model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                } if hasattr(response, 'usage') else {},
                "finish_reason": response.choices[0].finish_reason
            }

        except Exception as e:
            logger.error(f"Together AI chat error: {e}")
            return {"status": "error", "message": str(e)}

    async def complete(self, **kwargs) -> Dict[str, Any]:
        """
        Text completion

        Supported parameters:
            prompt: Input prompt
            model: Model to use
            max_tokens: Maximum tokens
            temperature: Sampling temperature
            top_p: Top-p sampling
            top_k: Top-k sampling
            repetition_penalty: Repetition penalty
            stop: Stop sequences

        Returns:
            Dict with completion
        """
        if not TOGETHER_AVAILABLE:
            return {
                "status": "error",
                "message": "together package not installed. Install with: pip install together"
            }

        if not self.api_key:
            return {
                "status": "error",
                "message": "TOGETHER_API_KEY not configured"
            }

        prompt = kwargs.get("prompt", "")
        model = kwargs.get("model", self.popular_models["chat"])
        max_tokens = kwargs.get("max_tokens", 512)
        temperature = kwargs.get("temperature", 0.7)
        top_p = kwargs.get("top_p", 0.7)
        top_k = kwargs.get("top_k", 50)
        repetition_penalty = kwargs.get("repetition_penalty", 1.0)
        stop = kwargs.get("stop", None)

        if not prompt:
            return {"status": "error", "message": "Prompt is required"}

        try:
            response = await self.client.completions.create(
                model=model,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                repetition_penalty=repetition_penalty,
                stop=stop
            )

            self.total_requests += 1

            if hasattr(response, 'usage'):
                self.total_tokens += response.usage.total_tokens

            return {
                "status": "success",
                "text": response.choices[0].text,
                "model": model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                } if hasattr(response, 'usage') else {},
                "finish_reason": response.choices[0].finish_reason
            }

        except Exception as e:
            logger.error(f"Together AI completion error: {e}")
            return {"status": "error", "message": str(e)}

    async def generate_image(self, **kwargs) -> Dict[str, Any]:
        """
        Generate images using Together AI

        Supported parameters:
            prompt: Text prompt
            model: Model to use (default: stabilityai/stable-diffusion-xl-base-1.0)
            width: Image width
            height: Image height
            steps: Number of steps
            n: Number of images

        Returns:
            Dict with image data
        """
        if not TOGETHER_AVAILABLE:
            return {
                "status": "error",
                "message": "together package not installed. Install with: pip install together"
            }

        if not self.api_key:
            return {
                "status": "error",
                "message": "TOGETHER_API_KEY not configured"
            }

        prompt = kwargs.get("prompt", "")
        model = kwargs.get("model", "stabilityai/stable-diffusion-xl-base-1.0")
        width = kwargs.get("width", 1024)
        height = kwargs.get("height", 1024)
        steps = kwargs.get("steps", 20)
        n = kwargs.get("n", 1)

        if not prompt:
            return {"status": "error", "message": "Prompt is required"}

        try:
            response = await self.client.images.generate(
                prompt=prompt,
                model=model,
                width=width,
                height=height,
                steps=steps,
                n=n
            )

            self.total_requests += 1

            return {
                "status": "success",
                "images": [
                    {
                        "url": img.url,
                        "b64_json": getattr(img, 'b64_json', None)
                    }
                    for img in response.data
                ],
                "model": model
            }

        except Exception as e:
            logger.error(f"Together AI image generation error: {e}")
            return {"status": "error", "message": str(e)}

    async def generate_embeddings(self, **kwargs) -> Dict[str, Any]:
        """
        Generate embeddings

        Supported parameters:
            input: Text or list of texts
            model: Embedding model

        Returns:
            Dict with embeddings
        """
        if not TOGETHER_AVAILABLE:
            return {
                "status": "error",
                "message": "together package not installed. Install with: pip install together"
            }

        if not self.api_key:
            return {
                "status": "error",
                "message": "TOGETHER_API_KEY not configured"
            }

        input_text = kwargs.get("input", "")
        model = kwargs.get("model", "togethercomputer/m2-bert-80M-8k-retrieval")

        if not input_text:
            return {"status": "error", "message": "Input text is required"}

        try:
            response = await self.client.embeddings.create(
                input=input_text,
                model=model
            )

            self.total_requests += 1

            return {
                "status": "success",
                "embeddings": [emb.embedding for emb in response.data],
                "model": model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "total_tokens": response.usage.total_tokens
                } if hasattr(response, 'usage') else {}
            }

        except Exception as e:
            logger.error(f"Together AI embeddings error: {e}")
            return {"status": "error", "message": str(e)}

    async def list_models(self) -> Dict[str, Any]:
        """List available models"""
        if not TOGETHER_AVAILABLE:
            return {
                "status": "error",
                "message": "together package not installed"
            }

        if not self.api_key:
            return {
                "status": "error",
                "message": "TOGETHER_API_KEY not configured"
            }

        try:
            models = await self.client.models.list()

            return {
                "status": "success",
                "models": [
                    {
                        "id": model.id,
                        "display_name": model.display_name,
                        "context_length": model.context_length,
                        "type": model.type
                    }
                    for model in models
                ]
            }

        except Exception as e:
            logger.error(f"Together AI list models error: {e}")
            return {"status": "error", "message": str(e)}

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return {
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens
        }


# Plugin metadata
PLUGIN_METADATA = {
    "name": "Together AI",
    "version": "1.0.0",
    "description": "Access to 100+ open-source models including Llama, Mistral, Qwen, DeepSeek",
    "author": "Windows-AI",
    "capabilities": [
        "chat",
        "text_completion",
        "image_generation",
        "embeddings",
        "code_generation"
    ],
    "popular_models": {
        "chat": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
        "code": "deepseek-ai/deepseek-coder-33b-instruct",
        "fast": "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "large": "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
        "vision": "meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo"
    },
    "documentation": "https://docs.together.ai/"
}


def create_plugin():
    """Factory function to create plugin instance"""
    return TogetherAIPlugin()
