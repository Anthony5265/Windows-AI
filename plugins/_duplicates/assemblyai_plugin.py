"""
AssemblyAI Speech-to-Text Plugin
"""

from typing import Dict, Any, Optional, List
import os


class AssemblyAIPlugin:
    """Plugin for AssemblyAI speech recognition"""
    
    name = "assemblyai"
    version = "1.0.0"
    description = "Integration with AssemblyAI for speech-to-text"
    author = "Windows AI Team"
    
    def __init__(self):
        self.api_key: Optional[str] = None
        self.client = None
        self._initialized = False
        
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the AssemblyAI plugin"""
        try:
            import assemblyai as aai
            
            self.api_key = (
                config.get("api_key") if config 
                else os.getenv("ASSEMBLYAI_API_KEY")
            )
            
            if not self.api_key:
                return False
            
            aai.settings.api_key = self.api_key
            self.client = aai
            self._initialized = True
            return True
            
        except ImportError:
            print("assemblyai not installed. Install with: pip install assemblyai")
            return False
        except Exception as e:
            print(f"Error initializing AssemblyAI plugin: {e}")
            return False
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an AssemblyAI action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}
            
        try:
            if action == "transcribe":
                return self._transcribe(params)
            elif action == "realtime":
                return self._realtime_transcription(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _transcribe(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Transcribe audio file"""
        audio_url = params.get("audio_url", "")
        speaker_labels = params.get("speaker_labels", False)
        
        config = self.client.TranscriptionConfig(speaker_labels=speaker_labels)
        transcriber = self.client.Transcriber()
        transcript = transcriber.transcribe(audio_url, config)
        
        return {
            "success": True,
            "text": transcript.text,
            "confidence": transcript.confidence,
            "utterances": transcript.utterances if speaker_labels else []
        }
    
    def _realtime_transcription(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Start real-time transcription"""
        return {
            "success": True,
            "message": "Real-time transcription requires streaming implementation"
        }
    
    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        return True
