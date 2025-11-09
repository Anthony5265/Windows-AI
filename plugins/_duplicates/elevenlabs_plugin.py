"""
ElevenLabs Text-to-Speech Plugin
"""

from typing import Dict, Any, Optional, List
import os


class ElevenLabsPlugin:
    """Plugin for ElevenLabs TTS"""
    
    name = "elevenlabs"
    version = "1.0.0"
    description = "Integration with ElevenLabs for text-to-speech"
    author = "Windows AI Team"
    
    def __init__(self):
        self.api_key: Optional[str] = None
        self.client = None
        self._initialized = False
        
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the ElevenLabs plugin"""
        try:
            from elevenlabs import set_api_key, generate, voices
            
            self.api_key = (
                config.get("api_key") if config 
                else os.getenv("ELEVENLABS_API_KEY")
            )
            
            if not self.api_key:
                return False
            
            set_api_key(self.api_key)
            self.generate = generate
            self.voices = voices
            self._initialized = True
            return True
            
        except ImportError:
            print("elevenlabs not installed. Install with: pip install elevenlabs")
            return False
        except Exception as e:
            print(f"Error initializing ElevenLabs plugin: {e}")
            return False
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an ElevenLabs action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}
            
        try:
            if action == "generate":
                return self._text_to_speech(params)
            elif action == "voices":
                return self._list_voices()
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _text_to_speech(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate speech from text"""
        text = params.get("text", "")
        voice = params.get("voice", "Bella")
        model = params.get("model", "eleven_monolingual_v1")
        
        audio = self.generate(
            text=text,
            voice=voice,
            model=model
        )
        
        return {
            "success": True,
            "audio": audio
        }
    
    def _list_voices(self) -> Dict[str, Any]:
        """List available voices"""
        voice_list = self.voices()
        
        return {
            "success": True,
            "voices": [
                {"name": v.name, "voice_id": v.voice_id}
                for v in voice_list
            ]
        }
    
    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        return True
