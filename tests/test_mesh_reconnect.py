import time

from mesh import MeshHub, MeshNode


def test_node_reconnects_and_hub_prunes():
    key = b"k" * 32
    hub = MeshHub(key=key, heartbeat_timeout=0.3, prune_interval=0.1)
    hub.start()

    received: list[str] = []

    node = MeshNode(received.append, key=key, heartbeat_interval=0.1, reconnect_interval=0.1)
    node.connect(("127.0.0.1", hub.port))
    time.sleep(0.2)

    # simulate connection drop from hub side
    with hub._lock:
        conn = hub._nodes[0]
    conn.close()

    # allow time for pruning and reconnection
    time.sleep(0.6)

    hub.distribute_task("again")
    time.sleep(0.2)

    assert "again" in received
    assert len(hub._nodes) == 1
    assert len(hub._last_heartbeat) == 1

    node.stop()
    hub.stop()
