"""Mesh hub responsible for node discovery and task distribution."""

from __future__ import annotations

import socket
import threading
from typing import List

from .protocol import SecureProtocol

__all__ = ["MeshHub"]


class MeshHub:
    """Accepts connections from :class:`MeshNode` instances."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 0,
        discovery_port: int = 0,
        key: bytes | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.discovery_port = discovery_port
        self.protocol = SecureProtocol(key)
        self._nodes: List[socket.socket] = []
        self._running = False
        self._lock = threading.Lock()

    # --------------------------------------------------------------- lifecycle
    def start(self) -> None:
        """Start TCP and UDP servers."""

        if self._running:
            return
        self._running = True

        # Discovery UDP socket
        self._discovery_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._discovery_sock.bind((self.host, self.discovery_port))
        self.discovery_port = self._discovery_sock.getsockname()[1]
        self._discovery_thread = threading.Thread(
            target=self._discovery_loop, daemon=True
        )
        self._discovery_thread.start()

        # TCP server for node connections
        self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_sock.bind((self.host, self.port))
        self.port = self._server_sock.getsockname()[1]
        self._server_sock.listen()
        self._server_thread = threading.Thread(
            target=self._server_loop, daemon=True
        )
        self._server_thread.start()

    def stop(self) -> None:
        self._running = False
        try:
            self._discovery_sock.close()
        except Exception:
            pass
        try:
            self._server_sock.close()
        except Exception:
            pass
        with self._lock:
            for node in self._nodes:
                try:
                    node.close()
                except Exception:
                    pass
            self._nodes.clear()

    # ------------------------------------------------------------- discovery
    def _discovery_loop(self) -> None:
        while self._running:
            try:
                data, addr = self._discovery_sock.recvfrom(1024)
            except OSError:
                break
            if data == b"DISCOVER":
                reply = f"{self.host}:{self.port}".encode()
                self._discovery_sock.sendto(reply, addr)

    # --------------------------------------------------------------- TCP server
    def _server_loop(self) -> None:
        while self._running:
            try:
                conn, _addr = self._server_sock.accept()
            except OSError:
                break
            with self._lock:
                self._nodes.append(conn)

    # ---------------------------------------------------------- task handling
    def distribute_task(self, task: str) -> None:
        """Send *task* to all connected nodes."""

        message = self.protocol.encrypt(task.encode())
        packet = len(message).to_bytes(4, "big") + message
        with self._lock:
            for conn in list(self._nodes):
                try:
                    conn.sendall(packet)
                except OSError:
                    self._nodes.remove(conn)

