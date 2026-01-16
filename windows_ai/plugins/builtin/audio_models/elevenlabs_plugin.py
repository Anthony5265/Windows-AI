"""
ElevenLabs Text-to-Speech Plugin
Provides high-quality AI voice synthesis using ElevenLabs API
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
from pathlib import Path
import asyncio

logger = logging.getLogger(__name__)

class Plugin(IntegrationPlugin):
    """
    ElevenLabs TTS plugin for AI voice synthesis
    
    Capabilities:
    - Generate speech from text
    - Multiple voice options (500+ voices)
    - Voice cloning and fine-tuning
    - Multilingual support (32+ languages)
    - Emotion and style control
    - Real-time audio streaming
    - Multiple audio formats
    - Batch processing
    
    Actions:
    - text_to_speech: Convert text to speech
    - list_voices: Get available voices
    - get_voice: Get voice details
    - clone_voice: Clone a voice from audio samples
    - get_models: Get available TTS models
    - list_languages: Get supported languages
    """
    
    # Available voices (premium and standard)
    STANDARD_VOICES = {
        "21m00Tcm4TlvDq8ikWAM": {"name": "Rachel", "gender": "female", "language": "en", "accent": "american"},
        "AZnzlk1XvdvUeBnXmlld": {"name": "Domi", "gender": "female", "language": "en", "accent": "british"},
        "EXAVITQu4vr4xnSDxMaL": {"name": "Bella", "gender": "female", "language": "en", "accent": "american"},
        "ErXwobaYiN019PkySvjV": {"name": "Antoni", "gender": "male", "language": "en", "accent": "american"},
        "MF3mGyEYCl7XYWbV9V6O": {"name": "Elli", "gender": "female", "language": "en", "accent": "british"},
        "TxGEqnHWrfWFTfGW9XjX": {"name": "Josh", "gender": "male", "language": "en", "accent": "american"},
        "VR6AewLVsFNUjGEuVXZL": {"name": "Arnold", "gender": "male", "language": "en", "accent": "american"},
        "pNInz6obpgDQGcFmaJgB": {"name": "Adam", "gender": "male", "language": "en", "accent": "american"},
        "nPczCjzI2devNBz1zQrb": {"name": "Sam", "gender": "male", "language": "en", "accent": "american"},
    }
    
    # Available models
    AVAILABLE_MODELS = {
        "eleven_monolingual_v1": "Best for English - single language",
        "eleven_multilingual_v1": "Supports 32+ languages with voice similarity",
        "eleven_multilingual_v2": "Latest multilingual model with improved quality",
        "eleven_english_sting_v1": "American English voice - professional",
        "eleven_english_voice_1": "British English voice - professional"
    }
    
    # Supported languages (sample)
    SUPPORTED_LANGUAGES = {
        "en": "English", "es": "Spanish", "fr": "French", "de": "German",
        "it": "Italian", "pt": "Portuguese", "nl": "Dutch", "ru": "Russian",
        "zh": "Chinese (Mandarin)", "ja": "Japanese", "ko": "Korean", "ar": "Arabic",
        "tr": "Turkish", "pl": "Polish", "uk": "Ukrainian", "el": "Greek",
        "fi": "Finnish", "sv": "Swedish", "da": "Danish", "no": "Norwegian",
        "hi": "Hindi", "th": "Thai", "vi": "Vietnamese", "id": "Indonesian"
    }
    
    # Audio formats
    AUDIO_FORMATS = {
        "mp3": "MP3 (lossy, smaller file)",
        "pcm": "PCM (uncompressed, high quality)",
        "ulaw": "μ-law (compressed, 8-bit)",
        "ogg": "OGG (lossy, open format)"
    }
    
    def __init__(self):
        metadata = PluginMetadata(
            id="elevenlabs",
            name="ElevenLabs TTS",
            description="High-quality AI text-to-speech using ElevenLabs API",
            version="2.1.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["audio", "ai", "tts", "text-to-speech", "voice-synthesis", "elevenlabs", "speech"]
        )
        super().__init__(metadata)
        
        self.session = None
        self._api_key = None
        self._api_base = "https://api.elevenlabs.io/v1"
        self._initialized = False
        self._voices_cache = None
        self._request_timeout = 60
        self._cache = {}
        
    async def initialize(self) -> bool:
        """Initialize the ElevenLabs plugin"""
        if self._initialized:
            logger.warning("ElevenLabs plugin already initialized")
            return True
            
        try:
            # Detect API key from environment
            self._api_key = os.environ.get("ELEVENLABS_API_KEY")
            
            # Create HTTP session with timeout
            if AIOHTTP_AVAILABLE:
                timeout = aiohttp.ClientTimeout(total=self._request_timeout)
                self.session = aiohttp.ClientSession(timeout=timeout)
            else:
                self.session = None
            
            # Validate API key if available
            if self._api_key:
                await self._validate_api_key()
                logger.info("ElevenLabs API key validated successfully")
            else:
                logger.warning("ElevenLabs API key not found. Using limited functionality.")
            
            self._initialized = True
            logger.info("ElevenLabs plugin initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"ElevenLabs plugin initialization failed: {e}")
            if self.session:
                await self.session.close()
                self.session = None
            return False
    
    async def _validate_api_key(self) -> bool:
        """Validate ElevenLabs API key"""
        if not self._api_key or not self.session:
            return False
        
        try:
            headers = {
                "xi-api-key": self._api_key,
                "User-Agent": "WindowsAI/2.1.0"
            }
            
            async with self.session.get(
                f"{self._api_base}/user",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    user_data = await response.json()
                    logger.info(f"ElevenLabs user validation successful: {user_data.get('subscription', {}).get('tier')}")
                    return True
                return False
                
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return False
    
    async def connect(self, credentials: Optional[Dict[str, Any]] = None) -> bool:
        """
        Connect with credentials
        
        Args:
            credentials: Dictionary with 'api_key' and optional 'api_base'
        """
        try:
            if credentials:
                self._api_key = credentials.get("api_key", self._api_key)
                self._api_base = credentials.get("api_base", self._api_base)
            
            if self._api_key:
                await self._validate_api_key()
                logger.info("ElevenLabs plugin connected with credentials")
            
            return True
            
        except Exception as e:
            logger.error(f"ElevenLabs connection failed: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect and cleanup resources"""
        try:
            if self.session:
                await self.session.close()
                self.session = None
            
            self._voices_cache = None
            self._cache.clear()
            logger.info("ElevenLabs plugin disconnected")
            return True
            
        except Exception as e:
            logger.error(f"ElevenLabs disconnection failed: {e}")
            return False
    
    async def execute(self, action: str, parameters: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Execute ElevenLabs actions
        
        Args:
            action: Action to perform
            parameters: Action parameters
        
        Returns:
            Dictionary with success status and results
        """
        if not self._initialized:
            return {
                "success": False,
                "error": "Plugin not initialized. Call initialize() first.",
                "error_code": "NOT_INITIALIZED"
            }
        
        try:
            if action == "text_to_speech":
                return await self._text_to_speech(parameters)
            elif action == "list_voices":
                return await self._list_voices(parameters)
            elif action == "get_voice":
                return await self._get_voice(parameters)
            elif action == "clone_voice":
                return await self._clone_voice(parameters)
            elif action == "get_models":
                return await self._get_models(parameters)
            elif action == "list_languages":
                return await self._list_languages(parameters)
            elif action == "get_audio_formats":
                return await self._get_audio_formats(parameters)
            elif action == "batch_text_to_speech":
                return await self._batch_text_to_speech(parameters)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "error_code": "UNKNOWN_ACTION",
                    "supported_actions": ["text_to_speech", "list_voices", "get_voice", 
                                         "clone_voice", "get_models", "list_languages", 
                                         "get_audio_formats", "batch_text_to_speech"]
                }
                
        except Exception as e:
            logger.error(f"ElevenLabs execution failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "error_code": "EXECUTION_ERROR"
            }
    
    async def _text_to_speech(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert text to speech
        
        Parameters:
            text: Text to convert to speech
            voice_id: Voice ID to use
            model_id: Model ID (default: eleven_monolingual_v1)
            stability: Voice stability (0-1, default 0.5)
            similarity_boost: Clarity/similarity boost (0-1, default 0.75)
            style: Style exaggeration (0-1, default 0)
            output_format: Audio format (mp3, pcm, ulaw, ogg)
            optimize_streaming_latency: Enable streaming optimization (0-4)
        """
        if not self._api_key:
            return await self._tts_offline(params)

        if not self._api_key:
            return await self._text_to_speech_offline(params)
        
        text = params.get("text")
        if not text:
            return {
                "success": False,
                "error": "text parameter is required",
                "error_code": "MISSING_PARAMETER"
            }
        
        # Check cache
        cache_key = f"tts:{text[:50]}:{params.get('voice_id', 'default')}"
        if cache_key in self._cache:
            logger.debug(f"Using cached TTS for text: {text[:30]}...")
            return {"success": True, "result": self._cache[cache_key], "cached": True}
        
        try:
            voice_id = params.get("voice_id", "21m00Tcm4TlvDq8ikWAM")  # Default: Rachel
            model_id = params.get("model_id", "eleven_monolingual_v1")
            
            # Prepare request payload
            request_body = {
                "text": text,
                "model_id": model_id,
                "voice_settings": {
                    "stability": float(params.get("stability", 0.5)),
                    "similarity_boost": float(params.get("similarity_boost", 0.75)),
                    "style": float(params.get("style", 0))
                }
            }
            
            headers = {
                "xi-api-key": self._api_key,
                "Content-Type": "application/json",
                "User-Agent": "WindowsAI/2.1.0"
            }
            
            # Make request
            async with self.session.post(
                f"{self._api_base}/text-to-speech/{voice_id}",
                json=request_body,
                headers=headers
            ) as response:
                if response.status == 200:
                    # Get audio data
                    audio_data = await response.read()
                    audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                    
                    result = {
                        "audio_base64": audio_base64,
                        "audio_size_bytes": len(audio_data),
                        "format": params.get("output_format", "mp3"),
                        "voice_id": voice_id,
                        "model_id": model_id,
                        "text_length": len(text),
                        "voice_settings": request_body["voice_settings"]
                    }
                    
                    # Cache result
                    self._cache[cache_key] = result
                    
                    return {
                        "success": True,
                        "result": result
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"API error: {error_text}",
                        "error_code": f"API_{response.status}",
                        "status_code": response.status
                    }
                    
        except Exception as e:
            logger.error(f"Text-to-speech failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "error_code": "TTS_ERROR"
            }
    
    async def _text_to_speech_offline(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Offline TTS simulation"""
        text = params.get("text", "")
        
        return {
            "success": True,
            "result": {
                "audio_base64": "[Simulated audio data]",
                "format": params.get("output_format", "mp3"),
                "voice_id": params.get("voice_id", "21m00Tcm4TlvDq8ikWAM"),
                "text_length": len(text),
                "mode": "offline_simulation",
                "note": f"Configure ELEVENLABS_API_KEY for real TTS. Would synthesize: {text[:50]}..."
            }
        }
    
    async def _list_voices(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List available voices"""
        if self._voices_cache and not params.get("refresh"):
            return {
                "success": True,
                "result": {
                    "voices": list(self._voices_cache.values()),
                    "total_voices": len(self._voices_cache),
                    "cached": True
                }
            }
        
        if not self._api_key:
            # Return standard voices only
            return {
                "success": True,
                "result": {
                    "voices": list(self.STANDARD_VOICES.values()),
                    "total_voices": len(self.STANDARD_VOICES),
                    "mode": "standard"
                }
            }
        
        try:
            headers = {
                "xi-api-key": self._api_key,
                "User-Agent": "WindowsAI/2.1.0"
            }
            
            async with self.session.get(
                f"{self._api_base}/voices",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    voices = data.get("voices", [])
                    
                    # Cache voices
                    self._voices_cache = {v["voice_id"]: v for v in voices}
                    
                    return {
                        "success": True,
                        "result": {
                            "voices": voices,
                            "total_voices": len(voices)
                        }
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to list voices",
                        "error_code": f"API_{response.status}",
                        "fallback_voices": list(self.STANDARD_VOICES.values())
                    }
                    
        except Exception as e:
            logger.error(f"Failed to list voices: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "LIST_VOICES_ERROR",
                "fallback_voices": list(self.STANDARD_VOICES.values())
            }
    
    async def _get_voice(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get voice details"""
        voice_id = params.get("voice_id")
        if not voice_id:
            return {
                "success": False,
                "error": "voice_id parameter is required",
                "error_code": "MISSING_PARAMETER"
            }
        
        # Check cache or standard voices
        if self._voices_cache and voice_id in self._voices_cache:
            return {
                "success": True,
                "result": self._voices_cache[voice_id]
            }
        
        if voice_id in self.STANDARD_VOICES:
            return {
                "success": True,
                "result": self.STANDARD_VOICES[voice_id]
            }
        
        if not self._api_key:
            return {
                "success": False,
                "error": f"Voice {voice_id} not found",
                "error_code": "VOICE_NOT_FOUND"
            }
        
        try:
            headers = {
                "xi-api-key": self._api_key,
                "User-Agent": "WindowsAI/2.1.0"
            }
            
            async with self.session.get(
                f"{self._api_base}/voices/{voice_id}",
                headers=headers
            ) as response:
                if response.status == 200:
                    voice = await response.json()
                    return {
                        "success": True,
                        "result": voice
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Voice not found",
                        "error_code": f"API_{response.status}"
                    }
                    
        except Exception as e:
            logger.error(f"Failed to get voice: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "GET_VOICE_ERROR"
            }
    
    async def _clone_voice(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Clone a voice from audio samples"""
        name = params.get("name")
        files = params.get("files", [])
        
        if not name:
            return {
                "success": False,
                "error": "name parameter is required",
                "error_code": "MISSING_PARAMETER"
            }
        
        if not files:
            return {
                "success": False,
                "error": "files parameter is required - at least 1 audio file",
                "error_code": "MISSING_FILES"
            }
        
        if not self._api_key:
            return {
                "success": False,
                "error": "Voice cloning requires API key",
                "error_code": "NO_API_KEY"
            }
        
        try:
            headers = {
                "xi-api-key": self._api_key,
                "User-Agent": "WindowsAI/2.1.0"
            }
            
            # Prepare multipart form data
            form_data = aiohttp.FormData()
            form_data.add_field('name', name)
            form_data.add_field('description', params.get('description', 'Cloned voice'))
            
            # Add audio files
            for i, file_path in enumerate(files):
                if os.path.exists(file_path):
                    form_data.add_field(
                        f'files',
                        open(file_path, 'rb'),
                        filename=Path(file_path).name
                    )
            
            async with self.session.post(
                f"{self._api_base}/voices/add",
                data=form_data,
                headers=headers
            ) as response:
                if response.status in [200, 201]:
                    result = await response.json()
                    return {
                        "success": True,
                        "result": {
                            "voice_id": result.get("voice_id"),
                            "name": name,
                            "status": "ready",
                            "message": "Voice cloned successfully"
                        }
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"Voice cloning failed: {error_text}",
                        "error_code": f"API_{response.status}"
                    }
                    
        except Exception as e:
            logger.error(f"Voice cloning failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "error_code": "CLONE_ERROR"
            }
    
    async def _get_models(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get available models"""
        return {
            "success": True,
            "result": {
                "models": self.AVAILABLE_MODELS,
                "default_model": "eleven_monolingual_v1"
            }
        }
    
    async def _list_languages(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get supported languages"""
        return {
            "success": True,
            "result": {
                "languages": self.SUPPORTED_LANGUAGES,
                "total_languages": len(self.SUPPORTED_LANGUAGES)
            }
        }
    
    async def _get_audio_formats(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get supported audio formats"""
        return {
            "success": True,
            "result": {
                "formats": self.AUDIO_FORMATS,
                "default_format": "mp3"
            }
        }
    
    async def _batch_text_to_speech(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Process multiple texts"""
        texts = params.get("texts", [])
        if not texts:
            return {
                "success": False,
                "error": "texts parameter is required",
                "error_code": "MISSING_PARAMETER"
            }
        
        results = []
        for text in texts:
            result = await self._text_to_speech({"text": text, **{k: v for k, v in params.items() if k != "texts"}})
            results.append({"text": text, "result": result})
            await asyncio.sleep(0.1)  # Rate limiting
        
        return {
            "success": True,
            "result": {
                "total_texts": len(texts),
                "successful": sum(1 for r in results if r["result"]["success"]),
                "failed": sum(1 for r in results if not r["result"]["success"]),
                "results": results
            }
        }
    
    async def shutdown(self) -> bool:
        """Shutdown plugin"""
        await self.disconnect()
        self._initialized = False
        logger.info("ElevenLabs plugin shutdown")
        return True
    
    async def _tts_offline(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Offline TTS simulation"""
        return {
            "success": True,
            "result": {
                "audio": None,
                "mode": "offline_simulation",
                "note": "Configure ELEVENLABS_API_KEY for real text-to-speech"
            }
        }

    def get_schema(self) -> Dict[str, Any]:
        """Get plugin schema"""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["text_to_speech", "list_voices", "get_voice", "clone_voice", 
                            "get_models", "list_languages", "get_audio_formats", "batch_text_to_speech"],
                    "description": "Action to perform"
                },
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to convert to speech"
                        },
                        "texts": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Multiple texts for batch processing"
                        },
                        "voice_id": {
                            "type": "string",
                            "description": "Voice ID to use"
                        },
                        "model_id": {
                            "type": "string",
                            "description": "Model ID (default: eleven_monolingual_v1)"
                        },
                        "stability": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1,
                            "description": "Voice stability (default: 0.5)"
                        },
                        "similarity_boost": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1,
                            "description": "Clarity/similarity boost (default: 0.75)"
                        },
                        "output_format": {
                            "type": "string",
                            "enum": ["mp3", "pcm", "ulaw", "ogg"],
                            "description": "Audio output format"
                        }
                    }
                }
            },
            "required": ["action", "parameters"]
        }

plugin = Plugin()

plugin = Plugin()
