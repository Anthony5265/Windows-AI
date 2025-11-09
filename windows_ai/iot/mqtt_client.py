"""
MQTT Client Module
Publish/subscribe messaging for IoT devices
"""
from typing import Dict, Any, List, Optional, Callable
import logging
import json
import time

logger = logging.getLogger(__name__)

try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    logger.warning("paho-mqtt not available. Install with: pip install paho-mqtt")


class MQTTClient:
    """Production MQTT client for IoT messaging"""

    def __init__(self):
        self.is_available = MQTT_AVAILABLE
        self.client = None
        self.connected = False
        self.subscriptions = {}
        self.message_handlers = {}

    def connect(self, broker: str = "localhost", port: int = 1883,
                username: str = None, password: str = None,
                client_id: str = None, **kwargs) -> Dict[str, Any]:
        """
        Connect to MQTT broker

        Args:
            broker: MQTT broker hostname/IP
            port: MQTT broker port (default: 1883)
            username: Username for authentication
            password: Password for authentication
            client_id: Client identifier
            clean_session: Clean session flag
            keepalive: Keepalive interval in seconds

        Returns:
            Dict with connection status
        """
        if not self.is_available:
            return {
                "status": "error",
                "message": "paho-mqtt not available. Install with: pip install paho-mqtt"
            }

        try:
            clean_session = kwargs.get("clean_session", True)
            keepalive = kwargs.get("keepalive", 60)

            # Create client
            if client_id:
                self.client = mqtt.Client(client_id=client_id, clean_session=clean_session)
            else:
                self.client = mqtt.Client(clean_session=clean_session)

            # Set authentication
            if username and password:
                self.client.username_pw_set(username, password)

            # Set callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            self.client.on_subscribe = self._on_subscribe
            self.client.on_publish = self._on_publish

            # Connect
            self.client.connect(broker, port, keepalive)

            # Start network loop in background
            self.client.loop_start()

            # Wait for connection
            timeout = 10
            start_time = time.time()
            while not self.connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)

            if self.connected:
                return {
                    "status": "success",
                    "message": "Connected to MQTT broker",
                    "broker": broker,
                    "port": port
                }
            else:
                return {
                    "status": "error",
                    "message": "Connection timeout"
                }

        except Exception as e:
            logger.error(f"MQTT connect error: {e}")
            return {"status": "error", "message": str(e)}

    def disconnect(self) -> Dict[str, Any]:
        """Disconnect from MQTT broker"""
        if not self.client:
            return {
                "status": "error",
                "message": "Not connected"
            }

        try:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False

            return {
                "status": "success",
                "message": "Disconnected from MQTT broker"
            }

        except Exception as e:
            logger.error(f"MQTT disconnect error: {e}")
            return {"status": "error", "message": str(e)}

    def publish(self, topic: str, payload: Any, qos: int = 0,
                retain: bool = False, as_json: bool = True) -> Dict[str, Any]:
        """
        Publish message to topic

        Args:
            topic: MQTT topic
            payload: Message payload
            qos: Quality of Service (0, 1, or 2)
            retain: Retain message flag
            as_json: Encode payload as JSON

        Returns:
            Dict with publish status
        """
        if not self.connected:
            return {
                "status": "error",
                "message": "Not connected to broker"
            }

        try:
            # Encode payload
            if as_json and not isinstance(payload, (str, bytes)):
                payload = json.dumps(payload)

            # Publish
            result = self.client.publish(topic, payload, qos=qos, retain=retain)

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                return {
                    "status": "success",
                    "message": "Message published",
                    "topic": topic,
                    "mid": result.mid
                }
            else:
                return {
                    "status": "error",
                    "message": f"Publish failed with code {result.rc}"
                }

        except Exception as e:
            logger.error(f"MQTT publish error: {e}")
            return {"status": "error", "message": str(e)}

    def subscribe(self, topic: str, qos: int = 0,
                 callback: Callable = None) -> Dict[str, Any]:
        """
        Subscribe to topic

        Args:
            topic: MQTT topic (supports wildcards: +, #)
            qos: Quality of Service
            callback: Optional callback function for messages

        Returns:
            Dict with subscription status
        """
        if not self.connected:
            return {
                "status": "error",
                "message": "Not connected to broker"
            }

        try:
            result, mid = self.client.subscribe(topic, qos=qos)

            if result == mqtt.MQTT_ERR_SUCCESS:
                self.subscriptions[topic] = {
                    "qos": qos,
                    "mid": mid
                }

                if callback:
                    self.message_handlers[topic] = callback

                return {
                    "status": "success",
                    "message": "Subscribed to topic",
                    "topic": topic,
                    "qos": qos,
                    "mid": mid
                }
            else:
                return {
                    "status": "error",
                    "message": f"Subscribe failed with code {result}"
                }

        except Exception as e:
            logger.error(f"MQTT subscribe error: {e}")
            return {"status": "error", "message": str(e)}

    def unsubscribe(self, topic: str) -> Dict[str, Any]:
        """Unsubscribe from topic"""
        if not self.connected:
            return {
                "status": "error",
                "message": "Not connected to broker"
            }

        try:
            result, mid = self.client.unsubscribe(topic)

            if result == mqtt.MQTT_ERR_SUCCESS:
                if topic in self.subscriptions:
                    del self.subscriptions[topic]
                if topic in self.message_handlers:
                    del self.message_handlers[topic]

                return {
                    "status": "success",
                    "message": "Unsubscribed from topic",
                    "topic": topic
                }
            else:
                return {
                    "status": "error",
                    "message": f"Unsubscribe failed with code {result}"
                }

        except Exception as e:
            logger.error(f"MQTT unsubscribe error: {e}")
            return {"status": "error", "message": str(e)}

    def get_status(self) -> Dict[str, Any]:
        """Get client status"""
        return {
            "status": "success",
            "connected": self.connected,
            "subscriptions": list(self.subscriptions.keys()),
            "subscription_count": len(self.subscriptions)
        }

    # Callback handlers
    def _on_connect(self, client, userdata, flags, rc):
        """Internal connect callback"""
        if rc == 0:
            self.connected = True
            logger.info("Connected to MQTT broker")
        else:
            logger.error(f"MQTT connection failed with code {rc}")
            self.connected = False

    def _on_disconnect(self, client, userdata, rc):
        """Internal disconnect callback"""
        self.connected = False
        if rc != 0:
            logger.warning(f"Unexpected MQTT disconnection (code {rc})")

    def _on_message(self, client, userdata, msg):
        """Internal message callback"""
        try:
            # Try to decode payload
            payload = msg.payload.decode('utf-8')

            # Try to parse as JSON
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                pass  # Keep as string

            # Call user callback if registered
            for topic_pattern, callback in self.message_handlers.items():
                if mqtt.topic_matches_sub(topic_pattern, msg.topic):
                    try:
                        callback(msg.topic, payload)
                    except Exception as e:
                        logger.error(f"Message handler error: {e}")

            logger.debug(f"Received message on {msg.topic}: {payload}")

        except Exception as e:
            logger.error(f"Message processing error: {e}")

    def _on_subscribe(self, client, userdata, mid, granted_qos):
        """Internal subscribe callback"""
        logger.debug(f"Subscribed (mid: {mid}, qos: {granted_qos})")

    def _on_publish(self, client, userdata, mid):
        """Internal publish callback"""
        logger.debug(f"Published (mid: {mid})")

    # High-level convenience methods
    def publish_sensor_data(self, device_id: str, sensor_type: str,
                           value: Any, **kwargs) -> Dict[str, Any]:
        """
        Publish sensor data in standard format

        Args:
            device_id: Device identifier
            sensor_type: Type of sensor
            value: Sensor reading
            unit: Measurement unit
            timestamp: Unix timestamp (auto-generated if not provided)

        Returns:
            Dict with publish status
        """
        import time

        data = {
            "device_id": device_id,
            "sensor_type": sensor_type,
            "value": value,
            "unit": kwargs.get("unit"),
            "timestamp": kwargs.get("timestamp", time.time())
        }

        topic = f"sensors/{device_id}/{sensor_type}"
        return self.publish(topic, data, qos=kwargs.get("qos", 1))

    def publish_device_status(self, device_id: str, status: str,
                             **kwargs) -> Dict[str, Any]:
        """
        Publish device status

        Args:
            device_id: Device identifier
            status: Device status (online, offline, error, etc.)
            details: Optional status details

        Returns:
            Dict with publish status
        """
        import time

        data = {
            "device_id": device_id,
            "status": status,
            "details": kwargs.get("details"),
            "timestamp": time.time()
        }

        topic = f"devices/{device_id}/status"
        return self.publish(topic, data, qos=kwargs.get("qos", 1), retain=True)

    def subscribe_device_commands(self, device_id: str,
                                  callback: Callable) -> Dict[str, Any]:
        """
        Subscribe to device commands

        Args:
            device_id: Device identifier
            callback: Callback function(topic, command)

        Returns:
            Dict with subscription status
        """
        topic = f"devices/{device_id}/commands/#"
        return self.subscribe(topic, qos=1, callback=callback)
