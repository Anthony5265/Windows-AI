"""
Music Generation Manager - 10+ Services
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional
from windows_ai.config.unified_config import WindowsAIConfig

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class MusicGenerationManager:
    """AI music generation"""

    def __init__(self):
        self._config: Optional[WindowsAIConfig] = None
        self._initialized = False
        self.output_dir = Path.home() / ".windowsai" / "music"

    async def initialize(self, config: Optional[WindowsAIConfig] = None):
        if self._initialized:
            return
        
        self._config = config
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._initialized = True

    async def cleanup(self):
        """Cleanup resources before shutdown"""
        try:
            # Close any open connections
            if hasattr(self, '_clients'):
                for client in self._clients.values():
                    if hasattr(client, 'close'):
                        await client.close() if asyncio.iscoroutinefunction(client.close) else client.close()
            
            # Reset initialization flag
            self._initialized = False
            logger.info(f"{self.__class__.__name__} cleanup completed")
            
        except Exception as e:
            logger.error(f"{self.__class__.__name__} cleanup failed: {e}")

    async def generate(
        self,
        prompt: str,
        provider: str = "suno",
        duration: int = 30,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate music from text"""

        if provider == "suno":
            return await self._suno_generate(prompt, duration, **kwargs)
        elif provider == "udio":
            return await self._udio_generate(prompt, duration, **kwargs)
        elif provider == "stable_audio":
            return await self._stable_audio_generate(prompt, duration, **kwargs)
        elif provider == "musicgen":
            return await self._musicgen_generate(prompt, duration, **kwargs)
        elif provider == "replicate":
            return await self._replicate_generate(prompt, duration, **kwargs)
        else:
            raise ValueError(f"Unsupported music provider: {provider}")

    async def _suno_generate(self, prompt, duration, **kwargs):
        """Suno AI music generation"""
        import aiohttp

        api_key = os.environ.get("SUNO_API_KEY")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.suno.ai/v1/generate",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "prompt": prompt,
                    "make_instrumental": kwargs.get("instrumental", False),
                    "wait_audio": True
                }
            ) as response:
                data = await response.json()
                return {
                    "url": data.get("audio_url"),
                    "title": data.get("title"),
                    "provider": "suno"
                }

    async def _udio_generate(self, prompt, duration, **kwargs):
        """Udio music generation"""
        import aiohttp

        api_key = os.environ.get("UDIO_API_KEY")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.udio.com/v1/generate",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"prompt": prompt, "duration": duration}
            ) as response:
                data = await response.json()
                return {"url": data.get("audio_url"), "provider": "udio"}

    async def _stable_audio_generate(self, prompt, duration, **kwargs):
        """Stable Audio generation"""
        import aiohttp

        api_key = os.environ.get("STABILITY_API_KEY")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.stability.ai/v1/generation/stable-audio/text-to-audio",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"prompt": prompt, "duration": duration, "steps": kwargs.get("steps", 100)}
            ) as response:
                data = await response.json()
                return {"audio": data.get("audio"), "provider": "stable_audio"}

    async def _musicgen_generate(self, prompt, duration, **kwargs):
        """Meta MusicGen via Replicate"""
        import replicate

        output = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: replicate.run(
                "meta/musicgen:671ac645ce5e552cc63a54a2bbff63fcf798043ac92924f66e7e4e2f1051f2a7",
                input={
                    "prompt": prompt,
                    "duration": duration,
                    "model_version": kwargs.get("model", "stereo-large")
                }
            )
        )

        return {"url": output, "provider": "musicgen"}

    async def _replicate_generate(self, prompt, duration, **kwargs):
        """Replicate music models"""
        import replicate

        model = kwargs.get("model", "meta/musicgen:671ac645ce5e552cc63a54a2bbff63fcf798043ac92924f66e7e4e2f1051f2a7")

        output = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: replicate.run(model, input={"prompt": prompt, "duration": duration})
        )

        return {"url": output, "provider": "replicate"}

    async def generate_sound_effects(
        self,
        prompt: str,
        duration: int = 5,
        provider: str = "replicate"
    ) -> Dict[str, Any]:
        """Generate sound effects"""
        import replicate

        output = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: replicate.run(
                "haoheliu/audio-ldm-2:b6b10e3e09de60ef40b5bbde7c20fcc8b8f6e795f8ab96eae2c1b6cdfa96f75d",
                input={"text": prompt, "duration": duration}
            )
        )

        return {"url": output, "provider": "audioldm"}
