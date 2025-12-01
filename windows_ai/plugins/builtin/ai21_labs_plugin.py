"""
AI21 Labs Plugin - Production Grade
Full integration with Jurassic-2 and AI21 Studio APIs
"""
from typing import Dict, Any, List, Optional
import os
import logging
import json
from datetime import datetime

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

logger = logging.getLogger(__name__)

class Plugin:
    """
    Production-grade AI21 Labs Plugin

    Supports:
    - Jurassic-2 Ultra, Mid, Light
    - Chat completions
    - Text generation
    - Contextual answers
    - Paraphrase
    - Text improvements
    - Grammatical error correction
    - Text segmentation
    - Summarization
    """

    def __init__(self):
        self.name = "AI21 Labs"
        self.version = "2.0.0"
        self.description = "Production AI21 Labs integration with Jurassic-2"

        # Configuration
        self.api_key = os.getenv("AI21_API_KEY", "")
        self.base_url = "https://api.ai21.com/studio/v1"
        self.timeout = 60

        # Model configurations
        self.models = {
            "j2-ultra": "j2-ultra",
            "j2-mid": "j2-mid",
            "j2-light": "j2-light"
        }

        # Usage tracking
        self.total_requests = 0
        self.total_cost = 0.0

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute AI21 Labs request

        Args:
            action (str): Action to perform
                - "complete": Text completion
                - "chat": Chat completion
                - "paraphrase": Paraphrase text
                - "improve": Improve text
                - "gec": Grammatical error correction
                - "summarize": Summarize text
                - "models": List available models
                - "stats": Get usage statistics
            **kwargs: Additional parameters

        Returns:
            Dict with status and results
        """
        if not HTTPX_AVAILABLE:
            return {
                "status": "error",
                "message": "httpx not installed. Install with: pip install httpx"
            }

        if not self.api_key:
            return {
                "status": "error",
                "message": "AI21 API key not configured. Set AI21_API_KEY environment variable."
            }

        try:
            action = kwargs.get("action", "complete")

            if action == "complete":
                return await self._complete(**kwargs)
            elif action == "chat":
                return await self._chat(**kwargs)
            elif action == "paraphrase":
                return await self._paraphrase(**kwargs)
            elif action == "improve":
                return await self._improve(**kwargs)
            elif action == "gec":
                return await self._gec(**kwargs)
            elif action == "summarize":
                return await self._summarize(**kwargs)
            elif action == "models":
                return self._list_models()
            elif action == "stats":
                return self._get_stats()
            else:
                return {"status": "error", "message": f"Unknown action: {action}"}

        except Exception as e:
            logger.error(f"AI21 Labs plugin error: {str(e)}", exc_info=True)
            return {"status": "error", "message": str(e)}

    async def _complete(self, **kwargs) -> Dict[str, Any]:
        """Text completion with Jurassic-2"""
        prompt = kwargs.get("prompt", "")
        model = kwargs.get("model", "j2-mid")
        max_tokens = kwargs.get("max_tokens", 200)
        temperature = kwargs.get("temperature", 0.7)

        if not prompt:
            return {"status": "error", "message": "No prompt provided"}

        model_id = self.models.get(model, self.models["j2-mid"])

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/{model_id}/complete",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "prompt": prompt,
                        "maxTokens": max_tokens,
                        "temperature": temperature
                    }
                )

                if response.status_code == 200:
                    self.total_requests += 1
                    data = response.json()

                    return {
                        "status": "success",
                        "completions": [c["data"]["text"] for c in data.get("completions", [])],
                        "model": model_id
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"API error: {response.text}",
                        "status_code": response.status_code
                    }

        except Exception as e:
            logger.error(f"Completion error: {str(e)}")
            raise

    async def _chat(self, **kwargs) -> Dict[str, Any]:
        """Chat completion"""
        messages = kwargs.get("messages", [])
        model = kwargs.get("model", "j2-ultra")
        max_tokens = kwargs.get("max_tokens", 500)

        if not messages:
            return {"status": "error", "message": "No messages provided"}

        model_id = self.models.get(model, self.models["j2-ultra"])

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/{model_id}/chat",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "messages": messages,
                        "maxTokens": max_tokens
                    }
                )

                if response.status_code == 200:
                    self.total_requests += 1
                    data = response.json()

                    return {
                        "status": "success",
                        "response": data.get("outputs", [{}])[0].get("text", ""),
                        "model": model_id
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"API error: {response.text}",
                        "status_code": response.status_code
                    }

        except Exception as e:
            logger.error(f"Chat error: {str(e)}")
            raise

    async def _paraphrase(self, **kwargs) -> Dict[str, Any]:
        """Paraphrase text"""
        text = kwargs.get("text", "")

        if not text:
            return {"status": "error", "message": "No text provided"}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/paraphrase",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={"text": text}
                )

                if response.status_code == 200:
                    self.total_requests += 1
                    data = response.json()

                    return {
                        "status": "success",
                        "suggestions": [s["text"] for s in data.get("suggestions", [])]
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"API error: {response.text}",
                        "status_code": response.status_code
                    }

        except Exception as e:
            logger.error(f"Paraphrase error: {str(e)}")
            raise

    async def _improve(self, **kwargs) -> Dict[str, Any]:
        """Improve text quality"""
        text = kwargs.get("text", "")

        if not text:
            return {"status": "error", "message": "No text provided"}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/improvements",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={"text": text}
                )

                if response.status_code == 200:
                    self.total_requests += 1
                    data = response.json()

                    return {
                        "status": "success",
                        "improvements": data.get("improvements", [])
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"API error: {response.text}",
                        "status_code": response.status_code
                    }

        except Exception as e:
            logger.error(f"Improve error: {str(e)}")
            raise

    async def _gec(self, **kwargs) -> Dict[str, Any]:
        """Grammatical error correction"""
        text = kwargs.get("text", "")

        if not text:
            return {"status": "error", "message": "No text provided"}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/gec",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={"text": text}
                )

                if response.status_code == 200:
                    self.total_requests += 1
                    data = response.json()

                    return {
                        "status": "success",
                        "corrected_text": data.get("correctedText", text),
                        "corrections": data.get("corrections", [])
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"API error: {response.text}",
                        "status_code": response.status_code
                    }

        except Exception as e:
            logger.error(f"GEC error: {str(e)}")
            raise

    async def _summarize(self, **kwargs) -> Dict[str, Any]:
        """Summarize text"""
        text = kwargs.get("text", "")

        if not text:
            return {"status": "error", "message": "No text provided"}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/summarize",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={"text": text}
                )

                if response.status_code == 200:
                    self.total_requests += 1
                    data = response.json()

                    return {
                        "status": "success",
                        "summary": data.get("summary", "")
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"API error: {response.text}",
                        "status_code": response.status_code
                    }

        except Exception as e:
            logger.error(f"Summarize error: {str(e)}")
            raise

    def _list_models(self) -> Dict[str, Any]:
        """List available AI21 models"""
        models = [
            {
                "id": "j2-ultra",
                "name": "Jurassic-2 Ultra",
                "description": "Most capable model for complex tasks",
                "context_window": 8192
            },
            {
                "id": "j2-mid",
                "name": "Jurassic-2 Mid",
                "description": "Balanced performance and cost",
                "context_window": 8192
            },
            {
                "id": "j2-light",
                "name": "Jurassic-2 Light",
                "description": "Fast and cost-effective",
                "context_window": 8192
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
                "total_requests": self.total_requests,
                "total_cost_usd": round(self.total_cost, 4),
                "timestamp": datetime.now().isoformat()
            }
        }
