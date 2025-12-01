"""Tuya Smart Device Adapter"""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class TuyaAdapter:
    """Adapter for Tuya smart devices"""
    
    def __init__(self, device_id: str, ip_address: str, local_key: str):
        self.device_id = device_id
        self.ip_address = ip_address
        self.local_key = local_key
        try:
            import tinytuya
            self.device = tinytuya.Device(device_id, ip_address, local_key)
            self.device.set_version(3.3)
        except ImportError:
            logger.warning("tinytuya not available. Install with: pip install tinytuya")
            self.device = None
    
    def get_status(self) -> Dict[str, Any]:
        """Get device status"""
        if not self.device:
            return {"status": "error", "message": "TinyTuya library not available"}
        try:
            data = self.device.status()
            return {"status": "success", "data": data}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def turn_on(self) -> Dict[str, Any]:
        """Turn device on"""
        if not self.device:
            return {"status": "error", "message": "TinyTuya library not available"}
        try:
            self.device.turn_on()
            return {"status": "success", "message": "Device turned on"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def turn_off(self) -> Dict[str, Any]:
        """Turn device off"""
        if not self.device:
            return {"status": "error", "message": "TinyTuya library not available"}
        try:
            self.device.turn_off()
            return {"status": "success", "message": "Device turned off"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def set_value(self, dps_id: int, value: Any) -> Dict[str, Any]:
        """Set DPS value"""
        if not self.device:
            return {"status": "error", "message": "TinyTuya library not available"}
        try:
            self.device.set_value(dps_id, value)
            return {"status": "success", "message": f"Set DPS {dps_id} to {value}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
