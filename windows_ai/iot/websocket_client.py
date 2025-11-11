"""
WebSocket Client Module
Real-time WebSocket connections for IoT devices
"""
from typing import Dict, Any, Callable, Optional
import logging
import threading
import json
import time

logger = logging.getLogger(__name__)

try:
    import websocket
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False
    logger.warning("websocket-client not available. Install with: pip install websocket-client")


class WebSocketClient:
    """
    WebSocket client for real-time IoT device communication
    """

    def __init__(self):
        self.is_available = WEBSOCKET_AVAILABLE
        self.ws = None
        self.connected = False
        self.message_handlers = []
        self.connection_thread = None

    def connect(self, url: str, **kwargs) -> Dict[str, Any]:
        """
        Connect to WebSocket server

        Args:
            url: WebSocket URL (ws:// or wss://)
            header: Custom headers dict
            timeout: Connection timeout in seconds
            on_message: Message callback function(message)
            on_error: Error callback function(error)
            on_close: Close callback function()

        Returns:
            Dict with connection status
        """
        if not self.is_available:
            return {
                "status": "error",
                "message": "websocket-client not available. Install with: pip install websocket-client"
            }

        if self.connected:
            return {
                "status": "error",
                "message": "Already connected"
            }

        try:
            # Get callbacks
            on_message = kwargs.get('on_message')
            on_error = kwargs.get('on_error')
            on_close = kwargs.get('on_close')

            # Create WebSocket
            self.ws = websocket.WebSocketApp(
                url,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close
            )

            # Register user callbacks
            if on_message:
                self.message_handlers.append(on_message)

            # Store callbacks
            self.user_error_callback = on_error
            self.user_close_callback = on_close

            # Start connection in background thread
            self.connection_thread = threading.Thread(
                target=self._run_forever,
                daemon=True
            )
            self.connection_thread.start()

            # Wait for connection
            timeout = kwargs.get('timeout', 10)
            start_time = time.time()
            while not self.connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)

            if self.connected:
                logger.info(f"Connected to WebSocket: {url}")
                return {
                    "status": "success",
                    "message": "Connected to WebSocket",
                    "url": url
                }
            else:
                return {
                    "status": "error",
                    "message": "Connection timeout"
                }

        except Exception as e:
            logger.error(f"WebSocket connect error: {e}")
            return {"status": "error", "message": str(e)}

    def disconnect(self) -> Dict[str, Any]:
        """Disconnect from WebSocket server"""
        if not self.connected:
            return {
                "status": "error",
                "message": "Not connected"
            }

        try:
            if self.ws:
                self.ws.close()

            self.connected = False
            logger.info("Disconnected from WebSocket")

            return {
                "status": "success",
                "message": "Disconnected from WebSocket"
            }

        except Exception as e:
            logger.error(f"WebSocket disconnect error: {e}")
            return {"status": "error", "message": str(e)}

    def send(self, data: Any, as_json: bool = True) -> Dict[str, Any]:
        """
        Send message to WebSocket server

        Args:
            data: Message data
            as_json: Encode as JSON

        Returns:
            Dict with send status
        """
        if not self.connected:
            return {
                "status": "error",
                "message": "Not connected"
            }

        try:
            # Encode message
            if as_json and not isinstance(data, (str, bytes)):
                data = json.dumps(data)

            # Send
            self.ws.send(data)

            return {
                "status": "success",
                "message": "Message sent"
            }

        except Exception as e:
            logger.error(f"WebSocket send error: {e}")
            return {"status": "error", "message": str(e)}

    def send_binary(self, data: bytes) -> Dict[str, Any]:
        """Send binary data"""
        if not self.connected:
            return {
                "status": "error",
                "message": "Not connected"
            }

        try:
            self.ws.send(data, opcode=websocket.ABNF.OPCODE_BINARY)

            return {
                "status": "success",
                "message": "Binary data sent"
            }

        except Exception as e:
            logger.error(f"WebSocket send binary error: {e}")
            return {"status": "error", "message": str(e)}

    def add_message_handler(self, handler: Callable):
        """
        Add message handler callback

        Args:
            handler: Callback function(message)
        """
        self.message_handlers.append(handler)

    def remove_message_handler(self, handler: Callable):
        """Remove message handler"""
        if handler in self.message_handlers:
            self.message_handlers.remove(handler)

    def get_status(self) -> Dict[str, Any]:
        """Get client status"""
        return {
            "status": "success",
            "available": self.is_available,
            "connected": self.connected,
            "handlers": len(self.message_handlers)
        }

    # Internal callbacks
    def _on_open(self, ws):
        """Internal open callback"""
        self.connected = True
        logger.debug("WebSocket connection opened")

    def _on_message(self, ws, message):
        """Internal message callback"""
        try:
            # Try to parse as JSON
            try:
                message = json.loads(message)
            except (json.JSONDecodeError, TypeError):
                pass  # Keep as string/bytes

            # Call user handlers
            for handler in self.message_handlers:
                try:
                    handler(message)
                except Exception as e:
                    logger.error(f"Message handler error: {e}")

        except Exception as e:
            logger.error(f"Message processing error: {e}")

    def _on_error(self, ws, error):
        """Internal error callback"""
        logger.error(f"WebSocket error: {error}")

        # Call user callback
        if hasattr(self, 'user_error_callback') and self.user_error_callback:
            try:
                self.user_error_callback(error)
            except Exception as e:
                logger.error(f"User error callback error: {e}")

    def _on_close(self, ws, close_status_code, close_msg):
        """Internal close callback"""
        self.connected = False
        logger.debug(f"WebSocket closed: {close_status_code} - {close_msg}")

        # Call user callback
        if hasattr(self, 'user_close_callback') and self.user_close_callback:
            try:
                self.user_close_callback()
            except Exception as e:
                logger.error(f"User close callback error: {e}")

    def _run_forever(self):
        """Run WebSocket forever (in background thread)"""
        try:
            self.ws.run_forever()
        except Exception as e:
            logger.error(f"WebSocket run error: {e}")


class WebSocketDeviceClient:
    """
    High-level WebSocket client for IoT device control
    """

    def __init__(self):
        self.client = WebSocketClient()
        self.device_id = None

    def connect_device(self, url: str, device_id: str,
                      on_update: Callable = None) -> Dict[str, Any]:
        """
        Connect to IoT device via WebSocket

        Args:
            url: WebSocket URL
            device_id: Device identifier
            on_update: Callback for device updates

        Returns:
            Dict with status
        """
        self.device_id = device_id

        # Add update handler if provided
        if on_update:
            self.client.add_message_handler(on_update)

        # Connect
        result = self.client.connect(url)

        if result["status"] == "success":
            # Send authentication/identification
            self.client.send({
                "type": "identify",
                "device_id": device_id
            })

        return result

    def send_command(self, command: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Send command to device

        Args:
            command: Command name
            params: Command parameters

        Returns:
            Dict with status
        """
        return self.client.send({
            "type": "command",
            "device_id": self.device_id,
            "command": command,
            "params": params or {}
        })

    def request_state(self) -> Dict[str, Any]:
        """Request device state"""
        return self.client.send({
            "type": "get_state",
            "device_id": self.device_id
        })

    def disconnect(self) -> Dict[str, Any]:
        """Disconnect from device"""
        return self.client.disconnect()

    def get_status(self) -> Dict[str, Any]:
        """Get connection status"""
        return self.client.get_status()
