"""
AudioCraft Plugin
Meta AudioCraft music and audio generation from text prompts via Replicate API
"""

from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType
from typing import Dict, Any, Optional, List
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    aiohttp = None
import os
import logging
import json
import asyncio

logger = logging.getLogger(__name__)


class Plugin(IntegrationPlugin):
    """
    AudioCraft plugin for AI-powered music and audio generation

    Capabilities:
    - Generate music from text descriptions using MusicGen
    - Generate sound effects and ambient audio (AudioGen)
    - Continue/extend existing music clips
    - List available AudioCraft models on Replicate

    Actions:
    - generate_music: Generate a music clip from a text prompt
    - generate_audio_sfx: Generate sound effects or ambient audio from a prompt
    - continue_music: Extend an existing audio clip given a prompt
    - get_models: List available AudioCraft models
    """

    # Replicate model versions (pinned for reproducibility; update when newer versions ship)
    MUSICGEN_MODEL = "meta/musicgen:671ac645ce5e552cc63a54a2bbff63fcf798043055d2dac5fc9e36a837eedcfb"
    AUDIOGEN_MODEL = "meta/audiogen:b3b2d13c45c6faf30c38acacd65a7c07d9ed58e8a58e2c96fd10e9aca3d47e6b"

    AVAILABLE_MODELS = {
        "musicgen-small": "Small MusicGen model – fast, lower quality",
        "musicgen-medium": "Medium MusicGen model – balanced quality/speed",
        "musicgen-large": "Large MusicGen model – highest quality",
        "audiogen-medium": "Medium AudioGen model – general audio/SFX",
    }

    def __init__(self):
        metadata = PluginMetadata(
            id="audiocraft",
            name="Meta AudioCraft",
            description="AI music and audio generation from text prompts using Meta AudioCraft via Replicate",
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["audio", "ai", "music-generation", "meta", "audiocraft"],
        )
        super().__init__(metadata)

        self.session = None
        self._api_key = None
        self._api_base = "https://api.replicate.com/v1"
        self._initialized = False
        self._poll_interval = 2  # seconds between prediction status polls

    async def initialize(self) -> bool:
        """Initialize the AudioCraft plugin"""
        if self._initialized:
            return True
        try:
            self._api_key = os.environ.get("REPLICATE_API_TOKEN")
            if AIOHTTP_AVAILABLE:
                timeout = aiohttp.ClientTimeout(total=300)
                self.session = aiohttp.ClientSession(timeout=timeout)
            else:
                self.session = None
            self._initialized = True
            if not self._api_key:
                logger.warning(
                    "REPLICATE_API_TOKEN not set. AudioCraft plugin running in offline simulation mode."
                )
            else:
                logger.info("Meta AudioCraft plugin initialized with Replicate API key")
            return True
        except Exception as e:
            logger.error(f"AudioCraft plugin initialization failed: {e}")
            return False

    async def connect(self, credentials: Optional[Dict[str, Any]] = None) -> bool:
        """Update credentials"""
        try:
            if credentials:
                self._api_key = credentials.get("api_key", self._api_key)
                self._api_base = credentials.get("api_base", self._api_base)
            return True
        except Exception as e:
            logger.error(f"AudioCraft connection failed: {e}")
            return False

    async def disconnect(self) -> bool:
        """Close HTTP session"""
        try:
            if self.session:
                await self.session.close()
                self.session = None
            return True
        except Exception as e:
            logger.error(f"AudioCraft disconnect failed: {e}")
            return False

    async def execute(self, action: str, params: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Dispatch to action handlers"""
        if not self._initialized:
            await self.initialize()
        try:
            if action == "generate_music":
                return await self._generate_music(params)
            elif action == "generate_audio_sfx":
                return await self._generate_audio_sfx(params)
            elif action == "continue_music":
                return await self._continue_music(params)
            elif action == "get_models":
                return await self._get_models(params)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "supported_actions": ["generate_music", "generate_audio_sfx", "continue_music", "get_models"],
                }
        except Exception as e:
            logger.error(f"AudioCraft execute failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    # ------------------------------------------------------------------
    # Action implementations
    # ------------------------------------------------------------------

    async def _generate_music(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a music clip from a text prompt.

        Parameters:
            prompt (str): Text description of the music to generate
            duration (int): Duration in seconds (1-30, default 8)
            model_version (str): MusicGen variant (small/medium/large, default medium)
            temperature (float): Sampling temperature (default 1.0)
            top_k (int): Top-k sampling parameter (default 250)
            top_p (float): Top-p nucleus sampling (default 0.0)
            classifier_free_guidance (int): CFG scale (default 3)
        """
        prompt = params.get("prompt")
        if not prompt:
            return {"success": False, "error": "prompt is required"}

        if not self._api_key:
            return {
                "success": True,
                "result": {
                    "audio_url": "https://example.com/simulated_music.wav",
                    "prompt": prompt,
                    "duration": params.get("duration", 8),
                    "model": "musicgen-medium",
                    "format": "wav",
                    "sample_rate": 32000,
                },
                "mode": "offline_simulation",
            }

        model_version = params.get("model_version", "medium")
        replicate_input = {
            "prompt": prompt,
            "duration": min(int(params.get("duration", 8)), 30),
            "model_version": model_version,
            "temperature": float(params.get("temperature", 1.0)),
            "top_k": int(params.get("top_k", 250)),
            "top_p": float(params.get("top_p", 0.0)),
            "classifier_free_guidance": int(params.get("classifier_free_guidance", 3)),
            "output_format": "wav",
        }

        return await self._run_replicate_prediction(self.MUSICGEN_MODEL, replicate_input)

    async def _generate_audio_sfx(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate sound effects or ambient audio.

        Parameters:
            prompt (str): Text description of the audio to generate
            duration (int): Duration in seconds (1-30, default 5)
        """
        prompt = params.get("prompt")
        if not prompt:
            return {"success": False, "error": "prompt is required"}

        if not self._api_key:
            return {
                "success": True,
                "result": {
                    "audio_url": "https://example.com/simulated_sfx.wav",
                    "prompt": prompt,
                    "duration": params.get("duration", 5),
                    "model": "audiogen-medium",
                    "format": "wav",
                    "sample_rate": 16000,
                },
                "mode": "offline_simulation",
            }

        replicate_input = {
            "prompt": prompt,
            "duration": min(int(params.get("duration", 5)), 30),
        }

        return await self._run_replicate_prediction(self.AUDIOGEN_MODEL, replicate_input)

    async def _continue_music(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extend an existing audio clip.

        Parameters:
            prompt (str): Text description guiding the continuation
            audio_url (str): URL or base64 of the input audio clip
            duration (int): Duration of the continuation in seconds (default 8)
            model_version (str): MusicGen variant (default medium)
        """
        prompt = params.get("prompt")
        audio_url = params.get("audio_url")
        if not prompt or not audio_url:
            return {"success": False, "error": "prompt and audio_url are required"}

        if not self._api_key:
            return {
                "success": True,
                "result": {
                    "audio_url": "https://example.com/simulated_continuation.wav",
                    "prompt": prompt,
                    "source_audio": audio_url,
                    "duration": params.get("duration", 8),
                    "model": "musicgen-medium",
                },
                "mode": "offline_simulation",
            }

        replicate_input = {
            "prompt": prompt,
            "input_audio": audio_url,
            "duration": min(int(params.get("duration", 8)), 30),
            "model_version": params.get("model_version", "medium"),
            "continuation": True,
            "continuation_start": 0,
        }

        return await self._run_replicate_prediction(self.MUSICGEN_MODEL, replicate_input)

    async def _get_models(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Return available AudioCraft models"""
        return {
            "success": True,
            "result": {
                "models": [
                    {"id": k, "description": v} for k, v in self.AVAILABLE_MODELS.items()
                ],
                "default_music_model": "musicgen-medium",
                "default_sfx_model": "audiogen-medium",
            },
        }

    # ------------------------------------------------------------------
    # Replicate helpers
    # ------------------------------------------------------------------

    async def _run_replicate_prediction(
        self, model_version: str, input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a Replicate prediction and poll until complete"""
        if not self.session:
            return {"success": False, "error": "HTTP session not available"}

        headers = {
            "Authorization": f"Token {self._api_key}",
            "Content-Type": "application/json",
        }

        try:
            # Create prediction
            async with self.session.post(
                f"{self._api_base}/predictions",
                headers=headers,
                json={"version": model_version, "input": input_data},
            ) as resp:
                if resp.status not in (200, 201):
                    text = await resp.text()
                    return {"success": False, "error": f"API error {resp.status}: {text}"}
                prediction = await resp.json()

            prediction_id = prediction.get("id")
            if not prediction_id:
                return {"success": False, "error": "No prediction ID returned"}

            # Poll for completion
            for _ in range(150):  # up to ~5 minutes
                await asyncio.sleep(self._poll_interval)
                async with self.session.get(
                    f"{self._api_base}/predictions/{prediction_id}",
                    headers=headers,
                ) as poll_resp:
                    if poll_resp.status != 200:
                        continue
                    data = await poll_resp.json()
                    status = data.get("status")
                    if status == "succeeded":
                        output = data.get("output")
                        audio_url = output[0] if isinstance(output, list) else output
                        return {
                            "success": True,
                            "result": {
                                "audio_url": audio_url,
                                "prediction_id": prediction_id,
                                "model_version": model_version,
                                "input": input_data,
                            },
                        }
                    elif status in ("failed", "canceled"):
                        error = data.get("error", "Prediction failed")
                        return {"success": False, "error": error}

            return {"success": False, "error": "Prediction timed out"}

        except Exception as e:
            logger.error(f"Replicate prediction failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def shutdown(self):
        """Shutdown the plugin"""
        await self.disconnect()

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["generate_music", "generate_audio_sfx", "continue_music", "get_models"],
                    "description": "Action to perform",
                },
                "params": {
                    "type": "object",
                    "description": "Action-specific parameters",
                },
            },
            "required": ["action"],
        }


plugin = Plugin()

