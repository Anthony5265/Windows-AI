"""Wyze Camera/Sensor Adapter"""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class WyzeAdapter:
    """Adapter for Wyze cameras and sensors"""
    
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        try:
            from wyze_sdk import Client
            self.client = Client(email=email, password=password)
        except ImportError:
            logger.warning("wyze-sdk not available. Install with: pip install wyze-sdk")
            self.client = None
    
    def get_devices(self) -> Dict[str, Any]:
        """Get all Wyze devices"""
        if not self.client:
            return {"status": "error", "message": "Wyze SDK not available"}
        try:
            devices = self.client.devices_list()
            return {"status": "success", "devices": [d.to_dict() for d in devices]}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def turn_on(self, device_mac: str) -> Dict[str, Any]:
        """Turn device on"""
        if not self.client:
            return {"status": "error", "message": "Wyze SDK not available"}
        try:
            self.client.bulbs.turn_on(device_mac=device_mac, device_model="WLPA19")
            return {"status": "success", "message": "Device turned on"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def turn_off(self, device_mac: str) -> Dict[str, Any]:
        """Turn device off"""
        if not self.client:
            return {"status": "error", "message": "Wyze SDK not available"}
        try:
            self.client.bulbs.turn_off(device_mac=device_mac, device_model="WLPA19")
            return {"status": "success", "message": "Device turned off"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
