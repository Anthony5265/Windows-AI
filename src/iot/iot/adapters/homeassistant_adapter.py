"""
Home Assistant Integration Adapter
Universal adapter for Home Assistant smart home platform
"""
from typing import Dict, Any, List
import logging
import requests

logger = logging.getLogger(__name__)


class HomeAssistantAdapter:
    """Adapter for Home Assistant"""

    def __init__(self, base_url: str, access_token: str):
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

    def get_states(self) -> Dict[str, Any]:
        """Get all entity states"""
        try:
            response = requests.get(f"{self.base_url}/api/states",
                                   headers=self.headers, timeout=10)
            response.raise_for_status()
            return {"status": "success", "states": response.json()}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_entity(self, entity_id: str) -> Dict[str, Any]:
        """Get specific entity state"""
        try:
            response = requests.get(f"{self.base_url}/api/states/{entity_id}",
                                   headers=self.headers, timeout=10)
            response.raise_for_status()
            return {"status": "success", "entity": response.json()}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def call_service(self, domain: str, service: str,
                    entity_id: str = None, **kwargs) -> Dict[str, Any]:
        """Call Home Assistant service"""
        try:
            data = {"entity_id": entity_id} if entity_id else {}
            data.update(kwargs)

            response = requests.post(
                f"{self.base_url}/api/services/{domain}/{service}",
                headers=self.headers, json=data, timeout=10
            )
            response.raise_for_status()
            return {"status": "success", "response": response.json()}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def turn_on(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        """Turn on entity"""
        domain = entity_id.split('.')[0]
        return self.call_service(domain, "turn_on", entity_id, **kwargs)

    def turn_off(self, entity_id: str) -> Dict[str, Any]:
        """Turn off entity"""
        domain = entity_id.split('.')[0]
        return self.call_service(domain, "turn_off", entity_id)

    def set_light(self, entity_id: str, brightness: int = None,
                  rgb_color: List[int] = None, color_temp: int = None) -> Dict[str, Any]:
        """Control light"""
        params = {}
        if brightness is not None:
            params["brightness"] = brightness
        if rgb_color is not None:
            params["rgb_color"] = rgb_color
        if color_temp is not None:
            params["color_temp"] = color_temp
        return self.call_service("light", "turn_on", entity_id, **params)

    def set_climate(self, entity_id: str, temperature: float = None,
                   hvac_mode: str = None) -> Dict[str, Any]:
        """Control climate/thermostat"""
        params = {}
        if temperature is not None:
            params["temperature"] = temperature
        if hvac_mode is not None:
            params["hvac_mode"] = hvac_mode
        return self.call_service("climate", "set_temperature", entity_id, **params)

    def trigger_automation(self, entity_id: str) -> Dict[str, Any]:
        """Trigger automation"""
        return self.call_service("automation", "trigger", entity_id)

    def get_config(self) -> Dict[str, Any]:
        """Get Home Assistant configuration"""
        try:
            response = requests.get(f"{self.base_url}/api/config",
                                   headers=self.headers, timeout=10)
            response.raise_for_status()
            return {"status": "success", "config": response.json()}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_services(self) -> Dict[str, Any]:
        """Get available services"""
        try:
            response = requests.get(f"{self.base_url}/api/services",
                                   headers=self.headers, timeout=10)
            response.raise_for_status()
            return {"status": "success", "services": response.json()}
        except Exception as e:
            return {"status": "error", "message": str(e)}
