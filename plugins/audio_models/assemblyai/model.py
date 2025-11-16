"""
AssemblyAI - Advanced Speech-to-Text API Integration

This module provides a production-quality integration with AssemblyAI's
speech-to-text API, including support for transcription, speaker diarization,
auto-chapters, content moderation, and sentiment analysis.
"""

import os
import logging
import time
import json
from typing import Optional, Dict, Any, List, Union
from pathlib import Path
import requests
from enum import Enum

# Configure logging
logger = logging.getLogger(__name__)


class TranscriptStatus(Enum):
    """Enum for transcript processing status"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


class AssemblyAIError(Exception):
    """Base exception for AssemblyAI errors"""
    pass


class AssemblyAIAPIError(AssemblyAIError):
    """Exception raised for API-related errors"""
    pass


class AssemblyAIAuthenticationError(AssemblyAIError):
    """Exception raised for authentication failures"""
    pass


class AssemblyAIValidationError(AssemblyAIError):
    """Exception raised for validation errors"""
    pass


class AssemblyAI:
    """
    AssemblyAI - Advanced Speech Recognition with AI Features

    This class provides a comprehensive interface to AssemblyAI's API,
    supporting transcription with advanced features like speaker diarization,
    auto-chapters, sentiment analysis, and content moderation.

    Attributes:
        api_key (str): AssemblyAI API key
        model_type (str): Type of model (speech-to-text)
        name (str): Service name
        base_url (str): API base URL
    """

    SUPPORTED_FORMATS = ['.mp3', '.mp4', '.wav', '.flac', '.ogg', '.webm', '.m4a', '.aac']
    MAX_FILE_SIZE = 5 * 1024 * 1024 * 1024  # 5 GB
    DEFAULT_LANGUAGE = "en"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.assemblyai.com/v2",
        timeout: int = 300,
        max_retries: int = 3,
        poll_interval: int = 3
    ):
        """
        Initialize AssemblyAI client.

        Args:
            api_key: AssemblyAI API key. If not provided, looks for ASSEMBLYAI_API_KEY
            base_url: API base URL (default: https://api.assemblyai.com/v2)
            timeout: Request timeout in seconds (default: 300)
            max_retries: Maximum retry attempts (default: 3)
            poll_interval: Polling interval for transcript status (default: 3 seconds)

        Raises:
            AssemblyAIAuthenticationError: If no API key is provided
        """
        self.api_key = api_key or os.getenv('ASSEMBLYAI_API_KEY')
        if not self.api_key:
            raise AssemblyAIAuthenticationError(
                "API key required. Provide via api_key parameter or ASSEMBLYAI_API_KEY environment variable"
            )

        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.poll_interval = poll_interval
        self.model_type = "speech-to-text"
        self.name = "AssemblyAI"

        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': self.api_key,
            'Content-Type': 'application/json'
        })

        logger.info("Initialized AssemblyAI client")

    def _validate_audio_file(self, audio_path: Union[str, Path]) -> Path:
        """
        Validate audio file exists and meets requirements.

        Args:
            audio_path: Path to audio file

        Returns:
            Path object for validated file

        Raises:
            AssemblyAIValidationError: If file is invalid
        """
        path = Path(audio_path)

        if not path.exists():
            raise AssemblyAIValidationError(f"Audio file not found: {audio_path}")

        if not path.is_file():
            raise AssemblyAIValidationError(f"Path is not a file: {audio_path}")

        if path.suffix.lower() not in self.SUPPORTED_FORMATS:
            raise AssemblyAIValidationError(
                f"Unsupported format: {path.suffix}. Supported: {', '.join(self.SUPPORTED_FORMATS)}"
            )

        file_size = path.stat().st_size
        if file_size == 0:
            raise AssemblyAIValidationError("Audio file is empty")

        if file_size > self.MAX_FILE_SIZE:
            raise AssemblyAIValidationError(
                f"File too large: {file_size / 1024 / 1024 / 1024:.2f}GB. Maximum: 5GB"
            )

        return path

    def _upload_file(self, audio_path: Path) -> str:
        """
        Upload audio file to AssemblyAI.

        Args:
            audio_path: Path to audio file

        Returns:
            Upload URL

        Raises:
            AssemblyAIAPIError: If upload fails
        """
        upload_url = f"{self.base_url}/upload"

        logger.info(f"Uploading file: {audio_path.name}")

        try:
            with open(audio_path, 'rb') as audio_file:
                response = self.session.post(
                    upload_url,
                    headers={'Authorization': self.api_key},
                    data=audio_file,
                    timeout=self.timeout
                )

            if response.status_code == 200:
                result = response.json()
                upload_url = result.get('upload_url')
                logger.info(f"File uploaded successfully")
                return upload_url
            else:
                raise AssemblyAIAPIError(f"Upload failed: {response.text}")

        except requests.exceptions.RequestException as e:
            raise AssemblyAIAPIError(f"Upload failed: {str(e)}")

    def _submit_transcription(
        self,
        audio_url: str,
        language_code: Optional[str] = None,
        speaker_labels: bool = False,
        auto_chapters: bool = False,
        sentiment_analysis: bool = False,
        entity_detection: bool = False,
        content_safety: bool = False,
        auto_highlights: bool = False,
        punctuate: bool = True,
        format_text: bool = True
    ) -> str:
        """
        Submit transcription request.

        Args:
            audio_url: URL of audio file (local upload URL or public URL)
            language_code: Language code (e.g., 'en', 'es'). Auto-detected if None
            speaker_labels: Enable speaker diarization
            auto_chapters: Enable auto chapter detection
            sentiment_analysis: Enable sentiment analysis
            entity_detection: Enable entity detection
            content_safety: Enable content moderation
            auto_highlights: Enable auto highlights
            punctuate: Enable punctuation
            format_text: Enable text formatting

        Returns:
            Transcript ID

        Raises:
            AssemblyAIAPIError: If submission fails
        """
        endpoint = f"{self.base_url}/transcript"

        data = {
            'audio_url': audio_url,
            'speaker_labels': speaker_labels,
            'auto_chapters': auto_chapters,
            'sentiment_analysis': sentiment_analysis,
            'entity_detection': entity_detection,
            'content_safety': content_safety,
            'auto_highlights': auto_highlights,
            'punctuate': punctuate,
            'format_text': format_text
        }

        if language_code:
            data['language_code'] = language_code

        try:
            response = self.session.post(
                endpoint,
                json=data,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                transcript_id = result.get('id')
                logger.info(f"Transcription submitted: {transcript_id}")
                return transcript_id
            elif response.status_code == 401:
                raise AssemblyAIAuthenticationError("Invalid API key")
            else:
                raise AssemblyAIAPIError(f"Submission failed: {response.text}")

        except requests.exceptions.RequestException as e:
            raise AssemblyAIAPIError(f"Submission failed: {str(e)}")

    def _poll_transcript(self, transcript_id: str) -> Dict[str, Any]:
        """
        Poll for transcript completion.

        Args:
            transcript_id: Transcript ID to poll

        Returns:
            Completed transcript data

        Raises:
            AssemblyAIAPIError: If polling fails or transcript errors
        """
        endpoint = f"{self.base_url}/transcript/{transcript_id}"

        logger.info(f"Polling for transcript: {transcript_id}")

        while True:
            try:
                response = self.session.get(endpoint, timeout=30)

                if response.status_code == 200:
                    result = response.json()
                    status = result.get('status')

                    if status == TranscriptStatus.COMPLETED.value:
                        logger.info(f"Transcription complete")
                        return result
                    elif status == TranscriptStatus.ERROR.value:
                        error = result.get('error', 'Unknown error')
                        raise AssemblyAIAPIError(f"Transcription failed: {error}")
                    else:
                        logger.debug(f"Status: {status}, waiting...")
                        time.sleep(self.poll_interval)
                else:
                    raise AssemblyAIAPIError(f"Polling failed: {response.text}")

            except requests.exceptions.RequestException as e:
                raise AssemblyAIAPIError(f"Polling failed: {str(e)}")

    def transcribe(
        self,
        audio_path: Union[str, Path, None] = None,
        audio_url: Optional[str] = None,
        language: Optional[str] = None,
        speaker_labels: bool = False,
        auto_chapters: bool = False,
        sentiment_analysis: bool = False,
        entity_detection: bool = False,
        content_safety: bool = False,
        return_full_response: bool = False
    ) -> Union[str, Dict[str, Any]]:
        """
        Transcribe audio file or URL to text.

        Args:
            audio_path: Path to local audio file (either this or audio_url required)
            audio_url: Public URL to audio file (either this or audio_path required)
            language: Language code (e.g., 'en', 'es'). Auto-detected if None
            speaker_labels: Enable speaker diarization
            auto_chapters: Enable auto chapter detection
            sentiment_analysis: Enable sentiment analysis
            entity_detection: Enable entity detection
            content_safety: Enable content moderation
            return_full_response: Return full response with metadata

        Returns:
            Transcription text or full response dictionary

        Raises:
            AssemblyAIValidationError: If inputs are invalid
            AssemblyAIAPIError: If transcription fails

        Example:
            >>> aai = AssemblyAI(api_key="your-key")
            >>> text = aai.transcribe("audio.mp3", speaker_labels=True)
            >>> print(text)
        """
        if not audio_path and not audio_url:
            raise AssemblyAIValidationError("Either audio_path or audio_url must be provided")

        # Upload file if local path provided
        if audio_path:
            path = self._validate_audio_file(audio_path)
            audio_url = self._upload_file(path)

        # Submit transcription
        transcript_id = self._submit_transcription(
            audio_url=audio_url,
            language_code=language,
            speaker_labels=speaker_labels,
            auto_chapters=auto_chapters,
            sentiment_analysis=sentiment_analysis,
            entity_detection=entity_detection,
            content_safety=content_safety
        )

        # Poll for completion
        result = self._poll_transcript(transcript_id)

        if return_full_response:
            return result

        text = result.get('text', '')
        logger.info(f"Transcription: {len(text)} characters")
        return text

    def synthesize(self, text: str, voice: str = "default") -> bytes:
        """
        AssemblyAI does not provide text-to-speech synthesis.
        This method is included for interface compatibility.

        Args:
            text: Text to synthesize
            voice: Voice name (not used)

        Returns:
            Empty bytes

        Raises:
            NotImplementedError: AssemblyAI does not support TTS
        """
        raise NotImplementedError(
            "AssemblyAI does not support text-to-speech synthesis. "
            "Use a TTS-specific service like ElevenLabs or Azure Speech."
        )

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
            AssemblyAIValidationError: If inputs are invalid
            AssemblyAIAPIError: If detection fails

        Example:
            >>> aai = AssemblyAI(api_key="your-key")
            >>> lang = aai.detect_language("audio.mp3")
            >>> print(lang)  # 'en'
        """
        # AssemblyAI automatically detects language
        result = self.transcribe(
            audio_path=audio_path,
            audio_url=audio_url,
            return_full_response=True
        )

        if isinstance(result, dict):
            language = result.get('language_code', 'en')
            confidence = result.get('language_confidence', 0.0)
            logger.info(f"Detected language: {language} (confidence: {confidence:.2f})")
            return language

        return 'en'

    def get_transcript(self, transcript_id: str) -> Dict[str, Any]:
        """
        Get transcript by ID.

        Args:
            transcript_id: Transcript ID

        Returns:
            Transcript data

        Raises:
            AssemblyAIAPIError: If retrieval fails

        Example:
            >>> aai = AssemblyAI(api_key="your-key")
            >>> transcript = aai.get_transcript("transcript-id")
        """
        endpoint = f"{self.base_url}/transcript/{transcript_id}"

        try:
            response = self.session.get(endpoint, timeout=30)

            if response.status_code == 200:
                return response.json()
            else:
                raise AssemblyAIAPIError(f"Failed to get transcript: {response.text}")

        except requests.exceptions.RequestException as e:
            raise AssemblyAIAPIError(f"Request failed: {str(e)}")

    def list_transcripts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        List recent transcripts.

        Args:
            limit: Maximum number of transcripts to return

        Returns:
            List of transcript data dictionaries

        Raises:
            AssemblyAIAPIError: If request fails
        """
        endpoint = f"{self.base_url}/transcript"

        try:
            response = self.session.get(
                endpoint,
                params={'limit': limit},
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                return result.get('transcripts', [])
            else:
                raise AssemblyAIAPIError(f"Failed to list transcripts: {response.text}")

        except requests.exceptions.RequestException as e:
            raise AssemblyAIAPIError(f"Request failed: {str(e)}")

    def is_available(self) -> bool:
        """
        Check if AssemblyAI API is available.

        Returns:
            True if service is accessible, False otherwise

        Example:
            >>> aai = AssemblyAI(api_key="your-key")
            >>> if aai.is_available():
            ...     print("Service is ready")
        """
        try:
            # Try to list transcripts to verify API access
            endpoint = f"{self.base_url}/transcript"
            response = self.session.get(endpoint, params={'limit': 1}, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Availability check failed: {e}")
            return False

    def get_info(self) -> Dict[str, Any]:
        """
        Get information about AssemblyAI service.

        Returns:
            Dictionary with service information

        Example:
            >>> aai = AssemblyAI(api_key="your-key")
            >>> info = aai.get_info()
            >>> print(info['name'])
        """
        return {
            'name': self.name,
            'model_type': self.model_type,
            'provider': 'AssemblyAI',
            'supported_formats': self.SUPPORTED_FORMATS,
            'max_file_size_gb': self.MAX_FILE_SIZE / 1024 / 1024 / 1024,
            'capabilities': [
                'transcription',
                'speaker_diarization',
                'auto_chapters',
                'sentiment_analysis',
                'entity_detection',
                'content_moderation',
                'auto_highlights',
                'language_detection',
                'pii_redaction',
                'summarization'
            ],
            'supported_languages': [
                'en', 'es', 'fr', 'de', 'it', 'pt', 'nl', 'hi', 'ja',
                'zh', 'fi', 'ko', 'pl', 'ru', 'tr', 'uk', 'vi'
            ],
            'features': {
                'speaker_labels': 'Identify different speakers in audio',
                'auto_chapters': 'Automatically segment and summarize content',
                'sentiment_analysis': 'Analyze sentiment of transcribed text',
                'entity_detection': 'Detect and classify entities in text',
                'content_safety': 'Detect sensitive content',
                'auto_highlights': 'Extract key phrases and highlights',
                'pii_redaction': 'Redact personally identifiable information',
                'summarization': 'Generate summaries of transcripts'
            },
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
        return f"AssemblyAI(type='{self.model_type}')"


if __name__ == "__main__":
    # Example usage
    try:
        model = AssemblyAI()
        print(f"AssemblyAI initialized: {model}")
        print(f"Available: {model.is_available()}")

        info = model.get_info()
        print(f"\nService Info:")
        print(f"  Name: {info['name']}")
        print(f"  Type: {info['model_type']}")
        print(f"  Supported formats: {', '.join(info['supported_formats'])}")
        print(f"  Max file size: {info['max_file_size_gb']}GB")
        print(f"  Capabilities: {len(info['capabilities'])} features")
    except AssemblyAIAuthenticationError as e:
        print(f"Authentication error: {e}")
    except Exception as e:
        print(f"Error: {e}")
