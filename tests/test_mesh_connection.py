import time

from mesh import MeshHub, MeshNode


def test_node_discovery_and_task_distribution():
    key = b"k" * 32
    hub = MeshHub(key=key)
    hub.start()

    received: list[str] = []

    def handler(task: str) -> None:
        received.append(task)

    node = MeshNode(handler, key=key)
    address = node.discover(hub.discovery_port, host="127.0.0.1")
    node.connect(address)
    # give threads time to connect
    time.sleep(0.1)

    hub.distribute_task("work")
    time.sleep(0.1)

    node.stop()
    hub.stop()

    assert "work" in received
