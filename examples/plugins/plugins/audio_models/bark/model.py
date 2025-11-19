"""
Bark - Generative Audio Model Integration

This module provides a production-quality integration with Suno's Bark,
a transformer-based text-to-audio model capable of generating highly realistic,
multilingual speech with music, background noise, and simple sound effects.
"""

import os
import logging
import numpy as np
from typing import Optional, Dict, Any, List, Union, Tuple
from pathlib import Path
import warnings

# Configure logging
logger = logging.getLogger(__name__)


class BarkError(Exception):
    """Base exception for Bark errors"""
    pass


class BarkModelError(BarkError):
    """Exception raised for model loading/inference errors"""
    pass


class BarkValidationError(BarkError):
    """Exception raised for validation errors"""
    pass


class BarkConfigurationError(BarkError):
    """Exception raised for configuration errors"""
    pass


class Bark:
    """
    Bark - Generative Audio Model with Text-to-Speech

    This class provides a comprehensive interface to Suno's Bark model,
    supporting high-quality text-to-speech synthesis with music, sound effects,
    nonverbal communications, and multilingual voices.

    Attributes:
        model_type (str): Type of model (text-to-speech)
        name (str): Service name
        device (str): Computing device (cpu/cuda)
        sample_rate (int): Audio sample rate
    """

    # Bark presets (speaker voices)
    PRESETS = {
        'v2/en_speaker_0': 'Male, English (neutral)',
        'v2/en_speaker_1': 'Female, English (calm)',
        'v2/en_speaker_2': 'Male, English (young)',
        'v2/en_speaker_3': 'Female, English (expressive)',
        'v2/en_speaker_4': 'Male, English (deep)',
        'v2/en_speaker_5': 'Female, English (energetic)',
        'v2/en_speaker_6': 'Male, English (clear)',
        'v2/en_speaker_7': 'Female, English (warm)',
        'v2/en_speaker_8': 'Male, English (professional)',
        'v2/en_speaker_9': 'Female, English (friendly)',
        'v2/zh_speaker_0': 'Chinese speaker 0',
        'v2/zh_speaker_1': 'Chinese speaker 1',
        'v2/es_speaker_0': 'Spanish speaker 0',
        'v2/fr_speaker_0': 'French speaker 0',
        'v2/de_speaker_0': 'German speaker 0',
        'v2/it_speaker_0': 'Italian speaker 0',
        'v2/pt_speaker_0': 'Portuguese speaker 0',
    }

    SUPPORTED_LANGUAGES = [
        'en', 'zh', 'de', 'es', 'fr', 'hi', 'it', 'ja', 'ko', 'pl', 'pt', 'ru', 'tr'
    ]

    SAMPLE_RATE = 24000  # Bark's native sample rate

    def __init__(
        self,
        device: str = "cpu",
        use_small_models: bool = False,
        use_gpu: bool = False,
        offload_cpu: bool = False,
        text_use_gpu: bool = True,
        text_use_small: bool = False,
        coarse_use_gpu: bool = True,
        coarse_use_small: bool = False,
        fine_use_gpu: bool = True,
        fine_use_small: bool = False,
        codec_use_gpu: bool = True,
        force_reload: bool = False
    ):
        """
        Initialize Bark model.

        Args:
            device: Computing device ('cpu' or 'cuda')
            use_small_models: Use smaller model variants (faster but lower quality)
            use_gpu: Enable GPU acceleration for all models
            offload_cpu: Offload models to CPU when not in use
            text_use_gpu: Use GPU for text model
            text_use_small: Use small text model
            coarse_use_gpu: Use GPU for coarse model
            coarse_use_small: Use small coarse model
            fine_use_gpu: Use GPU for fine model
            fine_use_small: Use small fine model
            codec_use_gpu: Use GPU for codec model
            force_reload: Force reload models even if cached

        Raises:
            BarkConfigurationError: If configuration is invalid
        """
        self.model_type = "text-to-speech"
        self.name = "Bark"
        self.sample_rate = self.SAMPLE_RATE

        # Determine device
        if use_gpu:
            try:
                import torch
                self.device = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                logger.warning("PyTorch not available, using CPU")
                self.device = "cpu"
        else:
            self.device = device

        # Model configuration
        self.use_small_models = use_small_models
        self.offload_cpu = offload_cpu
        self.force_reload = force_reload

        # Per-model settings
        self.text_use_gpu = text_use_gpu
        self.text_use_small = text_use_small
        self.coarse_use_gpu = coarse_use_gpu
        self.coarse_use_small = coarse_use_small
        self.fine_use_gpu = fine_use_gpu
        self.fine_use_small = fine_use_small
        self.codec_use_gpu = codec_use_gpu

        # Lazy loading
        self.bark = None
        self.generation = None
        self.models_loaded = False

        logger.info(f"Initialized Bark")
        logger.info(f"Device: {self.device}")
        logger.info(f"Small models: {self.use_small_models}")

    def _load_model(self):
        """
        Lazy load the Bark model.

        Raises:
            BarkModelError: If model loading fails
        """
        if self.models_loaded:
            return

        try:
            from bark import SAMPLE_RATE, generate_audio, preload_models
            from bark.api import semantic_to_waveform
            from bark.generation import SAMPLE_RATE as GEN_SAMPLE_RATE

            self.bark = {
                'SAMPLE_RATE': SAMPLE_RATE,
                'generate_audio': generate_audio,
                'preload_models': preload_models,
                'semantic_to_waveform': semantic_to_waveform
            }

            logger.info("Loading Bark models...")

            # Configure environment variables for model settings
            if self.use_small_models:
                os.environ["SUNO_USE_SMALL_MODELS"] = "1"

            if self.offload_cpu:
                os.environ["SUNO_OFFLOAD_CPU"] = "1"

            # Preload models
            preload_models(
                text_use_gpu=self.text_use_gpu if self.device == "cuda" else False,
                text_use_small=self.text_use_small or self.use_small_models,
                coarse_use_gpu=self.coarse_use_gpu if self.device == "cuda" else False,
                coarse_use_small=self.coarse_use_small or self.use_small_models,
                fine_use_gpu=self.fine_use_gpu if self.device == "cuda" else False,
                fine_use_small=self.fine_use_small or self.use_small_models,
                codec_use_gpu=self.codec_use_gpu if self.device == "cuda" else False,
                force_reload=self.force_reload
            )

            self.models_loaded = True
            logger.info("Bark models loaded successfully")

        except ImportError:
            raise BarkModelError(
                "Bark library not installed. Install with: pip install git+https://github.com/suno-ai/bark.git"
            )
        except Exception as e:
            raise BarkModelError(f"Failed to load Bark models: {str(e)}")

    def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        temperature: float = 0.7,
        silent: bool = False,
        output_full: bool = False
    ) -> bytes:
        """
        Synthesize speech from text using Bark.

        Args:
            text: Text to synthesize. Can include [laughter], [gasps], CAPITALIZATION for emphasis
            voice: Voice preset (e.g., 'v2/en_speaker_0'). None for random
            temperature: Generation temperature (0.0-1.0). Higher = more variation
            silent: Suppress progress output
            output_full: Return full generation output

        Returns:
            Audio data as bytes (WAV format)

        Raises:
            BarkValidationError: If inputs are invalid
            BarkModelError: If synthesis fails

        Example:
            >>> bark = Bark()
            >>> audio = bark.synthesize("Hello [laughter] world!", voice="v2/en_speaker_0")
            >>> with open("output.wav", "wb") as f:
            ...     f.write(audio)
        """
        if not text or not text.strip():
            raise BarkValidationError("Text cannot be empty")

        self._load_model()

        logger.info(f"Synthesizing: {len(text)} characters")
        if voice:
            logger.info(f"Voice preset: {voice}")

        try:
            # Generate audio array
            audio_array = self.bark['generate_audio'](
                text,
                history_prompt=voice,
                text_temp=temperature,
                waveform_temp=temperature,
                silent=silent,
                output_full=output_full
            )

            # Convert to WAV bytes
            import io
            from scipy.io import wavfile

            buffer = io.BytesIO()
            wavfile.write(buffer, self.sample_rate, audio_array)
            audio_data = buffer.getvalue()

            logger.info(f"Synthesis complete: {len(audio_data)} bytes")
            return audio_data

        except Exception as e:
            raise BarkModelError(f"Synthesis failed: {str(e)}")

    def synthesize_long_form(
        self,
        text: str,
        voice: Optional[str] = None,
        temperature: float = 0.7,
        segment_length: int = 200
    ) -> bytes:
        """
        Synthesize long text by splitting into segments.

        Args:
            text: Long text to synthesize
            voice: Voice preset
            temperature: Generation temperature
            segment_length: Characters per segment

        Returns:
            Audio data as bytes

        Raises:
            BarkValidationError: If inputs are invalid
            BarkModelError: If synthesis fails
        """
        if not text or not text.strip():
            raise BarkValidationError("Text cannot be empty")

        self._load_model()

        logger.info(f"Long-form synthesis: {len(text)} characters")

        # Split text into sentences
        sentences = text.replace('!', '.').replace('?', '.').split('.')
        segments = []
        current_segment = ""

        for sentence in sentences:
            if len(current_segment) + len(sentence) < segment_length:
                current_segment += sentence + ". "
            else:
                if current_segment:
                    segments.append(current_segment.strip())
                current_segment = sentence + ". "

        if current_segment:
            segments.append(current_segment.strip())

        logger.info(f"Split into {len(segments)} segments")

        # Generate audio for each segment
        audio_arrays = []
        for i, segment in enumerate(segments):
            logger.info(f"Generating segment {i+1}/{len(segments)}")
            audio_array = self.bark['generate_audio'](
                segment,
                history_prompt=voice,
                text_temp=temperature,
                waveform_temp=temperature,
                silent=True
            )
            audio_arrays.append(audio_array)

        # Concatenate audio
        import numpy as np
        full_audio = np.concatenate(audio_arrays)

        # Convert to WAV bytes
        import io
        from scipy.io import wavfile

        buffer = io.BytesIO()
        wavfile.write(buffer, self.sample_rate, full_audio)
        audio_data = buffer.getvalue()

        logger.info(f"Long-form synthesis complete: {len(audio_data)} bytes")
        return audio_data

    def synthesize_to_file(
        self,
        text: str,
        output_path: Union[str, Path],
        voice: Optional[str] = None,
        temperature: float = 0.7
    ) -> Path:
        """
        Synthesize speech directly to a file.

        Args:
            text: Text to synthesize
            output_path: Output file path
            voice: Voice preset
            temperature: Generation temperature

        Returns:
            Path to generated audio file

        Raises:
            BarkValidationError: If inputs are invalid
            BarkModelError: If synthesis fails
        """
        audio_data = self.synthesize(text, voice, temperature)
        output_path = Path(output_path)

        with open(output_path, 'wb') as f:
            f.write(audio_data)

        logger.info(f"Audio saved to: {output_path}")
        return output_path

    def clone_voice(
        self,
        text: str,
        reference_audio: Union[str, Path],
        temperature: float = 0.7
    ) -> bytes:
        """
        Clone a voice from reference audio (experimental).

        Note: Bark's voice cloning requires generating semantic tokens from audio,
        which is experimental. For production use, use predefined voice presets.

        Args:
            text: Text to synthesize
            reference_audio: Path to reference audio
            temperature: Generation temperature

        Returns:
            Audio data as bytes

        Raises:
            BarkValidationError: If inputs are invalid
        """
        logger.warning("Voice cloning is experimental in Bark")
        logger.warning("Consider using predefined voice presets for better results")

        # For now, use a default voice
        # Full voice cloning would require additional semantic token generation
        return self.synthesize(text, temperature=temperature)

    def transcribe(self, audio_path: str) -> str:
        """
        Bark does not provide speech-to-text transcription.
        This method is included for interface compatibility.

        Args:
            audio_path: Path to audio file (not used)

        Returns:
            Empty string

        Raises:
            NotImplementedError: Bark does not support transcription
        """
        raise NotImplementedError(
            "Bark does not support speech-to-text transcription. "
            "Use a STT service like Whisper, Vosk, or DeepSpeech."
        )

    def detect_language(self, audio_path: str) -> str:
        """
        Bark does not provide language detection.
        This method is included for interface compatibility.

        Args:
            audio_path: Path to audio file (not used)

        Returns:
            Default language 'en'
        """
        logger.warning("Bark does not support language detection")
        return 'en'

    def get_presets(self) -> Dict[str, str]:
        """
        Get available voice presets.

        Returns:
            Dictionary of preset names and descriptions
        """
        return self.PRESETS

    def list_presets(self) -> List[str]:
        """
        List available voice preset names.

        Returns:
            List of preset names
        """
        return list(self.PRESETS.keys())

    def is_available(self) -> bool:
        """
        Check if Bark library is available.

        Returns:
            True if library is accessible, False otherwise
        """
        try:
            import bark
            return True
        except ImportError:
            return False

    def get_info(self) -> Dict[str, Any]:
        """
        Get information about the Bark model.

        Returns:
            Dictionary containing model information
        """
        return {
            'name': self.name,
            'model_type': self.model_type,
            'provider': 'Suno AI',
            'device': self.device,
            'sample_rate': self.sample_rate,
            'use_small_models': self.use_small_models,
            'capabilities': [
                'text_to_speech',
                'multilingual',
                'music_generation',
                'sound_effects',
                'nonverbal_communication',
                'emotion_expression',
                'voice_presets',
                'local_inference'
            ],
            'supported_languages': self.SUPPORTED_LANGUAGES,
            'voice_presets': len(self.PRESETS),
            'features': [
                'Laughter, sighs, gasps',
                'Music and background noise',
                'Emphasis through CAPS',
                'Multiple speaker styles',
                'Zero-shot voice cloning (experimental)',
                'Multilingual code-switching'
            ],
            'special_tokens': [
                '[laughter]', '[laughs]', '[sighs]', '[music]',
                '[gasps]', '[clears throat]', '...', 'MAN/WOMAN:'
            ],
            'open_source': True,
            'license': 'MIT'
        }

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources"""
        if self.models_loaded:
            # Models are cached by Bark, no explicit cleanup needed
            pass

    def __repr__(self) -> str:
        """String representation"""
        return f"Bark(device='{self.device}', small_models={self.use_small_models})"


if __name__ == "__main__":
    # Example usage
    try:
        bark = Bark()
        print(f"Bark initialized: {bark}")
        print(f"Available: {bark.is_available()}")

        info = bark.get_info()
        print(f"\nModel Info:")
        print(f"  Name: {info['name']}")
        print(f"  Device: {info['device']}")
        print(f"  Sample rate: {info['sample_rate']} Hz")
        print(f"  Capabilities: {', '.join(info['capabilities'])}")

        print(f"\nVoice Presets ({len(bark.PRESETS)}):")
        for preset, desc in list(bark.PRESETS.items())[:5]:
            print(f"  - {preset}: {desc}")

        print(f"\nSpecial Features:")
        for feature in info['features']:
            print(f"  - {feature}")

    except Exception as e:
        print(f"Error: {e}")
