"""Tests for MeshNode reconnection and hub pruning."""

from __future__ import annotations

import socket
import time

from mesh import MeshHub, MeshNode


def test_node_reconnects_after_hub_restart() -> None:
    """Node should reconnect to the hub after the hub restarts."""

    key = b"k" * 32
    hub = MeshHub(key=key, heartbeat_timeout=0.3, prune_interval=0.1)
    hub.start()

    received: list[str] = []
    node = MeshNode(
        received.append,
        key=key,
        heartbeat_interval=0.1,
        reconnect_interval=0.1,
    )
    node.connect((hub.host, hub.port))
    # allow initial connection to establish
    time.sleep(0.2)

    hub.distribute_task("one")
    for _ in range(20):
        if received:
            break
        time.sleep(0.1)
    assert received == ["one"]

    # simulate hub going down and back up
    hub.stop()
    time.sleep(0.3)
    hub.start()
    # wait for node to reconnect
    for _ in range(20):
        with hub._lock:
            if hub._nodes:
                break
        time.sleep(0.1)

    hub.distribute_task("two")
    for _ in range(50):
        if len(received) == 2:
            break
        time.sleep(0.1)
    assert received == ["one", "two"]

    node.stop()
    hub.stop()


def test_hub_prunes_inactive_connection() -> None:
    """Hub should remove connections that stop sending heartbeats."""

    key = b"k" * 32
    hub = MeshHub(key=key, heartbeat_timeout=0.2, prune_interval=0.05)
    hub.start()

    sock = socket.create_connection((hub.host, hub.port))
    # The connection never sends heartbeats; wait for it to be pruned
    for _ in range(20):
        with hub._lock:
            if not hub._nodes:
                break
        time.sleep(0.1)

    with hub._lock:
        assert not hub._nodes

    sock.close()
    hub.stop()

