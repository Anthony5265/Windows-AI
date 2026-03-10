"""
Meta SeamlessM4T Plugin
Speech-to-speech and speech-to-text translation using Meta SeamlessM4T via Replicate
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
import base64

logger = logging.getLogger(__name__)


class Plugin(IntegrationPlugin):
    """
    Meta SeamlessM4T plugin for multilingual speech translation

    Capabilities:
    - Speech-to-speech translation between 100+ languages
    - Speech-to-text transcription with optional translation
    - List all supported language pairs

    Actions:
    - translate_speech: Translate spoken audio into another language (speech output)
    - transcribe_translate: Transcribe audio and optionally translate the text
    - get_languages: List all supported source and target languages
    """

    # Replicate model version for SeamlessM4T-Large
    SEAMLESS_MODEL = "cjwbw/seamless-m4t:668a4fec05a887143e5fe8d45df25ec4c794dd43669b9b03816bfa05d035a3b"

    SUPPORTED_LANGUAGES = {
        "afr": "Afrikaans", "amh": "Amharic", "arb": "Modern Standard Arabic",
        "ary": "Moroccan Arabic", "arz": "Egyptian Arabic", "ast": "Asturian",
        "azj": "North Azerbaijani", "bel": "Belarusian", "ben": "Bengali",
        "bos": "Bosnian", "bul": "Bulgarian", "cat": "Catalan", "ceb": "Cebuano",
        "ces": "Czech", "ckb": "Central Kurdish", "cmn": "Mandarin Chinese",
        "dan": "Danish", "deu": "German", "ell": "Greek", "eng": "English",
        "est": "Estonian", "fin": "Finnish", "fra": "French", "fuv": "Nigerian Fulfulde",
        "gaz": "West Central Oromo", "gle": "Irish", "glg": "Galician",
        "guj": "Gujarati", "heb": "Hebrew", "hin": "Hindi", "hrv": "Croatian",
        "hun": "Hungarian", "hye": "Armenian", "ibo": "Igbo", "ind": "Indonesian",
        "isl": "Icelandic", "ita": "Italian", "jav": "Javanese", "jpn": "Japanese",
        "kan": "Kannada", "kat": "Georgian", "kaz": "Kazakh", "khk": "Halh Mongolian",
        "khm": "Khmer", "kir": "Kyrgyz", "kor": "Korean", "lao": "Lao",
        "lit": "Lithuanian", "lug": "Ganda", "luo": "Luo", "lvs": "Standard Latvian",
        "mai": "Maithili", "mal": "Malayalam", "mar": "Marathi", "mkd": "Macedonian",
        "mlt": "Maltese", "mni": "Meitei", "mya": "Burmese", "nld": "Dutch",
        "nno": "Norwegian Nynorsk", "nob": "Norwegian Bokmål", "npi": "Nepali",
        "nya": "Nyanja", "ory": "Odia", "pan": "Punjabi", "pbt": "Southern Pashto",
        "pes": "Western Persian", "pol": "Polish", "por": "Portuguese", "ron": "Romanian",
        "rus": "Russian", "slk": "Slovak", "slv": "Slovenian", "sna": "Shona",
        "snd": "Sindhi", "som": "Somali", "spa": "Spanish", "srp": "Serbian",
        "swe": "Swedish", "swh": "Swahili", "tam": "Tamil", "tel": "Telugu",
        "tgk": "Tajik", "tgl": "Tagalog", "tha": "Thai", "tur": "Turkish",
        "ukr": "Ukrainian", "urd": "Urdu", "uzn": "Northern Uzbek", "vie": "Vietnamese",
        "xho": "Xhosa", "yor": "Yoruba", "yue": "Yue Chinese", "zsm": "Standard Malay",
        "zul": "Zulu",
    }

    def __init__(self):
        metadata = PluginMetadata(
            id="seamless_m4t",
            name="Meta SeamlessM4T",
            description="Multilingual speech-to-speech and speech-to-text translation using Meta SeamlessM4T",
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["audio", "ai", "translation", "meta", "seamless"],
        )
        super().__init__(metadata)

        self.session = None
        self._api_key = None
        self._api_base = "https://api.replicate.com/v1"
        self._initialized = False
        self._poll_interval = 2

    async def initialize(self) -> bool:
        """Initialize the SeamlessM4T plugin"""
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
                    "REPLICATE_API_TOKEN not set. SeamlessM4T plugin running in offline simulation mode."
                )
            else:
                logger.info("Meta SeamlessM4T plugin initialized with Replicate API key")
            return True
        except Exception as e:
            logger.error(f"SeamlessM4T initialization failed: {e}")
            return False

    async def connect(self, credentials: Optional[Dict[str, Any]] = None) -> bool:
        """Update connection credentials"""
        try:
            if credentials:
                self._api_key = credentials.get("api_key", self._api_key)
                self._api_base = credentials.get("api_base", self._api_base)
            return True
        except Exception as e:
            logger.error(f"SeamlessM4T connect failed: {e}")
            return False

    async def disconnect(self) -> bool:
        """Close HTTP session"""
        try:
            if self.session:
                await self.session.close()
                self.session = None
            return True
        except Exception as e:
            logger.error(f"SeamlessM4T disconnect failed: {e}")
            return False

    async def execute(self, action: str, params: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Dispatch to action handlers"""
        if not self._initialized:
            await self.initialize()
        try:
            if action == "translate_speech":
                return await self._translate_speech(params)
            elif action == "transcribe_translate":
                return await self._transcribe_translate(params)
            elif action == "get_languages":
                return await self._get_languages(params)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "supported_actions": ["translate_speech", "transcribe_translate", "get_languages"],
                }
        except Exception as e:
            logger.error(f"SeamlessM4T execute failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    # ------------------------------------------------------------------
    # Action implementations
    # ------------------------------------------------------------------

    async def _translate_speech(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Translate spoken audio into another language, returning synthesised speech.

        Parameters:
            audio_file (str): Path, URL, or base64 source audio
            source_language (str): BCP-47 / SeamlessM4T language code (e.g. "eng")
            target_language (str): Target language code (e.g. "fra")
        """
        audio_file = params.get("audio_file")
        source_language = params.get("source_language", "eng")
        target_language = params.get("target_language", "fra")

        if not audio_file:
            return {"success": False, "error": "audio_file is required"}
        if target_language not in self.SUPPORTED_LANGUAGES:
            return {"success": False, "error": f"Unsupported target language: {target_language}"}

        if not self._api_key:
            return {
                "success": True,
                "result": {
                    "audio_url": "https://example.com/simulated_translated_speech.wav",
                    "source_language": source_language,
                    "source_language_name": self.SUPPORTED_LANGUAGES.get(source_language, source_language),
                    "target_language": target_language,
                    "target_language_name": self.SUPPORTED_LANGUAGES.get(target_language, target_language),
                    "task": "S2ST",
                },
                "mode": "offline_simulation",
            }

        replicate_input = {
            "audio": self._resolve_audio(audio_file),
            "task_name": "S2ST (Speech to Speech translation)",
            "src_lang": source_language,
            "tgt_lang": target_language,
        }
        return await self._run_replicate_prediction(self.SEAMLESS_MODEL, replicate_input)

    async def _transcribe_translate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transcribe audio to text and optionally translate into another language.

        Parameters:
            audio_file (str): Path, URL, or base64 source audio
            source_language (str): Source language code (default "eng")
            target_language (str): Target language for translation (optional; if omitted, transcribes only)
        """
        audio_file = params.get("audio_file")
        source_language = params.get("source_language", "eng")
        target_language = params.get("target_language")

        if not audio_file:
            return {"success": False, "error": "audio_file is required"}

        if not self._api_key:
            result: Dict[str, Any] = {
                "text": "This is a simulated transcription of the provided audio file.",
                "source_language": source_language,
                "source_language_name": self.SUPPORTED_LANGUAGES.get(source_language, source_language),
            }
            if target_language:
                result["translated_text"] = "Ceci est une transcription simulée du fichier audio fourni."
                result["target_language"] = target_language
                result["target_language_name"] = self.SUPPORTED_LANGUAGES.get(target_language, target_language)
                result["task"] = "S2TT"
            else:
                result["task"] = "ASR"
            return {"success": True, "result": result, "mode": "offline_simulation"}

        task_name = (
            "S2TT (Speech to Text translation)"
            if target_language
            else "ASR (Automatic Speech Recognition)"
        )
        replicate_input: Dict[str, Any] = {
            "audio": self._resolve_audio(audio_file),
            "task_name": task_name,
            "src_lang": source_language,
        }
        if target_language:
            replicate_input["tgt_lang"] = target_language

        return await self._run_replicate_prediction(self.SEAMLESS_MODEL, replicate_input)

    async def _get_languages(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Return all supported languages"""
        return {
            "success": True,
            "result": {
                "languages": [
                    {"code": k, "name": v} for k, v in self.SUPPORTED_LANGUAGES.items()
                ],
                "total": len(self.SUPPORTED_LANGUAGES),
                "note": "All codes follow SeamlessM4T 3-letter language identifiers",
            },
        }

    # ------------------------------------------------------------------
    # Replicate helpers
    # ------------------------------------------------------------------

    def _resolve_audio(self, audio_file: str) -> str:
        """Return a URL or data URI for the audio file"""
        if os.path.isfile(audio_file):
            with open(audio_file, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            return f"data:audio/wav;base64,{b64}"
        return audio_file

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

            for _ in range(150):
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
                        return {"success": True, "result": data.get("output", data)}
                    elif status in ("failed", "canceled"):
                        return {"success": False, "error": data.get("error", "Prediction failed")}

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
                    "enum": ["translate_speech", "transcribe_translate", "get_languages"],
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

