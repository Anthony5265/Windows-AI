from __future__ import annotations

import os
import ssl
import threading
import time
from typing import List, Optional

try:
    import paho.mqtt.client as mqtt
except Exception:  # pragma: no cover
    mqtt = None  # type: ignore

from .models import Device, DeviceAdapter


class MQTTAdapter(DeviceAdapter):
    """Adapter for MQTT devices.

    Connects to an MQTT broker (if configured) and performs lightweight
    discovery using Home Assistant MQTT Discovery topics. Falls back to a
    static device when no broker is available.
    """

    protocol = "mqtt"

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        tls: bool = False,
        client_id: Optional[str] = None,
        timeout_sec: int = 3,
    ) -> None:
        self.host = host or os.environ.get("MQTT_BROKER", "localhost")
        self.port = int(port or os.environ.get("MQTT_PORT", "1883"))
        self.username = username or os.environ.get("MQTT_USERNAME")
        self.password = password or os.environ.get("MQTT_PASSWORD")
        self.tls = tls or (os.environ.get("MQTT_TLS", "false").lower() == "true")
        self.client_id = client_id or os.environ.get("MQTT_CLIENT_ID", "windows-ai")
        self.timeout_sec = timeout_sec
        self._client: Optional["mqtt.Client"] = None

    def _build_client(self) -> Optional["mqtt.Client"]:
        if mqtt is None:
            return None
        client = mqtt.Client(client_id=self.client_id, clean_session=True)
        if self.username:
            client.username_pw_set(self.username, password=self.password)
        if self.tls:
            client.tls_set(cert_reqs=ssl.CERT_REQUIRED)
        return client

    def _try_connect(self) -> bool:
        client = self._build_client()
        if client is None:
            return False

        connected = threading.Event()

        def on_connect(_client, _userdata, _flags, rc):
            if rc == 0:
                connected.set()

        client.on_connect = on_connect
        try:
            client.connect(self.host, self.port, keepalive=10)
        except Exception:
            return False

        client.loop_start()
        connected.wait(self.timeout_sec)
        if not connected.is_set():
            client.loop_stop()
            try:
                client.disconnect()
            except Exception:
                pass
            return False

        self._client = client
        return True

    def discover(self) -> List[Device]:
        """Discover MQTT devices.

        If an MQTT broker is reachable, subscribe to Home Assistant discovery
        topics for a short window and collect announced devices. Otherwise,
        return a single fallback device so higher-level flows can proceed.
        """

        devices: List[Device] = []

        if self._try_connect():
            assert self._client is not None
            discovered = {}
            ready = threading.Event()

            def on_message(_client, _userdata, msg):
                try:
                    topic = msg.topic
                    payload = msg.payload.decode("utf-8", errors="ignore")
                except Exception:
                    return
                # Home Assistant discovery topics look like:
                # homeassistant/<component>/<object_id>/config
                if topic.startswith("homeassistant/") and topic.endswith("/config"):
                    parts = topic.split("/")
                    if len(parts) >= 3:
                        object_id = parts[2]
                        name = object_id.replace("_", " ")
                        discovered[object_id] = name

            self._client.on_message = on_message
            try:
                self._client.subscribe("homeassistant/+/+/config", qos=0)
            except Exception:
                # If subscription fails, fall back
                pass

            # Listen briefly for announcements
            start = time.time()
            while time.time() - start < self.timeout_sec:
                time.sleep(0.1)

            try:
                self._client.loop_stop()
                self._client.disconnect()
            except Exception:
                pass

            for object_id, name in discovered.items():
                devices.append(Device(id=f"mqtt-{object_id}", name=name, protocol=self.protocol))

        if not devices:
            devices.append(Device(id="mqtt-1", name="MQTT Sensor", protocol=self.protocol))
        return devices
