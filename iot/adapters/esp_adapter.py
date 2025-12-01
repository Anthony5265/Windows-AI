"""ESP32/ESP8266 Device Adapter"""
from typing import Dict, Any
import logging
import requests

logger = logging.getLogger(__name__)

class ESPAdapter:
    """Adapter for ESP32/ESP8266 devices"""
    
    def __init__(self, device_ip: str, port: int = 80):
        self.device_ip = device_ip
        self.port = port
        self.base_url = f"http://{device_ip}:{port}"
    
    def send_command(self, endpoint: str, method: str = "GET", data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send HTTP command to ESP device"""
        try:
            url = f"{self.base_url}/{endpoint.lstrip('/')}"
            if method == "GET":
                response = requests.get(url, timeout=5)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=5)
            else:
                return {"status": "error", "message": f"Unsupported method: {method}"}
            
            return {"status": "success", "data": response.text, "status_code": response.status_code}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        """Get device status"""
        return self.send_command("/status")
    
    def control_gpio(self, pin: int, state: bool) -> Dict[str, Any]:
        """Control GPIO pin"""
        return self.send_command(f"/gpio/{pin}/{'on' if state else 'off'}")
    
    def read_sensor(self, sensor_type: str) -> Dict[str, Any]:
        """Read sensor data"""
        return self.send_command(f"/sensor/{sensor_type}")
    
    def restart(self) -> Dict[str, Any]:
        """Restart device"""
        return self.send_command("/restart", method="POST")
