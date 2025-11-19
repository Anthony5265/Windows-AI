"""
Coqui TTS - Open-Source Text-to-Speech Integration

This module provides a production-quality integration with Coqui TTS,
an open-source deep learning toolkit for Text-to-Speech with support
for multiple languages, voices, and advanced voice cloning capabilities.
"""

import os
import logging
import json
import numpy as np
from typing import Optional, Dict, Any, List, Union
from pathlib import Path
import warnings

# Configure logging
logger = logging.getLogger(__name__)


class CoquiTTSError(Exception):
    """Base exception for Coqui TTS errors"""
    pass


class CoquiTTSModelError(CoquiTTSError):
    """Exception raised for model loading/inference errors"""
    pass


class CoquiTTSValidationError(CoquiTTSError):
    """Exception raised for validation errors"""
    pass


class CoquiTTSConfigurationError(CoquiTTSError):
    """Exception raised for configuration errors"""
    pass


class CoquiTTS:
    """
    Coqui TTS - Open-Source Multi-Speaker Text-to-Speech

    This class provides a comprehensive interface to Coqui TTS library,
    supporting high-quality text-to-speech synthesis with multiple models,
    languages, voice cloning, and speaker embeddings.

    Attributes:
        model_type (str): Type of model (text-to-speech)
        name (str): Service name
        model_name (str): TTS model name
        vocoder_name (str): Vocoder model name
        device (str): Computing device (cpu/cuda)
    """

    # Popular pre-trained models
    MODELS = {
        'tts_models/en/ljspeech/tacotron2-DDC': 'English single speaker (LJSpeech)',
        'tts_models/en/ljspeech/glow-tts': 'English fast synthesis (Glow-TTS)',
        'tts_models/en/ljspeech/vits': 'English high quality (VITS)',
        'tts_models/en/vctk/vits': 'English multi-speaker (VCTK)',
        'tts_models/en/jenny/jenny': 'English high quality (Jenny)',
        'tts_models/multilingual/multi-dataset/your_tts': 'Multilingual with voice cloning',
        'tts_models/multilingual/multi-dataset/xtts_v2': 'Multilingual XTTS v2',
    }

    SUPPORTED_LANGUAGES = [
        'en', 'es', 'fr', 'de', 'it', 'pt', 'pl', 'tr', 'ru', 'nl',
        'cs', 'ar', 'zh-cn', 'ja', 'ko', 'hu', 'hi'
    ]

    def __init__(
        self,
        model_name: Optional[str] = None,
        vocoder_name: Optional[str] = None,
        device: str = "cpu",
        use_cuda: bool = False,
        speakers_file: Optional[str] = None,
        language: str = "en",
        gpu_id: int = 0
    ):
        """
        Initialize Coqui TTS model.

        Args:
            model_name: TTS model name or path. Uses default if None
            vocoder_name: Vocoder model name or path (optional)
            device: Computing device ('cpu' or 'cuda')
            use_cuda: Enable CUDA acceleration if available
            speakers_file: Path to speakers JSON file for multi-speaker models
            language: Default language code
            gpu_id: GPU device ID to use

        Raises:
            CoquiTTSConfigurationError: If configuration is invalid
        """
        self.model_type = "text-to-speech"
        self.name = "Coqui TTS"
        self.language = language
        self.gpu_id = gpu_id

        # Lazy import TTS to avoid import errors if not installed
        self.tts = None
        self.model = None
        self.vocoder = None
        self.synthesizer = None

        # Determine device
        if use_cuda:
            try:
                import torch
                self.device = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                logger.warning("PyTorch not available, using CPU")
                self.device = "cpu"
        else:
            self.device = device

        # Model configuration
        self.model_name = model_name or 'tts_models/en/ljspeech/vits'
        self.vocoder_name = vocoder_name
        self.speakers_file = speakers_file

        # Speaker settings
        self.available_speakers = []
        self.available_languages = []

        logger.info(f"Initialized Coqui TTS with model: {self.model_name}")
        logger.info(f"Device: {self.device}")

    def _load_model(self):
        """
        Lazy load the TTS model.

        Raises:
            CoquiTTSModelError: If model loading fails
        """
        if self.tts is not None:
            return

        try:
            from TTS.api import TTS

            logger.info(f"Loading model: {self.model_name}")

            # Initialize TTS
            self.tts = TTS(
                model_name=self.model_name,
                vocoder_name=self.vocoder_name,
                gpu=(self.device == "cuda")
            )

            # Get available speakers and languages
            if hasattr(self.tts, 'speakers') and self.tts.speakers:
                self.available_speakers = self.tts.speakers
                logger.info(f"Available speakers: {len(self.available_speakers)}")

            if hasattr(self.tts, 'languages') and self.tts.languages:
                self.available_languages = self.tts.languages
                logger.info(f"Available languages: {len(self.available_languages)}")

            logger.info("Model loaded successfully")

        except ImportError:
            raise CoquiTTSModelError(
                "TTS library not installed. Install with: pip install TTS"
            )
        except Exception as e:
            raise CoquiTTSModelError(f"Failed to load model: {str(e)}")

    def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        speaker: Optional[str] = None,
        language: Optional[str] = None,
        speaker_wav: Optional[str] = None,
        emotion: Optional[str] = None,
        speed: float = 1.0
    ) -> bytes:
        """
        Synthesize speech from text.

        Args:
            text: Text to synthesize
            voice: Voice name (alias for speaker)
            speaker: Speaker name for multi-speaker models
            language: Language code (overrides default)
            speaker_wav: Path to reference audio for voice cloning
            emotion: Emotion style (if supported by model)
            speed: Speech speed multiplier (default: 1.0)

        Returns:
            Audio data as bytes (WAV format)

        Raises:
            CoquiTTSValidationError: If inputs are invalid
            CoquiTTSModelError: If synthesis fails

        Example:
            >>> tts = CoquiTTS()
            >>> audio = tts.synthesize("Hello, world!", speaker="p273")
            >>> with open("output.wav", "wb") as f:
            ...     f.write(audio)
        """
        if not text or not text.strip():
            raise CoquiTTSValidationError("Text cannot be empty")

        self._load_model()

        # Use voice parameter as speaker if provided
        speaker = speaker or voice
        lang = language or self.language

        logger.info(f"Synthesizing: {len(text)} characters")
        if speaker:
            logger.info(f"Speaker: {speaker}")
        if lang:
            logger.info(f"Language: {lang}")

        try:
            # Prepare synthesis arguments
            kwargs = {}

            if speaker and speaker in self.available_speakers:
                kwargs['speaker'] = speaker
            elif speaker and self.available_speakers:
                logger.warning(f"Speaker '{speaker}' not found, using default")

            if lang and lang in self.available_languages:
                kwargs['language'] = lang

            if speaker_wav and Path(speaker_wav).exists():
                kwargs['speaker_wav'] = speaker_wav
                logger.info(f"Using speaker reference: {speaker_wav}")

            if speed != 1.0:
                kwargs['speed'] = speed

            # Synthesize to file
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                tmp_path = tmp_file.name

            self.tts.tts_to_file(
                text=text,
                file_path=tmp_path,
                **kwargs
            )

            # Read the generated audio
            with open(tmp_path, 'rb') as f:
                audio_data = f.read()

            # Clean up
            Path(tmp_path).unlink()

            logger.info(f"Synthesis complete: {len(audio_data)} bytes")
            return audio_data

        except Exception as e:
            raise CoquiTTSModelError(f"Synthesis failed: {str(e)}")

    def synthesize_to_file(
        self,
        text: str,
        output_path: Union[str, Path],
        speaker: Optional[str] = None,
        language: Optional[str] = None,
        speaker_wav: Optional[str] = None,
        speed: float = 1.0
    ) -> Path:
        """
        Synthesize speech directly to a file.

        Args:
            text: Text to synthesize
            output_path: Output file path
            speaker: Speaker name
            language: Language code
            speaker_wav: Reference audio for voice cloning
            speed: Speech speed multiplier

        Returns:
            Path to generated audio file

        Raises:
            CoquiTTSValidationError: If inputs are invalid
            CoquiTTSModelError: If synthesis fails
        """
        if not text or not text.strip():
            raise CoquiTTSValidationError("Text cannot be empty")

        self._load_model()

        output_path = Path(output_path)
        lang = language or self.language

        logger.info(f"Synthesizing to file: {output_path}")

        try:
            kwargs = {}

            if speaker and speaker in self.available_speakers:
                kwargs['speaker'] = speaker

            if lang and lang in self.available_languages:
                kwargs['language'] = lang

            if speaker_wav and Path(speaker_wav).exists():
                kwargs['speaker_wav'] = speaker_wav

            if speed != 1.0:
                kwargs['speed'] = speed

            self.tts.tts_to_file(
                text=text,
                file_path=str(output_path),
                **kwargs
            )

            logger.info(f"Audio saved to: {output_path}")
            return output_path

        except Exception as e:
            raise CoquiTTSModelError(f"File synthesis failed: {str(e)}")

    def clone_voice(
        self,
        text: str,
        reference_audio: Union[str, Path],
        language: Optional[str] = None
    ) -> bytes:
        """
        Clone a voice from reference audio and synthesize text.

        Args:
            text: Text to synthesize
            reference_audio: Path to reference audio file
            language: Language code

        Returns:
            Audio data as bytes

        Raises:
            CoquiTTSValidationError: If inputs are invalid
            CoquiTTSModelError: If cloning fails
        """
        ref_path = Path(reference_audio)

        if not ref_path.exists():
            raise CoquiTTSValidationError(f"Reference audio not found: {reference_audio}")

        logger.info(f"Cloning voice from: {ref_path.name}")

        return self.synthesize(
            text=text,
            speaker_wav=str(ref_path),
            language=language
        )

    def transcribe(self, audio_path: str) -> str:
        """
        Coqui TTS does not provide speech-to-text transcription.
        This method is included for interface compatibility.

        Args:
            audio_path: Path to audio file (not used)

        Returns:
            Empty string

        Raises:
            NotImplementedError: Coqui TTS does not support transcription
        """
        raise NotImplementedError(
            "Coqui TTS does not support speech-to-text transcription. "
            "Use a STT service like Whisper, Vosk, or DeepSpeech."
        )

    def detect_language(self, audio_path: str) -> str:
        """
        Coqui TTS does not provide language detection.
        This method is included for interface compatibility.

        Args:
            audio_path: Path to audio file (not used)

        Returns:
            Default language
        """
        logger.warning("Coqui TTS does not support language detection")
        return self.language

    def list_models(self) -> List[str]:
        """
        List available TTS models.

        Returns:
            List of model names
        """
        try:
            from TTS.api import TTS
            return TTS.list_models()
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return list(self.MODELS.keys())

    def get_speakers(self) -> List[str]:
        """
        Get available speakers for the current model.

        Returns:
            List of speaker names
        """
        self._load_model()
        return self.available_speakers

    def get_languages(self) -> List[str]:
        """
        Get available languages for the current model.

        Returns:
            List of language codes
        """
        self._load_model()
        return self.available_languages if self.available_languages else self.SUPPORTED_LANGUAGES

    def is_available(self) -> bool:
        """
        Check if TTS library is available.

        Returns:
            True if library is accessible, False otherwise
        """
        try:
            import TTS
            return True
        except ImportError:
            return False

    def get_info(self) -> Dict[str, Any]:
        """
        Get information about the TTS model.

        Returns:
            Dictionary containing model information
        """
        return {
            'name': self.name,
            'model_type': self.model_type,
            'provider': 'Coqui AI',
            'model_name': self.model_name,
            'vocoder_name': self.vocoder_name,
            'device': self.device,
            'language': self.language,
            'capabilities': [
                'text_to_speech',
                'multi_speaker',
                'multilingual',
                'voice_cloning',
                'custom_models',
                'fine_tuning',
                'local_inference'
            ],
            'supported_languages': self.get_languages(),
            'available_speakers': self.get_speakers() if self.tts else [],
            'models': self.MODELS,
            'open_source': True,
            'license': 'MPL-2.0'
        }

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources"""
        if self.tts is not None:
            # Clean up model resources
            self.tts = None
            self.model = None
            self.vocoder = None

    def __repr__(self) -> str:
        """String representation"""
        return f"CoquiTTS(model='{self.model_name}', device='{self.device}')"


if __name__ == "__main__":
    # Example usage
    try:
        tts = CoquiTTS()
        print(f"Coqui TTS initialized: {tts}")
        print(f"Available: {tts.is_available()}")

        info = tts.get_info()
        print(f"\nModel Info:")
        print(f"  Name: {info['name']}")
        print(f"  Model: {info['model_name']}")
        print(f"  Device: {info['device']}")
        print(f"  Capabilities: {', '.join(info['capabilities'])}")

        # List available models
        print(f"\nAvailable Models:")
        for model, desc in tts.MODELS.items():
            print(f"  - {model}: {desc}")

    except Exception as e:
        print(f"Error: {e}")
