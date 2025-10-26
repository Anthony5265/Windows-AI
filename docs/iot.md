# IoT Adapter Configuration

The `iot` package exposes a small registry of protocol adapters.  Each adapter
implements discovery and pairing logic for a specific protocol and can be
registered at runtime, enabling a pluggable architecture.

## Built-in adapters

- **MQTT** – lightweight messaging for sensors and home automation.
- **Matter** – local, secure home automation standard.
- **Zigbee** – mesh network for low-power devices.

## Example configuration

### MQTT

```python
from iot import MQTTAdapter, register_adapter

# Configure custom broker settings
mqtt = MQTTAdapter()
register_adapter("mqtt", mqtt)
```

### Matter

```python
from iot import MatterAdapter, register_adapter

register_adapter("matter", MatterAdapter())
```

### Zigbee

```python
from iot import ZigbeeAdapter, register_adapter

register_adapter("zigbee", ZigbeeAdapter())
```

These snippets can be placed in your application startup code to make the
adapters available to the Control Center's discovery and pairing dialogs.
