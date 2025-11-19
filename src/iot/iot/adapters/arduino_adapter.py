"""Arduino Device Adapter"""
from typing import Dict, Any
import logging
import time

logger = logging.getLogger(__name__)

class ArduinoAdapter:
    """Adapter for Arduino devices via serial"""
    
    def __init__(self, port: str, baudrate: int = 9600):
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self._connect()
    
    def _connect(self):
        """Connect to Arduino"""
        try:
            import serial
            self.serial = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2)  # Wait for Arduino to reset
        except ImportError:
            logger.warning("pyserial not available. Install with: pip install pyserial")
        except Exception as e:
            logger.error(f"Arduino connection error: {e}")
    
    def send_command(self, command: str) -> Dict[str, Any]:
        """Send command to Arduino"""
        if not self.serial:
            return {"status": "error", "message": "Serial not available or not connected"}
        try:
            self.serial.write(f"{command}\n".encode())
            time.sleep(0.1)
            response = self.serial.readline().decode().strip()
            return {"status": "success", "response": response}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def read_analog(self, pin: int) -> Dict[str, Any]:
        """Read analog pin"""
        return self.send_command(f"READ_ANALOG:{pin}")
    
    def read_digital(self, pin: int) -> Dict[str, Any]:
        """Read digital pin"""
        return self.send_command(f"READ_DIGITAL:{pin}")
    
    def write_digital(self, pin: int, state: bool) -> Dict[str, Any]:
        """Write to digital pin"""
        return self.send_command(f"WRITE_DIGITAL:{pin}:{'HIGH' if state else 'LOW'}")
    
    def write_pwm(self, pin: int, value: int) -> Dict[str, Any]:
        """Write PWM value (0-255)"""
        return self.send_command(f"WRITE_PWM:{pin}:{max(0, min(255, value))}")
    
    def close(self):
        """Close serial connection"""
        if self.serial:
            self.serial.close()
