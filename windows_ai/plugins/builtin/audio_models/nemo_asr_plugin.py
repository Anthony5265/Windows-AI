"""
NVIDIA NeMo ASR Plugin
Automatic speech recognition using NVIDIA NeMo models via the NVIDIA API
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
import base64

logger = logging.getLogger(__name__)


class Plugin(IntegrationPlugin):
    """
    NVIDIA NeMo ASR plugin for high-accuracy speech recognition

    Capabilities:
    - Transcribe audio files using state-of-the-art NeMo ASR models
    - Automatic language identification across dozens of languages
    - Word-level timestamps and confidence scores
    - List available NeMo ASR models

    Actions:
    - transcribe: Convert audio to text with optional timestamps
    - identify_language: Detect the spoken language from an audio clip
    - get_models: List available NeMo ASR models
    """

    AVAILABLE_MODELS = {
        "stt_en_conformer_ctc_large": "English CTC Conformer Large – high accuracy",
        "stt_en_conformer_transducer_large": "English Transducer Conformer Large – best quality",
        "stt_multilingual_fastconformer_hybrid_large_pc": "Multilingual FastConformer",
        "stt_en_fastconformer_hybrid_large_streaming_80ms": "English streaming ASR",
        "stt_de_conformer_ctc_large": "German CTC Conformer Large",
        "stt_fr_conformer_ctc_large": "French CTC Conformer Large",
        "stt_es_conformer_ctc_large": "Spanish CTC Conformer Large",
    }

    SUPPORTED_LANGUAGES = {
        "en": "English", "de": "German", "fr": "French", "es": "Spanish",
        "it": "Italian", "pt": "Portuguese", "nl": "Dutch", "ru": "Russian",
        "zh": "Chinese", "ja": "Japanese", "ko": "Korean", "ar": "Arabic",
        "pl": "Polish", "cs": "Czech", "hi": "Hindi", "uk": "Ukrainian",
    }

    def __init__(self):
        metadata = PluginMetadata(
            id="nemo_asr",
            name="NVIDIA NeMo ASR",
            description="High-accuracy automatic speech recognition using NVIDIA NeMo models",
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["audio", "ai", "asr", "nvidia", "nemo"],
        )
        super().__init__(metadata)

        self.session = None
        self._api_key = None
        self._api_base = "https://api.nvidia.com/v1/nemo"
        self._model = "stt_en_conformer_transducer_large"
        self._initialized = False

    async def initialize(self) -> bool:
        """Initialize the NeMo ASR plugin"""
        if self._initialized:
            return True
        try:
            self._api_key = os.environ.get("NVIDIA_API_KEY")
            if AIOHTTP_AVAILABLE:
                timeout = aiohttp.ClientTimeout(total=300)
                self.session = aiohttp.ClientSession(timeout=timeout)
            else:
                self.session = None
            self._initialized = True
            if not self._api_key:
                logger.warning(
                    "NVIDIA_API_KEY not set. NeMo ASR plugin running in offline simulation mode."
                )
            else:
                logger.info("NVIDIA NeMo ASR plugin initialized")
            return True
        except Exception as e:
            logger.error(f"NeMo ASR initialization failed: {e}")
            return False

    async def connect(self, credentials: Optional[Dict[str, Any]] = None) -> bool:
        """Update connection credentials"""
        try:
            if credentials:
                self._api_key = credentials.get("api_key", self._api_key)
                self._api_base = credentials.get("api_base", self._api_base)
                self._model = credentials.get("model", self._model)
            return True
        except Exception as e:
            logger.error(f"NeMo ASR connect failed: {e}")
            return False

    async def disconnect(self) -> bool:
        """Close HTTP session"""
        try:
            if self.session:
                await self.session.close()
                self.session = None
            return True
        except Exception as e:
            logger.error(f"NeMo ASR disconnect failed: {e}")
            return False

    async def execute(self, action: str, params: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Dispatch to action handlers"""
        if not self._initialized:
            await self.initialize()
        try:
            if action == "transcribe":
                return await self._transcribe(params)
            elif action == "identify_language":
                return await self._identify_language(params)
            elif action == "get_models":
                return await self._get_models(params)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "supported_actions": ["transcribe", "identify_language", "get_models"],
                }
        except Exception as e:
            logger.error(f"NeMo ASR execute failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    # ------------------------------------------------------------------
    # Action implementations
    # ------------------------------------------------------------------

    async def _transcribe(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transcribe an audio file.

        Parameters:
            audio_file (str): File path or base64-encoded audio
            model (str): NeMo ASR model to use (default: stt_en_conformer_transducer_large)
            language (str): Language hint (optional)
            timestamps (bool): Return word-level timestamps (default False)
        """
        audio_file = params.get("audio_file")
        if not audio_file:
            return {"success": False, "error": "audio_file is required"}

        if not self._api_key:
            return {
                "success": True,
                "result": {
                    "text": "Sample transcription text produced by NVIDIA NeMo ASR.",
                    "language": params.get("language", "en"),
                    "confidence": 0.97,
                    "duration_seconds": 5.0,
                    "words": [
                        {"word": "Sample", "start": 0.0, "end": 0.3, "confidence": 0.99},
                        {"word": "transcription", "start": 0.4, "end": 0.9, "confidence": 0.98},
                        {"word": "text", "start": 1.0, "end": 1.2, "confidence": 0.97},
                    ] if params.get("timestamps") else [],
                    "model": params.get("model", self._model),
                },
                "mode": "offline_simulation",
            }

        model = params.get("model", self._model)
        audio_b64 = self._maybe_encode_file(audio_file)

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": model,
            "audio": audio_b64,
            "timestamps": bool(params.get("timestamps", False)),
        }
        if params.get("language"):
            payload["language"] = params["language"]

        try:
            async with self.session.post(
                f"{self._api_base}/asr/transcribe",
                headers=headers,
                json=payload,
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {"success": True, "result": data}
                else:
                    text = await resp.text()
                    return {"success": False, "error": f"API error {resp.status}: {text}"}
        except Exception as e:
            logger.error(f"NeMo ASR transcription failed: {e}")
            return {"success": False, "error": str(e)}

    async def _identify_language(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect the spoken language from an audio clip.

        Parameters:
            audio_file (str): File path or base64-encoded audio
        """
        audio_file = params.get("audio_file")
        if not audio_file:
            return {"success": False, "error": "audio_file is required"}

        if not self._api_key:
            return {
                "success": True,
                "result": {
                    "language": "en",
                    "language_name": "English",
                    "confidence": 0.96,
                    "alternatives": [
                        {"language": "en", "confidence": 0.96},
                        {"language": "de", "confidence": 0.02},
                        {"language": "fr", "confidence": 0.01},
                    ],
                },
                "mode": "offline_simulation",
            }

        audio_b64 = self._maybe_encode_file(audio_file)
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        try:
            async with self.session.post(
                f"{self._api_base}/asr/language-identify",
                headers=headers,
                json={"audio": audio_b64},
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    lang_code = data.get("language", "unknown")
                    data["language_name"] = self.SUPPORTED_LANGUAGES.get(lang_code, "Unknown")
                    return {"success": True, "result": data}
                else:
                    text = await resp.text()
                    return {"success": False, "error": f"API error {resp.status}: {text}"}
        except Exception as e:
            logger.error(f"NeMo language identification failed: {e}")
            return {"success": False, "error": str(e)}

    async def _get_models(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Return available NeMo ASR models"""
        return {
            "success": True,
            "result": {
                "models": [
                    {"id": k, "description": v} for k, v in self.AVAILABLE_MODELS.items()
                ],
                "default_model": self._model,
                "supported_languages": list(self.SUPPORTED_LANGUAGES.keys()),
            },
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _maybe_encode_file(self, audio_file: str) -> str:
        """Return base64-encoded audio, reading from disk if it's a file path"""
        if os.path.isfile(audio_file):
            with open(audio_file, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        # Assume already base64
        return audio_file

    async def shutdown(self):
        """Shutdown the plugin"""
        await self.disconnect()

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["transcribe", "identify_language", "get_models"],
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

