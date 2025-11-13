# IoT Integration

The Windows AI platform includes basic adapters for common home automation
protocols. These adapters expose discovery and pairing APIs that can be used
from the Control Center GUI or programmatically.

## Supported Protocols

- **MQTT** – Lightweight publish/subscribe messaging for sensors and devices.
- **Matter** – Secure, IP‑based interoperability standard for smart home
  devices.
- **Zigbee** – Mesh‑network protocol used by many low‑power accessories.
- **Home Assistant** – Community‑driven home automation platform with broad
device support.

Use `iot.discover_devices()` to list devices for a protocol and
`iot.pair_device()` to pair with a selected device. Device events can be bound
to terminal workflows using `iot.WorkflowAutomation`.
