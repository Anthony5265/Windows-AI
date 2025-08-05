import time

from mesh import MeshHub, MeshNode


def test_node_reconnects_after_disconnect():
    key = b"k" * 32
    hub = MeshHub(key=key)
    hub.start()

    received: list[str] = []

    def handler(task: str) -> None:
        received.append(task)

    node = MeshNode(handler, key=key, heartbeat_interval=0.1)
    address = node.discover(hub.discovery_port, host="127.0.0.1")
    node.connect(address)

    time.sleep(0.3)
    hub.distribute_task("one")
    time.sleep(0.3)
    assert "one" in received

    with hub._lock:
        conn = next(iter(hub._nodes))
        conn.close()

    time.sleep(1.0)
    hub.distribute_task("two")
    time.sleep(0.3)

    node.stop()
    hub.stop()

    assert "two" in received

