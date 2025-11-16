"""
ElevenLabs - Advanced AI Text-to-Speech and Voice Cloning Integration

This module provides a production-quality integration with ElevenLabs API,
supporting high-quality text-to-speech synthesis, voice cloning, voice design,
and multilingual speech generation with advanced voice controls.
"""

import os
import logging
import json
import time
from typing import Optional, Dict, Any, List, Union, Iterator
from pathlib import Path
import requests
from io import BytesIO

# Configure logging
logger = logging.getLogger(__name__)


class ElevenLabsError(Exception):
    """Base exception for ElevenLabs errors"""
    pass


class ElevenLabsAPIError(ElevenLabsError):
    """Exception raised for API-related errors"""
    pass


class ElevenLabsAuthenticationError(ElevenLabsError):
    """Exception raised for authentication failures"""
    pass


class ElevenLabsValidationError(ElevenLabsError):
    """Exception raised for validation errors"""
    pass


class ElevenLabs:
    """
    ElevenLabs - Advanced AI Text-to-Speech with Voice Cloning

    This class provides a comprehensive interface to ElevenLabs API,
    supporting high-quality text-to-speech synthesis, voice cloning,
    multilingual voices, and streaming capabilities with advanced
    voice parameter controls.

    Attributes:
        api_key (str): ElevenLabs API key
        model_type (str): Type of model (text-to-speech)
        name (str): Service name
        base_url (str): API base URL
        default_voice_id (str): Default voice ID to use
    """

    DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Rachel voice
    DEFAULT_MODEL = "eleven_multilingual_v2"
    MAX_TEXT_LENGTH = 5000  # characters per request

    # Available models
    MODELS = {
        'eleven_multilingual_v2': 'Latest multilingual model with improved quality',
        'eleven_multilingual_v1': 'Multilingual model for 29 languages',
        'eleven_monolingual_v1': 'English-only high quality model',
        'eleven_turbo_v2': 'Fastest model with lower latency'
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.elevenlabs.io/v1",
        default_voice_id: Optional[str] = None,
        default_model: str = DEFAULT_MODEL,
        timeout: int = 300,
        max_retries: int = 3
    ):
        """
        Initialize ElevenLabs client.

        Args:
            api_key: ElevenLabs API key. If not provided, looks for ELEVENLABS_API_KEY
            base_url: API base URL (default: https://api.elevenlabs.io/v1)
            default_voice_id: Default voice ID to use
            default_model: Default model to use (default: eleven_multilingual_v2)
            timeout: Request timeout in seconds (default: 300)
            max_retries: Maximum retry attempts (default: 3)

        Raises:
            ElevenLabsAuthenticationError: If no API key is provided
        """
        self.api_key = api_key or os.getenv('ELEVENLABS_API_KEY')
        if not self.api_key:
            raise ElevenLabsAuthenticationError(
                "API key required. Provide via api_key parameter or ELEVENLABS_API_KEY environment variable"
            )

        self.base_url = base_url.rstrip('/')
        self.default_voice_id = default_voice_id or self.DEFAULT_VOICE_ID
        self.default_model = default_model
        self.timeout = timeout
        self.max_retries = max_retries
        self.model_type = "text-to-speech"
        self.name = "ElevenLabs"

        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'xi-api-key': self.api_key,
            'Content-Type': 'application/json'
        })

        # Cache for voices
        self._voices_cache = None
        self._cache_time = 0
        self._cache_ttl = 3600  # 1 hour

        logger.info(f"Initialized ElevenLabs client with model: {self.default_model}")

    def transcribe(self, audio_path: str) -> str:
        """
        ElevenLabs does not provide speech-to-text transcription.
        This method is included for interface compatibility.

        Args:
            audio_path: Path to audio file (not used)

        Returns:
            Empty string

        Raises:
            NotImplementedError: ElevenLabs does not support transcription
        """
        raise NotImplementedError(
            "ElevenLabs does not support speech-to-text transcription. "
            "Use a STT service like Whisper, Azure Speech, AssemblyAI, or Deepgram."
        )

    def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        model: Optional[str] = None,
        voice_settings: Optional[Dict[str, float]] = None,
        output_format: str = "mp3_44100_128",
        optimize_streaming_latency: int = 0
    ) -> bytes:
        """
        Synthesize speech from text using ElevenLabs TTS.

        Args:
            text: Text to synthesize (max 5000 characters)
            voice: Voice ID or name. Uses default if None
            model: Model ID to use (default: eleven_multilingual_v2)
            voice_settings: Voice settings dict with stability, similarity_boost, style, use_speaker_boost
            output_format: Audio format ('mp3_44100_128', 'mp3_44100_192', 'pcm_16000', 'pcm_22050', 'pcm_24000', 'pcm_44100')
            optimize_streaming_latency: Latency optimization (0-4). Higher = lower latency

        Returns:
            Audio data as bytes

        Raises:
            ElevenLabsValidationError: If inputs are invalid
            ElevenLabsAPIError: If synthesis fails

        Example:
            >>> elevenlabs = ElevenLabs(api_key="your-key")
            >>> audio = elevenlabs.synthesize("Hello, world!", voice="Rachel")
            >>> with open("output.mp3", "wb") as f:
            ...     f.write(audio)
        """
        if not text or not text.strip():
            raise ElevenLabsValidationError("Text cannot be empty")

        if len(text) > self.MAX_TEXT_LENGTH:
            raise ElevenLabsValidationError(
                f"Text too long: {len(text)} characters. Maximum: {self.MAX_TEXT_LENGTH}"
            )

        # Resolve voice ID
        voice_id = self._resolve_voice_id(voice) if voice else self.default_voice_id
        model_id = model or self.default_model

        logger.info(f"Synthesizing speech: {len(text)} characters with voice {voice_id}")

        # Build voice settings
        settings = voice_settings or {
            'stability': 0.5,
            'similarity_boost': 0.75,
            'style': 0.0,
            'use_speaker_boost': True
        }

        endpoint = f"{self.base_url}/text-to-speech/{voice_id}"

        params = {}
        if optimize_streaming_latency > 0:
            params['optimize_streaming_latency'] = optimize_streaming_latency
        if output_format:
            params['output_format'] = output_format

        payload = {
            'text': text,
            'model_id': model_id,
            'voice_settings': settings
        }

        for attempt in range(self.max_retries):
            try:
                response = self.session.post(
                    endpoint,
                    params=params,
                    json=payload,
                    timeout=self.timeout
                )

                if response.status_code == 200:
                    logger.info(f"Synthesis complete: {len(response.content)} bytes")
                    return response.content
                elif response.status_code == 401:
                    raise ElevenLabsAuthenticationError("Invalid API key")
                elif response.status_code == 429:
                    wait_time = 2 ** attempt
                    logger.warning(f"Rate limited. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                elif response.status_code == 400:
                    error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                    error_msg = error_data.get('detail', {}).get('message', response.text)
                    raise ElevenLabsValidationError(f"Invalid request: {error_msg}")
                else:
                    raise ElevenLabsAPIError(f"Synthesis failed: {response.text}")

            except requests.exceptions.Timeout:
                if attempt < self.max_retries - 1:
                    logger.warning(f"Timeout. Retry {attempt + 1}/{self.max_retries}")
                    continue
                raise ElevenLabsAPIError("Request timeout after retries")
            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"Request failed: {e}. Retrying...")
                    time.sleep(2 ** attempt)
                    continue
                raise ElevenLabsAPIError(f"Synthesis failed: {str(e)}")

        raise ElevenLabsAPIError("Max retries exceeded")

    def synthesize_stream(
        self,
        text: str,
        voice: Optional[str] = None,
        model: Optional[str] = None,
        voice_settings: Optional[Dict[str, float]] = None,
        chunk_size: int = 1024
    ) -> Iterator[bytes]:
        """
        Synthesize speech with streaming for lower latency.

        Args:
            text: Text to synthesize
            voice: Voice ID or name
            model: Model ID to use
            voice_settings: Voice settings dict
            chunk_size: Size of chunks to yield

        Yields:
            Audio data chunks as bytes

        Raises:
            ElevenLabsValidationError: If inputs are invalid
            ElevenLabsAPIError: If synthesis fails

        Example:
            >>> elevenlabs = ElevenLabs(api_key="your-key")
            >>> for chunk in elevenlabs.synthesize_stream("Hello, world!"):
            ...     # Process audio chunk
            ...     pass
        """
        if not text or not text.strip():
            raise ElevenLabsValidationError("Text cannot be empty")

        voice_id = self._resolve_voice_id(voice) if voice else self.default_voice_id
        model_id = model or self.default_model

        logger.info(f"Streaming synthesis: {len(text)} characters")

        settings = voice_settings or {
            'stability': 0.5,
            'similarity_boost': 0.75
        }

        endpoint = f"{self.base_url}/text-to-speech/{voice_id}/stream"

        payload = {
            'text': text,
            'model_id': model_id,
            'voice_settings': settings
        }

        try:
            response = self.session.post(
                endpoint,
                json=payload,
                stream=True,
                timeout=self.timeout
            )

            if response.status_code == 200:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        yield chunk
            else:
                raise ElevenLabsAPIError(f"Streaming failed: {response.text}")

        except requests.exceptions.RequestException as e:
            raise ElevenLabsAPIError(f"Streaming failed: {str(e)}")

    def detect_language(self, audio_path: str) -> str:
        """
        ElevenLabs does not provide language detection.
        This method is included for interface compatibility.

        Args:
            audio_path: Path to audio file (not used)

        Returns:
            Default language 'en'

        Note:
            This is a stub method for interface compatibility
        """
        logger.warning("ElevenLabs does not support language detection")
        return 'en'

    def get_voices(self, refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get available voices from ElevenLabs.

        Args:
            refresh: Force refresh of cached voices

        Returns:
            List of voice dictionaries with id, name, and metadata

        Raises:
            ElevenLabsAPIError: If request fails

        Example:
            >>> elevenlabs = ElevenLabs(api_key="your-key")
            >>> voices = elevenlabs.get_voices()
            >>> for voice in voices:
            ...     print(f"{voice['name']}: {voice['voice_id']}")
        """
        # Check cache
        if not refresh and self._voices_cache and (time.time() - self._cache_time) < self._cache_ttl:
            return self._voices_cache

        endpoint = f"{self.base_url}/voices"

        try:
            response = self.session.get(endpoint, timeout=30)

            if response.status_code == 200:
                data = response.json()
                voices = data.get('voices', [])

                # Update cache
                self._voices_cache = voices
                self._cache_time = time.time()

                logger.info(f"Retrieved {len(voices)} voices")
                return voices
            else:
                raise ElevenLabsAPIError(f"Failed to get voices: {response.text}")

        except requests.exceptions.RequestException as e:
            raise ElevenLabsAPIError(f"Failed to get voices: {str(e)}")

    def get_voice_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get voice by name.

        Args:
            name: Voice name (case-insensitive)

        Returns:
            Voice dictionary or None if not found

        Example:
            >>> elevenlabs = ElevenLabs(api_key="your-key")
            >>> voice = elevenlabs.get_voice_by_name("Rachel")
            >>> print(voice['voice_id'])
        """
        voices = self.get_voices()
        name_lower = name.lower()

        for voice in voices:
            if voice.get('name', '').lower() == name_lower:
                return voice

        return None

    def _resolve_voice_id(self, voice_identifier: str) -> str:
        """
        Resolve voice name to voice ID.

        Args:
            voice_identifier: Voice ID or name

        Returns:
            Voice ID

        Raises:
            ElevenLabsValidationError: If voice not found
        """
        # Check if it's already a valid voice ID (alphanumeric string)
        if len(voice_identifier) > 10 and voice_identifier.replace('_', '').isalnum():
            return voice_identifier

        # Try to find by name
        voice = self.get_voice_by_name(voice_identifier)
        if voice:
            return voice['voice_id']

        raise ElevenLabsValidationError(f"Voice not found: {voice_identifier}")

    def get_user_info(self) -> Dict[str, Any]:
        """
        Get user account information and quota.

        Returns:
            User info including character quota and usage

        Raises:
            ElevenLabsAPIError: If request fails

        Example:
            >>> elevenlabs = ElevenLabs(api_key="your-key")
            >>> info = elevenlabs.get_user_info()
            >>> print(f"Characters left: {info['character_count']}")
        """
        endpoint = f"{self.base_url}/user"

        try:
            response = self.session.get(endpoint, timeout=30)

            if response.status_code == 200:
                return response.json()
            else:
                raise ElevenLabsAPIError(f"Failed to get user info: {response.text}")

        except requests.exceptions.RequestException as e:
            raise ElevenLabsAPIError(f"Failed to get user info: {str(e)}")

    def is_available(self) -> bool:
        """
        Check if ElevenLabs API is available.

        Returns:
            True if service is accessible, False otherwise

        Example:
            >>> elevenlabs = ElevenLabs(api_key="your-key")
            >>> if elevenlabs.is_available():
            ...     print("Service is ready")
        """
        try:
            # Try to get voices to verify API access
            self.get_voices()
            return True
        except Exception as e:
            logger.error(f"Availability check failed: {e}")
            return False

    def get_info(self) -> Dict[str, Any]:
        """
        Get information about ElevenLabs service.

        Returns:
            Dictionary with service information

        Example:
            >>> elevenlabs = ElevenLabs(api_key="your-key")
            >>> info = elevenlabs.get_info()
            >>> print(info['name'])
        """
        # Try to get user info for quota details
        user_info = {}
        try:
            user_info = self.get_user_info()
        except:
            pass

        # Get available voices
        voices_list = []
        try:
            voices_list = self.get_voices()
        except:
            pass

        return {
            'name': self.name,
            'model_type': self.model_type,
            'provider': 'ElevenLabs',
            'default_model': self.default_model,
            'default_voice_id': self.default_voice_id,
            'max_text_length': self.MAX_TEXT_LENGTH,
            'capabilities': [
                'text_to_speech',
                'voice_cloning',
                'voice_design',
                'streaming',
                'multilingual',
                'emotion_control',
                'custom_voices',
                'fine_tuning'
            ],
            'models': self.MODELS,
            'supported_languages': [
                'en', 'es', 'fr', 'de', 'it', 'pt', 'pl', 'tr', 'ru', 'nl',
                'cs', 'ar', 'zh', 'ja', 'ko', 'hi', 'sv', 'da', 'no', 'fi',
                'ro', 'sk', 'uk', 'el', 'id', 'ms', 'th', 'vi', 'fil'
            ],
            'output_formats': [
                'mp3_44100_128', 'mp3_44100_192',
                'pcm_16000', 'pcm_22050', 'pcm_24000', 'pcm_44100'
            ],
            'voice_settings': {
                'stability': 'Controls voice consistency (0.0-1.0)',
                'similarity_boost': 'Enhances voice similarity (0.0-1.0)',
                'style': 'Style exaggeration (0.0-1.0)',
                'use_speaker_boost': 'Boost speaker similarity (boolean)'
            },
            'available_voices_count': len(voices_list),
            'user_quota': user_info.get('subscription', {}) if user_info else {},
            'base_url': self.base_url
        }

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources"""
        self.session.close()

    def __repr__(self) -> str:
        """String representation"""
        return f"ElevenLabs(model='{self.default_model}', type='{self.model_type}')"


if __name__ == "__main__":
    # Example usage
    try:
        model = ElevenLabs()
        print(f"ElevenLabs initialized: {model}")
        print(f"Available: {model.is_available()}")

        info = model.get_info()
        print(f"\nService Info:")
        print(f"  Name: {info['name']}")
        print(f"  Type: {info['model_type']}")
        print(f"  Default model: {info['default_model']}")
        print(f"  Max text length: {info['max_text_length']} characters")
        print(f"  Available voices: {info['available_voices_count']}")
        print(f"  Capabilities: {len(info['capabilities'])} features")

        # List some voices
        voices = model.get_voices()
        if voices:
            print(f"\nSample Voices:")
            for voice in voices[:5]:
                print(f"  - {voice['name']}: {voice['voice_id']}")
    except ElevenLabsAuthenticationError as e:
        print(f"Authentication error: {e}")
    except Exception as e:
        print(f"Error: {e}")
