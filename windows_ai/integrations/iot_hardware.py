"""
IoT & Hardware Manager - 10+ Platforms
Home automation, sensors, smart devices
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional
from windows_ai.config.unified_config import WindowsAIConfig

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class IoTHardwareManager:
    """Unified IoT and hardware operations"""

    def __init__(self):
        self._config: Optional[WindowsAIConfig] = None
        self._initialized = False

    async def initialize(self, config: Optional[WindowsAIConfig] = None):
        if self._initialized:
            return
        
        self._config = config
        self._initialized = True

    # ==================== HOME ASSISTANT ====================

    async def cleanup(self):
        """Cleanup resources before shutdown"""
        try:
            # Close any open connections
            if hasattr(self, '_clients'):
                for client in self._clients.values():
                    if hasattr(client, 'close'):
                        await client.close() if asyncio.iscoroutinefunction(client.close) else client.close()
            
            # Reset initialization flag
            self._initialized = False
            logger.info(f"{self.__class__.__name__} cleanup completed")
            
        except Exception as e:
            logger.error(f"{self.__class__.__name__} cleanup failed: {e}")

    async def homeassistant_get_states(self) -> List[Dict]:
        """Get Home Assistant entity states"""
        import aiohttp

        base_url = os.environ.get("HOMEASSISTANT_URL", "http://localhost:8123")
        token = os.environ.get("HOMEASSISTANT_TOKEN")

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{base_url}/api/states",
                headers={"Authorization": f"Bearer {token}"}
            ) as response:
                return await response.json()

    async def homeassistant_call_service(self, domain: str, service: str, entity_id: str, data: Dict = None) -> Dict:
        """Call Home Assistant service"""
        import aiohttp

        base_url = os.environ.get("HOMEASSISTANT_URL", "http://localhost:8123")
        token = os.environ.get("HOMEASSISTANT_TOKEN")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{base_url}/api/services/{domain}/{service}",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={"entity_id": entity_id, **(data or {})}
            ) as response:
                return await response.json()

    async def homeassistant_turn_on(self, entity_id: str) -> Dict:
        """Turn on Home Assistant entity"""
        domain = entity_id.split(".")[0]
        return await self.homeassistant_call_service(domain, "turn_on", entity_id)

    async def homeassistant_turn_off(self, entity_id: str) -> Dict:
        """Turn off Home Assistant entity"""
        domain = entity_id.split(".")[0]
        return await self.homeassistant_call_service(domain, "turn_off", entity_id)

    # ==================== PHILIPS HUE ====================

    async def hue_get_lights(self) -> List[Dict]:
        """Get Philips Hue lights"""
        import aiohttp

        bridge_ip = os.environ.get("HUE_BRIDGE_IP")
        username = os.environ.get("HUE_USERNAME")

        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://{bridge_ip}/api/{username}/lights") as response:
                data = await response.json()
                return [{"id": k, "name": v["name"], "on": v["state"]["on"]} for k, v in data.items()]

    async def hue_set_light(self, light_id: str, on: bool = None, brightness: int = None, color: str = None) -> bool:
        """Set Philips Hue light state"""
        import aiohttp

        bridge_ip = os.environ.get("HUE_BRIDGE_IP")
        username = os.environ.get("HUE_USERNAME")

        state = {}
        if on is not None:
            state["on"] = on
        if brightness is not None:
            state["bri"] = brightness
        if color is not None:
            # Convert hex color to Philips Hue XY color space
            if color.startswith('#'):
                color = color[1:]
            # Parse RGB values
            try:
                r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
                # Normalize to 0-1
                r, g, b = r/255.0, g/255.0, b/255.0
                # Apply gamma correction
                r = pow((r + 0.055) / 1.055, 2.4) if r > 0.04045 else r / 12.92
                g = pow((g + 0.055) / 1.055, 2.4) if g > 0.04045 else g / 12.92
                b = pow((b + 0.055) / 1.055, 2.4) if b > 0.04045 else b / 12.92
                # Convert to XY using CIE 1931 color space
                X = r * 0.649926 + g * 0.103455 + b * 0.197109
                Y = r * 0.234327 + g * 0.743075 + b * 0.022598
                Z = r * 0.000000 + g * 0.053077 + b * 1.035763
                # Calculate xy coordinates
                total = X + Y + Z
                if total > 0:
                    x = X / total
                    y = Y / total
                    state["xy"] = [round(x, 4), round(y, 4)]
            except (ValueError, IndexError) as e:
                logger.warning(f"Invalid color format: {color}, error: {e}")

        async with aiohttp.ClientSession() as session:
            async with session.put(
                f"http://{bridge_ip}/api/{username}/lights/{light_id}/state",
                json=state
            ) as response:
                return response.status == 200

    # ==================== SMARTTHINGS ====================

    async def smartthings_get_devices(self) -> List[Dict]:
        """Get SmartThings devices"""
        import aiohttp

        token = os.environ.get("SMARTTHINGS_TOKEN")

        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.smartthings.com/v1/devices",
                headers={"Authorization": f"Bearer {token}"}
            ) as response:
                data = await response.json()
                return [{"id": d["deviceId"], "label": d["label"], "type": d["type"]}
                        for d in data.get("items", [])]

    async def smartthings_execute_command(self, device_id: str, capability: str, command: str, args: List = None) -> bool:
        """Execute SmartThings command"""
        import aiohttp

        token = os.environ.get("SMARTTHINGS_TOKEN")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://api.smartthings.com/v1/devices/{device_id}/commands",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={"commands": [{"capability": capability, "command": command, "arguments": args or []}]}
            ) as response:
                return response.status == 200

    # ==================== TUYA ====================

    async def tuya_get_devices(self) -> List[Dict]:
        """Get Tuya devices"""
        import aiohttp
        import time
        import hashlib
        import hmac

        client_id = os.environ.get("TUYA_CLIENT_ID")
        secret = os.environ.get("TUYA_SECRET")
        region = os.environ.get("TUYA_REGION", "us")

        timestamp = str(int(time.time() * 1000))
        string_to_sign = f"{client_id}{timestamp}"
        sign = hmac.new(secret.encode(), string_to_sign.encode(), hashlib.sha256).hexdigest().upper()

        async with aiohttp.ClientSession() as session:
            # Get access token
            async with session.get(
                f"https://openapi.tuya{region}.com/v1.0/token?grant_type=1",
                headers={"client_id": client_id, "sign": sign, "t": timestamp, "sign_method": "HMAC-SHA256"}
            ) as response:
                token_data = await response.json()
                access_token = token_data["result"]["access_token"]

            # Get devices
            async with session.get(
                f"https://openapi.tuya{region}.com/v1.0/users/{token_data['result']['uid']}/devices",
                headers={"client_id": client_id, "access_token": access_token}
            ) as response:
                data = await response.json()
                return data.get("result", [])

    # ==================== ARDUINO IOT CLOUD ====================

    async def arduino_get_things(self) -> List[Dict]:
        """Get Arduino IoT Cloud things"""
        import aiohttp

        client_id = os.environ.get("ARDUINO_CLIENT_ID")
        client_secret = os.environ.get("ARDUINO_CLIENT_SECRET")

        async with aiohttp.ClientSession() as session:
            # Get access token
            async with session.post(
                "https://api2.arduino.cc/iot/v1/clients/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "audience": "https://api2.arduino.cc/iot"
                }
            ) as response:
                token_data = await response.json()
                access_token = token_data["access_token"]

            # Get things
            async with session.get(
                "https://api2.arduino.cc/iot/v2/things",
                headers={"Authorization": f"Bearer {access_token}"}
            ) as response:
                return await response.json()

    # ==================== MQTT ====================

    async def mqtt_publish(self, topic: str, message: str, broker: str = None, port: int = 1883) -> bool:
        """Publish MQTT message"""
        import paho.mqtt.client as mqtt

        broker = broker or os.environ.get("MQTT_BROKER", "localhost")
        client = mqtt.Client()

        username = os.environ.get("MQTT_USERNAME")
        password = os.environ.get("MQTT_PASSWORD")
        if username:
            client.username_pw_set(username, password)

        client.connect(broker, port)
        result = client.publish(topic, message)
        client.disconnect()
        return result.rc == 0

    async def mqtt_subscribe(self, topic: str, callback, broker: str = None, port: int = 1883):
        """Subscribe to MQTT topic"""
        import paho.mqtt.client as mqtt

        broker = broker or os.environ.get("MQTT_BROKER", "localhost")
        client = mqtt.Client()

        username = os.environ.get("MQTT_USERNAME")
        password = os.environ.get("MQTT_PASSWORD")
        if username:
            client.username_pw_set(username, password)

        client.on_message = lambda c, u, m: callback(m.topic, m.payload.decode())
        client.connect(broker, port)
        client.subscribe(topic)
        client.loop_start()
        return client

    # ==================== PARTICLE ====================

    async def particle_get_devices(self) -> List[Dict]:
        """Get Particle devices"""
        import aiohttp

        token = os.environ.get("PARTICLE_ACCESS_TOKEN")

        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.particle.io/v1/devices",
                headers={"Authorization": f"Bearer {token}"}
            ) as response:
                return await response.json()

    async def particle_call_function(self, device_id: str, function_name: str, arg: str = "") -> Dict:
        """Call Particle device function"""
        import aiohttp

        token = os.environ.get("PARTICLE_ACCESS_TOKEN")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://api.particle.io/v1/devices/{device_id}/{function_name}",
                headers={"Authorization": f"Bearer {token}"},
                data={"arg": arg}
            ) as response:
                return await response.json()

    # ==================== AI IOT ====================

    async def ai_analyze_sensor_data(self, data: List[Dict], context: str = None) -> Dict:
        """AI-powered sensor data analysis"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": """Analyze IoT sensor data and provide:
1. Anomaly detection
2. Trend analysis
3. Predictions
4. Recommended actions
Return JSON with findings."""},
            {"role": "user", "content": f"Data: {data}\nContext: {context or 'General IoT monitoring'}"}
        ]

        response = await ai.chat(Provider.OPENAI, messages)
        import json
        try:
            return json.loads(response["content"])
        except:
            return {"analysis": response["content"]}

    def list_platforms(self) -> List[str]:
        return ["home_assistant", "philips_hue", "smartthings", "tuya", "arduino",
                "mqtt", "particle", "raspberry_pi", "esp32", "zigbee", "zwave"]
