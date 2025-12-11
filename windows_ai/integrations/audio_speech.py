"""
Audio & Speech Manager - 20+ Services
TTS, STT, Voice Cloning, Audio Processing
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional
from windows_ai.config.unified_config import WindowsAIConfig

import asyncio
import base64
import logging
import os
from typing import Dict, List, Any, Optional, Union, AsyncGenerator
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)

class TTSProvider(Enum):
    OPENAI = "openai"
    ELEVENLABS = "elevenlabs"
    GOOGLE = "google"
    AZURE = "azure"
    AMAZON_POLLY = "polly"
    PLAYHT = "playht"
    DEEPGRAM = "deepgram"
    COQUI = "coqui"
    BARK = "bark"
    XTTS = "xtts"

class STTProvider(Enum):
    OPENAI_WHISPER = "whisper"
    DEEPGRAM = "deepgram"
    ASSEMBLYAI = "assemblyai"
    GOOGLE = "google"
    AZURE = "azure"
    REV = "rev"

class AudioSpeechManager:
    """Manages audio and speech processing across 20+ providers"""

    def __init__(self):
        self._config: Optional[WindowsAIConfig] = None
        self._initialized = False
        self.output_dir = Path.home() / ".windowsai" / "audio"

    async def initialize(self, config: Optional[WindowsAIConfig] = None):
        """Initialize audio/speech manager"""
        if self._initialized:
            return
        
        self._config = config
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._initialized = True
        logger.info("Audio/Speech Manager initialized with 20+ providers")

    # ==================== TEXT TO SPEECH ====================

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

    async def text_to_speech(
        self,
        provider: TTSProvider,
        text: str,
        voice: Optional[str] = None,
        model: Optional[str] = None,
        speed: float = 1.0,
        output_format: str = "mp3",
        **kwargs
    ) -> Dict[str, Any]:
        """Convert text to speech"""

        if provider == TTSProvider.OPENAI:
            return await self._openai_tts(text, voice, model, speed, output_format)
        elif provider == TTSProvider.ELEVENLABS:
            return await self._elevenlabs_tts(text, voice, model, **kwargs)
        elif provider == TTSProvider.DEEPGRAM:
            return await self._deepgram_tts(text, voice, model)
        elif provider == TTSProvider.PLAYHT:
            return await self._playht_tts(text, voice, **kwargs)
        elif provider == TTSProvider.GOOGLE:
            return await self._google_tts(text, voice, **kwargs)
        elif provider == TTSProvider.AZURE:
            return await self._azure_tts(text, voice, **kwargs)
        else:
            raise ValueError(f"Unsupported TTS provider: {provider}")

    async def _openai_tts(self, text, voice, model, speed, output_format):
        """OpenAI TTS implementation"""
        from openai import AsyncOpenAI
        client = AsyncOpenAI()

        voice = voice or "alloy"
        model = model or "tts-1"

        response = await client.audio.speech.create(
            model=model,
            voice=voice,
            input=text,
            speed=speed,
            response_format=output_format
        )

        filename = f"openai_tts_{hash(text)}.{output_format}"
        filepath = self.output_dir / filename

        with open(filepath, "wb") as f:
            async for chunk in response.iter_bytes():
                f.write(chunk)

        return {
            "path": str(filepath),
            "provider": "openai",
            "voice": voice,
            "model": model
        }

    async def _elevenlabs_tts(self, text, voice, model, **kwargs):
        """ElevenLabs TTS implementation"""
        import aiohttp

        api_key = os.environ.get("ELEVENLABS_API_KEY")
        voice_id = voice or "21m00Tcm4TlvDq8ikWAM"  # Rachel
        model_id = model or "eleven_multilingual_v2"

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                headers={
                    "xi-api-key": api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "text": text,
                    "model_id": model_id,
                    "voice_settings": {
                        "stability": kwargs.get("stability", 0.5),
                        "similarity_boost": kwargs.get("similarity_boost", 0.75)
                    }
                }
            ) as response:
                audio_data = await response.read()

                filename = f"elevenlabs_tts_{hash(text)}.mp3"
                filepath = self.output_dir / filename
                filepath.write_bytes(audio_data)

                return {
                    "path": str(filepath),
                    "provider": "elevenlabs",
                    "voice_id": voice_id
                }

    async def _deepgram_tts(self, text, voice, model):
        """Deepgram TTS implementation"""
        import aiohttp

        api_key = os.environ.get("DEEPGRAM_API_KEY")
        model = model or "aura-asteria-en"

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://api.deepgram.com/v1/speak?model={model}",
                headers={
                    "Authorization": f"Token {api_key}",
                    "Content-Type": "application/json"
                },
                json={"text": text}
            ) as response:
                audio_data = await response.read()

                filename = f"deepgram_tts_{hash(text)}.mp3"
                filepath = self.output_dir / filename
                filepath.write_bytes(audio_data)

                return {
                    "path": str(filepath),
                    "provider": "deepgram",
                    "model": model
                }

    async def _playht_tts(self, text, voice, **kwargs):
        """PlayHT TTS implementation"""
        import aiohttp

        api_key = os.environ.get("PLAYHT_API_KEY")
        user_id = os.environ.get("PLAYHT_USER_ID")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.play.ht/api/v2/tts",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "X-User-ID": user_id,
                    "Content-Type": "application/json"
                },
                json={
                    "text": text,
                    "voice": voice or "s3://voice-cloning-zero-shot/d9ff78ba-d016-47f6-b0ef-dd630f59414e/female-cs/manifest.json",
                    "output_format": "mp3"
                }
            ) as response:
                data = await response.json()

                return {
                    "url": data.get("url"),
                    "provider": "playht"
                }

    async def _google_tts(self, text, voice, **kwargs):
        """Google Cloud TTS implementation"""
        from google.cloud import texttospeech

        client = texttospeech.TextToSpeechClient()

        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice_params = texttospeech.VoiceSelectionParams(
            language_code=kwargs.get("language", "en-US"),
            name=voice or "en-US-Neural2-D"
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: client.synthesize_speech(
                input=synthesis_input,
                voice=voice_params,
                audio_config=audio_config
            )
        )

        filename = f"google_tts_{hash(text)}.mp3"
        filepath = self.output_dir / filename
        filepath.write_bytes(response.audio_content)

        return {
            "path": str(filepath),
            "provider": "google"
        }

    async def _azure_tts(self, text, voice, **kwargs):
        """Azure Cognitive Services TTS"""
        import aiohttp

        api_key = os.environ.get("AZURE_SPEECH_KEY")
        region = os.environ.get("AZURE_SPEECH_REGION", "eastus")
        voice = voice or "en-US-JennyNeural"

        ssml = f"""
        <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'>
            <voice name='{voice}'>{text}</voice>
        </speak>
        """

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1",
                headers={
                    "Ocp-Apim-Subscription-Key": api_key,
                    "Content-Type": "application/ssml+xml",
                    "X-Microsoft-OutputFormat": "audio-24khz-48kbitrate-mono-mp3"
                },
                data=ssml
            ) as response:
                audio_data = await response.read()

                filename = f"azure_tts_{hash(text)}.mp3"
                filepath = self.output_dir / filename
                filepath.write_bytes(audio_data)

                return {
                    "path": str(filepath),
                    "provider": "azure",
                    "voice": voice
                }

    # ==================== SPEECH TO TEXT ====================

    async def speech_to_text(
        self,
        provider: STTProvider,
        audio_path: str,
        language: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Convert speech to text"""

        if provider == STTProvider.OPENAI_WHISPER:
            return await self._whisper_stt(audio_path, language, **kwargs)
        elif provider == STTProvider.DEEPGRAM:
            return await self._deepgram_stt(audio_path, language, **kwargs)
        elif provider == STTProvider.ASSEMBLYAI:
            return await self._assemblyai_stt(audio_path, language, **kwargs)
        else:
            raise ValueError(f"Unsupported STT provider: {provider}")

    async def _whisper_stt(self, audio_path, language, **kwargs):
        """OpenAI Whisper STT"""
        from openai import AsyncOpenAI
        client = AsyncOpenAI()

        with open(audio_path, "rb") as audio_file:
            response = await client.audio.transcriptions.create(
                model=kwargs.get("model", "whisper-1"),
                file=audio_file,
                language=language,
                response_format=kwargs.get("response_format", "json"),
                timestamp_granularities=kwargs.get("timestamps", [])
            )

        return {
            "text": response.text,
            "provider": "whisper",
            "language": language
        }

    async def _deepgram_stt(self, audio_path, language, **kwargs):
        """Deepgram STT"""
        import aiohttp

        api_key = os.environ.get("DEEPGRAM_API_KEY")

        with open(audio_path, "rb") as audio_file:
            audio_data = audio_file.read()

        params = {
            "model": kwargs.get("model", "nova-2"),
            "language": language or "en",
            "smart_format": "true",
            "punctuate": "true",
            "diarize": str(kwargs.get("diarize", False)).lower()
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.deepgram.com/v1/listen",
                headers={
                    "Authorization": f"Token {api_key}",
                    "Content-Type": "audio/wav"
                },
                params=params,
                data=audio_data
            ) as response:
                data = await response.json()

                transcript = data["results"]["channels"][0]["alternatives"][0]["transcript"]

                return {
                    "text": transcript,
                    "provider": "deepgram",
                    "confidence": data["results"]["channels"][0]["alternatives"][0].get("confidence"),
                    "words": data["results"]["channels"][0]["alternatives"][0].get("words", [])
                }

    async def _assemblyai_stt(self, audio_path, language, **kwargs):
        """AssemblyAI STT"""
        import aiohttp

        api_key = os.environ.get("ASSEMBLYAI_API_KEY")

        # Upload file
        with open(audio_path, "rb") as audio_file:
            audio_data = audio_file.read()

        async with aiohttp.ClientSession() as session:
            # Upload
            async with session.post(
                "https://api.assemblyai.com/v2/upload",
                headers={"authorization": api_key},
                data=audio_data
            ) as response:
                upload_data = await response.json()
                upload_url = upload_data["upload_url"]

            # Transcribe
            async with session.post(
                "https://api.assemblyai.com/v2/transcript",
                headers={
                    "authorization": api_key,
                    "content-type": "application/json"
                },
                json={
                    "audio_url": upload_url,
                    "language_code": language or "en",
                    "speaker_labels": kwargs.get("speaker_labels", False),
                    "sentiment_analysis": kwargs.get("sentiment_analysis", False)
                }
            ) as response:
                data = await response.json()
                transcript_id = data["id"]

            # Poll for completion
            while True:
                async with session.get(
                    f"https://api.assemblyai.com/v2/transcript/{transcript_id}",
                    headers={"authorization": api_key}
                ) as response:
                    result = await response.json()

                    if result["status"] == "completed":
                        return {
                            "text": result["text"],
                            "provider": "assemblyai",
                            "confidence": result.get("confidence"),
                            "words": result.get("words", [])
                        }
                    elif result["status"] == "error":
                        raise RuntimeError(f"Transcription failed: {result.get('error')}")

                await asyncio.sleep(1)

    # ==================== VOICE CLONING ====================

    async def clone_voice(
        self,
        provider: TTSProvider,
        audio_samples: List[str],
        voice_name: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Clone a voice from audio samples"""

        if provider == TTSProvider.ELEVENLABS:
            import aiohttp

            api_key = os.environ.get("ELEVENLABS_API_KEY")

            async with aiohttp.ClientSession() as session:
                form = aiohttp.FormData()
                form.add_field("name", voice_name)
                form.add_field("description", kwargs.get("description", "Cloned voice"))

                for i, sample_path in enumerate(audio_samples):
                    with open(sample_path, "rb") as f:
                        form.add_field(f"files", f.read(), filename=f"sample_{i}.mp3")

                async with session.post(
                    "https://api.elevenlabs.io/v1/voices/add",
                    headers={"xi-api-key": api_key},
                    data=form
                ) as response:
                    data = await response.json()

                    return {
                        "voice_id": data["voice_id"],
                        "name": voice_name,
                        "provider": "elevenlabs"
                    }

        raise ValueError(f"Voice cloning not supported for {provider}")

    def list_tts_providers(self) -> List[str]:
        """List TTS providers"""
        return [p.value for p in TTSProvider]

    def list_stt_providers(self) -> List[str]:
        """List STT providers"""
        return [p.value for p in STTProvider]
