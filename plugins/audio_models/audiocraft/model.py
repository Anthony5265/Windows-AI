"""
AudioCraft - Meta's Audio Generation Platform Integration

This module provides a production-quality integration with Meta's AudioCraft,
a unified platform for audio generation including MusicGen for music,
AudioGen for sound effects, and EnCodec for audio compression.
"""

import os
import logging
import torch
import numpy as np
from typing import Optional, Dict, Any, List, Union
from pathlib import Path
import warnings

# Configure logging
logger = logging.getLogger(__name__)


class AudioCraftError(Exception):
    """Base exception for AudioCraft errors"""
    pass


class AudioCraftModelError(AudioCraftError):
    """Exception raised for model loading/inference errors"""
    pass


class AudioCraftValidationError(AudioCraftError):
    """Exception raised for validation errors"""
    pass


class AudioCraftConfigurationError(AudioCraftError):
    """Exception raised for configuration errors"""
    pass


class AudioCraft:
    """
    AudioCraft - Meta's Unified Audio Generation Platform

    This class provides a comprehensive interface to Meta's AudioCraft library,
    supporting music generation (MusicGen), audio generation (AudioGen),
    and high-quality audio encoding/decoding (EnCodec).

    Attributes:
        model_type (str): Type of model (audio-generation)
        name (str): Service name
        device (str): Computing device (cpu/cuda)
        sample_rate (int): Audio sample rate
    """

    # Available models
    MODELS = {
        'facebook/musicgen-small': 'MusicGen Small (300M parameters, fast)',
        'facebook/musicgen-medium': 'MusicGen Medium (1.5B parameters, balanced)',
        'facebook/musicgen-large': 'MusicGen Large (3.3B parameters, high quality)',
        'facebook/musicgen-melody': 'MusicGen Melody (conditioning on melody)',
        'facebook/audiogen-medium': 'AudioGen Medium (sound effects)',
    }

    GENERATION_TYPES = ['music', 'sound', 'audio']
    SAMPLE_RATE = 32000  # AudioCraft default sample rate

    def __init__(
        self,
        model_name: str = 'facebook/musicgen-small',
        device: Optional[str] = None,
        use_gpu: bool = True,
        cache_dir: Optional[str] = None,
        duration: float = 10.0
    ):
        """
        Initialize AudioCraft model.

        Args:
            model_name: Model name or path
            device: Computing device ('cpu' or 'cuda'). Auto-detect if None
            use_gpu: Enable GPU acceleration if available
            cache_dir: Directory to cache models
            duration: Default generation duration in seconds

        Raises:
            AudioCraftConfigurationError: If configuration is invalid
        """
        self.model_type = "audio-generation"
        self.name = "AudioCraft"
        self.sample_rate = self.SAMPLE_RATE

        # Determine device
        if device is None:
            if use_gpu and torch.cuda.is_available():
                self.device = "cuda"
            else:
                self.device = "cpu"
        else:
            self.device = device

        self.model_name = model_name
        self.cache_dir = cache_dir
        self.default_duration = duration

        # Lazy loading
        self.model = None
        self.processor = None
        self.model_loaded = False

        logger.info(f"Initialized AudioCraft with model: {self.model_name}")
        logger.info(f"Device: {self.device}")

    def _load_model(self):
        """
        Lazy load the AudioCraft model.

        Raises:
            AudioCraftModelError: If model loading fails
        """
        if self.model_loaded:
            return

        try:
            from audiocraft.models import MusicGen, AudioGen

            logger.info(f"Loading AudioCraft model: {self.model_name}")

            # Determine model type
            if 'musicgen' in self.model_name.lower():
                self.model = MusicGen.get_pretrained(
                    self.model_name,
                    device=self.device
                )
                self.generation_type = 'music'
            elif 'audiogen' in self.model_name.lower():
                self.model = AudioGen.get_pretrained(
                    self.model_name,
                    device=self.device
                )
                self.generation_type = 'sound'
            else:
                # Default to MusicGen
                self.model = MusicGen.get_pretrained(
                    self.model_name,
                    device=self.device
                )
                self.generation_type = 'music'

            # Set generation parameters
            self.model.set_generation_params(
                duration=self.default_duration
            )

            self.model_loaded = True
            logger.info(f"AudioCraft model loaded successfully ({self.generation_type})")

        except ImportError:
            raise AudioCraftModelError(
                "AudioCraft library not installed. Install with: pip install audiocraft"
            )
        except Exception as e:
            raise AudioCraftModelError(f"Failed to load model: {str(e)}")

    def generate(
        self,
        prompt: Union[str, List[str]],
        duration: Optional[float] = None,
        temperature: float = 1.0,
        top_k: int = 250,
        top_p: float = 0.0,
        cfg_coef: float = 3.0,
        two_step_cfg: bool = False
    ) -> Union[np.ndarray, List[np.ndarray]]:
        """
        Generate audio from text prompt(s).

        Args:
            prompt: Text description(s) of audio to generate
            duration: Generation duration in seconds (uses default if None)
            temperature: Sampling temperature (higher = more random)
            top_k: Top-k filtering parameter
            top_p: Top-p (nucleus) sampling parameter
            cfg_coef: Classifier-free guidance coefficient (higher = follow prompt more)
            two_step_cfg: Use two-step classifier-free guidance

        Returns:
            Generated audio array(s) as numpy arrays

        Raises:
            AudioCraftValidationError: If inputs are invalid
            AudioCraftModelError: If generation fails

        Example:
            >>> audiocraft = AudioCraft()
            >>> audio = audiocraft.generate("upbeat electronic dance music")
            >>> audiocraft.save_audio(audio, "output.wav")
        """
        if not prompt or (isinstance(prompt, str) and not prompt.strip()):
            raise AudioCraftValidationError("Prompt cannot be empty")

        self._load_model()

        # Convert single prompt to list
        prompts = [prompt] if isinstance(prompt, str) else prompt

        logger.info(f"Generating audio for {len(prompts)} prompt(s)")
        for p in prompts[:3]:  # Log first 3 prompts
            logger.info(f"  Prompt: {p}")

        try:
            # Set generation parameters
            gen_duration = duration or self.default_duration
            self.model.set_generation_params(
                duration=gen_duration,
                temperature=temperature,
                top_k=top_k,
                top_p=top_p,
                cfg_coef=cfg_coef,
                two_step_cfg=two_step_cfg
            )

            # Generate audio
            with torch.no_grad():
                audio_tensors = self.model.generate(prompts)

            # Convert to numpy
            audio_arrays = audio_tensors.cpu().numpy()

            logger.info(f"Generation complete: {audio_arrays.shape}")

            # Return single array if single prompt, otherwise list
            if isinstance(prompt, str):
                return audio_arrays[0]
            else:
                return [audio_arrays[i] for i in range(len(prompts))]

        except Exception as e:
            raise AudioCraftModelError(f"Audio generation failed: {str(e)}")

    def generate_with_melody(
        self,
        prompt: str,
        melody_audio: Union[str, Path, np.ndarray, torch.Tensor],
        duration: Optional[float] = None,
        temperature: float = 1.0,
        cfg_coef: float = 3.0
    ) -> np.ndarray:
        """
        Generate music conditioned on a melody (MusicGen Melody only).

        Args:
            prompt: Text description of music style
            melody_audio: Path to melody audio file or audio array
            duration: Generation duration in seconds
            temperature: Sampling temperature
            cfg_coef: Classifier-free guidance coefficient

        Returns:
            Generated audio array

        Raises:
            AudioCraftValidationError: If inputs are invalid
            AudioCraftModelError: If generation fails
        """
        if 'melody' not in self.model_name.lower():
            raise AudioCraftValidationError(
                "Melody conditioning requires musicgen-melody model"
            )

        self._load_model()

        logger.info(f"Generating music with melody conditioning")

        try:
            # Load melody if path provided
            if isinstance(melody_audio, (str, Path)):
                import torchaudio
                melody, sr = torchaudio.load(str(melody_audio))
                # Resample if needed
                if sr != self.sample_rate:
                    resampler = torchaudio.transforms.Resample(sr, self.sample_rate)
                    melody = resampler(melody)
            elif isinstance(melody_audio, np.ndarray):
                melody = torch.from_numpy(melody_audio).unsqueeze(0)
            else:
                melody = melody_audio

            # Set generation parameters
            gen_duration = duration or self.default_duration
            self.model.set_generation_params(
                duration=gen_duration,
                temperature=temperature,
                cfg_coef=cfg_coef
            )

            # Generate with melody
            with torch.no_grad():
                audio_tensor = self.model.generate_with_chroma(
                    [prompt],
                    melody.to(self.device),
                    self.sample_rate
                )

            audio_array = audio_tensor.cpu().numpy()[0]

            logger.info(f"Melody-conditioned generation complete")
            return audio_array

        except Exception as e:
            raise AudioCraftModelError(f"Melody generation failed: {str(e)}")

    def generate_continuation(
        self,
        prompt: str,
        audio_prefix: Union[str, Path, np.ndarray, torch.Tensor],
        duration: Optional[float] = None
    ) -> np.ndarray:
        """
        Generate audio continuation from existing audio.

        Args:
            prompt: Text description
            audio_prefix: Prefix audio to continue from
            duration: Duration to generate

        Returns:
            Generated continuation audio array

        Raises:
            AudioCraftModelError: If generation fails
        """
        self._load_model()

        logger.info("Generating audio continuation")

        try:
            # Load prefix audio if path provided
            if isinstance(audio_prefix, (str, Path)):
                import torchaudio
                prefix, sr = torchaudio.load(str(audio_prefix))
                if sr != self.sample_rate:
                    resampler = torchaudio.transforms.Resample(sr, self.sample_rate)
                    prefix = resampler(prefix)
            elif isinstance(audio_prefix, np.ndarray):
                prefix = torch.from_numpy(audio_prefix).unsqueeze(0)
            else:
                prefix = audio_prefix

            # Set duration
            gen_duration = duration or self.default_duration
            self.model.set_generation_params(duration=gen_duration)

            # Generate continuation
            with torch.no_grad():
                audio_tensor = self.model.generate_continuation(
                    prefix.to(self.device),
                    self.sample_rate,
                    [prompt]
                )

            audio_array = audio_tensor.cpu().numpy()[0]

            logger.info("Continuation generation complete")
            return audio_array

        except Exception as e:
            raise AudioCraftModelError(f"Continuation generation failed: {str(e)}")

    def save_audio(
        self,
        audio: Union[np.ndarray, torch.Tensor],
        output_path: Union[str, Path],
        sample_rate: Optional[int] = None
    ) -> Path:
        """
        Save audio to file.

        Args:
            audio: Audio array to save
            output_path: Output file path
            sample_rate: Sample rate (uses model default if None)

        Returns:
            Path to saved file

        Raises:
            AudioCraftModelError: If saving fails
        """
        output_path = Path(output_path)
        sr = sample_rate or self.sample_rate

        try:
            import torchaudio

            # Convert to tensor if numpy
            if isinstance(audio, np.ndarray):
                audio_tensor = torch.from_numpy(audio)
            else:
                audio_tensor = audio

            # Ensure correct shape (channels, samples)
            if audio_tensor.dim() == 1:
                audio_tensor = audio_tensor.unsqueeze(0)

            # Save
            torchaudio.save(str(output_path), audio_tensor.cpu(), sr)

            logger.info(f"Audio saved to: {output_path}")
            return output_path

        except Exception as e:
            raise AudioCraftModelError(f"Failed to save audio: {str(e)}")

    def transcribe(self, audio_path: str) -> str:
        """
        AudioCraft does not provide speech-to-text transcription.
        This method is included for interface compatibility.

        Args:
            audio_path: Path to audio file (not used)

        Raises:
            NotImplementedError: AudioCraft does not support transcription
        """
        raise NotImplementedError(
            "AudioCraft does not support speech-to-text transcription. "
            "Use a STT service like Whisper."
        )

    def synthesize(self, text: str, voice: str = "default") -> bytes:
        """
        Generate audio from text description.

        Args:
            text: Text description of audio to generate
            voice: Not used for AudioCraft (included for compatibility)

        Returns:
            Audio data as bytes (WAV format)

        Example:
            >>> audiocraft = AudioCraft()
            >>> audio = audiocraft.synthesize("peaceful piano melody")
        """
        audio_array = self.generate(text)

        # Convert to WAV bytes
        import io
        from scipy.io import wavfile

        buffer = io.BytesIO()
        wavfile.write(buffer, self.sample_rate, audio_array.T)
        return buffer.getvalue()

    def detect_language(self, audio_path: str) -> str:
        """
        AudioCraft does not provide language detection.
        This method is included for interface compatibility.

        Args:
            audio_path: Path to audio file (not used)

        Returns:
            Default language 'en'
        """
        logger.warning("AudioCraft does not support language detection")
        return 'en'

    def is_available(self) -> bool:
        """
        Check if AudioCraft library is available.

        Returns:
            True if library is accessible, False otherwise
        """
        try:
            import audiocraft
            return True
        except ImportError:
            return False

    def get_info(self) -> Dict[str, Any]:
        """
        Get information about the AudioCraft model.

        Returns:
            Dictionary containing model information
        """
        return {
            'name': self.name,
            'model_type': self.model_type,
            'provider': 'Meta AI',
            'model_name': self.model_name,
            'device': self.device,
            'sample_rate': self.sample_rate,
            'default_duration': self.default_duration,
            'generation_type': self.generation_type if self.model_loaded else 'unknown',
            'capabilities': [
                'music_generation',
                'audio_generation',
                'sound_effects',
                'melody_conditioning',
                'audio_continuation',
                'text_to_audio',
                'local_inference'
            ],
            'models': self.MODELS,
            'features': [
                'High-quality music generation',
                'Sound effects generation',
                'Melody-guided generation',
                'Audio continuation',
                'Controllable generation',
                'Multiple model sizes'
            ],
            'parameters': {
                'temperature': 'Randomness of generation (0.0-2.0)',
                'top_k': 'Top-k filtering (0-500)',
                'top_p': 'Nucleus sampling (0.0-1.0)',
                'cfg_coef': 'Prompt adherence (1.0-15.0)',
                'duration': 'Generation length in seconds'
            },
            'open_source': True,
            'license': 'MIT'
        }

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources"""
        if self.model is not None:
            del self.model
            self.model = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

    def __repr__(self) -> str:
        """String representation"""
        return f"AudioCraft(model='{self.model_name}', device='{self.device}')"


if __name__ == "__main__":
    # Example usage
    try:
        audiocraft = AudioCraft()
        print(f"AudioCraft initialized: {audiocraft}")
        print(f"Available: {audiocraft.is_available()}")

        info = audiocraft.get_info()
        print(f"\nModel Info:")
        print(f"  Name: {info['name']}")
        print(f"  Model: {info['model_name']}")
        print(f"  Device: {info['device']}")
        print(f"  Sample rate: {info['sample_rate']} Hz")

        print(f"\nAvailable Models:")
        for model, desc in audiocraft.MODELS.items():
            print(f"  - {model}: {desc}")

        print(f"\nFeatures:")
        for feature in info['features']:
            print(f"  - {feature}")

    except Exception as e:
        print(f"Error: {e}")
