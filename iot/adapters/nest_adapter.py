"""Google Nest Thermostat/Camera Adapter"""
from typing import Dict, Any
import logging
import requests

logger = logging.getLogger(__name__)

class NestAdapter:
    """Adapter for Google Nest devices"""
    
    def __init__(self, access_token: str, project_id: str):
        self.access_token = access_token
        self.project_id = project_id
        self.base_url = "https://smartdevicemanagement.googleapis.com/v1"
        self.headers = {"Authorization": f"Bearer {access_token}"}
    
    def list_devices(self) -> Dict[str, Any]:
        """List all Nest devices"""
        try:
            url = f"{self.base_url}/enterprises/{self.project_id}/devices"
            response = requests.get(url, headers=self.headers, timeout=10)
            return {"status": "success", "devices": response.json()}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_device(self, device_id: str) -> Dict[str, Any]:
        """Get device information"""
        try:
            url = f"{self.base_url}/{device_id}"
            response = requests.get(url, headers=self.headers, timeout=10)
            return {"status": "success", "device": response.json()}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def set_thermostat_mode(self, device_id: str, mode: str) -> Dict[str, Any]:
        """Set thermostat mode (HEAT, COOL, HEATCOOL, OFF)"""
        try:
            url = f"{self.base_url}/{device_id}:executeCommand"
            data = {"command": "sdm.devices.commands.ThermostatMode.SetMode", "params": {"mode": mode}}
            response = requests.post(url, headers=self.headers, json=data, timeout=10)
            return {"status": "success", "response": response.json()}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def set_temperature(self, device_id: str, temperature: float) -> Dict[str, Any]:
        """Set target temperature"""
        try:
            url = f"{self.base_url}/{device_id}:executeCommand"
            data = {"command": "sdm.devices.commands.ThermostatTemperatureSetpoint.SetHeat", 
                   "params": {"heatCelsius": temperature}}
            response = requests.post(url, headers=self.headers, json=data, timeout=10)
            return {"status": "success", "response": response.json()}
        except Exception as e:
            return {"status": "error", "message": str(e)}
