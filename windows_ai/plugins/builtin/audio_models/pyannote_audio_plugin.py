"""
PyAnnote Audio Plugin
Speaker diarization and segmentation using the PyAnnote Audio API
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
    PyAnnote Audio plugin for speaker diarization and audio segmentation

    Capabilities:
    - Speaker diarization: who spoke when
    - Speaker identification against a reference database
    - Audio segmentation into speech / non-speech regions
    - Overlap detection between simultaneous speakers

    Actions:
    - diarize: Segment audio by speaker identity and time
    - identify_speakers: Match detected speakers to known voice profiles
    - segment_audio: Partition audio into speech / silence / noise segments
    """

    def __init__(self):
        metadata = PluginMetadata(
            id="pyannote_audio",
            name="PyAnnote Audio",
            description="Speaker diarization and audio segmentation using PyAnnote Audio",
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["audio", "ai", "diarization", "speaker", "pyannote"],
        )
        super().__init__(metadata)

        self.session = None
        self._api_key = None
        self._api_base = "https://api.pyannote.ai/v1"
        self._initialized = False

    async def initialize(self) -> bool:
        """Initialize the PyAnnote Audio plugin"""
        if self._initialized:
            return True
        try:
            self._api_key = os.environ.get("PYANNOTE_API_KEY")
            if AIOHTTP_AVAILABLE:
                timeout = aiohttp.ClientTimeout(total=300)
                self.session = aiohttp.ClientSession(timeout=timeout)
            else:
                self.session = None
            self._initialized = True
            if not self._api_key:
                logger.warning(
                    "PYANNOTE_API_KEY not set. PyAnnote Audio plugin running in offline simulation mode."
                )
            else:
                logger.info("PyAnnote Audio plugin initialized")
            return True
        except Exception as e:
            logger.error(f"PyAnnote Audio initialization failed: {e}")
            return False

    async def connect(self, credentials: Optional[Dict[str, Any]] = None) -> bool:
        """Update connection credentials"""
        try:
            if credentials:
                self._api_key = credentials.get("api_key", self._api_key)
                self._api_base = credentials.get("api_base", self._api_base)
            return True
        except Exception as e:
            logger.error(f"PyAnnote Audio connect failed: {e}")
            return False

    async def disconnect(self) -> bool:
        """Close HTTP session"""
        try:
            if self.session:
                await self.session.close()
                self.session = None
            return True
        except Exception as e:
            logger.error(f"PyAnnote Audio disconnect failed: {e}")
            return False

    async def execute(self, action: str, params: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Dispatch to action handlers"""
        if not self._initialized:
            await self.initialize()
        try:
            if action == "diarize":
                return await self._diarize(params)
            elif action == "identify_speakers":
                return await self._identify_speakers(params)
            elif action == "segment_audio":
                return await self._segment_audio(params)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "supported_actions": ["diarize", "identify_speakers", "segment_audio"],
                }
        except Exception as e:
            logger.error(f"PyAnnote Audio execute failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    # ------------------------------------------------------------------
    # Action implementations
    # ------------------------------------------------------------------

    async def _diarize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform speaker diarization on an audio file.

        Parameters:
            audio_file (str): File path or base64-encoded audio (or URL)
            num_speakers (int): Expected number of speakers (optional, auto-detected if omitted)
            min_speakers (int): Minimum number of speakers (optional)
            max_speakers (int): Maximum number of speakers (optional)
        """
        audio_file = params.get("audio_file")
        if not audio_file:
            return {"success": False, "error": "audio_file is required"}

        if not self._api_key:
            return {
                "success": True,
                "result": {
                    "num_speakers": 2,
                    "diarization": [
                        {"speaker": "SPEAKER_00", "start": 0.0, "end": 4.2},
                        {"speaker": "SPEAKER_01", "start": 4.5, "end": 9.1},
                        {"speaker": "SPEAKER_00", "start": 9.3, "end": 13.0},
                        {"speaker": "SPEAKER_01", "start": 13.4, "end": 17.8},
                    ],
                    "total_duration": 17.8,
                    "speaker_durations": {
                        "SPEAKER_00": 7.9,
                        "SPEAKER_01": 7.0,
                    },
                },
                "mode": "offline_simulation",
            }

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {"url": self._resolve_audio_url(audio_file)}
        if params.get("num_speakers"):
            payload["numSpeakers"] = int(params["num_speakers"])
        if params.get("min_speakers"):
            payload["minSpeakers"] = int(params["min_speakers"])
        if params.get("max_speakers"):
            payload["maxSpeakers"] = int(params["max_speakers"])

        try:
            async with self.session.post(
                f"{self._api_base}/diarize",
                headers=headers,
                json=payload,
            ) as resp:
                if resp.status in (200, 201):
                    data = await resp.json()
                    return {"success": True, "result": data}
                else:
                    text = await resp.text()
                    return {"success": False, "error": f"API error {resp.status}: {text}"}
        except Exception as e:
            logger.error(f"PyAnnote diarization failed: {e}")
            return {"success": False, "error": str(e)}

    async def _identify_speakers(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Match diarized speakers against a set of reference voice profiles.

        Parameters:
            audio_file (str): File path, URL, or base64 audio to identify speakers in
            voiceprints (list): List of {"name": str, "audio_url": str} reference profiles
        """
        audio_file = params.get("audio_file")
        voiceprints = params.get("voiceprints", [])
        if not audio_file:
            return {"success": False, "error": "audio_file is required"}

        if not self._api_key:
            speaker_map = {}
            for i, vp in enumerate(voiceprints):
                speaker_map[f"SPEAKER_0{i}"] = {"name": vp.get("name", f"Person_{i}"), "confidence": 0.91}
            if not speaker_map:
                speaker_map = {
                    "SPEAKER_00": {"name": "Alice", "confidence": 0.93},
                    "SPEAKER_01": {"name": "Bob", "confidence": 0.88},
                }
            return {
                "success": True,
                "result": {
                    "speaker_map": speaker_map,
                    "identified": len(speaker_map),
                    "unidentified": 0,
                },
                "mode": "offline_simulation",
            }

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "url": self._resolve_audio_url(audio_file),
            "voiceprints": voiceprints,
        }
        try:
            async with self.session.post(
                f"{self._api_base}/identify",
                headers=headers,
                json=payload,
            ) as resp:
                if resp.status in (200, 201):
                    data = await resp.json()
                    return {"success": True, "result": data}
                else:
                    text = await resp.text()
                    return {"success": False, "error": f"API error {resp.status}: {text}"}
        except Exception as e:
            logger.error(f"PyAnnote speaker identification failed: {e}")
            return {"success": False, "error": str(e)}

    async def _segment_audio(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Segment audio into speech, silence, and noise regions.

        Parameters:
            audio_file (str): File path, URL, or base64 audio
            min_duration_on (float): Minimum speech segment duration in seconds (default 0.1)
            min_duration_off (float): Minimum silence duration in seconds (default 0.1)
        """
        audio_file = params.get("audio_file")
        if not audio_file:
            return {"success": False, "error": "audio_file is required"}

        if not self._api_key:
            return {
                "success": True,
                "result": {
                    "segments": [
                        {"type": "silence", "start": 0.0, "end": 0.5},
                        {"type": "speech", "start": 0.5, "end": 4.3},
                        {"type": "silence", "start": 4.3, "end": 4.9},
                        {"type": "speech", "start": 4.9, "end": 9.2},
                        {"type": "noise", "start": 9.2, "end": 9.7},
                        {"type": "speech", "start": 9.7, "end": 13.5},
                        {"type": "silence", "start": 13.5, "end": 14.0},
                    ],
                    "total_speech_duration": 12.1,
                    "total_silence_duration": 1.6,
                    "total_noise_duration": 0.5,
                    "speech_ratio": 0.82,
                },
                "mode": "offline_simulation",
            }

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "url": self._resolve_audio_url(audio_file),
            "minDurationOn": float(params.get("min_duration_on", 0.1)),
            "minDurationOff": float(params.get("min_duration_off", 0.1)),
        }
        try:
            async with self.session.post(
                f"{self._api_base}/segment",
                headers=headers,
                json=payload,
            ) as resp:
                if resp.status in (200, 201):
                    data = await resp.json()
                    return {"success": True, "result": data}
                else:
                    text = await resp.text()
                    return {"success": False, "error": f"API error {resp.status}: {text}"}
        except Exception as e:
            logger.error(f"PyAnnote audio segmentation failed: {e}")
            return {"success": False, "error": str(e)}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _resolve_audio_url(self, audio_file: str) -> str:
        """If it's a local path, base64-encode and embed; otherwise return as-is"""
        if os.path.isfile(audio_file):
            with open(audio_file, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            return f"data:audio/wav;base64,{b64}"
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
                    "enum": ["diarize", "identify_speakers", "segment_audio"],
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

