"""Mesh node that discovers and connects to a :class:`MeshHub`."""

from __future__ import annotations

import socket
import threading
from typing import Callable, Tuple

from .protocol import SecureProtocol

__all__ = ["MeshNode"]


class MeshNode:
    """Client node connecting to a hub and receiving tasks."""

    def __init__(
        self,
        handle_task: Callable[[str], None],
        key: bytes | None = None,
    ) -> None:
        self.handle_task = handle_task
        self.protocol = SecureProtocol(key)
        self._sock: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._running = False

    # ---------------------------------------------------------- discovery
    @staticmethod
    def discover(port: int, host: str = "255.255.255.255") -> Tuple[str, int]:
        """Broadcast a discovery message returning hub address."""

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(1)
        sock.sendto(b"DISCOVER", (host, port))
        data, _addr = sock.recvfrom(1024)
        sock.close()
        host_str, port_str = data.decode().split(":")
        return host_str, int(port_str)

    # --------------------------------------------------------- connection
    def connect(self, addr: Tuple[str, int]) -> None:
        """Connect to the hub at *addr*."""

        self._sock = socket.create_connection(addr)
        self._running = True
        self._thread = threading.Thread(target=self._listen, daemon=True)
        self._thread.start()

    def _listen(self) -> None:
        assert self._sock is not None
        sock = self._sock
        while self._running:
            try:
                header = sock.recv(4)
                if not header:
                    break
                length = int.from_bytes(header, "big")
                data = b""
                while len(data) < length:
                    chunk = sock.recv(length - len(data))
                    if not chunk:
                        break
                    data += chunk
                if len(data) != length:
                    break
                message = self.protocol.decrypt(data).decode()
                self.handle_task(message)
            except OSError:
                break

    def stop(self) -> None:
        self._running = False
        try:
            if self._sock:
                self._sock.close()
        except Exception:
            pass
        if self._thread:
            self._thread.join(timeout=1)
