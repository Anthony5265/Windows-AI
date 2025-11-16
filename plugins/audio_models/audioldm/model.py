"""
AudioLDM - Text-to-Audio Diffusion Model Integration

This module provides a production-quality integration with AudioLDM,
a latent diffusion model for text-to-audio generation capable of producing
high-quality sound effects, ambient sounds, and audio from text descriptions.
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


class AudioLDMError(Exception):
    """Base exception for AudioLDM errors"""
    pass


class AudioLDMModelError(AudioLDMError):
    """Exception raised for model loading/inference errors"""
    pass


class AudioLDMValidationError(AudioLDMError):
    """Exception raised for validation errors"""
    pass


class AudioLDMConfigurationError(AudioLDMError):
    """Exception raised for configuration errors"""
    pass


class AudioLDM:
    """
    AudioLDM - Text-to-Audio Latent Diffusion Model

    This class provides a comprehensive interface to AudioLDM,
    supporting high-quality text-to-audio generation using latent
    diffusion models for sound effects and ambient audio.

    Attributes:
        model_type (str): Type of model (audio-generation)
        name (str): Service name
        device (str): Computing device (cpu/cuda)
        sample_rate (int): Audio sample rate
    """

    # Available models
    MODELS = {
        'cvssp/audioldm-s-full': 'AudioLDM Small (Full)',
        'cvssp/audioldm-l-full': 'AudioLDM Large (Full)',
        'cvssp/audioldm-m-full': 'AudioLDM Medium (Full)',
        'cvssp/audioldm2': 'AudioLDM 2 (Latest)',
        'cvssp/audioldm2-large': 'AudioLDM 2 Large',
        'cvssp/audioldm2-music': 'AudioLDM 2 Music',
    }

    SAMPLE_RATE = 16000  # AudioLDM default sample rate

    def __init__(
        self,
        model_name: str = 'cvssp/audioldm-s-full',
        device: Optional[str] = None,
        use_gpu: bool = True,
        cache_dir: Optional[str] = None
    ):
        """
        Initialize AudioLDM model.

        Args:
            model_name: Model name from HuggingFace
            device: Computing device ('cpu' or 'cuda'). Auto-detect if None
            use_gpu: Enable GPU acceleration if available
            cache_dir: Directory to cache models

        Raises:
            AudioLDMConfigurationError: If configuration is invalid
        """
        self.model_type = "audio-generation"
        self.name = "AudioLDM"
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

        # Lazy loading
        self.model = None
        self.processor = None
        self.vocoder = None
        self.model_loaded = False

        logger.info(f"Initialized AudioLDM with model: {self.model_name}")
        logger.info(f"Device: {self.device}")

    def _load_model(self):
        """
        Lazy load the AudioLDM model.

        Raises:
            AudioLDMModelError: If model loading fails
        """
        if self.model_loaded:
            return

        try:
            from diffusers import AudioLDMPipeline, AudioLDM2Pipeline

            logger.info(f"Loading AudioLDM model: {self.model_name}")

            # Use AudioLDM2 pipeline for version 2 models
            if 'audioldm2' in self.model_name.lower():
                self.model = AudioLDM2Pipeline.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                    cache_dir=self.cache_dir
                ).to(self.device)
            else:
                self.model = AudioLDMPipeline.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                    cache_dir=self.cache_dir
                ).to(self.device)

            # Enable memory optimizations if using CUDA
            if self.device == "cuda":
                try:
                    self.model.enable_attention_slicing()
                except:
                    pass

            self.model_loaded = True
            logger.info("AudioLDM model loaded successfully")

        except ImportError:
            raise AudioLDMModelError(
                "Diffusers library not installed. Install with: pip install diffusers"
            )
        except Exception as e:
            raise AudioLDMModelError(f"Failed to load model: {str(e)}")

    def generate(
        self,
        prompt: Union[str, List[str]],
        negative_prompt: Optional[Union[str, List[str]]] = None,
        duration: float = 5.0,
        num_inference_steps: int = 50,
        guidance_scale: float = 2.5,
        num_waveforms_per_prompt: int = 1,
        audio_length_in_s: Optional[float] = None
    ) -> Union[np.ndarray, List[np.ndarray]]:
        """
        Generate audio from text prompt(s).

        Args:
            prompt: Text description(s) of audio to generate
            negative_prompt: Text describing what to avoid
            duration: Audio duration in seconds
            num_inference_steps: Number of denoising steps (higher = better quality)
            guidance_scale: Guidance scale for classifier-free guidance
            num_waveforms_per_prompt: Number of audio samples to generate per prompt
            audio_length_in_s: Alias for duration (for compatibility)

        Returns:
            Generated audio array(s)

        Raises:
            AudioLDMValidationError: If inputs are invalid
            AudioLDMModelError: If generation fails

        Example:
            >>> audioldm = AudioLDM()
            >>> audio = audioldm.generate("dog barking in the distance")
            >>> audioldm.save_audio(audio, "dog_bark.wav")
        """
        if not prompt or (isinstance(prompt, str) and not prompt.strip()):
            raise AudioLDMValidationError("Prompt cannot be empty")

        self._load_model()

        # Use audio_length_in_s if provided
        audio_duration = audio_length_in_s or duration

        logger.info(f"Generating audio: {audio_duration}s")
        if isinstance(prompt, str):
            logger.info(f"Prompt: {prompt}")
        else:
            logger.info(f"Generating {len(prompt)} audio samples")

        try:
            with torch.no_grad():
                result = self.model(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    audio_length_in_s=audio_duration,
                    num_inference_steps=num_inference_steps,
                    guidance_scale=guidance_scale,
                    num_waveforms_per_prompt=num_waveforms_per_prompt
                )

            audio_arrays = result.audios

            logger.info(f"Generation complete: {audio_arrays.shape}")

            # Return single array if single prompt, otherwise list
            if isinstance(prompt, str) and num_waveforms_per_prompt == 1:
                return audio_arrays[0]
            else:
                return audio_arrays

        except Exception as e:
            raise AudioLDMModelError(f"Audio generation failed: {str(e)}")

    def generate_batch(
        self,
        prompts: List[str],
        duration: float = 5.0,
        num_inference_steps: int = 50,
        guidance_scale: float = 2.5
    ) -> List[np.ndarray]:
        """
        Generate multiple audio samples from a batch of prompts.

        Args:
            prompts: List of text descriptions
            duration: Audio duration in seconds
            num_inference_steps: Number of denoising steps
            guidance_scale: Guidance scale

        Returns:
            List of generated audio arrays

        Raises:
            AudioLDMValidationError: If inputs are invalid
            AudioLDMModelError: If generation fails
        """
        return self.generate(
            prompt=prompts,
            duration=duration,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale
        )

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
            AudioLDMModelError: If saving fails
        """
        output_path = Path(output_path)
        sr = sample_rate or self.sample_rate

        try:
            from scipy.io import wavfile

            # Convert to numpy if tensor
            if isinstance(audio, torch.Tensor):
                audio = audio.cpu().numpy()

            # Ensure correct format
            audio = np.int16(audio * 32767)

            wavfile.write(str(output_path), sr, audio)

            logger.info(f"Audio saved to: {output_path}")
            return output_path

        except Exception as e:
            raise AudioLDMModelError(f"Failed to save audio: {str(e)}")

    def synthesize(self, text: str, voice: str = "default") -> bytes:
        """
        Generate audio from text description (compatibility method).

        Args:
            text: Text description of audio to generate
            voice: Not used for AudioLDM (included for compatibility)

        Returns:
            Audio data as bytes (WAV format)

        Example:
            >>> audioldm = AudioLDM()
            >>> audio = audioldm.synthesize("rain falling on leaves")
        """
        audio_array = self.generate(text)

        # Convert to WAV bytes
        import io
        from scipy.io import wavfile

        buffer = io.BytesIO()
        audio_int = np.int16(audio_array * 32767)
        wavfile.write(buffer, self.sample_rate, audio_int)
        return buffer.getvalue()

    def transcribe(self, audio_path: str) -> str:
        """
        AudioLDM does not provide speech-to-text transcription.
        This method is included for interface compatibility.

        Args:
            audio_path: Path to audio file (not used)

        Raises:
            NotImplementedError: AudioLDM does not support transcription
        """
        raise NotImplementedError(
            "AudioLDM does not support speech-to-text transcription. "
            "Use a STT service like Whisper."
        )

    def detect_language(self, audio_path: str) -> str:
        """
        AudioLDM does not provide language detection.
        This method is included for interface compatibility.

        Args:
            audio_path: Path to audio file (not used)

        Returns:
            Default language 'en'
        """
        logger.warning("AudioLDM does not support language detection")
        return 'en'

    def is_available(self) -> bool:
        """
        Check if AudioLDM library is available.

        Returns:
            True if library is accessible, False otherwise
        """
        try:
            import diffusers
            return True
        except ImportError:
            return False

    def get_info(self) -> Dict[str, Any]:
        """
        Get information about the AudioLDM model.

        Returns:
            Dictionary containing model information
        """
        return {
            'name': self.name,
            'model_type': self.model_type,
            'provider': 'University of Surrey (CVSSP)',
            'model_name': self.model_name,
            'device': self.device,
            'sample_rate': self.sample_rate,
            'capabilities': [
                'text_to_audio',
                'sound_effects',
                'ambient_sounds',
                'negative_prompts',
                'controllable_generation',
                'batch_generation',
                'local_inference'
            ],
            'models': self.MODELS,
            'features': [
                'Latent diffusion for audio',
                'High-quality sound effects',
                'Negative prompt support',
                'Controllable audio length',
                'Multiple inference steps',
                'Guidance scale control'
            ],
            'parameters': {
                'duration': 'Audio length in seconds',
                'num_inference_steps': 'Denoising steps (10-200)',
                'guidance_scale': 'Prompt adherence (1.0-20.0)',
                'negative_prompt': 'What to avoid in generation'
            },
            'open_source': True,
            'license': 'Creative Commons'
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
        return f"AudioLDM(model='{self.model_name}', device='{self.device}')"


if __name__ == "__main__":
    # Example usage
    try:
        audioldm = AudioLDM()
        print(f"AudioLDM initialized: {audioldm}")
        print(f"Available: {audioldm.is_available()}")

        info = audioldm.get_info()
        print(f"\nModel Info:")
        print(f"  Name: {info['name']}")
        print(f"  Model: {info['model_name']}")
        print(f"  Device: {info['device']}")
        print(f"  Sample rate: {info['sample_rate']} Hz")

        print(f"\nAvailable Models:")
        for model, desc in audioldm.MODELS.items():
            print(f"  - {model}: {desc}")

        print(f"\nFeatures:")
        for feature in info['features']:
            print(f"  - {feature}")

    except Exception as e:
        print(f"Error: {e}")
