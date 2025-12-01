# Mesh Networking

The mesh package provides lightweight peer discovery and task distribution for
local clusters. A hub advertises itself via UDP and accepts TCP connections from
nodes. Messages are encrypted using a simple XOR + HMAC based protocol to avoid
plaintext transmission.

## Starting a hub

```python
from mesh import MeshHub

hub = MeshHub()
hub.start()
print("Discovery port:", hub.discovery_port)
print("TCP port:", hub.port)
```

## Connecting a node

```python
from mesh import MeshNode

received = []

def handler(task: str) -> None:
    received.append(task)

node = MeshNode(handler)
address = node.discover(hub.discovery_port)
node.connect(address)
```

## Distributing work

```python
hub.distribute_task("hello")
```

Nodes receive tasks through the provided callback. When finished, stop the hub
and nodes with `stop()`.
