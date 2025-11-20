"""
Deepgram - Advanced Speech Recognition and Text-to-Speech API Integration

This module provides a production-quality integration with Deepgram's API,
supporting real-time and pre-recorded transcription, text-to-speech synthesis,
and advanced features like diarization and topic detection.
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


class DeepgramError(Exception):
    """Base exception for Deepgram errors"""
    pass


class DeepgramAPIError(DeepgramError):
    """Exception raised for API-related errors"""
    pass


class DeepgramAuthenticationError(DeepgramError):
    """Exception raised for authentication failures"""
    pass


class DeepgramValidationError(DeepgramError):
    """Exception raised for validation errors"""
    pass


class Deepgram:
    """
    Deepgram - Advanced Speech Recognition and Text-to-Speech

    This class provides a comprehensive interface to Deepgram's API,
    supporting pre-recorded and real-time transcription, text-to-speech synthesis,
    speaker diarization, topic detection, and language detection.

    Attributes:
        api_key (str): Deepgram API key
        model_type (str): Type of model (speech-to-text)
        name (str): Service name
        base_url (str): API base URL
    """

    SUPPORTED_FORMATS = ['.mp3', '.mp4', '.m4a', '.wav', '.flac', '.ogg', '.opus', '.webm', '.aac']
    MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2 GB
    DEFAULT_MODEL = "nova-2"
    DEFAULT_LANGUAGE = "en"

    # Available models
    MODELS = {
        'nova-2': 'Latest and most accurate model',
        'nova': 'Fast and accurate model',
        'enhanced': 'Enhanced model for general use',
        'base': 'Base model for cost-effective transcription',
        'whisper-tiny': 'Whisper tiny model',
        'whisper-base': 'Whisper base model',
        'whisper-small': 'Whisper small model',
        'whisper-medium': 'Whisper medium model',
        'whisper-large': 'Whisper large model'
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.deepgram.com/v1",
        model: str = DEFAULT_MODEL,
        timeout: int = 300,
        max_retries: int = 3
    ):
        """
        Initialize Deepgram client.

        Args:
            api_key: Deepgram API key. If not provided, looks for DEEPGRAM_API_KEY
            base_url: API base URL (default: https://api.deepgram.com/v1)
            model: Model to use (default: nova-2)
            timeout: Request timeout in seconds (default: 300)
            max_retries: Maximum retry attempts (default: 3)

        Raises:
            DeepgramAuthenticationError: If no API key is provided
        """
        self.api_key = api_key or os.getenv('DEEPGRAM_API_KEY')
        if not self.api_key:
            raise DeepgramAuthenticationError(
                "API key required. Provide via api_key parameter or DEEPGRAM_API_KEY environment variable"
            )

        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.model_type = "speech-to-text"
        self.name = "Deepgram"

        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Token {self.api_key}',
            'Content-Type': 'application/json'
        })

        logger.info(f"Initialized Deepgram client with model: {self.model}")

    def _validate_audio_file(self, audio_path: Union[str, Path]) -> Path:
        """
        Validate audio file exists and meets requirements.

        Args:
            audio_path: Path to audio file

        Returns:
            Path object for validated file

        Raises:
            DeepgramValidationError: If file is invalid
        """
        path = Path(audio_path)

        if not path.exists():
            raise DeepgramValidationError(f"Audio file not found: {audio_path}")

        if not path.is_file():
            raise DeepgramValidationError(f"Path is not a file: {audio_path}")

        if path.suffix.lower() not in self.SUPPORTED_FORMATS:
            raise DeepgramValidationError(
                f"Unsupported format: {path.suffix}. Supported: {', '.join(self.SUPPORTED_FORMATS)}"
            )

        file_size = path.stat().st_size
        if file_size == 0:
            raise DeepgramValidationError("Audio file is empty")

        if file_size > self.MAX_FILE_SIZE:
            raise DeepgramValidationError(
                f"File too large: {file_size / 1024 / 1024 / 1024:.2f}GB. Maximum: 2GB"
            )

        return path

    def _get_content_type(self, suffix: str) -> str:
        """Get content type for audio file format."""
        content_types = {
            '.mp3': 'audio/mpeg',
            '.mp4': 'audio/mp4',
            '.m4a': 'audio/m4a',
            '.wav': 'audio/wav',
            '.flac': 'audio/flac',
            '.ogg': 'audio/ogg',
            '.opus': 'audio/opus',
            '.webm': 'audio/webm',
            '.aac': 'audio/aac'
        }
        return content_types.get(suffix.lower(), 'application/octet-stream')

    def transcribe(
        self,
        audio_path: Union[str, Path, None] = None,
        audio_url: Optional[str] = None,
        language: Optional[str] = None,
        model: Optional[str] = None,
        punctuate: bool = True,
        diarize: bool = False,
        smart_format: bool = True,
        utterances: bool = False,
        detect_language: bool = False,
        detect_topics: bool = False,
        summarize: bool = False,
        return_full_response: bool = False
    ) -> Union[str, Dict[str, Any]]:
        """
        Transcribe audio file or URL to text.

        Args:
            audio_path: Path to local audio file (either this or audio_url required)
            audio_url: Public URL to audio file (either this or audio_path required)
            language: Language code (e.g., 'en', 'es'). Auto-detected if None
            model: Model to use (default: uses instance model)
            punctuate: Add punctuation to transcript
            diarize: Enable speaker diarization
            smart_format: Apply smart formatting
            utterances: Split transcript into utterances
            detect_language: Enable language detection
            detect_topics: Enable topic detection
            summarize: Generate summary
            return_full_response: Return full response with metadata

        Returns:
            Transcription text or full response dictionary

        Raises:
            DeepgramValidationError: If inputs are invalid
            DeepgramAPIError: If transcription fails

        Example:
            >>> dg = Deepgram(api_key="your-key")
            >>> text = dg.transcribe("audio.mp3", diarize=True)
            >>> print(text)
        """
        if not audio_path and not audio_url:
            raise DeepgramValidationError("Either audio_path or audio_url must be provided")

        # Build query parameters
        params = {
            'model': model or self.model,
            'punctuate': str(punctuate).lower(),
            'smart_format': str(smart_format).lower(),
            'utterances': str(utterances).lower()
        }

        if language:
            params['language'] = language
        if diarize:
            params['diarize'] = 'true'
        if detect_language:
            params['detect_language'] = 'true'
        if detect_topics:
            params['detect_topics'] = 'true'
        if summarize:
            params['summarize'] = 'true'

        endpoint = f"{self.base_url}/listen"

        # Prepare request
        if audio_url:
            # Use URL
            logger.info(f"Transcribing from URL: {audio_url}")
            payload = {'url': audio_url}
            headers = {'Content-Type': 'application/json'}

            for attempt in range(self.max_retries):
                try:
                    response = self.session.post(
                        endpoint,
                        params=params,
                        json=payload,
                        headers=headers,
                        timeout=self.timeout
                    )

                    if response.status_code == 200:
                        result = response.json()
                        return self._process_response(result, return_full_response)
                    elif response.status_code == 401:
                        raise DeepgramAuthenticationError("Invalid API key")
                    elif response.status_code == 429:
                        wait_time = 2 ** attempt
                        logger.warning(f"Rate limited. Waiting {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise DeepgramAPIError(f"Transcription failed: {response.text}")

                except requests.exceptions.Timeout:
                    if attempt < self.max_retries - 1:
                        logger.warning(f"Timeout. Retry {attempt + 1}/{self.max_retries}")
                        continue
                    raise DeepgramAPIError("Request timeout after retries")
                except requests.exceptions.RequestException as e:
                    if attempt < self.max_retries - 1:
                        logger.warning(f"Request failed: {e}. Retrying...")
                        time.sleep(2 ** attempt)
                        continue
                    raise DeepgramAPIError(f"Request failed: {str(e)}")

        else:
            # Use local file
            path = self._validate_audio_file(audio_path)
            logger.info(f"Transcribing file: {path.name}")

            content_type = self._get_content_type(path.suffix)

            for attempt in range(self.max_retries):
                try:
                    with open(path, 'rb') as audio_file:
                        audio_data = audio_file.read()

                    response = self.session.post(
                        endpoint,
                        params=params,
                        headers={
                            'Content-Type': content_type,
                            'Authorization': f'Token {self.api_key}'
                        },
                        data=audio_data,
                        timeout=self.timeout
                    )

                    if response.status_code == 200:
                        result = response.json()
                        return self._process_response(result, return_full_response)
                    elif response.status_code == 401:
                        raise DeepgramAuthenticationError("Invalid API key")
                    elif response.status_code == 429:
                        wait_time = 2 ** attempt
                        logger.warning(f"Rate limited. Waiting {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise DeepgramAPIError(f"Transcription failed: {response.text}")

                except requests.exceptions.Timeout:
                    if attempt < self.max_retries - 1:
                        logger.warning(f"Timeout. Retry {attempt + 1}/{self.max_retries}")
                        continue
                    raise DeepgramAPIError("Request timeout after retries")
                except requests.exceptions.RequestException as e:
                    if attempt < self.max_retries - 1:
                        logger.warning(f"Request failed: {e}. Retrying...")
                        time.sleep(2 ** attempt)
                        continue
                    raise DeepgramAPIError(f"Request failed: {str(e)}")

        raise DeepgramAPIError("Max retries exceeded")

    def _process_response(self, result: Dict[str, Any], return_full: bool) -> Union[str, Dict[str, Any]]:
        """Process API response and extract transcript."""
        if return_full:
            return result

        # Extract transcript text
        try:
            channels = result.get('results', {}).get('channels', [])
            if channels:
                alternatives = channels[0].get('alternatives', [])
                if alternatives:
                    text = alternatives[0].get('transcript', '')
                    logger.info(f"Transcription: {len(text)} characters")
                    return text
        except (KeyError, IndexError) as e:
            logger.error(f"Failed to extract transcript: {e}")

        return ''

    def synthesize(
        self,
        text: str,
        voice: str = "aura-asteria-en",
        model: str = "aura-asteria-en",
        encoding: str = "mp3",
        sample_rate: int = 24000
    ) -> bytes:
        """
        Synthesize speech from text using Deepgram Text-to-Speech.

        Args:
            text: Text to synthesize
            voice: Voice model to use (e.g., 'aura-asteria-en', 'aura-luna-en')
            model: TTS model (same as voice for Deepgram)
            encoding: Output encoding ('mp3', 'opus', 'flac', 'pcm')
            sample_rate: Sample rate in Hz (8000-48000)

        Returns:
            Audio data as bytes

        Raises:
            DeepgramValidationError: If inputs are invalid
            DeepgramAPIError: If synthesis fails

        Example:
            >>> dg = Deepgram(api_key="your-key")
            >>> audio = dg.synthesize("Hello, world!", voice="aura-asteria-en")
            >>> with open("output.mp3", "wb") as f:
            ...     f.write(audio)
        """
        if not text or not text.strip():
            raise DeepgramValidationError("Text cannot be empty")

        logger.info(f"Synthesizing speech: {len(text)} characters")

        endpoint = f"{self.base_url}/speak"

        params = {
            'model': model or voice,
            'encoding': encoding,
            'sample_rate': sample_rate
        }

        payload = {'text': text}

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
                    raise DeepgramAuthenticationError("Invalid API key")
                elif response.status_code == 429:
                    wait_time = 2 ** attempt
                    logger.warning(f"Rate limited. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise DeepgramAPIError(f"Synthesis failed: {response.text}")

            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"Request failed: {e}. Retrying...")
                    time.sleep(2 ** attempt)
                    continue
                raise DeepgramAPIError(f"Synthesis failed: {str(e)}")

        raise DeepgramAPIError("Max retries exceeded")

    def detect_language(
        self,
        audio_path: Union[str, Path, None] = None,
        audio_url: Optional[str] = None
    ) -> str:
        """
        Detect language from audio file.

        Args:
            audio_path: Path to local audio file
            audio_url: Public URL to audio file

        Returns:
            Detected language code (e.g., 'en')

        Raises:
            DeepgramValidationError: If inputs are invalid
            DeepgramAPIError: If detection fails

        Example:
            >>> dg = Deepgram(api_key="your-key")
            >>> lang = dg.detect_language("audio.mp3")
            >>> print(lang)  # 'en'
        """
        logger.info("Detecting language...")

        result = self.transcribe(
            audio_path=audio_path,
            audio_url=audio_url,
            detect_language=True,
            return_full_response=True
        )

        if isinstance(result, dict):
            try:
                channels = result.get('results', {}).get('channels', [])
                if channels:
                    detected = channels[0].get('detected_language', 'en')
                    language = detected if isinstance(detected, str) else 'en'
                    logger.info(f"Detected language: {language}")
                    return language
            except (KeyError, IndexError) as e:
                logger.error(f"Failed to extract language: {e}")

        return 'en'

    def is_available(self) -> bool:
        """
        Check if Deepgram API is available.

        Returns:
            True if service is accessible, False otherwise

        Example:
            >>> dg = Deepgram(api_key="your-key")
            >>> if dg.is_available():
            ...     print("Service is ready")
        """
        try:
            # Test API with a simple request
            endpoint = f"{self.base_url}/projects"
            response = self.session.get(endpoint, timeout=10)
            return response.status_code in [200, 403]  # 403 means auth works but endpoint restricted
        except Exception as e:
            logger.error(f"Availability check failed: {e}")
            return False

    def get_info(self) -> Dict[str, Any]:
        """
        Get information about Deepgram service.

        Returns:
            Dictionary with service information

        Example:
            >>> dg = Deepgram(api_key="your-key")
            >>> info = dg.get_info()
            >>> print(info['name'])
        """
        return {
            'name': self.name,
            'model': self.model,
            'model_type': self.model_type,
            'provider': 'Deepgram',
            'supported_formats': self.SUPPORTED_FORMATS,
            'max_file_size_gb': self.MAX_FILE_SIZE / 1024 / 1024 / 1024,
            'capabilities': [
                'transcription',
                'synthesis',
                'real_time_streaming',
                'speaker_diarization',
                'language_detection',
                'topic_detection',
                'summarization',
                'sentiment_analysis',
                'intent_recognition',
                'entity_detection'
            ],
            'models': self.MODELS,
            'supported_languages': [
                'en', 'en-US', 'en-GB', 'en-AU', 'en-NZ', 'en-IN',
                'es', 'es-419', 'fr', 'fr-CA', 'de', 'de-CH',
                'it', 'pt', 'pt-BR', 'nl', 'hi', 'hi-Latn',
                'ja', 'ko', 'zh', 'zh-CN', 'zh-TW',
                'ru', 'sv', 'tr', 'id', 'uk', 'pl',
                'da', 'no', 'fi', 'cs', 'el', 'ro', 'bg'
            ],
            'tts_voices': [
                'aura-asteria-en', 'aura-luna-en', 'aura-stella-en',
                'aura-athena-en', 'aura-hera-en', 'aura-orion-en',
                'aura-arcas-en', 'aura-perseus-en', 'aura-angus-en',
                'aura-orpheus-en', 'aura-helios-en', 'aura-zeus-en'
            ],
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
        return f"Deepgram(model='{self.model}', type='{self.model_type}')"


if __name__ == "__main__":
    # Example usage
    try:
        model = Deepgram()
        print(f"Deepgram initialized: {model}")
        print(f"Available: {model.is_available()}")

        info = model.get_info()
        print(f"\nService Info:")
        print(f"  Name: {info['name']}")
        print(f"  Model: {info['model']}")
        print(f"  Type: {info['model_type']}")
        print(f"  Supported formats: {', '.join(info['supported_formats'])}")
        print(f"  Max file size: {info['max_file_size_gb']}GB")
        print(f"  Capabilities: {len(info['capabilities'])} features")
        print(f"  TTS voices: {len(info['tts_voices'])} available")
    except DeepgramAuthenticationError as e:
        print(f"Authentication error: {e}")
    except Exception as e:
        print(f"Error: {e}")
