# Mesh Networking

The `mesh` package offers a lightweight communication layer for small local
clusters. A hub advertises itself over UDP while nodes discover and connect via
TCP. Messages are encrypted using a shared key to avoid plaintext transmission
and include integrity checks.

## Setup

### Starting a hub

```python
from mesh import MeshHub

hub = MeshHub()
hub.start()
print("Discovery:", hub.discovery_port)
print("TCP:", hub.port)
```

### Connecting a node

```python
from mesh import MeshNode

received = []

def handle(task: str) -> None:
    received.append(task)

addr = MeshNode.discover(hub.discovery_port)
node = MeshNode(handle)
node.connect(addr)
```

### Sending tasks

```python
hub.distribute_task("hello")
```

Nodes invoke the provided callback for each task. When finished call
`node.stop()` and `hub.stop()`.

## GUI

Run `python -m control_center.mesh_gui` for a small interface that can start a
hub, discover it, connect a node, and broadcast tasks.

## API Reference

### MeshHub

- `MeshHub(host="127.0.0.1", port=0, discovery_port=0, key=None)` – create a
  hub using random ports by default.
- `start()` / `stop()` – manage the hub lifecycle.
- `distribute_task(task: str)` – encrypt and broadcast *task* to all connected
  nodes.

### MeshNode

- `MeshNode(handle_task, key=None)` – callback receives tasks as strings.
- `discover(port)` – broadcast a discovery packet returning the hub address.
- `connect(addr)` – connect to the hub and begin receiving tasks.
- `stop()` – end the connection and heartbeat thread.

### SecureProtocol

Used internally to provide XOR encryption with an HMAC for integrity.
