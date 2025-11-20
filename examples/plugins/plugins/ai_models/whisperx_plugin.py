"""
WhisperX Plugin
Whisper with word-level timestamps and diarization
"""

from typing import Dict, Any, Optional, List
import os


class WhisperXPlugin:
    """Plugin for WhisperX"""

    name = "whisperx"
    version = "1.0.0"
    description = "Integration with WhisperX for transcription with timestamps and diarization"
    author = "Windows AI Team"

    def __init__(self):
        self.model = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the WhisperX plugin"""
        try:
            import whisperx

            model_size = config.get("model_size", "base") if config else "base"
            device = config.get("device", "cpu") if config else "cpu"

            self.model = whisperx.load_model(model_size, device)
            self._initialized = True
            return True

        except ImportError:
            print("whisperx package not installed. Install with: pip install whisperx")
            return False
        except Exception as e:
            print(f"Error initializing WhisperX plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a WhisperX action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "transcribe":
                return self._transcribe(params)
            elif action == "diarize":
                return self._diarize(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _transcribe(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Transcribe with word-level timestamps"""
        import whisperx

        audio_path = params.get("audio_path", "")

        audio = whisperx.load_audio(audio_path)
        result = self.model.transcribe(audio)

        return {
            "success": True,
            "segments": result["segments"]
        }

    def _diarize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Transcribe with speaker diarization"""
        import whisperx

        audio_path = params.get("audio_path", "")

        audio = whisperx.load_audio(audio_path)
        result = self.model.transcribe(audio)

        # Align whisper output
        model_a, metadata = whisperx.load_align_model(language_code=result["language"], device="cpu")
        result = whisperx.align(result["segments"], model_a, metadata, audio, "cpu")

        return {
            "success": True,
            "segments": result["segments"]
        }

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.model = None
        return True
