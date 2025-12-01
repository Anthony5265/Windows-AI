"""
Philips Hue Smart Lighting Adapter
Controls Philips Hue lights, bridges, and scenes
"""
from typing import Dict, Any, List
import logging
import requests

logger = logging.getLogger(__name__)


class PhillipsHueAdapter:
    """Adapter for Philips Hue smart lighting system"""

    def __init__(self, bridge_ip: str, api_key: str = None):
        self.bridge_ip = bridge_ip
        self.api_key = api_key
        self.base_url = f"http://{bridge_ip}/api"

    def discover_bridge(self) -> Dict[str, Any]:
        """Discover Hue bridge on network"""
        try:
            response = requests.get("https://discovery.meethue.com/", timeout=5)
            bridges = response.json()
            return {"status": "success", "bridges": bridges}
        except Exception as e:
            logger.error(f"Bridge discovery error: {e}")
            return {"status": "error", "message": str(e)}

    def register(self, app_name: str = "Windows-AI") -> Dict[str, Any]:
        """Register application with bridge"""
        try:
            data = {"devicetype": app_name}
            response = requests.post(f"{self.base_url}", json=data, timeout=5)
            result = response.json()[0]

            if "success" in result:
                self.api_key = result["success"]["username"]
                return {
                    "status": "success",
                    "api_key": self.api_key,
                    "message": "Press bridge button within 30 seconds"
                }
            else:
                return {"status": "error", "message": result.get("error", {}).get("description")}

        except Exception as e:
            logger.error(f"Registration error: {e}")
            return {"status": "error", "message": str(e)}

    def get_lights(self) -> Dict[str, Any]:
        """Get all lights"""
        try:
            url = f"{self.base_url}/{self.api_key}/lights"
            response = requests.get(url, timeout=5)
            lights = response.json()
            return {"status": "success", "lights": lights}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def set_light(self, light_id: int, on: bool = None, brightness: int = None,
                  hue: int = None, saturation: int = None, color_temp: int = None) -> Dict[str, Any]:
        """Control light state"""
        try:
            state = {}
            if on is not None:
                state["on"] = on
            if brightness is not None:
                state["bri"] = max(0, min(254, brightness))
            if hue is not None:
                state["hue"] = max(0, min(65535, hue))
            if saturation is not None:
                state["sat"] = max(0, min(254, saturation))
            if color_temp is not None:
                state["ct"] = max(153, min(500, color_temp))

            url = f"{self.base_url}/{self.api_key}/lights/{light_id}/state"
            response = requests.put(url, json=state, timeout=5)
            return {"status": "success", "response": response.json()}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_groups(self) -> Dict[str, Any]:
        """Get all groups/rooms"""
        try:
            url = f"{self.base_url}/{self.api_key}/groups"
            response = requests.get(url, timeout=5)
            return {"status": "success", "groups": response.json()}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def set_group(self, group_id: int, on: bool = None, brightness: int = None) -> Dict[str, Any]:
        """Control group state"""
        try:
            state = {}
            if on is not None:
                state["on"] = on
            if brightness is not None:
                state["bri"] = max(0, min(254, brightness))

            url = f"{self.base_url}/{self.api_key}/groups/{group_id}/action"
            response = requests.put(url, json=state, timeout=5)
            return {"status": "success", "response": response.json()}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_scenes(self) -> Dict[str, Any]:
        """Get all scenes"""
        try:
            url = f"{self.base_url}/{self.api_key}/scenes"
            response = requests.get(url, timeout=5)
            return {"status": "success", "scenes": response.json()}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def activate_scene(self, scene_id: str, group_id: int = 0) -> Dict[str, Any]:
        """Activate scene"""
        try:
            url = f"{self.base_url}/{self.api_key}/groups/{group_id}/action"
            response = requests.put(url, json={"scene": scene_id}, timeout=5)
            return {"status": "success", "response": response.json()}
        except Exception as e:
            return {"status": "error", "message": str(e)}
