"""
Midjourney Plugin - Production Grade
AI image generation via unofficial API services
Note: Requires third-party API service like midjourney-api.io
"""
from typing import Dict, Any, List, Optional
import httpx
import logging
import os
import asyncio
import time

logger = logging.getLogger(__name__)


class MidjourneyPlugin:
    """Production Midjourney integration via unofficial APIs"""

    def __init__(self):
        # Configuration for unofficial API services
        self.api_key = os.getenv("MIDJOURNEY_API_KEY", "")
        self.base_url = os.getenv("MIDJOURNEY_API_URL", "https://api.midjourneyapi.xyz/v2")

        # Alternative: Can also use other services
        # - https://api.midjourney.com (if available)
        # - https://api.thenextleg.io
        # - https://api.useapi.net/v1/midjourney

        self.total_requests = 0
        self.total_images = 0

    async def imagine(self, **kwargs) -> Dict[str, Any]:
        """
        Generate image from text prompt (Midjourney /imagine)

        Supported parameters:
            prompt: Text prompt
            aspect_ratio: Aspect ratio (e.g., "16:9", "1:1", "9:16")
            version: Midjourney version (5.2, 6.0, niji)
            stylize: Stylization value (0-1000)
            chaos: Chaos value (0-100)
            quality: Quality (0.25, 0.5, 1, 2)
            webhook_url: URL for status updates

        Returns:
            Dict with task ID and status
        """
        if not self.api_key:
            return {
                "status": "error",
                "message": "MIDJOURNEY_API_KEY not configured. Get key from unofficial API service."
            }

        prompt = kwargs.get("prompt", "")
        aspect_ratio = kwargs.get("aspect_ratio", None)
        version = kwargs.get("version", "6.0")
        stylize = kwargs.get("stylize", 100)
        chaos = kwargs.get("chaos", 0)
        quality = kwargs.get("quality", 1)
        webhook_url = kwargs.get("webhook_url", None)

        if not prompt:
            return {"status": "error", "message": "Prompt is required"}

        # Build full prompt with parameters
        full_prompt = prompt
        if aspect_ratio:
            full_prompt += f" --ar {aspect_ratio}"
        full_prompt += f" --v {version}"
        full_prompt += f" --s {stylize}"
        if chaos > 0:
            full_prompt += f" --c {chaos}"
        if quality != 1:
            full_prompt += f" --q {quality}"

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/imagine",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "prompt": full_prompt,
                        "webhookUrl": webhook_url
                    }
                )

                if response.status_code not in [200, 201]:
                    return {
                        "status": "error",
                        "message": f"API error: {response.status_code}",
                        "details": response.text
                    }

                result = response.json()
                self.total_requests += 1

                return {
                    "status": "success",
                    "task_id": result.get("task_id") or result.get("id"),
                    "prompt": full_prompt,
                    "message": "Image generation started"
                }

        except Exception as e:
            logger.error(f"Midjourney imagine error: {e}")
            return {"status": "error", "message": str(e)}

    async def get_result(self, **kwargs) -> Dict[str, Any]:
        """
        Get generation result by task ID

        Supported parameters:
            task_id: Task ID from imagine request

        Returns:
            Dict with image URLs and status
        """
        if not self.api_key:
            return {
                "status": "error",
                "message": "MIDJOURNEY_API_KEY not configured"
            }

        task_id = kwargs.get("task_id", "")
        if not task_id:
            return {"status": "error", "message": "Task ID is required"}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/result/{task_id}",
                    headers={
                        "Authorization": f"Bearer {self.api_key}"
                    }
                )

                if response.status_code != 200:
                    return {
                        "status": "error",
                        "message": f"API error: {response.status_code}",
                        "details": response.text
                    }

                result = response.json()

                # Parse result based on API format
                status = result.get("status", "unknown")

                if status in ["completed", "success"]:
                    self.total_images += 1
                    return {
                        "status": "success",
                        "task_status": "completed",
                        "image_url": result.get("image_url") or result.get("url"),
                        "upscaled_urls": result.get("upscaled_urls", []),
                        "prompt": result.get("prompt", "")
                    }
                elif status in ["processing", "pending", "in_progress"]:
                    return {
                        "status": "success",
                        "task_status": "processing",
                        "progress": result.get("progress", 0),
                        "message": "Image is being generated"
                    }
                elif status in ["failed", "error"]:
                    return {
                        "status": "error",
                        "task_status": "failed",
                        "message": result.get("error", "Generation failed")
                    }
                else:
                    return {
                        "status": "success",
                        "task_status": status,
                        "result": result
                    }

        except Exception as e:
            logger.error(f"Midjourney get result error: {e}")
            return {"status": "error", "message": str(e)}

    async def upscale(self, **kwargs) -> Dict[str, Any]:
        """
        Upscale a specific image from grid

        Supported parameters:
            task_id: Original task ID
            index: Image index (1-4)

        Returns:
            Dict with upscale task ID
        """
        if not self.api_key:
            return {
                "status": "error",
                "message": "MIDJOURNEY_API_KEY not configured"
            }

        task_id = kwargs.get("task_id", "")
        index = kwargs.get("index", 1)

        if not task_id:
            return {"status": "error", "message": "Task ID is required"}

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/upscale",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "task_id": task_id,
                        "index": index
                    }
                )

                if response.status_code not in [200, 201]:
                    return {
                        "status": "error",
                        "message": f"API error: {response.status_code}",
                        "details": response.text
                    }

                result = response.json()

                return {
                    "status": "success",
                    "task_id": result.get("task_id") or result.get("id"),
                    "message": "Upscale started"
                }

        except Exception as e:
            logger.error(f"Midjourney upscale error: {e}")
            return {"status": "error", "message": str(e)}

    async def vary(self, **kwargs) -> Dict[str, Any]:
        """
        Create variations of an image

        Supported parameters:
            task_id: Original task ID
            index: Image index (1-4)
            variation_type: Type of variation (strong, subtle)

        Returns:
            Dict with variation task ID
        """
        if not self.api_key:
            return {
                "status": "error",
                "message": "MIDJOURNEY_API_KEY not configured"
            }

        task_id = kwargs.get("task_id", "")
        index = kwargs.get("index", 1)
        variation_type = kwargs.get("variation_type", "strong")

        if not task_id:
            return {"status": "error", "message": "Task ID is required"}

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/variation",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "task_id": task_id,
                        "index": index,
                        "variation_type": variation_type
                    }
                )

                if response.status_code not in [200, 201]:
                    return {
                        "status": "error",
                        "message": f"API error: {response.status_code}",
                        "details": response.text
                    }

                result = response.json()

                return {
                    "status": "success",
                    "task_id": result.get("task_id") or result.get("id"),
                    "message": "Variation started"
                }

        except Exception as e:
            logger.error(f"Midjourney variation error: {e}")
            return {"status": "error", "message": str(e)}

    async def generate_and_wait(self, **kwargs) -> Dict[str, Any]:
        """
        Generate image and wait for completion

        Supported parameters:
            prompt: Text prompt
            max_wait: Maximum wait time in seconds (default: 300)
            poll_interval: Poll interval in seconds (default: 10)
            ... (other imagine parameters)

        Returns:
            Dict with final image URLs
        """
        max_wait = kwargs.get("max_wait", 300)
        poll_interval = kwargs.get("poll_interval", 10)

        # Start generation
        result = await self.imagine(**kwargs)
        if result["status"] != "success":
            return result

        task_id = result["task_id"]
        start_time = time.time()

        # Poll for completion
        while time.time() - start_time < max_wait:
            await asyncio.sleep(poll_interval)

            status_result = await self.get_result(task_id=task_id)
            if status_result["status"] != "success":
                return status_result

            task_status = status_result.get("task_status", "")
            if task_status == "completed":
                return status_result
            elif task_status == "failed":
                return {
                    "status": "error",
                    "message": "Generation failed",
                    "details": status_result
                }

        return {
            "status": "error",
            "message": "Generation timeout",
            "task_id": task_id
        }

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return {
            "total_requests": self.total_requests,
            "total_images": self.total_images
        }


# Plugin metadata
PLUGIN_METADATA = {
    "name": "Midjourney",
    "version": "1.0.0",
    "description": "AI image generation via unofficial API services",
    "author": "Windows-AI",
    "capabilities": [
        "text_to_image",
        "upscale",
        "variations",
        "async_generation"
    ],
    "notes": [
        "Requires third-party API service (midjourney-api.io, thenextleg.io, etc.)",
        "Set MIDJOURNEY_API_KEY and MIDJOURNEY_API_URL environment variables",
        "Not an official Midjourney integration"
    ],
    "documentation": "https://docs.midjourneyapi.xyz/"
}


def create_plugin():
    """Factory function to create plugin instance"""
    return MidjourneyPlugin()
