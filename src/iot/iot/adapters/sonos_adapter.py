"""Sonos Speaker Adapter"""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class SonosAdapter:
    """Adapter for Sonos speakers"""
    
    def __init__(self, speaker_ip: str = None):
        try:
            import soco
            if speaker_ip:
                self.speaker = soco.SoCo(speaker_ip)
            else:
                self.speaker = soco.discovery.any_soco()
        except ImportError:
            logger.warning("soco not available. Install with: pip install soco")
            self.speaker = None
    
    def play(self) -> Dict[str, Any]:
        """Play music"""
        if not self.speaker:
            return {"status": "error", "message": "Soco library not available"}
        try:
            self.speaker.play()
            return {"status": "success", "message": "Playing"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def pause(self) -> Dict[str, Any]:
        """Pause music"""
        if not self.speaker:
            return {"status": "error", "message": "Soco library not available"}
        try:
            self.speaker.pause()
            return {"status": "success", "message": "Paused"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def set_volume(self, volume: int) -> Dict[str, Any]:
        """Set volume (0-100)"""
        if not self.speaker:
            return {"status": "error", "message": "Soco library not available"}
        try:
            self.speaker.volume = max(0, min(100, volume))
            return {"status": "success", "volume": volume}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_current_track(self) -> Dict[str, Any]:
        """Get current track information"""
        if not self.speaker:
            return {"status": "error", "message": "Soco library not available"}
        try:
            track = self.speaker.get_current_track_info()
            return {"status": "success", "track": track}
        except Exception as e:
            return {"status": "error", "message": str(e)}
