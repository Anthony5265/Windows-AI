"""
Play.ht Text-to-Speech Plugin
"""

from typing import Dict, Any, Optional, List
import os


class PlayHTPlugin:
    """Plugin for Play.ht TTS"""
    
    name = "playht"
    version = "1.0.0"
    description = "Integration with Play.ht for text-to-speech"
    author = "Windows AI Team"
    
    def __init__(self):
        self.api_key: Optional[str] = None
        self.user_id: Optional[str] = None
        self.client = None
        self._initialized = False
        
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Play.ht plugin"""
        try:
            import requests
            
            self.api_key = (
                config.get("api_key") if config 
                else os.getenv("PLAYHT_API_KEY")
            )
            
            self.user_id = (
                config.get("user_id") if config 
                else os.getenv("PLAYHT_USER_ID")
            )
            
            if not self.api_key or not self.user_id:
                return False
            
            self.client = requests
            self.base_url = "https://api.play.ht/api/v2"
            self._initialized = True
            return True
            
        except ImportError:
            print("requests not installed. Install with: pip install requests")
            return False
        except Exception as e:
            print(f"Error initializing Play.ht plugin: {e}")
            return False
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Play.ht action"""
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
        voice = params.get("voice", "larry")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "X-User-Id": self.user_id,
            "Content-Type": "application/json"
        }
        
        response = self.client.post(
            f"{self.base_url}/tts",
            headers=headers,
            json={
                "text": text,
                "voice": voice,
                "quality": "premium"
            }
        )
        
        if response.status_code == 200:
            return {
                "success": True,
                "audio_url": response.json().get("audio_url")
            }
        return {"success": False, "error": response.text}
    
    def _list_voices(self) -> Dict[str, Any]:
        """List available voices"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "X-User-Id": self.user_id
        }
        
        response = self.client.get(
            f"{self.base_url}/voices",
            headers=headers
        )
        
        if response.status_code == 200:
            return {
                "success": True,
                "voices": response.json()
            }
        return {"success": False, "error": response.text}
    
    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        return True
