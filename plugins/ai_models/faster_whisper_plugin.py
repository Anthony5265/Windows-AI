"""
Faster Whisper Plugin
Optimized Whisper implementation using CTranslate2
"""

from typing import Dict, Any, Optional, List
import os


class FasterWhisperPlugin:
    """Plugin for Faster Whisper"""

    name = "faster_whisper"
    version = "1.0.0"
    description = "Integration with Faster Whisper for optimized speech recognition"
    author = "Windows AI Team"

    def __init__(self):
        self.model = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Faster Whisper plugin"""
        try:
            from faster_whisper import WhisperModel

            model_size = config.get("model_size", "base") if config else "base"
            device = config.get("device", "cpu") if config else "cpu"

            self.model = WhisperModel(model_size, device=device)
            self._initialized = True
            return True

        except ImportError:
            print("faster-whisper package not installed. Install with: pip install faster-whisper")
            return False
        except Exception as e:
            print(f"Error initializing Faster Whisper plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Faster Whisper action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "transcribe":
                return self._transcribe(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _transcribe(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Transcribe audio to text"""
        audio_path = params.get("audio_path", "")
        language = params.get("language", None)

        segments, info = self.model.transcribe(audio_path, language=language)

        text = " ".join([segment.text for segment in segments])

        return {
            "success": True,
            "text": text,
            "language": info.language
        }

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.model = None
        return True
