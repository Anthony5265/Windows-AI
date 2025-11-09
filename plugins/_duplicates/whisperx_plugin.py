"""
WhisperX Plugin
Advanced speech recognition with word-level timestamps and speaker diarization
"""

from typing import Dict, Any, Optional, List
import os


class WhisperXPlugin:
    """Plugin for WhisperX advanced speech recognition"""

    name = "whisperx"
    version = "1.0.0"
    description = "Advanced speech recognition with word-level timestamps and speaker diarization"
    author = "Windows AI Team"

    def __init__(self):
        self.device: Optional[str] = None
        self.compute_type: Optional[str] = None
        self.hf_token: Optional[str] = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the WhisperX plugin"""
        try:
            import torch
            # Check if CUDA is available
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.compute_type = "float16" if self.device == "cuda" else "int8"

            # Get Hugging Face token for diarization
            self.hf_token = (
                config.get("hf_token") if config
                else os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")
            )

            # Override device if specified in config
            if config and "device" in config:
                self.device = config["device"]
            if config and "compute_type" in config:
                self.compute_type = config["compute_type"]

            self._initialized = True
            return True

        except ImportError as e:
            print(f"Required packages not installed. Install with: pip install whisperx torch")
            print(f"Import error: {e}")
            return False
        except Exception as e:
            print(f"Error initializing WhisperX plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a WhisperX action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please check dependencies and configuration."}

        try:
            if action == "transcribe":
                return self._transcribe(params)
            elif action == "transcribe_with_alignment":
                return self._transcribe_with_alignment(params)
            elif action == "transcribe_with_diarization":
                return self._transcribe_with_diarization(params)
            elif action == "detect_language":
                return self._detect_language(params)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {"error": f"Execution error: {str(e)}"}

    def _transcribe(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Basic transcription without alignment or diarization"""
        audio_path = params.get("audio_path")
        model_size = params.get("model", "large-v2")
        language = params.get("language")  # None for auto-detection
        batch_size = params.get("batch_size", 16)

        if not audio_path:
            return {"error": "audio_path parameter required"}

        if not os.path.exists(audio_path):
            return {"error": f"Audio file not found: {audio_path}"}

        try:
            import whisperx

            # Load model
            model = whisperx.load_model(
                model_size,
                device=self.device,
                compute_type=self.compute_type
            )

            # Load audio
            audio = whisperx.load_audio(audio_path)

            # Transcribe
            result = model.transcribe(audio, batch_size=batch_size, language=language)

            return {
                "text": result["text"],
                "language": result["language"],
                "segments": result["segments"],
                "model": model_size
            }

        except Exception as e:
            return {"error": f"Transcription failed: {str(e)}"}

    def _transcribe_with_alignment(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Transcription with word-level timestamp alignment"""
        audio_path = params.get("audio_path")
        model_size = params.get("model", "large-v2")
        language = params.get("language")  # None for auto-detection
        batch_size = params.get("batch_size", 16)
        align_model = params.get("align_model")  # None for auto-selection

        if not audio_path:
            return {"error": "audio_path parameter required"}

        if not os.path.exists(audio_path):
            return {"error": f"Audio file not found: {audio_path}"}

        try:
            import whisperx

            # Load model
            model = whisperx.load_model(
                model_size,
                device=self.device,
                compute_type=self.compute_type
            )

            # Load audio
            audio = whisperx.load_audio(audio_path)

            # Transcribe
            result = model.transcribe(audio, batch_size=batch_size, language=language)

            # Load alignment model
            align_model_name = align_model or result["language"]
            model_a, metadata = whisperx.load_align_model(
                language_code=align_model_name,
                device=self.device
            )

            # Align
            result = whisperx.align(
                result["segments"],
                model_a,
                metadata,
                audio,
                self.device,
                return_char_alignments=False
            )

            return {
                "text": result["text"] if "text" in result else "",
                "language": result["language"] if "language" in result else align_model_name,
                "segments": result["segments"],
                "model": model_size,
                "aligned": True
            }

        except Exception as e:
            return {"error": f"Transcription with alignment failed: {str(e)}"}

    def _transcribe_with_diarization(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Transcription with speaker diarization"""
        audio_path = params.get("audio_path")
        model_size = params.get("model", "large-v2")
        language = params.get("language")  # None for auto-detection
        batch_size = params.get("batch_size", 16)
        align_model = params.get("align_model")  # None for auto-selection
        min_speakers = params.get("min_speakers")
        max_speakers = params.get("max_speakers")

        if not audio_path:
            return {"error": "audio_path parameter required"}

        if not os.path.exists(audio_path):
            return {"error": f"Audio file not found: {audio_path}"}

        if not self.hf_token:
            return {"error": "Hugging Face token required for diarization. Set HF_TOKEN environment variable or provide in config."}

        try:
            import whisperx
            from whisperx.diarize import DiarizationPipeline

            # Load model
            model = whisperx.load_model(
                model_size,
                device=self.device,
                compute_type=self.compute_type
            )

            # Load audio
            audio = whisperx.load_audio(audio_path)

            # Transcribe
            result = model.transcribe(audio, batch_size=batch_size, language=language)

            # Load alignment model
            align_model_name = align_model or result["language"]
            model_a, metadata = whisperx.load_align_model(
                language_code=align_model_name,
                device=self.device
            )

            # Align
            result = whisperx.align(
                result["segments"],
                model_a,
                metadata,
                audio,
                self.device,
                return_char_alignments=False
            )

            # Diarize
            diarize_model = DiarizationPipeline(
                use_auth_token=self.hf_token,
                device=self.device
            )

            diarize_segments = diarize_model(
                audio,
                min_speakers=min_speakers,
                max_speakers=max_speakers
            )

            # Assign speakers
            result = whisperx.assign_word_speakers(diarize_segments, result)

            return {
                "text": result["text"] if "text" in result else "",
                "language": result["language"] if "language" in result else align_model_name,
                "segments": result["segments"],
                "model": model_size,
                "aligned": True,
                "diarized": True
            }

        except Exception as e:
            return {"error": f"Transcription with diarization failed: {str(e)}"}

    def _detect_language(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Detect the language of an audio file"""
        audio_path = params.get("audio_path")
        model_size = params.get("model", "large-v2")

        if not audio_path:
            return {"error": "audio_path parameter required"}

        if not os.path.exists(audio_path):
            return {"error": f"Audio file not found: {audio_path}"}

        try:
            import whisperx

            # Load model
            model = whisperx.load_model(
                model_size,
                device=self.device,
                compute_type=self.compute_type
            )

            # Load audio
            audio = whisperx.load_audio(audio_path)

            # Detect language (transcribe with language=None)
            result = model.transcribe(audio, language=None)

            return {
                "language": result["language"],
                "model": model_size
            }

        except Exception as e:
            return {"error": f"Language detection failed: {str(e)}"}

    def cleanup(self):
        """Cleanup resources"""
        # Clear any cached models if needed
        import gc
        gc.collect()
        if self.device == "cuda":
            import torch
            torch.cuda.empty_cache()
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = WhisperXPlugin
PLUGIN_NAME = "whisperx"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Advanced speech recognition with word-level timestamps and speaker diarization"
PLUGIN_ACTIONS = [
    "transcribe",
    "transcribe_with_alignment",
    "transcribe_with_diarization",
    "detect_language"
]