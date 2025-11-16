"""
MusicGen - Meta's Music Generation Model Integration

This module provides a production-quality integration with Meta's MusicGen,
a controllable music generation model capable of generating high-quality music
from text descriptions or melody conditioning.
"""

import os
import logging
import torch
import numpy as np
from typing import Optional, Dict, Any, List, Union
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)


class MusicGenError(Exception):
    """Base exception for MusicGen errors"""
    pass


class MusicGenModelError(MusicGenError):
    """Exception raised for model loading/inference errors"""
    pass


class MusicGenValidationError(MusicGenError):
    """Exception raised for validation errors"""
    pass


class MusicGen:
    """
    MusicGen - Meta's Controllable Music Generation

    This class provides a comprehensive interface to Meta's MusicGen,
    supporting text-to-music generation with optional melody conditioning.

    Attributes:
        model_type (str): Type of model (music-generation)
        name (str): Service name
        device (str): Computing device (cpu/cuda)
        sample_rate (int): Audio sample rate
    """

    MODELS = {
        'facebook/musicgen-small': 'Small (300M parameters, fast)',
        'facebook/musicgen-medium': 'Medium (1.5B parameters, balanced)',
        'facebook/musicgen-large': 'Large (3.3B parameters, high quality)',
        'facebook/musicgen-melody': 'Melody-conditioned generation',
    }

    SAMPLE_RATE = 32000

    def __init__(
        self,
        model_name: str = 'facebook/musicgen-small',
        device: Optional[str] = None,
        use_gpu: bool = True
    ):
        """Initialize MusicGen model."""
        self.model_type = "music-generation"
        self.name = "MusicGen"
        self.sample_rate = self.SAMPLE_RATE

        if device is None:
            self.device = "cuda" if (use_gpu and torch.cuda.is_available()) else "cpu"
        else:
            self.device = device

        self.model_name = model_name
        self.model = None
        self.processor = None
        self.model_loaded = False

        logger.info(f"Initialized MusicGen: {self.model_name}")
        logger.info(f"Device: {self.device}")

    def _load_model(self):
        """Lazy load the MusicGen model."""
        if self.model_loaded:
            return

        try:
            from audiocraft.models import MusicGen as MG

            logger.info(f"Loading MusicGen model: {self.model_name}")
            self.model = MG.get_pretrained(self.model_name, device=self.device)
            self.model.set_generation_params(duration=10.0)
            self.model_loaded = True
            logger.info("MusicGen model loaded successfully")

        except ImportError:
            raise MusicGenModelError(
                "AudioCraft library not installed. Install with: pip install audiocraft"
            )
        except Exception as e:
            raise MusicGenModelError(f"Failed to load model: {str(e)}")

    def generate(
        self,
        prompt: Union[str, List[str]],
        duration: float = 10.0,
        temperature: float = 1.0,
        top_k: int = 250,
        top_p: float = 0.0,
        cfg_coef: float = 3.0
    ) -> Union[np.ndarray, List[np.ndarray]]:
        """
        Generate music from text description(s).

        Args:
            prompt: Text description(s) of music
            duration: Music duration in seconds
            temperature: Sampling temperature
            top_k: Top-k filtering
            top_p: Nucleus sampling
            cfg_coef: Classifier-free guidance coefficient

        Returns:
            Generated audio array(s)

        Example:
            >>> musicgen = MusicGen()
            >>> audio = musicgen.generate("upbeat electronic dance music")
        """
        if not prompt or (isinstance(prompt, str) and not prompt.strip()):
            raise MusicGenValidationError("Prompt cannot be empty")

        self._load_model()

        prompts = [prompt] if isinstance(prompt, str) else prompt
        logger.info(f"Generating music: {duration}s")

        try:
            self.model.set_generation_params(
                duration=duration,
                temperature=temperature,
                top_k=top_k,
                top_p=top_p,
                cfg_coef=cfg_coef
            )

            with torch.no_grad():
                audio_tensors = self.model.generate(prompts)

            audio_arrays = audio_tensors.cpu().numpy()
            logger.info(f"Generation complete: {audio_arrays.shape}")

            return audio_arrays[0] if isinstance(prompt, str) else [audio_arrays[i] for i in range(len(prompts))]

        except Exception as e:
            raise MusicGenModelError(f"Music generation failed: {str(e)}")

    def generate_with_melody(
        self,
        prompt: str,
        melody: Union[str, Path, np.ndarray, torch.Tensor],
        duration: Optional[float] = None,
        temperature: float = 1.0
    ) -> np.ndarray:
        """Generate music conditioned on melody (requires melody model)."""
        if 'melody' not in self.model_name.lower():
            raise MusicGenValidationError("Melody conditioning requires musicgen-melody model")

        self._load_model()

        try:
            if isinstance(melody, (str, Path)):
                import torchaudio
                melody_tensor, sr = torchaudio.load(str(melody))
                if sr != self.sample_rate:
                    resampler = torchaudio.transforms.Resample(sr, self.sample_rate)
                    melody_tensor = resampler(melody_tensor)
            elif isinstance(melody, np.ndarray):
                melody_tensor = torch.from_numpy(melody).unsqueeze(0)
            else:
                melody_tensor = melody

            if duration:
                self.model.set_generation_params(duration=duration, temperature=temperature)

            with torch.no_grad():
                audio_tensor = self.model.generate_with_chroma(
                    [prompt],
                    melody_tensor.to(self.device),
                    self.sample_rate
                )

            return audio_tensor.cpu().numpy()[0]

        except Exception as e:
            raise MusicGenModelError(f"Melody generation failed: {str(e)}")

    def synthesize(self, text: str, voice: str = "default") -> bytes:
        """Generate music from text (compatibility method)."""
        audio_array = self.generate(text)
        import io
        from scipy.io import wavfile
        buffer = io.BytesIO()
        wavfile.write(buffer, self.sample_rate, audio_array.T)
        return buffer.getvalue()

    def transcribe(self, audio_path: str) -> str:
        """Not supported."""
        raise NotImplementedError("MusicGen does not support transcription")

    def detect_language(self, audio_path: str) -> str:
        """Not supported."""
        return 'en'

    def is_available(self) -> bool:
        """Check if MusicGen is available."""
        try:
            import audiocraft
            return True
        except ImportError:
            return False

    def get_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            'name': self.name,
            'model_type': self.model_type,
            'provider': 'Meta AI',
            'model_name': self.model_name,
            'device': self.device,
            'sample_rate': self.sample_rate,
            'capabilities': [
                'music_generation',
                'text_to_music',
                'melody_conditioning',
                'controllable_generation',
                'local_inference'
            ],
            'models': self.MODELS,
            'open_source': True,
            'license': 'MIT'
        }

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.model is not None:
            del self.model
            self.model = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

    def __repr__(self) -> str:
        return f"MusicGen(model='{self.model_name}', device='{self.device}')"


if __name__ == "__main__":
    try:
        musicgen = MusicGen()
        print(f"MusicGen initialized: {musicgen}")
        print(f"Available: {musicgen.is_available()}")

        info = musicgen.get_info()
        print(f"\nModel Info:")
        print(f"  Name: {info['name']}")
        print(f"  Model: {info['model_name']}")
        print(f"  Device: {info['device']}")

    except Exception as e:
        print(f"Error: {e}")
