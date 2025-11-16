"""
Whisper Audio Model - OpenAI Speech-to-Text Integration

This module provides a production-quality integration with OpenAI's Whisper API
for speech-to-text transcription and language detection.
"""

import os
import logging
from typing import Optional, Dict, Any, Iterator, BinaryIO, Union
from pathlib import Path
import requests
import json
import time

# Configure logging
logger = logging.getLogger(__name__)


class WhisperError(Exception):
    """Base exception for Whisper-related errors"""
    pass


class WhisperAPIError(WhisperError):
    """Exception raised for API-related errors"""
    pass


class WhisperAuthenticationError(WhisperError):
    """Exception raised for authentication failures"""
    pass


class WhisperValidationError(WhisperError):
    """Exception raised for validation errors"""
    pass


class Whisper:
    """
    OpenAI Whisper - Advanced Speech-to-Text Model

    This class provides a comprehensive interface to OpenAI's Whisper API,
    supporting transcription, translation, and language detection with
    robust error handling and streaming capabilities.

    Attributes:
        api_key (str): OpenAI API key for authentication
        model_type (str): Type of model (speech-to-text)
        base_url (str): Base URL for OpenAI API
        model (str): Whisper model variant to use
        timeout (int): Request timeout in seconds
    """

    SUPPORTED_FORMATS = ['.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm']
    MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB
    DEFAULT_MODEL = "whisper-1"
    API_VERSION = "v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        base_url: str = "https://api.openai.com/v1",
        timeout: int = 300,
        max_retries: int = 3
    ):
        """
        Initialize Whisper model with API credentials.

        Args:
            api_key: OpenAI API key. If not provided, will look for OPENAI_API_KEY env var
            model: Whisper model variant (default: whisper-1)
            base_url: API base URL (default: https://api.openai.com/v1)
            timeout: Request timeout in seconds (default: 300)
            max_retries: Maximum number of retry attempts (default: 3)

        Raises:
            WhisperAuthenticationError: If no API key is provided
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise WhisperAuthenticationError(
                "API key required. Provide via api_key parameter or OPENAI_API_KEY environment variable"
            )

        self.model = model
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.model_type = "speech-to-text"
        self.name = "OpenAI Whisper"

        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}'
        })

        logger.info(f"Initialized Whisper model: {self.model}")

    def _validate_audio_file(self, audio_path: Union[str, Path]) -> Path:
        """
        Validate audio file exists and meets requirements.

        Args:
            audio_path: Path to audio file

        Returns:
            Path object for the validated file

        Raises:
            WhisperValidationError: If file is invalid
        """
        path = Path(audio_path)

        if not path.exists():
            raise WhisperValidationError(f"Audio file not found: {audio_path}")

        if not path.is_file():
            raise WhisperValidationError(f"Path is not a file: {audio_path}")

        if path.suffix.lower() not in self.SUPPORTED_FORMATS:
            raise WhisperValidationError(
                f"Unsupported format: {path.suffix}. Supported: {', '.join(self.SUPPORTED_FORMATS)}"
            )

        file_size = path.stat().st_size
        if file_size > self.MAX_FILE_SIZE:
            raise WhisperValidationError(
                f"File too large: {file_size / 1024 / 1024:.2f}MB. Maximum: 25MB"
            )

        if file_size == 0:
            raise WhisperValidationError("Audio file is empty")

        return path

    def _make_request(
        self,
        endpoint: str,
        files: Optional[Dict] = None,
        data: Optional[Dict] = None,
        method: str = "POST"
    ) -> Dict[str, Any]:
        """
        Make HTTP request to OpenAI API with retry logic.

        Args:
            endpoint: API endpoint path
            files: Files to upload
            data: Form data
            method: HTTP method

        Returns:
            JSON response as dictionary

        Raises:
            WhisperAPIError: If request fails after retries
        """
        url = f"{self.base_url}/{endpoint}"

        for attempt in range(self.max_retries):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    files=files,
                    data=data,
                    timeout=self.timeout
                )

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 401:
                    raise WhisperAuthenticationError("Invalid API key")
                elif response.status_code == 429:
                    # Rate limit - wait and retry
                    wait_time = 2 ** attempt
                    logger.warning(f"Rate limited. Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    continue
                else:
                    error_msg = response.text
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('error', {}).get('message', error_msg)
                    except:
                        pass
                    raise WhisperAPIError(f"API request failed: {error_msg}")

            except requests.exceptions.Timeout:
                if attempt < self.max_retries - 1:
                    logger.warning(f"Request timeout. Retry {attempt + 1}/{self.max_retries}")
                    continue
                raise WhisperAPIError("Request timeout after retries")
            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"Request failed: {e}. Retry {attempt + 1}/{self.max_retries}")
                    time.sleep(2 ** attempt)
                    continue
                raise WhisperAPIError(f"Request failed: {str(e)}")

        raise WhisperAPIError("Max retries exceeded")

    def transcribe(
        self,
        audio_path: Union[str, Path],
        language: Optional[str] = None,
        prompt: Optional[str] = None,
        temperature: float = 0.0,
        response_format: str = "json",
        timestamp_granularities: Optional[list] = None
    ) -> Union[str, Dict[str, Any]]:
        """
        Transcribe audio file to text.

        Args:
            audio_path: Path to audio file
            language: ISO-639-1 language code (e.g., 'en', 'es'). Auto-detected if None
            prompt: Optional text to guide the model's style
            temperature: Sampling temperature (0-1). Higher = more random
            response_format: Output format ('json', 'text', 'srt', 'verbose_json', 'vtt')
            timestamp_granularities: List of timestamp granularities (['word', 'segment'])

        Returns:
            Transcription text (if response_format='text') or dictionary with metadata

        Raises:
            WhisperValidationError: If audio file is invalid
            WhisperAPIError: If transcription fails

        Example:
            >>> whisper = Whisper(api_key="sk-...")
            >>> result = whisper.transcribe("audio.mp3", language="en")
            >>> print(result['text'])
        """
        path = self._validate_audio_file(audio_path)

        logger.info(f"Transcribing: {path.name}")

        with open(path, 'rb') as audio_file:
            files = {
                'file': (path.name, audio_file, f'audio/{path.suffix[1:]}')
            }

            data = {
                'model': self.model,
                'response_format': response_format,
                'temperature': temperature
            }

            if language:
                data['language'] = language
            if prompt:
                data['prompt'] = prompt
            if timestamp_granularities:
                data['timestamp_granularities[]'] = timestamp_granularities

            result = self._make_request('audio/transcriptions', files=files, data=data)

        if response_format == 'text':
            return result.get('text', '')

        logger.info(f"Transcription complete: {len(result.get('text', ''))} characters")
        return result

    def translate(
        self,
        audio_path: Union[str, Path],
        prompt: Optional[str] = None,
        temperature: float = 0.0,
        response_format: str = "json"
    ) -> Union[str, Dict[str, Any]]:
        """
        Translate audio to English text.

        Args:
            audio_path: Path to audio file
            prompt: Optional text to guide translation
            temperature: Sampling temperature (0-1)
            response_format: Output format ('json', 'text', 'srt', 'verbose_json', 'vtt')

        Returns:
            Translated text or dictionary with metadata

        Raises:
            WhisperValidationError: If audio file is invalid
            WhisperAPIError: If translation fails
        """
        path = self._validate_audio_file(audio_path)

        logger.info(f"Translating to English: {path.name}")

        with open(path, 'rb') as audio_file:
            files = {
                'file': (path.name, audio_file, f'audio/{path.suffix[1:]}')
            }

            data = {
                'model': self.model,
                'response_format': response_format,
                'temperature': temperature
            }

            if prompt:
                data['prompt'] = prompt

            result = self._make_request('audio/translations', files=files, data=data)

        if response_format == 'text':
            return result.get('text', '')

        return result

    def synthesize(self, text: str, voice: str = "default") -> bytes:
        """
        OpenAI Whisper does not provide text-to-speech synthesis.
        This method is included for interface compatibility.

        Args:
            text: Text to synthesize (not used)
            voice: Voice name (not used)

        Returns:
            Empty bytes

        Raises:
            NotImplementedError: Whisper does not support TTS
        """
        raise NotImplementedError(
            "OpenAI Whisper does not support text-to-speech synthesis. "
            "Use a TTS service like ElevenLabs, Azure Speech, or Deepgram."
        )

    def detect_language(self, audio_path: Union[str, Path]) -> str:
        """
        Detect the language spoken in audio file.

        Args:
            audio_path: Path to audio file

        Returns:
            ISO-639-1 language code (e.g., 'en', 'es', 'fr')

        Raises:
            WhisperValidationError: If audio file is invalid
            WhisperAPIError: If detection fails

        Example:
            >>> whisper = Whisper(api_key="sk-...")
            >>> lang = whisper.detect_language("audio.mp3")
            >>> print(lang)  # 'en'
        """
        # Use verbose_json format to get language information
        result = self.transcribe(audio_path, response_format="verbose_json")

        if isinstance(result, dict):
            language = result.get('language', 'unknown')
            logger.info(f"Detected language: {language}")
            return language

        return 'unknown'

    def is_available(self) -> bool:
        """
        Check if the Whisper API is available and credentials are valid.

        Returns:
            True if API is accessible, False otherwise

        Example:
            >>> whisper = Whisper(api_key="sk-...")
            >>> if whisper.is_available():
            ...     print("Service is ready")
        """
        try:
            # Make a simple API call to verify availability
            url = f"{self.base_url.replace('/v1', '')}/v1/models"
            response = self.session.get(url, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Availability check failed: {e}")
            return False

    def get_info(self) -> Dict[str, Any]:
        """
        Get information about the model and its capabilities.

        Returns:
            Dictionary containing model information

        Example:
            >>> whisper = Whisper(api_key="sk-...")
            >>> info = whisper.get_info()
            >>> print(info['model'])
        """
        return {
            'name': self.name,
            'model': self.model,
            'model_type': self.model_type,
            'provider': 'OpenAI',
            'supported_formats': self.SUPPORTED_FORMATS,
            'max_file_size_mb': self.MAX_FILE_SIZE / 1024 / 1024,
            'capabilities': [
                'transcription',
                'translation',
                'language_detection',
                'timestamps',
                'multiple_formats'
            ],
            'supported_languages': [
                'en', 'zh', 'de', 'es', 'ru', 'ko', 'fr', 'ja', 'pt', 'tr',
                'pl', 'ca', 'nl', 'ar', 'sv', 'it', 'id', 'hi', 'fi', 'vi',
                'he', 'uk', 'el', 'ms', 'cs', 'ro', 'da', 'hu', 'ta', 'no',
                'th', 'ur', 'hr', 'bg', 'lt', 'la', 'mi', 'ml', 'cy', 'sk',
                'te', 'fa', 'lv', 'bn', 'sr', 'az', 'sl', 'kn', 'et', 'mk',
                'br', 'eu', 'is', 'hy', 'ne', 'mn', 'bs', 'kk', 'sq', 'sw',
                'gl', 'mr', 'pa', 'si', 'km', 'sn', 'yo', 'so', 'af', 'oc',
                'ka', 'be', 'tg', 'sd', 'gu', 'am', 'yi', 'lo', 'uz', 'fo',
                'ht', 'ps', 'tk', 'nn', 'mt', 'sa', 'lb', 'my', 'bo', 'tl',
                'mg', 'as', 'tt', 'haw', 'ln', 'ha', 'ba', 'jw', 'su'
            ],
            'api_version': self.API_VERSION,
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
        return f"Whisper(model='{self.model}', type='{self.model_type}')"


if __name__ == "__main__":
    # Example usage
    try:
        model = Whisper()
        print(f"Whisper model initialized: {model}")
        print(f"Available: {model.is_available()}")

        info = model.get_info()
        print(f"\nModel Info:")
        print(f"  Name: {info['name']}")
        print(f"  Type: {info['model_type']}")
        print(f"  Supported formats: {', '.join(info['supported_formats'])}")
        print(f"  Max file size: {info['max_file_size_mb']}MB")
    except WhisperAuthenticationError as e:
        print(f"Authentication error: {e}")
    except Exception as e:
        print(f"Error: {e}")
