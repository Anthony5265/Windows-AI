"""
Runway ML Plugin - Production Grade
AI video generation with Gen-2, Gen-3, and image models
"""
from typing import Dict, Any, List, Optional
import httpx
import logging
import os
import asyncio
import time

logger = logging.getLogger(__name__)


class RunwayMLPlugin:
    """Production Runway ML integration"""

    def __init__(self):
        self.api_key = os.getenv("RUNWAY_API_KEY", "")
        self.base_url = "https://api.runwayml.com/v1"

        # Available models
        self.models = {
            "gen3a_turbo": "gen3a_turbo",
            "gen2": "gen2",
            "gen1": "gen1"
        }

        self.total_requests = 0
        self.total_videos = 0

    async def generate_video(self, **kwargs) -> Dict[str, Any]:
        """
        Generate video from text or image

        Supported parameters:
            prompt: Text prompt for video generation
            model: Model to use (gen3a_turbo, gen2)
            image_url: Optional image URL for image-to-video
            duration: Video duration in seconds (4, 5, or 10)
            width: Video width (default: 1280)
            height: Video height (default: 768)
            seed: Random seed for reproducibility
            watermark: Add watermark (default: False)

        Returns:
            Dict with task ID
        """
        if not self.api_key:
            return {
                "status": "error",
                "message": "RUNWAY_API_KEY not configured"
            }

        prompt = kwargs.get("prompt", "")
        model = kwargs.get("model", "gen3a_turbo")
        image_url = kwargs.get("image_url", None)
        duration = kwargs.get("duration", 5)
        width = kwargs.get("width", 1280)
        height = kwargs.get("height", 768)
        seed = kwargs.get("seed", None)
        watermark = kwargs.get("watermark", False)

        if not prompt and not image_url:
            return {"status": "error", "message": "Prompt or image URL is required"}

        try:
            payload = {
                "model": model,
                "promptText": prompt,
                "duration": duration,
                "width": width,
                "height": height,
                "watermark": watermark
            }

            if image_url:
                payload["promptImage"] = image_url

            if seed is not None:
                payload["seed"] = seed

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/generate",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "X-Runway-Version": "2024-09-13"
                    },
                    json=payload
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
                    "task_id": result.get("id"),
                    "prompt": prompt,
                    "model": model,
                    "message": "Video generation started"
                }

        except Exception as e:
            logger.error(f"Runway video generation error: {e}")
            return {"status": "error", "message": str(e)}

    async def get_task_status(self, **kwargs) -> Dict[str, Any]:
        """
        Get generation task status

        Supported parameters:
            task_id: Task ID from generate request

        Returns:
            Dict with status and video URL if completed
        """
        if not self.api_key:
            return {
                "status": "error",
                "message": "RUNWAY_API_KEY not configured"
            }

        task_id = kwargs.get("task_id", "")
        if not task_id:
            return {"status": "error", "message": "Task ID is required"}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/tasks/{task_id}",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "X-Runway-Version": "2024-09-13"
                    }
                )

                if response.status_code != 200:
                    return {
                        "status": "error",
                        "message": f"API error: {response.status_code}",
                        "details": response.text
                    }

                result = response.json()
                task_status = result.get("status", "unknown")

                if task_status == "SUCCEEDED":
                    self.total_videos += 1
                    return {
                        "status": "success",
                        "task_status": "completed",
                        "video_url": result.get("output", [None])[0] if result.get("output") else None,
                        "artifacts": result.get("output", []),
                        "progress": 100
                    }
                elif task_status in ["PENDING", "RUNNING"]:
                    return {
                        "status": "success",
                        "task_status": "processing",
                        "progress": result.get("progress", 0),
                        "message": "Video is being generated"
                    }
                elif task_status == "FAILED":
                    return {
                        "status": "error",
                        "task_status": "failed",
                        "message": result.get("failure", "Generation failed")
                    }
                else:
                    return {
                        "status": "success",
                        "task_status": task_status.lower(),
                        "result": result
                    }

        except Exception as e:
            logger.error(f"Runway get status error: {e}")
            return {"status": "error", "message": str(e)}

    async def upscale_video(self, **kwargs) -> Dict[str, Any]:
        """
        Upscale video resolution

        Supported parameters:
            video_url: URL of video to upscale
            target_resolution: Target resolution (e.g., "4k")

        Returns:
            Dict with upscale task ID
        """
        if not self.api_key:
            return {
                "status": "error",
                "message": "RUNWAY_API_KEY not configured"
            }

        video_url = kwargs.get("video_url", "")
        target_resolution = kwargs.get("target_resolution", "4k")

        if not video_url:
            return {"status": "error", "message": "Video URL is required"}

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/upscale",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "X-Runway-Version": "2024-09-13"
                    },
                    json={
                        "videoUrl": video_url,
                        "targetResolution": target_resolution
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
                    "task_id": result.get("id"),
                    "message": "Upscale started"
                }

        except Exception as e:
            logger.error(f"Runway upscale error: {e}")
            return {"status": "error", "message": str(e)}

    async def extend_video(self, **kwargs) -> Dict[str, Any]:
        """
        Extend video duration

        Supported parameters:
            video_url: URL of video to extend
            prompt: Text prompt for extension
            duration: Additional duration in seconds

        Returns:
            Dict with extend task ID
        """
        if not self.api_key:
            return {
                "status": "error",
                "message": "RUNWAY_API_KEY not configured"
            }

        video_url = kwargs.get("video_url", "")
        prompt = kwargs.get("prompt", "")
        duration = kwargs.get("duration", 5)

        if not video_url:
            return {"status": "error", "message": "Video URL is required"}

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/extend",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "X-Runway-Version": "2024-09-13"
                    },
                    json={
                        "videoUrl": video_url,
                        "promptText": prompt,
                        "duration": duration
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
                    "task_id": result.get("id"),
                    "message": "Video extension started"
                }

        except Exception as e:
            logger.error(f"Runway extend error: {e}")
            return {"status": "error", "message": str(e)}

    async def generate_and_wait(self, **kwargs) -> Dict[str, Any]:
        """
        Generate video and wait for completion

        Supported parameters:
            max_wait: Maximum wait time in seconds (default: 600)
            poll_interval: Poll interval in seconds (default: 10)
            ... (other generate parameters)

        Returns:
            Dict with video URL
        """
        max_wait = kwargs.get("max_wait", 600)
        poll_interval = kwargs.get("poll_interval", 10)

        # Start generation
        result = await self.generate_video(**kwargs)
        if result["status"] != "success":
            return result

        task_id = result["task_id"]
        start_time = time.time()

        # Poll for completion
        while time.time() - start_time < max_wait:
            await asyncio.sleep(poll_interval)

            status_result = await self.get_task_status(task_id=task_id)
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

    async def list_models(self) -> Dict[str, Any]:
        """List available models"""
        return {
            "status": "success",
            "models": list(self.models.keys()),
            "descriptions": {
                "gen3a_turbo": "Latest fast video generation model",
                "gen2": "Previous generation video model",
                "gen1": "Original video generation model"
            }
        }

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return {
            "total_requests": self.total_requests,
            "total_videos": self.total_videos
        }


# Plugin metadata
PLUGIN_METADATA = {
    "name": "Runway ML",
    "version": "1.0.0",
    "description": "AI video generation with Gen-2, Gen-3, and image models",
    "author": "Windows-AI",
    "capabilities": [
        "text_to_video",
        "image_to_video",
        "video_upscaling",
        "video_extension",
        "async_generation"
    ],
    "models": ["gen3a_turbo", "gen2", "gen1"],
    "documentation": "https://docs.runwayml.com/"
}


def create_plugin():
    """Factory function to create plugin instance"""
    return RunwayMLPlugin()
