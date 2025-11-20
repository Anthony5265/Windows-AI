"""
Audio Processing Module - Production Grade
Speech-to-text, text-to-speech, audio analysis, and voice activity detection
"""
from typing import Dict, Any, List, Optional
import logging
import os
import io

logger = logging.getLogger(__name__)

# Optional dependencies
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False


class AudioProcessor:
    """Production audio processing capabilities"""

    def __init__(self):
        self.sample_rate = 16000

    async def transcribe(self, audio_path: str = None, audio_data: bytes = None,
                        provider: str = "whisper", model: str = "base") -> Dict[str, Any]:
        """
        Transcribe audio to text

        Args:
            audio_path: Path to audio file
            audio_data: Raw audio bytes
            provider: STT provider (whisper, azure, google, assemblyai)
            model: Model to use

        Returns:
            Dict with transcription results
        """
        if provider == "whisper":
            return await self._whisper_transcribe(audio_path, audio_data, model)
        elif provider == "azure":
            return await self._azure_transcribe(audio_path, audio_data)
        elif provider == "google":
            return await self._google_transcribe(audio_path, audio_data)
        else:
            return {"status": "error", "message": f"Unknown provider: {provider}"}

    async def _whisper_transcribe(self, audio_path: str = None, audio_data: bytes = None,
                                  model: str = "base") -> Dict[str, Any]:
        """Transcribe using OpenAI Whisper"""
        try:
            import whisper as whisper_model

            model_instance = whisper_model.load_model(model)

            if audio_path:
                result = model_instance.transcribe(audio_path)
            elif audio_data:
                # Save temp file
                temp_path = "/tmp/temp_audio.wav"
                with open(temp_path, "wb") as f:
                    f.write(audio_data)
                result = model_instance.transcribe(temp_path)
                os.remove(temp_path)
            else:
                return {"status": "error", "message": "No audio provided"}

            return {
                "status": "success",
                "text": result["text"],
                "segments": result.get("segments", []),
                "language": result.get("language", "unknown")
            }
        except ImportError:
            return {"status": "error", "message": "Whisper not installed. Install with: pip install openai-whisper"}
        except Exception as e:
            logger.error(f"Whisper transcribe error: {e}")
            return {"status": "error", "message": str(e)}

    async def _azure_transcribe(self, audio_path: str = None, audio_data: bytes = None) -> Dict[str, Any]:
        """Transcribe using Azure Speech Services"""
        try:
            import azure.cognitiveservices.speech as speechsdk

            speech_key = os.getenv("AZURE_SPEECH_KEY", "")
            service_region = os.getenv("AZURE_SPEECH_REGION", "eastus")

            if not speech_key:
                return {"status": "error", "message": "AZURE_SPEECH_KEY not configured"}

            speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)

            if audio_path:
                audio_config = speechsdk.AudioConfig(filename=audio_path)
            else:
                return {"status": "error", "message": "Azure requires audio file path"}

            speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
            result = speech_recognizer.recognize_once()

            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                return {
                    "status": "success",
                    "text": result.text
                }
            else:
                return {
                    "status": "error",
                    "message": "Recognition failed",
                    "reason": str(result.reason)
                }
        except ImportError:
            return {"status": "error", "message": "Azure Speech SDK not installed"}
        except Exception as e:
            logger.error(f"Azure transcribe error: {e}")
            return {"status": "error", "message": str(e)}

    async def text_to_speech(self, text: str, provider: str = "elevenlabs",
                            voice: str = None, output_path: str = None) -> Dict[str, Any]:
        """
        Convert text to speech

        Args:
            text: Text to synthesize
            provider: TTS provider (elevenlabs, azure, google)
            voice: Voice ID or name
            output_path: Path to save audio file

        Returns:
            Dict with audio data or file path
        """
        if provider == "elevenlabs":
            return await self._elevenlabs_tts(text, voice, output_path)
        elif provider == "azure":
            return await self._azure_tts(text, voice, output_path)
        else:
            return {"status": "error", "message": f"Unknown TTS provider: {provider}"}

    async def _elevenlabs_tts(self, text: str, voice: str = None,
                             output_path: str = None) -> Dict[str, Any]:
        """Text-to-speech using ElevenLabs"""
        try:
            from elevenlabs import generate, voices

            api_key = os.getenv("ELEVENLABS_API_KEY", "")
            if not api_key:
                return {"status": "error", "message": "ELEVENLABS_API_KEY not configured"}

            audio = generate(
                text=text,
                voice=voice or "Bella",
                api_key=api_key
            )

            if output_path:
                with open(output_path, "wb") as f:
                    f.write(audio)
                return {"status": "success", "path": output_path}
            else:
                return {"status": "success", "audio": audio}
        except ImportError:
            return {"status": "error", "message": "ElevenLabs not installed. Install with: pip install elevenlabs"}
        except Exception as e:
            logger.error(f"ElevenLabs TTS error: {e}")
            return {"status": "error", "message": str(e)}

    async def analyze_audio(self, audio_path: str) -> Dict[str, Any]:
        """
        Analyze audio features

        Args:
            audio_path: Path to audio file

        Returns:
            Dict with audio analysis (duration, sample rate, features)
        """
        if not LIBROSA_AVAILABLE:
            return {"status": "error", "message": "librosa not installed"}

        try:
            # Load audio
            y, sr = librosa.load(audio_path, sr=self.sample_rate)

            # Extract features
            duration = len(y) / sr
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)

            return {
                "status": "success",
                "duration": float(duration),
                "sample_rate": sr,
                "tempo": float(tempo),
                "spectral_centroid_mean": float(np.mean(spectral_centroids)),
                "mfcc_mean": [float(np.mean(mfcc)) for mfcc in mfccs]
            }
        except Exception as e:
            logger.error(f"Audio analysis error: {e}")
            return {"status": "error", "message": str(e)}

    async def detect_voice_activity(self, audio_path: str, threshold: float = 0.02) -> Dict[str, Any]:
        """
        Detect voice activity in audio

        Args:
            audio_path: Path to audio file
            threshold: Energy threshold for VAD

        Returns:
            Dict with voice activity segments
        """
        if not LIBROSA_AVAILABLE:
            return {"status": "error", "message": "librosa not installed"}

        try:
            y, sr = librosa.load(audio_path, sr=self.sample_rate)

            # Calculate energy
            frame_length = int(0.025 * sr)
            hop_length = int(0.010 * sr)
            energy = np.array([
                sum(abs(y[i:i+frame_length]**2))
                for i in range(0, len(y), hop_length)
            ])

            # Detect voice activity
            is_voice = energy > threshold
            segments = []
            start = None

            for i, voice in enumerate(is_voice):
                time = i * hop_length / sr
                if voice and start is None:
                    start = time
                elif not voice and start is not None:
                    segments.append({"start": start, "end": time})
                    start = None

            return {
                "status": "success",
                "segments": segments,
                "total_speech_duration": sum(s["end"] - s["start"] for s in segments)
            }
        except Exception as e:
            logger.error(f"VAD error: {e}")
            return {"status": "error", "message": str(e)}


# Legacy compatibility functions
def input_processor(audio: Any) -> Dict[str, Any]:
    """Legacy audio input processor"""
    if isinstance(audio, dict):
        duration = float(audio.get("duration", 0))
        data = audio.get("data")
    else:
        duration = len(audio) / 1000 if hasattr(audio, "__len__") else 0
        data = audio

    use_remote = duration > 5.0
    return {"data": data, "duration": duration, "use_remote": use_remote}


def task_planner(processed_audio: Dict[str, Any]) -> Dict[str, Any]:
    """Legacy task planner"""
    step = {
        "type": "transcribe",
        "mode": "remote" if processed_audio.get("use_remote") else "local",
        "audio": processed_audio.get("data"),
    }
    return {"steps": [step]}
