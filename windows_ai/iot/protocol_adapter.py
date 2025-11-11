"""
Protocol Abstraction Layer
Unified interface for all IoT protocols (MQTT, CoAP, WebSocket, HTTP, Zigbee, Z-Wave)
"""
from typing import Dict, Any, Optional, Callable
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class Protocol(Enum):
    """Supported IoT protocols"""
    MQTT = "mqtt"
    COAP = "coap"
    WEBSOCKET = "websocket"
    HTTP = "http"
    ZIGBEE = "zigbee"
    ZWAVE = "zwave"
    BLE = "ble"


class ProtocolAdapter:
    """
    Unified protocol adapter
    Provides consistent interface across different IoT protocols
    """

    def __init__(self):
        self.connections = {}
        self._init_protocols()

    def _init_protocols(self):
        """Initialize protocol clients"""
        try:
            from .mqtt_client import MQTTClient
            self.mqtt = MQTTClient()
        except Exception as e:
            logger.warning(f"MQTT client initialization failed: {e}")
            self.mqtt = None

        try:
            from .coap_client import CoAPClient
            self.coap = CoAPClient()
        except Exception as e:
            logger.warning(f"CoAP client initialization failed: {e}")
            self.coap = None

        try:
            from .websocket_client import WebSocketClient
            self.websocket_class = WebSocketClient
        except Exception as e:
            logger.warning(f"WebSocket client initialization failed: {e}")
            self.websocket_class = None

        try:
            from .http_client import HTTPClient
            self.http_class = HTTPClient
        except Exception as e:
            logger.warning(f"HTTP client initialization failed: {e}")
            self.http_class = None

    def connect(self, protocol: Protocol, connection_id: str,
                **kwargs) -> Dict[str, Any]:
        """
        Connect to device using specified protocol

        Args:
            protocol: Protocol to use
            connection_id: Unique connection identifier
            **kwargs: Protocol-specific connection parameters

        Returns:
            Dict with connection status
        """
        if connection_id in self.connections:
            return {
                "status": "error",
                "message": f"Connection already exists: {connection_id}"
            }

        try:
            if protocol == Protocol.MQTT:
                result = self._connect_mqtt(connection_id, **kwargs)

            elif protocol == Protocol.COAP:
                result = {"status": "success", "message": "CoAP is connectionless"}
                self.connections[connection_id] = {
                    "protocol": Protocol.COAP,
                    "client": self.coap
                }

            elif protocol == Protocol.WEBSOCKET:
                result = self._connect_websocket(connection_id, **kwargs)

            elif protocol == Protocol.HTTP:
                result = self._connect_http(connection_id, **kwargs)

            elif protocol == Protocol.ZIGBEE:
                result = {"status": "error", "message": "Zigbee not yet implemented"}

            elif protocol == Protocol.ZWAVE:
                result = {"status": "error", "message": "Z-Wave not yet implemented"}

            else:
                result = {
                    "status": "error",
                    "message": f"Unsupported protocol: {protocol}"
                }

            return result

        except Exception as e:
            logger.error(f"Connect error: {e}")
            return {"status": "error", "message": str(e)}

    def disconnect(self, connection_id: str) -> Dict[str, Any]:
        """
        Disconnect from device

        Args:
            connection_id: Connection identifier

        Returns:
            Dict with status
        """
        if connection_id not in self.connections:
            return {
                "status": "error",
                "message": f"Connection not found: {connection_id}"
            }

        try:
            conn = self.connections[connection_id]
            protocol = conn["protocol"]

            if protocol == Protocol.MQTT:
                result = self.mqtt.disconnect()

            elif protocol == Protocol.WEBSOCKET:
                result = conn["client"].disconnect()

            elif protocol == Protocol.HTTP:
                conn["client"].close()
                result = {"status": "success", "message": "HTTP client closed"}

            else:
                result = {"status": "success", "message": "Disconnected"}

            # Remove connection
            del self.connections[connection_id]

            return result

        except Exception as e:
            logger.error(f"Disconnect error: {e}")
            return {"status": "error", "message": str(e)}

    def send_command(self, connection_id: str, command: str,
                    params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Send command to device

        Args:
            connection_id: Connection identifier
            command: Command name
            params: Command parameters

        Returns:
            Dict with response
        """
        if connection_id not in self.connections:
            return {
                "status": "error",
                "message": f"Connection not found: {connection_id}"
            }

        try:
            conn = self.connections[connection_id]
            protocol = conn["protocol"]
            params = params or {}

            if protocol == Protocol.MQTT:
                topic = conn.get("command_topic", f"devices/{connection_id}/commands")
                return self.mqtt.publish(topic, {"command": command, "params": params})

            elif protocol == Protocol.COAP:
                uri = conn.get("base_uri", f"coap://device/command")
                return self.coap.post(uri, {"command": command, "params": params})

            elif protocol == Protocol.WEBSOCKET:
                return conn["client"].send({
                    "type": "command",
                    "command": command,
                    "params": params
                })

            elif protocol == Protocol.HTTP:
                return conn["client"].post("/command", json_data={
                    "command": command,
                    "params": params
                })

            else:
                return {
                    "status": "error",
                    "message": f"Command not supported for protocol: {protocol}"
                }

        except Exception as e:
            logger.error(f"Send command error: {e}")
            return {"status": "error", "message": str(e)}

    def get_state(self, connection_id: str) -> Dict[str, Any]:
        """
        Get device state

        Args:
            connection_id: Connection identifier

        Returns:
            Dict with device state
        """
        if connection_id not in self.connections:
            return {
                "status": "error",
                "message": f"Connection not found: {connection_id}"
            }

        try:
            conn = self.connections[connection_id]
            protocol = conn["protocol"]

            if protocol == Protocol.COAP:
                uri = conn.get("state_uri", f"coap://device/state")
                return self.coap.get(uri)

            elif protocol == Protocol.HTTP:
                return conn["client"].get("/state")

            elif protocol == Protocol.WEBSOCKET:
                return conn["client"].send({"type": "get_state"})

            else:
                return {
                    "status": "error",
                    "message": f"Get state not supported for protocol: {protocol}"
                }

        except Exception as e:
            logger.error(f"Get state error: {e}")
            return {"status": "error", "message": str(e)}

    def subscribe(self, connection_id: str, topic: str,
                 callback: Callable) -> Dict[str, Any]:
        """
        Subscribe to device updates

        Args:
            connection_id: Connection identifier
            topic: Topic/resource to subscribe to
            callback: Callback function for updates

        Returns:
            Dict with status
        """
        if connection_id not in self.connections:
            return {
                "status": "error",
                "message": f"Connection not found: {connection_id}"
            }

        try:
            conn = self.connections[connection_id]
            protocol = conn["protocol"]

            if protocol == Protocol.MQTT:
                return self.mqtt.subscribe(topic, callback=callback)

            elif protocol == Protocol.COAP:
                uri = conn.get("base_uri", f"coap://device/{topic}")
                return self.coap.observe(uri, callback)

            elif protocol == Protocol.WEBSOCKET:
                conn["client"].add_message_handler(callback)
                return {"status": "success", "message": "Handler added"}

            else:
                return {
                    "status": "error",
                    "message": f"Subscribe not supported for protocol: {protocol}"
                }

        except Exception as e:
            logger.error(f"Subscribe error: {e}")
            return {"status": "error", "message": str(e)}

    def list_connections(self) -> Dict[str, Any]:
        """List all active connections"""
        connections = []

        for conn_id, conn in self.connections.items():
            connections.append({
                "connection_id": conn_id,
                "protocol": conn["protocol"].value,
                "metadata": conn.get("metadata", {})
            })

        return {
            "status": "success",
            "connections": connections,
            "count": len(connections)
        }

    def get_connection_info(self, connection_id: str) -> Dict[str, Any]:
        """Get connection information"""
        if connection_id not in self.connections:
            return {
                "status": "error",
                "message": f"Connection not found: {connection_id}"
            }

        conn = self.connections[connection_id]

        return {
            "status": "success",
            "connection": {
                "connection_id": connection_id,
                "protocol": conn["protocol"].value,
                "metadata": conn.get("metadata", {})
            }
        }

    # Protocol-specific connection methods
    def _connect_mqtt(self, connection_id: str, **kwargs) -> Dict[str, Any]:
        """Connect via MQTT"""
        if not self.mqtt:
            return {"status": "error", "message": "MQTT client not available"}

        result = self.mqtt.connect(**kwargs)

        if result["status"] == "success":
            self.connections[connection_id] = {
                "protocol": Protocol.MQTT,
                "client": self.mqtt,
                "command_topic": kwargs.get("command_topic"),
                "metadata": kwargs
            }

        return result

    def _connect_websocket(self, connection_id: str, **kwargs) -> Dict[str, Any]:
        """Connect via WebSocket"""
        if not self.websocket_class:
            return {"status": "error", "message": "WebSocket client not available"}

        client = self.websocket_class()
        result = client.connect(**kwargs)

        if result["status"] == "success":
            self.connections[connection_id] = {
                "protocol": Protocol.WEBSOCKET,
                "client": client,
                "metadata": kwargs
            }

        return result

    def _connect_http(self, connection_id: str, **kwargs) -> Dict[str, Any]:
        """Connect via HTTP"""
        if not self.http_class:
            return {"status": "error", "message": "HTTP client not available"}

        client = self.http_class(**kwargs)

        self.connections[connection_id] = {
            "protocol": Protocol.HTTP,
            "client": client,
            "metadata": kwargs
        }

        return {
            "status": "success",
            "message": "HTTP client initialized",
            "base_url": kwargs.get("base_url")
        }
