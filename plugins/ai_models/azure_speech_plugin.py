"""
Azure Speech Services Plugin
Microsoft's speech recognition and synthesis
"""

from typing import Dict, Any, Optional, List
import os


class AzureSpeechPlugin:
    """Plugin for Azure Speech Services"""

    name = "azure_speech"
    version = "1.0.0"
    description = "Integration with Azure Speech Services"
    author = "Windows AI Team"

    def __init__(self):
        self.speech_key: Optional[str] = None
        self.service_region: Optional[str] = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Azure Speech plugin"""
        try:
            import azure.cognitiveservices.speech as speechsdk

            self.speech_key = (
                config.get("speech_key") if config
                else os.getenv("AZURE_SPEECH_KEY")
            )
            self.service_region = (
                config.get("service_region") if config
                else os.getenv("AZURE_SPEECH_REGION", "eastus")
            )

            if not self.speech_key:
                return False

            self.speechsdk = speechsdk
            self._initialized = True
            return True

        except ImportError:
            print("azure-cognitiveservices-speech package not installed. Install with: pip install azure-cognitiveservices-speech")
            return False
        except Exception as e:
            print(f"Error initializing Azure Speech plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an Azure Speech action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "transcribe":
                return self._transcribe(params)
            elif action == "synthesize":
                return self._synthesize(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _transcribe(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Transcribe audio to text"""
        audio_path = params.get("audio_path", "")

        speech_config = self.speechsdk.SpeechConfig(
            subscription=self.speech_key,
            region=self.service_region
        )
        audio_config = self.speechsdk.audio.AudioConfig(filename=audio_path)

        speech_recognizer = self.speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_config
        )

        result = speech_recognizer.recognize_once()

        if result.reason == self.speechsdk.ResultReason.RecognizedSpeech:
            return {
                "success": True,
                "text": result.text
            }
        else:
            return {"success": False, "error": "Recognition failed"}

    def _synthesize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize text to speech"""
        text = params.get("text", "")
        output_path = params.get("output_path", "output.wav")

        speech_config = self.speechsdk.SpeechConfig(
            subscription=self.speech_key,
            region=self.service_region
        )
        audio_config = self.speechsdk.audio.AudioOutputConfig(filename=output_path)

        speech_synthesizer = self.speechsdk.SpeechSynthesizer(
            speech_config=speech_config,
            audio_config=audio_config
        )

        result = speech_synthesizer.speak_text_async(text).get()

        if result.reason == self.speechsdk.ResultReason.SynthesizingAudioCompleted:
            return {
                "success": True,
                "output_path": output_path
            }
        else:
            return {"success": False, "error": "Synthesis failed"}

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        return True
