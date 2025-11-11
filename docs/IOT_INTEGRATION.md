# IoT Integration Guide

Complete guide for Windows-AI IoT device management and integration.

## Table of Contents

1. [Overview](#overview)
2. [Device Discovery](#device-discovery)
3. [Supported Protocols](#supported-protocols)
4. [Device Adapters](#device-adapters)
5. [Security](#security)
6. [Examples](#examples)

## Overview

Windows-AI provides comprehensive IoT integration with:
- **Multi-protocol support**: MQTT, CoAP, WebSocket, HTTP, Zigbee, Z-Wave
- **Auto-discovery**: mDNS/Bonjour, SSDP/UPnP, BLE scanning
- **10+ device adapters**: Philips Hue, Nest, Ring, Wyze, TP-Link, Sonos, Home Assistant, Tuya, ESP32, Arduino
- **Persistent storage**: Device registry with auto-save
- **Network topology mapping**: Visual network relationships

## Device Discovery

### mDNS/Bonjour Discovery

Discover devices using Zeroconf/Bonjour protocol:

```python
from windows_ai.iot.discovery import DeviceDiscovery

discovery = DeviceDiscovery()

# Start discovery
discovery.start_discovery(protocols=['mdns'], duration=30)

# Get discovered devices
result = discovery.get_discovered_devices()
print(f"Found {result['count']} devices")
```

### SSDP/UPnP Discovery

Discover UPnP devices (smart TVs, media players, routers):

```python
discovery.start_discovery(protocols=['ssdp'], duration=30)
```

### Bluetooth LE Scanning

Discover BLE devices (wearables, sensors, beacons):

```python
discovery.start_discovery(protocols=['ble'], duration=30, rssi_threshold=-70)
```

### All Protocols

Discover using all available protocols:

```python
discovery.start_discovery(protocols=['mdns', 'ssdp', 'ble'], duration=60)
```

## Supported Protocols

### MQTT

Publish/Subscribe messaging for IoT devices:

```python
from windows_ai.iot.mqtt_client import MQTTClient

client = MQTTClient()
client.connect(broker="mqtt.example.com", port=1883)
client.publish("sensors/temperature", {"value": 22.5, "unit": "celsius"})
client.subscribe("devices/commands/#", callback=my_callback)
```

### CoAP

Constrained Application Protocol for resource-limited devices:

```python
from windows_ai.iot.coap_client import CoAPClient

client = CoAPClient()
result = client.get("coap://device.local/sensor/temp")
client.post("coap://device.local/actuator", {"state": "on"})
```

### WebSocket

Real-time bidirectional communication:

```python
from windows_ai.iot.websocket_client import WebSocketClient

client = WebSocketClient()
client.connect("ws://device.local:8080", on_message=handle_message)
client.send({"command": "get_status"})
```

### HTTP/REST

Standard HTTP API communication:

```python
from windows_ai.iot.http_client import IoTDeviceHTTPClient

client = IoTDeviceHTTPClient("http://device.local", api_key="your-key")
client.get_status()
client.send_command("turn_on", {"brightness": 80})
```

### Protocol Abstraction

Unified interface for all protocols:

```python
from windows_ai.iot.protocol_adapter import ProtocolAdapter, Protocol

adapter = ProtocolAdapter()
adapter.connect(Protocol.MQTT, "device1", broker="mqtt.local", port=1883)
adapter.send_command("device1", "turn_on")
adapter.get_state("device1")
```

## Device Adapters

### Philips Hue

```python
from iot.adapters.phillips_hue_adapter import PhillipsHueAdapter

hue = PhillipsHueAdapter(bridge_ip="192.168.1.100", api_key="your-api-key")
hue.get_lights()
hue.set_light(light_id=1, on=True, brightness=200)
hue.set_group(group_id=1, on=True)
hue.activate_scene("romantic")
```

### Home Assistant

```python
from iot.adapters.homeassistant_adapter import HomeAssistantAdapter

ha = HomeAssistantAdapter(
    base_url="http://homeassistant.local:8123",
    access_token="your-token"
)
ha.get_states()
ha.turn_on("light.living_room")
ha.set_light("light.bedroom", brightness=150, rgb_color=[255, 200, 100])
ha.set_climate("climate.thermostat", temperature=22.0)
```

### TP-Link Kasa

```python
from iot.adapters.tp_link_adapter import TPLinkAdapter

device = TPLinkAdapter(device_ip="192.168.1.150")
device.get_info()
device.turn_on()
device.set_brightness(75)
device.get_energy_usage()
```

### ESP32/ESP8266

```python
from iot.adapters.esp_adapter import ESPAdapter

esp = ESPAdapter(device_ip="192.168.1.200")
esp.get_status()
esp.control_gpio(pin=2, state=True)
esp.read_sensor("temperature")
```

### Arduino

```python
from iot.adapters.arduino_adapter import ArduinoAdapter

arduino = ArduinoAdapter(port="/dev/ttyUSB0", baudrate=9600)
arduino.read_analog(pin=A0)
arduino.write_digital(pin=13, state=True)
arduino.write_pwm(pin=9, value=128)
```

## Security

### TLS/SSL Encryption

Enable TLS for MQTT:

```python
client.connect(broker="mqtt.example.com", port=8883, use_tls=True)
```

### API Key Authentication

```python
http_client = HTTPClient(
    base_url="https://api.device.com",
    api_key="your-api-key-here"
)
```

### Basic Authentication

```python
http_client = HTTPClient(
    base_url="https://device.local",
    auth=("username", "password")
)
```

### Rate Limiting

Built-in rate limiting prevents abuse:
- Max 100 requests per device per minute
- Automatic backoff on errors

## Network Topology

Map device relationships:

```python
from windows_ai.iot.topology import NetworkTopology

topo = NetworkTopology()
topo.add_node("router1", "gateway", "Main Router", ip_address="192.168.1.1")
topo.add_node("hue_bridge", "hub", "Hue Bridge", ip_address="192.168.1.100")
topo.add_link("router1", "hue_bridge", "ethernet")

# Export topology
topo.export_topology("network_map.json")
topo.export_topology("network_map.dot", format="dot")
```

## Device Manager

Centralized device management with persistent storage:

```python
from windows_ai.iot.device_manager import DeviceManager

manager = DeviceManager()

# Register device
manager.register_device(
    device_id="living_room_light",
    device_type="light",
    name="Living Room Light",
    ip_address="192.168.1.150",
    capabilities=["on_off", "dimming", "color"]
)

# List devices
devices = manager.list_devices(device_type="light")

# Device groups
manager.create_device_group("bedroom", ["light1", "light2", "switch1"])
manager.get_group_devices("bedroom")

# Statistics
stats = manager.get_device_statistics()
```

## Troubleshooting

### Discovery Issues

**Problem**: No devices discovered

**Solutions**:
- Ensure devices are on the same network
- Check firewall settings (allow UDP multicast)
- Verify mDNS/Bonjour is enabled on network
- Increase discovery duration

### Connection Failures

**Problem**: Cannot connect to device

**Solutions**:
- Verify device IP address is correct
- Check device is powered on and connected
- Test with ping or curl
- Verify API key/credentials
- Check TLS/SSL settings

### Protocol Errors

**Problem**: Protocol not available

**Solutions**:
- Install required libraries: `pip install paho-mqtt aiocoap websocket-client`
- Check import statements
- Verify protocol is supported by device

## Best Practices

1. **Use device groups** for batch operations
2. **Enable persistent storage** for device registry
3. **Implement error handling** for network failures
4. **Use appropriate protocols** (MQTT for sensors, HTTP for control)
5. **Secure all connections** with TLS/authentication
6. **Monitor device health** with regular pings
7. **Rate limit requests** to prevent device overload

## Examples

### Complete Home Automation

```python
from windows_ai.iot.device_manager import DeviceManager
from iot.adapters.phillips_hue_adapter import PhillipsHueAdapter
from iot.adapters.homeassistant_adapter import HomeAssistantAdapter

# Initialize
manager = DeviceManager()
hue = PhillipsHueAdapter(bridge_ip="192.168.1.100", api_key="key")
ha = HomeAssistantAdapter("http://ha.local:8123", "token")

# Morning routine
hue.set_group(group_id=1, on=True, brightness=100)  # Bedroom lights
ha.set_climate("climate.bedroom", temperature=21.0)  # Heating
ha.call_service("media_player", "play_media", "media_player.bedroom")  # Music

# Evening routine
hue.activate_scene("romantic")
ha.turn_off("light.outdoor")
```

## API Reference

Full API documentation available at:
- Python: `help(windows_ai.iot)`
- TypeScript: `/apps/actions-api/src/iot.ts`

## Support

For issues and questions:
- GitHub: https://github.com/anthropics/windows-ai
- Documentation: https://docs.windows-ai.com
