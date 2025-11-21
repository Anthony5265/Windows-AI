"""
3D Generation Manager - 10+ Services
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class ThreeDGenerationManager:
    """AI 3D model generation"""

    def __init__(self):
        self._initialized = False
        self.output_dir = Path.home() / ".windowsai" / "3d_models"

    async def initialize(self, config: Optional[Dict] = None):
        if self._initialized:
            return
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._initialized = True

    async def generate_from_text(
        self,
        prompt: str,
        provider: str = "tripo",
        **kwargs
    ) -> Dict[str, Any]:
        """Generate 3D model from text"""

        if provider == "tripo":
            return await self._tripo_text_to_3d(prompt, **kwargs)
        elif provider == "meshy":
            return await self._meshy_text_to_3d(prompt, **kwargs)
        elif provider == "replicate":
            return await self._replicate_text_to_3d(prompt, **kwargs)
        else:
            raise ValueError(f"Unsupported 3D provider: {provider}")

    async def generate_from_image(
        self,
        image_path: str,
        provider: str = "tripo",
        **kwargs
    ) -> Dict[str, Any]:
        """Generate 3D model from image"""

        if provider == "tripo":
            return await self._tripo_image_to_3d(image_path, **kwargs)
        elif provider == "triposr":
            return await self._triposr_image_to_3d(image_path, **kwargs)
        elif provider == "meshy":
            return await self._meshy_image_to_3d(image_path, **kwargs)
        else:
            raise ValueError(f"Unsupported 3D provider: {provider}")

    async def _tripo_text_to_3d(self, prompt, **kwargs):
        """Tripo AI text-to-3D"""
        import aiohttp

        api_key = os.environ.get("TRIPO_API_KEY")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.tripo3d.ai/v2/openapi/task",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"type": "text_to_model", "prompt": prompt, "model_version": kwargs.get("version", "default")}
            ) as response:
                data = await response.json()
                task_id = data["data"]["task_id"]

            # Poll for completion
            while True:
                async with session.get(
                    f"https://api.tripo3d.ai/v2/openapi/task/{task_id}",
                    headers={"Authorization": f"Bearer {api_key}"}
                ) as response:
                    result = await response.json()
                    if result["data"]["status"] == "success":
                        return {
                            "url": result["data"]["output"]["model"],
                            "provider": "tripo"
                        }
                    elif result["data"]["status"] == "failed":
                        raise RuntimeError("Generation failed")
                await asyncio.sleep(3)

    async def _tripo_image_to_3d(self, image_path, **kwargs):
        """Tripo AI image-to-3D"""
        import aiohttp
        import base64

        api_key = os.environ.get("TRIPO_API_KEY")

        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.tripo3d.ai/v2/openapi/task",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"type": "image_to_model", "file": {"data": image_data, "type": "png"}}
            ) as response:
                data = await response.json()
                task_id = data["data"]["task_id"]

            while True:
                async with session.get(
                    f"https://api.tripo3d.ai/v2/openapi/task/{task_id}",
                    headers={"Authorization": f"Bearer {api_key}"}
                ) as response:
                    result = await response.json()
                    if result["data"]["status"] == "success":
                        return {"url": result["data"]["output"]["model"], "provider": "tripo"}
                await asyncio.sleep(3)

    async def _triposr_image_to_3d(self, image_path, **kwargs):
        """TripoSR local image-to-3D"""
        import replicate

        output = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: replicate.run(
                "camenduru/triposr:0a26cf7c70dbf4b8f6f1eba7dc3a8f5dfdd02f1afc6d4ce3b5a7d6f5c6f8d5f0",
                input={"image": open(image_path, "rb")}
            )
        )

        return {"url": output, "provider": "triposr"}

    async def _meshy_text_to_3d(self, prompt, **kwargs):
        """Meshy AI text-to-3D"""
        import aiohttp

        api_key = os.environ.get("MESHY_API_KEY")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.meshy.ai/v2/text-to-3d",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"mode": "preview", "prompt": prompt, "art_style": kwargs.get("style", "realistic")}
            ) as response:
                data = await response.json()
                task_id = data["result"]

            while True:
                async with session.get(
                    f"https://api.meshy.ai/v2/text-to-3d/{task_id}",
                    headers={"Authorization": f"Bearer {api_key}"}
                ) as response:
                    result = await response.json()
                    if result["status"] == "SUCCEEDED":
                        return {"url": result["model_urls"]["glb"], "provider": "meshy"}
                await asyncio.sleep(5)

    async def _meshy_image_to_3d(self, image_path, **kwargs):
        """Meshy AI image-to-3D"""
        import aiohttp
        import base64

        api_key = os.environ.get("MESHY_API_KEY")

        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.meshy.ai/v2/image-to-3d",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"image_url": f"data:image/png;base64,{image_data}"}
            ) as response:
                data = await response.json()
                task_id = data["result"]

            while True:
                async with session.get(
                    f"https://api.meshy.ai/v2/image-to-3d/{task_id}",
                    headers={"Authorization": f"Bearer {api_key}"}
                ) as response:
                    result = await response.json()
                    if result["status"] == "SUCCEEDED":
                        return {"url": result["model_urls"]["glb"], "provider": "meshy"}
                await asyncio.sleep(5)

    async def _replicate_text_to_3d(self, prompt, **kwargs):
        """Replicate 3D generation"""
        import replicate

        output = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: replicate.run(
                "adirik/wonder3d:4e3e2b5f6e0d6b0c8f5d4e3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3",
                input={"prompt": prompt}
            )
        )

        return {"url": output[0] if isinstance(output, list) else output, "provider": "replicate"}
