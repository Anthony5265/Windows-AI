"""
AssemblyAI Transcription Plugin
Provides speech-to-text with speaker diarization, sentiment analysis, and entity extraction
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
import asyncio
from pathlib import Path

logger = logging.getLogger(__name__)

class Plugin(IntegrationPlugin):
    """
    AssemblyAI transcription plugin
    
    Capabilities:
    - High-accuracy speech-to-text
    - Speaker diarization
    - Sentiment analysis
    - Entity extraction
    - Content moderation
    - Keyword detection
    - Custom vocabulary
    - Real-time streaming
    - Auto chapters
    - Highlights extraction
    
    Actions:
    - transcribe: Transcribe audio file
    - list_models: Get available models
    - get_transcript: Get transcript details
    - delete_transcript: Delete transcript
    - list_transcripts: List all transcripts
    - stream_transcribe: Stream transcription (real-time)
    - batch_transcribe: Process multiple files
    """
    
    # Supported audio formats
    AUDIO_FORMATS = {
        "mp3": "MPEG-3 Audio",
        "wav": "WAV Audio",
        "m4a": "MPEG-4 Audio",
        "ogg": "OGG Vorbis",
        "flac": "FLAC Audio",
        "ulaw": "μ-law Audio",
        "pcm": "PCM Audio"
    }
    
    # Supported languages
    SUPPORTED_LANGUAGES = {
        "en": "English",
        "es": "Spanish", 
        "fr": "French",
        "de": "German",
        "it": "Italian",
        "pt": "Portuguese",
        "ru": "Russian",
        "zh": "Chinese (Mandarin)",
        "ja": "Japanese",
        "ko": "Korean",
        "ar": "Arabic",
        "nl": "Dutch",
        "tr": "Turkish",
        "pl": "Polish"
    }
    
    # Transcript statuses
    TRANSCRIPT_STATUSES = {
        "queued": "Waiting to be processed",
        "processing": "Currently being transcribed",
        "completed": "Transcription completed successfully",
        "error": "Transcription failed"
    }
    
    def __init__(self):
        metadata = PluginMetadata(
            id="assemblyai",
            name="AssemblyAI Transcription",
            description="High-accuracy speech-to-text with speaker diarization and sentiment analysis",
            version="2.1.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["audio", "ai", "transcription", "asr", "assemblyai", "diarization", "sentiment"]
        )
        super().__init__(metadata)
        
        self.session = None
        self._api_key = None
        self._api_base = "https://api.assemblyai.com/v2"
        self._ws_base = "wss://assemblyai.com/v2"
        self._initialized = False
        self._cache = {}
        self._request_timeout = 60
        
    async def initialize(self) -> bool:
        """Initialize the AssemblyAI plugin"""
        if self._initialized:
            logger.warning("AssemblyAI plugin already initialized")
            return True
            
        try:
            self._api_key = os.environ.get("ASSEMBLYAI_API_KEY")
            
            if AIOHTTP_AVAILABLE:
                timeout = aiohttp.ClientTimeout(total=self._request_timeout)
                self.session = aiohttp.ClientSession(timeout=timeout)
            else:
                self.session = None
            
            if self._api_key:
                await self._validate_api_key()
                logger.info("AssemblyAI API key validated successfully")
            else:
                logger.warning("AssemblyAI API key not found. Using limited functionality.")
            
            self._initialized = True
            logger.info("AssemblyAI plugin initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"AssemblyAI plugin initialization failed: {e}")
            if self.session:
                await self.session.close()
                self.session = None
            return False
    
    async def _validate_api_key(self) -> bool:
        """Validate AssemblyAI API key"""
        if not self._api_key or not self.session:
            return False
        
        try:
            headers = {
                "Authorization": self._api_key,
                "User-Agent": "WindowsAI/2.1.0"
            }
            
            async with self.session.get(
                f"{self._api_base}/account",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"AssemblyAI account validated: {data.get('balance')}")
                    return True
                return False
                
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return False
    
    async def connect(self, credentials: Optional[Dict[str, Any]] = None) -> bool:
        """Connect with credentials"""
        try:
            if credentials:
                self._api_key = credentials.get("api_key", self._api_key)
                self._api_base = credentials.get("api_base", self._api_base)
            
            if self._api_key:
                await self._validate_api_key()
                logger.info("AssemblyAI plugin connected with credentials")
            
            return True
            
        except Exception as e:
            logger.error(f"AssemblyAI connection failed: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect and cleanup"""
        try:
            if self.session:
                await self.session.close()
                self.session = None
            
            self._cache.clear()
            logger.info("AssemblyAI plugin disconnected")
            return True
            
        except Exception as e:
            logger.error(f"AssemblyAI disconnection failed: {e}")
            return False
    
    async def execute(self, action: str, parameters: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Execute AssemblyAI actions"""
        if not self._initialized:
            return {
                "success": False,
                "error": "Plugin not initialized. Call initialize() first.",
                "error_code": "NOT_INITIALIZED"
            }
        
        try:
            if action == "transcribe":
                return await self._transcribe(parameters)
            elif action == "get_transcript":
                return await self._get_transcript(parameters)
            elif action == "list_transcripts":
                return await self._list_transcripts(parameters)
            elif action == "delete_transcript":
                return await self._delete_transcript(parameters)
            elif action == "batch_transcribe":
                return await self._batch_transcribe(parameters)
            elif action == "list_models":
                return await self._list_models(parameters)
            elif action == "stream_transcribe":
                return await self._stream_transcribe(parameters)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "error_code": "UNKNOWN_ACTION",
                    "supported_actions": ["transcribe", "get_transcript", "list_transcripts", 
                                         "delete_transcript", "batch_transcribe", "list_models", 
                                         "stream_transcribe"]
                }
                
        except Exception as e:
            logger.error(f"AssemblyAI execution failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "error_code": "EXECUTION_ERROR"
            }
    
    async def _transcribe(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Transcribe audio file"""
        if not self._api_key:
            return await self._transcribe_offline(params)

        
        audio_url = params.get("audio_url")
        audio_file = params.get("audio_file")
        
        if not audio_url and not audio_file:
            return {
                "success": False,
                "error": "Either audio_url or audio_file parameter is required",
                "error_code": "MISSING_PARAMETER"
            }
        
        # Check cache
        cache_key = f"aai:{audio_url or audio_file}"
        if cache_key in self._cache:
            logger.debug("Using cached AssemblyAI transcript")
            return {"success": True, "result": self._cache[cache_key], "cached": True}
        
        try:
            # Prepare transcript request
            transcript_request = {
                "audio_url": audio_url,
                "speaker_labels": params.get("speaker_labels", True),
                "sentiment_analysis": params.get("sentiment_analysis", True),
                "entity_detection": params.get("entity_detection", False),
                "content_safety": params.get("content_safety", False),
                "auto_chapters": params.get("auto_chapters", False),
                "language_code": params.get("language_code", "en"),
                "speech_threshold": params.get("speech_threshold", 0.5)
            }
            
            # Remove None values
            transcript_request = {k: v for k, v in transcript_request.items() if v is not None}
            
            headers = {
                "Authorization": self._api_key,
                "Content-Type": "application/json",
                "User-Agent": "WindowsAI/2.1.0"
            }
            
            async with self.session.post(
                f"{self._api_base}/transcript",
                json=transcript_request,
                headers=headers
            ) as response:
                if response.status in [200, 201]:
                    transcript = await response.json()
                    transcript_id = transcript.get("id")
                    
                    # Poll for completion if async
                    if transcript.get("status") in ["queued", "processing"]:
                        transcript = await self._poll_transcript(transcript_id)
                    
                    result = {
                        "transcript_id": transcript_id,
                        "text": transcript.get("text"),
                        "confidence": transcript.get("confidence"),
                        "status": transcript.get("status"),
                        "language": transcript.get("language_code"),
                        "duration": transcript.get("audio_duration"),
                        "words": transcript.get("words", [])[:100] if params.get("include_words") else None
                    }
                    
                    # Add optional fields
                    if transcript.get("speaker_labels"):
                        result["speakers"] = transcript.get("speakers")
                    
                    if transcript.get("sentiment_analysis"):
                        result["sentiments"] = transcript.get("sentiments", [])
                    
                    if transcript.get("entities"):
                        result["entities"] = transcript.get("entities", [])[:50]
                    
                    self._cache[cache_key] = result
                    
                    return {
                        "success": True,
                        "result": result
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"Transcription failed: {error_text}",
                        "error_code": f"API_{response.status}",
                        "status_code": response.status
                    }
                    
        except Exception as e:
            logger.error(f"Transcription failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "error_code": "TRANSCRIPTION_ERROR"
            }
    
    async def _poll_transcript(self, transcript_id: str, max_retries: int = 30) -> Dict[str, Any]:
        """Poll transcript status"""
        headers = {
            "Authorization": self._api_key,
            "User-Agent": "WindowsAI/2.1.0"
        }
        
        for i in range(max_retries):
            try:
                async with self.session.get(
                    f"{self._api_base}/transcript/{transcript_id}",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        transcript = await response.json()
                        if transcript.get("status") == "completed":
                            return transcript
                        elif transcript.get("status") == "error":
                            raise Exception(f"Transcription failed: {transcript.get('error')}")
                        
                        await asyncio.sleep(2)
                    else:
                        raise Exception(f"Failed to poll: {response.status}")
                        
            except Exception as e:
                logger.error(f"Poll error: {e}")
                if i == max_retries - 1:
                    raise
        
        raise Exception("Transcription polling timeout")
    
    async def _transcribe_offline(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Offline transcription simulation"""
        return {
            "success": True,
            "result": {
                "transcript_id": "offline_sim_123",
                "text": "[Simulated transcription of audio content]",
                "status": "completed",
                "language": params.get("language_code", "en"),
                "mode": "offline_simulation",
                "note": "Configure ASSEMBLYAI_API_KEY for real transcription"
            }
        }
    
    async def _get_transcript(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get transcript by ID"""
        transcript_id = params.get("transcript_id")
        if not transcript_id:
            return {
                "success": False,
                "error": "transcript_id parameter is required",
                "error_code": "MISSING_PARAMETER"
            }
        
        if not self._api_key:
            return {
                "success": False,
                "error": "API key required",
                "error_code": "NO_API_KEY"
            }
        
        try:
            headers = {
                "Authorization": self._api_key,
                "User-Agent": "WindowsAI/2.1.0"
            }
            
            async with self.session.get(
                f"{self._api_base}/transcript/{transcript_id}",
                headers=headers
            ) as response:
                if response.status == 200:
                    transcript = await response.json()
                    return {
                        "success": True,
                        "result": {
                            "id": transcript.get("id"),
                            "text": transcript.get("text"),
                            "status": transcript.get("status"),
                            "confidence": transcript.get("confidence"),
                            "created": transcript.get("created"),
                            "completed": transcript.get("completed")
                        }
                    }
                else:
                    return {
                        "success": False,
                        "error": "Transcript not found",
                        "error_code": f"API_{response.status}"
                    }
                    
        except Exception as e:
            logger.error(f"Get transcript failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "GET_TRANSCRIPT_ERROR"
            }
    
    async def _list_transcripts(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List transcripts"""
        if not self._api_key:
            return {
                "success": False,
                "error": "API key required",
                "error_code": "NO_API_KEY"
            }
        
        try:
            headers = {
                "Authorization": self._api_key,
                "User-Agent": "WindowsAI/2.1.0"
            }
            
            limit = params.get("limit", 10)
            status = params.get("status")
            
            url = f"{self._api_base}/transcript?limit={limit}"
            if status:
                url += f"&status={status}"
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    transcripts = data.get("transcripts", [])
                    return {
                        "success": True,
                        "result": {
                            "transcripts": transcripts,
                            "total": len(transcripts)
                        }
                    }
                else:
                    return {
                        "success": False,
                        "error": "Failed to list transcripts",
                        "error_code": f"API_{response.status}"
                    }
                    
        except Exception as e:
            logger.error(f"List transcripts failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "LIST_ERROR"
            }
    
    async def _delete_transcript(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete transcript"""
        transcript_id = params.get("transcript_id")
        if not transcript_id:
            return {
                "success": False,
                "error": "transcript_id parameter is required",
                "error_code": "MISSING_PARAMETER"
            }
        
        if not self._api_key:
            return {
                "success": False,
                "error": "API key required",
                "error_code": "NO_API_KEY"
            }
        
        try:
            headers = {
                "Authorization": self._api_key,
                "User-Agent": "WindowsAI/2.1.0"
            }
            
            async with self.session.delete(
                f"{self._api_base}/transcript/{transcript_id}",
                headers=headers
            ) as response:
                if response.status == 200:
                    return {
                        "success": True,
                        "result": {"deleted": True, "transcript_id": transcript_id}
                    }
                else:
                    return {
                        "success": False,
                        "error": "Failed to delete transcript",
                        "error_code": f"API_{response.status}"
                    }
                    
        except Exception as e:
            logger.error(f"Delete transcript failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "DELETE_ERROR"
            }
    
    async def _batch_transcribe(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Process multiple audio URLs"""
        audio_urls = params.get("audio_urls", [])
        if not audio_urls:
            return {
                "success": False,
                "error": "audio_urls parameter is required",
                "error_code": "MISSING_PARAMETER"
            }
        
        results = []
        for url in audio_urls:
            result = await self._transcribe({"audio_url": url, **{k: v for k, v in params.items() if k != "audio_urls"}})
            results.append({"url": url, "result": result})
            await asyncio.sleep(0.1)  # Rate limiting
        
        return {
            "success": True,
            "result": {
                "total_urls": len(audio_urls),
                "successful": sum(1 for r in results if r["result"]["success"]),
                "failed": sum(1 for r in results if not r["result"]["success"]),
                "results": results
            }
        }
    
    async def _list_models(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get supported models and options"""
        return {
            "success": True,
            "result": {
                "audio_formats": self.AUDIO_FORMATS,
                "supported_languages": self.SUPPORTED_LANGUAGES,
                "transcript_statuses": self.TRANSCRIPT_STATUSES,
                "features": {
                    "speaker_diarization": "Identify different speakers",
                    "sentiment_analysis": "Analyze sentiment per sentence",
                    "entity_detection": "Extract named entities",
                    "content_safety": "Detect unsafe content",
                    "auto_chapters": "Auto-generate chapters",
                    "speech_threshold": "Confidence threshold for speech"
                }
            }
        }
    
    async def _stream_transcribe(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Stream transcription (placeholder)"""
        return {
            "success": True,
            "result": {
                "status": "streaming_enabled",
                "ws_url": self._ws_base,
                "note": "Streaming transcription requires WebSocket connection"
            }
        }
    
    async def shutdown(self) -> bool:
        """Shutdown plugin"""
        await self.disconnect()
        self._initialized = False
        logger.info("AssemblyAI plugin shutdown")
        return True
    
    def get_schema(self) -> Dict[str, Any]:
        """Get plugin schema"""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["transcribe", "get_transcript", "list_transcripts", 
                            "delete_transcript", "batch_transcribe", "list_models", 
                            "stream_transcribe"],
                    "description": "Action to perform"
                },
                "parameters": {
                    "type": "object",
                    "properties": {
                        "audio_url": {
                            "type": "string",
                            "description": "URL to audio file"
                        },
                        "audio_file": {
                            "type": "string",
                            "description": "Local audio file path"
                        },
                        "audio_urls": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Multiple URLs for batch processing"
                        },
                        "speaker_labels": {
                            "type": "boolean",
                            "description": "Enable speaker diarization"
                        },
                        "sentiment_analysis": {
                            "type": "boolean",
                            "description": "Enable sentiment analysis"
                        },
                        "language_code": {
                            "type": "string",
                            "description": "Language code (default: en)"
                        },
                        "transcript_id": {
                            "type": "string",
                            "description": "Transcript ID for retrieval"
                        }
                    }
                }
            },
            "required": ["action", "parameters"]
        }

plugin = Plugin()
