"""
Video Generation Manager - 15+ Services
AI video generation, editing, and processing
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)

class VideoProvider(Enum):
    RUNWAY = "runway"
    PIKA = "pika"
    LUMA = "luma"
    KLING = "kling"
    STABLE_VIDEO = "stable_video"
    REPLICATE = "replicate"
    FAL = "fal"
    HEYGEN = "heygen"
    SYNTHESIA = "synthesia"
    DID = "d_id"

class VideoGenerationManager:
    """Manages video generation across 15+ providers"""

    def __init__(self):
        self._initialized = False
        self.output_dir = Path.home() / ".windowsai" / "videos"

    async def initialize(self, config: Optional[Dict] = None):
        """Initialize video generation"""
        if self._initialized:
            return
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._initialized = True
        logger.info("Video Generation Manager initialized")

    async def generate(
        self,
        provider: VideoProvider,
        prompt: str,
        duration: int = 5,
        aspect_ratio: str = "16:9",
        **kwargs
    ) -> Dict[str, Any]:
        """Generate video from text prompt"""

        if provider == VideoProvider.RUNWAY:
            return await self._runway_generate(prompt, duration, **kwargs)
        elif provider == VideoProvider.LUMA:
            return await self._luma_generate(prompt, duration, aspect_ratio, **kwargs)
        elif provider == VideoProvider.STABLE_VIDEO:
            return await self._stable_video_generate(prompt, **kwargs)
        elif provider == VideoProvider.REPLICATE:
            return await self._replicate_generate(prompt, **kwargs)
        elif provider == VideoProvider.FAL:
            return await self._fal_generate(prompt, **kwargs)
        else:
            raise ValueError(f"Unsupported video provider: {provider}")

    async def _runway_generate(self, prompt, duration, **kwargs):
        """Runway Gen-3 video generation"""
        import aiohttp

        api_key = os.environ.get("RUNWAY_API_KEY")

        async with aiohttp.ClientSession() as session:
            # Create generation task
            async with session.post(
                "https://api.runwayml.com/v1/generations",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": kwargs.get("model", "gen3a_turbo"),
                    "prompt": prompt,
                    "duration": duration,
                    "watermark": kwargs.get("watermark", False)
                }
            ) as response:
                data = await response.json()
                task_id = data.get("id")

            # Poll for completion
            while True:
                async with session.get(
                    f"https://api.runwayml.com/v1/generations/{task_id}",
                    headers={"Authorization": f"Bearer {api_key}"}
                ) as response:
                    result = await response.json()

                    if result.get("status") == "SUCCEEDED":
                        return {
                            "url": result.get("output", [{}])[0].get("url"),
                            "provider": "runway",
                            "model": kwargs.get("model", "gen3a_turbo")
                        }
                    elif result.get("status") == "FAILED":
                        raise RuntimeError(f"Generation failed: {result.get('failure')}")

                await asyncio.sleep(2)

    async def _luma_generate(self, prompt, duration, aspect_ratio, **kwargs):
        """Luma Dream Machine video generation"""
        import aiohttp

        api_key = os.environ.get("LUMA_API_KEY")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.lumalabs.ai/dream-machine/v1/generations",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "prompt": prompt,
                    "aspect_ratio": aspect_ratio,
                    "loop": kwargs.get("loop", False)
                }
            ) as response:
                data = await response.json()
                generation_id = data.get("id")

            # Poll for completion
            while True:
                async with session.get(
                    f"https://api.lumalabs.ai/dream-machine/v1/generations/{generation_id}",
                    headers={"Authorization": f"Bearer {api_key}"}
                ) as response:
                    result = await response.json()

                    if result.get("state") == "completed":
                        return {
                            "url": result.get("assets", {}).get("video"),
                            "provider": "luma"
                        }
                    elif result.get("state") == "failed":
                        raise RuntimeError(f"Generation failed: {result.get('failure_reason')}")

                await asyncio.sleep(3)

    async def _stable_video_generate(self, prompt, **kwargs):
        """Stable Video Diffusion"""
        import replicate

        output = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: replicate.run(
                "stability-ai/stable-video-diffusion:3f0457e4619daac51203dedb472816fd4af51f3149fa7a9e0b5ffcf1b8172438",
                input={
                    "input_image": kwargs.get("image_url"),
                    "motion_bucket_id": kwargs.get("motion", 127),
                    "fps": kwargs.get("fps", 7),
                    "cond_aug": kwargs.get("cond_aug", 0.02)
                }
            )
        )

        return {
            "url": output,
            "provider": "stable_video"
        }

    async def _replicate_generate(self, prompt, **kwargs):
        """Replicate video generation"""
        import replicate

        model = kwargs.get("model", "minimax/video-01")

        output = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: replicate.run(
                model,
                input={
                    "prompt": prompt,
                    **{k: v for k, v in kwargs.items() if k != "model"}
                }
            )
        )

        return {
            "url": output if isinstance(output, str) else output[0] if output else None,
            "provider": "replicate",
            "model": model
        }

    async def _fal_generate(self, prompt, **kwargs):
        """Fal.ai video generation"""
        import fal_client

        model = kwargs.get("model", "fal-ai/kling-video/v1/standard/text-to-video")

        result = await fal_client.submit_async(
            model,
            arguments={
                "prompt": prompt,
                "duration": kwargs.get("duration", "5"),
                "aspect_ratio": kwargs.get("aspect_ratio", "16:9")
            }
        )

        return {
            "url": result.get("video", {}).get("url"),
            "provider": "fal",
            "model": model
        }

    # ==================== IMAGE TO VIDEO ====================

    async def image_to_video(
        self,
        provider: VideoProvider,
        image_path: str,
        prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate video from image"""

        if provider == VideoProvider.RUNWAY:
            return await self._runway_img2vid(image_path, prompt, **kwargs)
        elif provider == VideoProvider.LUMA:
            return await self._luma_img2vid(image_path, prompt, **kwargs)
        elif provider == VideoProvider.STABLE_VIDEO:
            return await self._stable_video_img2vid(image_path, **kwargs)
        else:
            raise ValueError(f"Image-to-video not supported for {provider}")

    async def _runway_img2vid(self, image_path, prompt, **kwargs):
        """Runway image-to-video"""
        import aiohttp
        import base64

        api_key = os.environ.get("RUNWAY_API_KEY")

        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.runwayml.com/v1/image_to_video",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": kwargs.get("model", "gen3a_turbo"),
                    "promptImage": f"data:image/png;base64,{image_data}",
                    "promptText": prompt or ""
                }
            ) as response:
                data = await response.json()
                task_id = data.get("id")

            # Poll for completion
            while True:
                async with session.get(
                    f"https://api.runwayml.com/v1/tasks/{task_id}",
                    headers={"Authorization": f"Bearer {api_key}"}
                ) as response:
                    result = await response.json()

                    if result.get("status") == "SUCCEEDED":
                        return {
                            "url": result.get("output", [{}])[0].get("url"),
                            "provider": "runway"
                        }
                    elif result.get("status") == "FAILED":
                        raise RuntimeError("Generation failed")

                await asyncio.sleep(2)

    async def _luma_img2vid(self, image_path, prompt, **kwargs):
        """Luma image-to-video"""
        import aiohttp
        import base64

        api_key = os.environ.get("LUMA_API_KEY")

        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.lumalabs.ai/dream-machine/v1/generations",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "prompt": prompt or "",
                    "keyframes": {
                        "frame0": {
                            "type": "image",
                            "url": f"data:image/png;base64,{image_data}"
                        }
                    }
                }
            ) as response:
                data = await response.json()
                generation_id = data.get("id")

            while True:
                async with session.get(
                    f"https://api.lumalabs.ai/dream-machine/v1/generations/{generation_id}",
                    headers={"Authorization": f"Bearer {api_key}"}
                ) as response:
                    result = await response.json()

                    if result.get("state") == "completed":
                        return {
                            "url": result.get("assets", {}).get("video"),
                            "provider": "luma"
                        }

                await asyncio.sleep(3)

    async def _stable_video_img2vid(self, image_path, **kwargs):
        """Stable Video Diffusion image-to-video"""
        import replicate

        output = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: replicate.run(
                "stability-ai/stable-video-diffusion:3f0457e4619daac51203dedb472816fd4af51f3149fa7a9e0b5ffcf1b8172438",
                input={
                    "input_image": open(image_path, "rb"),
                    "motion_bucket_id": kwargs.get("motion", 127),
                    "fps": kwargs.get("fps", 7)
                }
            )
        )

        return {
            "url": output,
            "provider": "stable_video"
        }

    # ==================== AI AVATARS ====================

    async def create_avatar_video(
        self,
        provider: VideoProvider,
        script: str,
        avatar_id: Optional[str] = None,
        voice_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create video with AI avatar"""

        if provider == VideoProvider.HEYGEN:
            return await self._heygen_avatar(script, avatar_id, voice_id, **kwargs)
        elif provider == VideoProvider.SYNTHESIA:
            return await self._synthesia_avatar(script, avatar_id, voice_id, **kwargs)
        elif provider == VideoProvider.DID:
            return await self._did_avatar(script, avatar_id, voice_id, **kwargs)
        else:
            raise ValueError(f"Avatar videos not supported for {provider}")

    async def _heygen_avatar(self, script, avatar_id, voice_id, **kwargs):
        """HeyGen avatar video"""
        import aiohttp

        api_key = os.environ.get("HEYGEN_API_KEY")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.heygen.com/v2/video/generate",
                headers={
                    "X-Api-Key": api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "video_inputs": [{
                        "character": {
                            "type": "avatar",
                            "avatar_id": avatar_id or "default"
                        },
                        "voice": {
                            "type": "text",
                            "input_text": script,
                            "voice_id": voice_id or "default"
                        }
                    }],
                    "dimension": kwargs.get("dimension", {"width": 1920, "height": 1080})
                }
            ) as response:
                data = await response.json()
                video_id = data.get("data", {}).get("video_id")

            # Poll for completion
            while True:
                async with session.get(
                    f"https://api.heygen.com/v1/video_status.get?video_id={video_id}",
                    headers={"X-Api-Key": api_key}
                ) as response:
                    result = await response.json()

                    if result.get("data", {}).get("status") == "completed":
                        return {
                            "url": result.get("data", {}).get("video_url"),
                            "provider": "heygen"
                        }

                await asyncio.sleep(5)

    async def _synthesia_avatar(self, script, avatar_id, voice_id, **kwargs):
        """Synthesia avatar video"""
        import aiohttp

        api_key = os.environ.get("SYNTHESIA_API_KEY")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.synthesia.io/v2/videos",
                headers={
                    "Authorization": api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "input": [{
                        "scriptText": script,
                        "avatar": avatar_id or "anna_costume1_cameraA",
                        "background": kwargs.get("background", "off_white")
                    }],
                    "aspectRatio": kwargs.get("aspect_ratio", "16:9")
                }
            ) as response:
                data = await response.json()
                video_id = data.get("id")

            while True:
                async with session.get(
                    f"https://api.synthesia.io/v2/videos/{video_id}",
                    headers={"Authorization": api_key}
                ) as response:
                    result = await response.json()

                    if result.get("status") == "complete":
                        return {
                            "url": result.get("download"),
                            "provider": "synthesia"
                        }

                await asyncio.sleep(10)

    async def _did_avatar(self, script, avatar_id, voice_id, **kwargs):
        """D-ID avatar video"""
        import aiohttp

        api_key = os.environ.get("DID_API_KEY")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.d-id.com/talks",
                headers={
                    "Authorization": f"Basic {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "source_url": avatar_id or "https://d-id-public-bucket.s3.amazonaws.com/or-roman.jpg",
                    "script": {
                        "type": "text",
                        "input": script,
                        "provider": {
                            "type": "microsoft",
                            "voice_id": voice_id or "en-US-JennyNeural"
                        }
                    }
                }
            ) as response:
                data = await response.json()
                talk_id = data.get("id")

            while True:
                async with session.get(
                    f"https://api.d-id.com/talks/{talk_id}",
                    headers={"Authorization": f"Basic {api_key}"}
                ) as response:
                    result = await response.json()

                    if result.get("status") == "done":
                        return {
                            "url": result.get("result_url"),
                            "provider": "d_id"
                        }

                await asyncio.sleep(3)

    def list_providers(self) -> List[str]:
        """List video providers"""
        return [p.value for p in VideoProvider]
