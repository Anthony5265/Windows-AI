"""
TP-Link Smart Device Adapter
Controls TP-Link Kasa smart plugs, switches, and bulbs
"""
from typing import Dict, Any
import logging
import requests
import json

logger = logging.getLogger(__name__)


class TPLinkAdapter:
    """Adapter for TP-Link Kasa devices"""

    def __init__(self, device_ip: str):
        self.device_ip = device_ip
        self.port = 9999

    def send_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Send command to TP-Link device"""
        try:
            import socket
            
            # Encrypt command (TP-Link encryption)
            encrypted = self._encrypt(json.dumps(command))
            
            # Send to device
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.device_ip, self.port))
            sock.send(encrypted)
            
            # Receive response
            data = sock.recv(4096)
            sock.close()
            
            # Decrypt response
            decrypted = self._decrypt(data[4:])  # Skip first 4 bytes
            response = json.loads(decrypted)
            
            return {"status": "success", "response": response}
            
        except Exception as e:
            logger.error(f"TP-Link command error: {e}")
            return {"status": "error", "message": str(e)}

    def get_info(self) -> Dict[str, Any]:
        """Get device information"""
        command = {"system": {"get_sysinfo": {}}}
        return self.send_command(command)

    def turn_on(self) -> Dict[str, Any]:
        """Turn device on"""
        command = {"system": {"set_relay_state": {"state": 1}}}
        return self.send_command(command)

    def turn_off(self) -> Dict[str, Any]:
        """Turn device off"""
        command = {"system": {"set_relay_state": {"state": 0}}}
        return self.send_command(command)

    def set_brightness(self, brightness: int) -> Dict[str, Any]:
        """Set bulb brightness (0-100)"""
        command = {
            "smartlife.iot.smartbulb.lightingservice": {
                "transition_light_state": {
                    "brightness": max(0, min(100, brightness))
                }
            }
        }
        return self.send_command(command)

    def set_color_temp(self, color_temp: int) -> Dict[str, Any]:
        """Set color temperature (2500-9000K)"""
        command = {
            "smartlife.iot.smartbulb.lightingservice": {
                "transition_light_state": {
                    "color_temp": max(2500, min(9000, color_temp))
                }
            }
        }
        return self.send_command(command)

    def get_energy_usage(self) -> Dict[str, Any]:
        """Get energy usage statistics"""
        command = {"emeter": {"get_realtime": {}}}
        return self.send_command(command)

    def _encrypt(self, data: str) -> bytes:
        """TP-Link encryption"""
        key = 171
        result = bytearray(4)  # 4-byte header
        for byte in data.encode('utf-8'):
            key = key ^ byte
            result.append(key)
        return bytes(result)

    def _decrypt(self, data: bytes) -> str:
        """TP-Link decryption"""
        key = 171
        result = []
        for byte in data:
            val = key ^ byte
            key = byte
            result.append(val)
        return bytes(result).decode('utf-8')
