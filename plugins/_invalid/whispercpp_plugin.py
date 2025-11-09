"""
Whisper.cpp Plugin
Speech-to-text transcription using Whisper.cpp
"""

from typing import Dict, Any, Optional
import os


class WhisperCppPlugin:
    """Plugin for Whisper.cpp speech-to-text"""

    name = "whispercpp"
    version = "1.0.0"
    description = "Speech-to-text transcription using Whisper.cpp"
    author = "Windows AI Team"

    def __init__(self):
        self.model = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Whisper.cpp plugin"""
        try:
            import whispercpp as w

            # Get model path from config or use default
            model_path = (
                config.get("model_path") if config
                else os.getenv("WHISPER_MODEL_PATH", "models/ggml-base.en.bin")
            )

            # Check if model file exists
            if not os.path.exists(model_path):
                print(f"Whisper model not found at {model_path}. Please download a model first.")
                return False

            # Initialize the model
            self.model = w.Whisper.from_pretrained(model_path)
            self._initialized = True
            return True

        except ImportError:
            print("whispercpp package not installed. Install with: pip install whispercpp")
            return False
        except Exception as e:
            print(f"Error initializing Whisper.cpp plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Whisper.cpp action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please provide model path."}

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
        language = params.get("language", "en")  # Default to English
        translate = params.get("translate", False)  # Whether to translate to English

        if not audio_path:
            return {"error": "audio_path parameter required"}

        if not os.path.exists(audio_path):
            return {"error": f"Audio file not found: {audio_path}"}

        try:
            # Load audio and transcribe
            result = self.model.transcribe(audio_path, language=language, translate=translate)

            return {
                "text": result["text"],
                "language": result.get("language", language),
                "segments": result.get("segments", []),
                "duration": result.get("duration")
            }

        except Exception as e:
            return {"error": f"Transcription failed: {str(e)}"}

    def cleanup(self):
        """Cleanup resources"""
        self.model = None
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = WhisperCppPlugin
PLUGIN_NAME = "whispercpp"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Speech-to-text transcription using Whisper.cpp"
PLUGIN_ACTIONS = ["transcribe"]