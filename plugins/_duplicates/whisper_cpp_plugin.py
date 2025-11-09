"""
Whisper.cpp Plugin for Faster-Whisper Support
Provides speech-to-text transcription using faster-whisper
"""

from typing import Dict, Any, Optional
import os


class WhisperCppPlugin:
    """Plugin for faster-whisper speech-to-text transcription"""

    name = "whisper_cpp"
    version = "1.0.0"
    description = "Speech-to-text transcription using faster-whisper"
    author = "Windows AI Team"

    def __init__(self):
        self.model = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the faster-whisper plugin"""
        try:
            from faster_whisper import WhisperModel

            # Get model size from config or use default
            model_size = config.get("model_size", "base") if config else "base"

            # Initialize the model (CPU by default, can be configured for GPU)
            device = config.get("device", "cpu") if config else "cpu"
            compute_type = config.get("compute_type", "int8") if config else "int8"

            self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
            self._initialized = True
            return True

        except ImportError:
            print("faster-whisper package not installed. Install with: pip install faster-whisper")
            return False
        except Exception as e:
            print(f"Error initializing Whisper plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Whisper action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please check model configuration."}

        try:
            if action == "transcribe":
                return self._transcribe(params)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {"error": str(e)}

    def _transcribe(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Transcribe audio file to text"""
        audio_path = params.get("audio_path")
        language = params.get("language")  # Optional language hint
        task = params.get("task", "transcribe")  # "transcribe" or "translate"
        vad_filter = params.get("vad_filter", True)  # Voice activity detection
        beam_size = params.get("beam_size", 5)

        if not audio_path:
            return {"error": "audio_path parameter is required"}

        if not os.path.exists(audio_path):
            return {"error": f"Audio file not found: {audio_path}"}

        # Perform transcription
        segments, info = self.model.transcribe(
            audio_path,
            language=language,
            task=task,
            beam_size=beam_size,
            vad_filter=vad_filter
        )

        # Collect all text segments
        transcription = ""
        segments_list = []

        for segment in segments:
            transcription += segment.text
            segments_list.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text
            })

        return {
            "transcription": transcription.strip(),
            "segments": segments_list,
            "language": info.language,
            "language_probability": info.language_probability,
            "duration": info.duration
        }

    def cleanup(self):
        """Cleanup resources"""
        self.model = None
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = WhisperCppPlugin
PLUGIN_NAME = "whisper_cpp"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Speech-to-text transcription using faster-whisper"
PLUGIN_ACTIONS = ["transcribe"]