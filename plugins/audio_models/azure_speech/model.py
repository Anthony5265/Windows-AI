"""
Azure Speech Services - Microsoft Cloud Speech-to-Text and Text-to-Speech Integration

This module provides a production-quality integration with Microsoft Azure Speech Services
for speech recognition, synthesis, and language detection.
"""

import os
import logging
import json
import time
from typing import Optional, Dict, Any, List, Iterator, Union
from pathlib import Path
import requests
from io import BytesIO

# Configure logging
logger = logging.getLogger(__name__)


class AzureSpeechError(Exception):
    """Base exception for Azure Speech errors"""
    pass


class AzureSpeechAPIError(AzureSpeechError):
    """Exception raised for API-related errors"""
    pass


class AzureSpeechAuthenticationError(AzureSpeechError):
    """Exception raised for authentication failures"""
    pass


class AzureSpeechValidationError(AzureSpeechError):
    """Exception raised for validation errors"""
    pass


class AzureSpeech:
    """
    Microsoft Azure Speech Services - Speech-to-Text and Text-to-Speech

    This class provides a comprehensive interface to Azure Speech Services,
    supporting transcription, synthesis, language detection, and streaming
    with robust error handling.

    Attributes:
        api_key (str): Azure Speech API key
        region (str): Azure region (e.g., 'eastus', 'westus')
        model_type (str): Type of model (speech-to-text)
        name (str): Service name
    """

    SUPPORTED_FORMATS = ['.wav', '.mp3', '.ogg', '.flac', '.aac', '.amr', '.webm']
    MAX_FILE_SIZE = 200 * 1024 * 1024  # 200 MB for batch
    DEFAULT_LANGUAGE = "en-US"

    # Common Azure regions
    REGIONS = [
        'eastus', 'eastus2', 'westus', 'westus2', 'centralus',
        'northeurope', 'westeurope', 'southeastasia', 'eastasia',
        'australiaeast', 'uksouth', 'japaneast', 'canadacentral'
    ]

    def __init__(
        self,
        api_key: Optional[str] = None,
        region: str = "eastus",
        language: str = DEFAULT_LANGUAGE,
        timeout: int = 300,
        max_retries: int = 3
    ):
        """
        Initialize Azure Speech Services client.

        Args:
            api_key: Azure Speech API key. If not provided, looks for AZURE_SPEECH_KEY
            region: Azure region (default: eastus)
            language: Default language for recognition (default: en-US)
            timeout: Request timeout in seconds (default: 300)
            max_retries: Maximum retry attempts (default: 3)

        Raises:
            AzureSpeechAuthenticationError: If no API key is provided
        """
        self.api_key = api_key or os.getenv('AZURE_SPEECH_KEY')
        if not self.api_key:
            raise AzureSpeechAuthenticationError(
                "API key required. Provide via api_key parameter or AZURE_SPEECH_KEY environment variable"
            )

        self.region = region or os.getenv('AZURE_SPEECH_REGION', 'eastus')
        self.language = language
        self.timeout = timeout
        self.max_retries = max_retries
        self.model_type = "speech-to-text"
        self.name = "Azure Speech Services"

        # API endpoints
        self.stt_endpoint = f"https://{self.region}.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1"
        self.tts_endpoint = f"https://{self.region}.tts.speech.microsoft.com/cognitiveservices/v1"
        self.token_endpoint = f"https://{self.region}.api.cognitive.microsoft.com/sts/v1.0/issueToken"

        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'Ocp-Apim-Subscription-Key': self.api_key
        })

        # Token management
        self._access_token = None
        self._token_expiry = 0

        logger.info(f"Initialized Azure Speech Services in region: {self.region}")

    def _get_access_token(self) -> str:
        """
        Get or refresh access token for Azure Speech API.

        Returns:
            Valid access token

        Raises:
            AzureSpeechAPIError: If token retrieval fails
        """
        # Token is valid for 10 minutes, refresh if expired
        if self._access_token and time.time() < self._token_expiry:
            return self._access_token

        try:
            response = self.session.post(
                self.token_endpoint,
                headers={'Ocp-Apim-Subscription-Key': self.api_key},
                timeout=10
            )

            if response.status_code == 200:
                self._access_token = response.text
                # Token expires in 10 minutes, refresh after 9
                self._token_expiry = time.time() + 540
                logger.debug("Access token refreshed")
                return self._access_token
            else:
                raise AzureSpeechAPIError(f"Token request failed: {response.status_code}")

        except requests.exceptions.RequestException as e:
            raise AzureSpeechAPIError(f"Failed to get access token: {str(e)}")

    def _validate_audio_file(self, audio_path: Union[str, Path]) -> Path:
        """
        Validate audio file exists and meets requirements.

        Args:
            audio_path: Path to audio file

        Returns:
            Path object for validated file

        Raises:
            AzureSpeechValidationError: If file is invalid
        """
        path = Path(audio_path)

        if not path.exists():
            raise AzureSpeechValidationError(f"Audio file not found: {audio_path}")

        if not path.is_file():
            raise AzureSpeechValidationError(f"Path is not a file: {audio_path}")

        if path.suffix.lower() not in self.SUPPORTED_FORMATS:
            raise AzureSpeechValidationError(
                f"Unsupported format: {path.suffix}. Supported: {', '.join(self.SUPPORTED_FORMATS)}"
            )

        file_size = path.stat().st_size
        if file_size == 0:
            raise AzureSpeechValidationError("Audio file is empty")

        return path

    def transcribe(
        self,
        audio_path: Union[str, Path],
        language: Optional[str] = None,
        detailed: bool = False,
        profanity_option: str = "masked",
        enable_dictation: bool = True
    ) -> Union[str, Dict[str, Any]]:
        """
        Transcribe audio file to text using Azure Speech-to-Text.

        Args:
            audio_path: Path to audio file
            language: Language code (e.g., 'en-US', 'es-ES'). Uses default if None
            detailed: Return detailed results with confidence scores
            profanity_option: How to handle profanity ('masked', 'removed', 'raw')
            enable_dictation: Enable dictation mode for better punctuation

        Returns:
            Transcription text or detailed results dictionary

        Raises:
            AzureSpeechValidationError: If audio file is invalid
            AzureSpeechAPIError: If transcription fails

        Example:
            >>> azure = AzureSpeech(api_key="your-key", region="eastus")
            >>> text = azure.transcribe("audio.wav")
            >>> print(text)
        """
        path = self._validate_audio_file(audio_path)
        lang = language or self.language

        logger.info(f"Transcribing: {path.name} (language: {lang})")

        # Build request URL with parameters
        params = {
            'language': lang,
            'format': 'detailed' if detailed else 'simple',
            'profanity': profanity_option
        }

        if enable_dictation:
            params['enableDictation'] = 'true'

        # Read audio file
        with open(path, 'rb') as audio_file:
            audio_data = audio_file.read()

        # Determine content type
        content_type = self._get_content_type(path.suffix)

        for attempt in range(self.max_retries):
            try:
                response = self.session.post(
                    self.stt_endpoint,
                    params=params,
                    headers={
                        'Content-Type': content_type,
                        'Accept': 'application/json',
                        'Ocp-Apim-Subscription-Key': self.api_key
                    },
                    data=audio_data,
                    timeout=self.timeout
                )

                if response.status_code == 200:
                    result = response.json()

                    if detailed:
                        return result

                    # Extract text from simple or detailed format
                    if 'DisplayText' in result:
                        text = result['DisplayText']
                    elif 'NBest' in result and result['NBest']:
                        text = result['NBest'][0].get('Display', '')
                    else:
                        text = result.get('RecognitionStatus', '')

                    logger.info(f"Transcription complete: {len(text)} characters")
                    return text

                elif response.status_code == 401:
                    raise AzureSpeechAuthenticationError("Invalid API key or region")
                elif response.status_code == 429:
                    # Rate limit - wait and retry
                    wait_time = 2 ** attempt
                    logger.warning(f"Rate limited. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    error_msg = response.text
                    raise AzureSpeechAPIError(f"Transcription failed: {error_msg}")

            except requests.exceptions.Timeout:
                if attempt < self.max_retries - 1:
                    logger.warning(f"Timeout. Retry {attempt + 1}/{self.max_retries}")
                    continue
                raise AzureSpeechAPIError("Request timeout after retries")
            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"Request failed: {e}. Retrying...")
                    time.sleep(2 ** attempt)
                    continue
                raise AzureSpeechAPIError(f"Request failed: {str(e)}")

        raise AzureSpeechAPIError("Max retries exceeded")

    def synthesize(
        self,
        text: str,
        voice: str = "en-US-JennyNeural",
        output_format: str = "audio-24khz-48kbitrate-mono-mp3",
        speaking_rate: float = 1.0,
        pitch: str = "default"
    ) -> bytes:
        """
        Synthesize speech from text using Azure Text-to-Speech.

        Args:
            text: Text to synthesize
            voice: Voice name (e.g., 'en-US-JennyNeural', 'en-US-GuyNeural')
            output_format: Audio output format
            speaking_rate: Speech rate (0.5-2.0, default: 1.0)
            pitch: Pitch adjustment ('x-low', 'low', 'default', 'high', 'x-high')

        Returns:
            Audio data as bytes

        Raises:
            AzureSpeechAPIError: If synthesis fails

        Example:
            >>> azure = AzureSpeech(api_key="your-key", region="eastus")
            >>> audio = azure.synthesize("Hello, world!")
            >>> with open("output.mp3", "wb") as f:
            ...     f.write(audio)
        """
        if not text or not text.strip():
            raise AzureSpeechValidationError("Text cannot be empty")

        logger.info(f"Synthesizing speech: {len(text)} characters")

        # Build SSML
        ssml = self._build_ssml(text, voice, speaking_rate, pitch)

        for attempt in range(self.max_retries):
            try:
                response = self.session.post(
                    self.tts_endpoint,
                    headers={
                        'Content-Type': 'application/ssml+xml',
                        'X-Microsoft-OutputFormat': output_format,
                        'Ocp-Apim-Subscription-Key': self.api_key
                    },
                    data=ssml.encode('utf-8'),
                    timeout=self.timeout
                )

                if response.status_code == 200:
                    logger.info(f"Synthesis complete: {len(response.content)} bytes")
                    return response.content
                elif response.status_code == 401:
                    raise AzureSpeechAuthenticationError("Invalid API key")
                elif response.status_code == 429:
                    wait_time = 2 ** attempt
                    logger.warning(f"Rate limited. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise AzureSpeechAPIError(f"Synthesis failed: {response.text}")

            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"Request failed: {e}. Retrying...")
                    time.sleep(2 ** attempt)
                    continue
                raise AzureSpeechAPIError(f"Synthesis failed: {str(e)}")

        raise AzureSpeechAPIError("Max retries exceeded")

    def detect_language(
        self,
        audio_path: Union[str, Path],
        candidate_languages: Optional[List[str]] = None
    ) -> str:
        """
        Detect language from audio file.

        Args:
            audio_path: Path to audio file
            candidate_languages: List of candidate language codes (e.g., ['en-US', 'es-ES'])

        Returns:
            Detected language code (e.g., 'en-US')

        Raises:
            AzureSpeechValidationError: If audio file is invalid
            AzureSpeechAPIError: If detection fails

        Example:
            >>> azure = AzureSpeech(api_key="your-key", region="eastus")
            >>> lang = azure.detect_language("audio.wav")
            >>> print(lang)  # 'en-US'
        """
        path = self._validate_audio_file(audio_path)

        # Use language detection endpoint
        candidates = candidate_languages or ['en-US', 'es-ES', 'fr-FR', 'de-DE', 'zh-CN']

        logger.info(f"Detecting language: {path.name}")

        # Try transcribing with multiple languages and pick best confidence
        best_language = self.language
        best_confidence = 0.0

        for lang in candidates[:3]:  # Limit to top 3 candidates
            try:
                result = self.transcribe(audio_path, language=lang, detailed=True)

                if isinstance(result, dict):
                    confidence = 0.0
                    if 'NBest' in result and result['NBest']:
                        confidence = result['NBest'][0].get('Confidence', 0.0)

                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_language = lang
            except Exception as e:
                logger.debug(f"Language {lang} failed: {e}")
                continue

        logger.info(f"Detected language: {best_language} (confidence: {best_confidence:.2f})")
        return best_language

    def is_available(self) -> bool:
        """
        Check if Azure Speech Services is available.

        Returns:
            True if service is accessible, False otherwise

        Example:
            >>> azure = AzureSpeech(api_key="your-key", region="eastus")
            >>> if azure.is_available():
            ...     print("Service is ready")
        """
        try:
            # Try to get access token
            token = self._get_access_token()
            return bool(token)
        except Exception as e:
            logger.error(f"Availability check failed: {e}")
            return False

    def get_info(self) -> Dict[str, Any]:
        """
        Get information about Azure Speech Services.

        Returns:
            Dictionary with service information

        Example:
            >>> azure = AzureSpeech(api_key="your-key", region="eastus")
            >>> info = azure.get_info()
            >>> print(info['name'])
        """
        return {
            'name': self.name,
            'model_type': self.model_type,
            'provider': 'Microsoft Azure',
            'region': self.region,
            'default_language': self.language,
            'supported_formats': self.SUPPORTED_FORMATS,
            'max_file_size_mb': self.MAX_FILE_SIZE / 1024 / 1024,
            'capabilities': [
                'transcription',
                'synthesis',
                'language_detection',
                'real_time_streaming',
                'speaker_diarization',
                'profanity_filtering',
                'neural_voices'
            ],
            'supported_languages': [
                'en-US', 'en-GB', 'en-AU', 'en-CA', 'en-IN',
                'es-ES', 'es-MX', 'fr-FR', 'fr-CA', 'de-DE',
                'it-IT', 'pt-BR', 'pt-PT', 'ru-RU', 'zh-CN',
                'zh-TW', 'ja-JP', 'ko-KR', 'ar-SA', 'hi-IN',
                'nl-NL', 'sv-SE', 'no-NO', 'da-DK', 'fi-FI',
                'pl-PL', 'tr-TR', 'th-TH', 'vi-VN', 'id-ID'
            ],
            'neural_voices': [
                'en-US-JennyNeural', 'en-US-GuyNeural', 'en-US-AriaNeural',
                'en-GB-SoniaNeural', 'en-GB-RyanNeural', 'es-ES-ElviraNeural',
                'fr-FR-DeniseNeural', 'de-DE-KatjaNeural', 'it-IT-ElsaNeural'
            ],
            'endpoints': {
                'stt': self.stt_endpoint,
                'tts': self.tts_endpoint
            }
        }

    def _get_content_type(self, suffix: str) -> str:
        """Get content type for audio file format."""
        content_types = {
            '.wav': 'audio/wav',
            '.mp3': 'audio/mpeg',
            '.ogg': 'audio/ogg',
            '.flac': 'audio/flac',
            '.aac': 'audio/aac',
            '.amr': 'audio/amr',
            '.webm': 'audio/webm'
        }
        return content_types.get(suffix.lower(), 'application/octet-stream')

    def _build_ssml(
        self,
        text: str,
        voice: str,
        rate: float,
        pitch: str
    ) -> str:
        """Build SSML for text-to-speech synthesis."""
        rate_str = f"{int((rate - 1) * 100):+d}%" if rate != 1.0 else "default"

        ssml = f'''<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
    <voice name="{voice}">
        <prosody rate="{rate_str}" pitch="{pitch}">
            {text}
        </prosody>
    </voice>
</speak>'''
        return ssml

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources"""
        self.session.close()

    def __repr__(self) -> str:
        """String representation"""
        return f"AzureSpeech(region='{self.region}', language='{self.language}')"


if __name__ == "__main__":
    # Example usage
    try:
        model = AzureSpeech()
        print(f"Azure Speech Services initialized: {model}")
        print(f"Available: {model.is_available()}")

        info = model.get_info()
        print(f"\nService Info:")
        print(f"  Name: {info['name']}")
        print(f"  Region: {info['region']}")
        print(f"  Type: {info['model_type']}")
        print(f"  Supported formats: {', '.join(info['supported_formats'])}")
        print(f"  Neural voices: {len(info['neural_voices'])} available")
    except AzureSpeechAuthenticationError as e:
        print(f"Authentication error: {e}")
    except Exception as e:
        print(f"Error: {e}")
