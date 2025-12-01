"""Ring Doorbell/Camera Adapter"""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class RingAdapter:
    """Adapter for Ring doorbells and cameras"""
    
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.auth_token = None
        try:
            from ring_doorbell import Ring
            self.ring = Ring(username, password)
        except ImportError:
            logger.warning("ring-doorbell library not available. Install with: pip install ring-doorbell")
            self.ring = None
    
    def get_devices(self) -> Dict[str, Any]:
        """Get all Ring devices"""
        if not self.ring:
            return {"status": "error", "message": "Ring library not available"}
        try:
            devices = self.ring.devices()
            return {"status": "success", "devices": [{"id": d.id, "name": d.name, "type": d.kind} 
                                                     for d in devices["doorbots"] + devices["stickup_cams"]]}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_video_url(self, device_id: str) -> Dict[str, Any]:
        """Get latest video URL"""
        if not self.ring:
            return {"status": "error", "message": "Ring library not available"}
        try:
            device = self.ring.devices()[device_id]
            video = device.history(limit=1)[0]
            return {"status": "success", "video_url": video["recording"]["url"]}
        except Exception as e:
            return {"status": "error", "message": str(e)}
