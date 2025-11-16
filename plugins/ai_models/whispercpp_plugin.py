"""
Whisper.cpp Plugin
Fast C++ implementation of Whisper
"""

from typing import Dict, Any, Optional, List
import os


class WhisperCppPlugin:
    """Plugin for Whisper.cpp"""

    name = "whispercpp"
    version = "1.0.0"
    description = "Integration with Whisper.cpp for fast speech recognition"
    author = "Windows AI Team"

    def __init__(self):
        self.model_path: Optional[str] = None
        self.model = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Whisper.cpp plugin"""
        try:
            from whispercpp import Whisper

            self.model_path = (
                config.get("model_path") if config
                else os.getenv("WHISPERCPP_MODEL", "models/ggml-base.bin")
            )

            self.model = Whisper(self.model_path)
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

        result = self.model.transcribe(audio_path)

        return {
            "success": True,
            "text": result
        }

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.model = None
        return True
