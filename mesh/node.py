"""Mesh node that discovers and connects to a :class:`MeshHub`."""

from __future__ import annotations

import socket
import threading
import time
from typing import Callable, Tuple

from .protocol import SecureProtocol

__all__ = ["MeshNode"]


class MeshNode:
    """Client node connecting to a hub and receiving tasks."""

    def __init__(
        self,
        handle_task: Callable[[str], None],
        key: bytes | None = None,
        heartbeat_interval: float = 1.0,
    ) -> None:
        self.handle_task = handle_task
        self.protocol = SecureProtocol(key)
        self.heartbeat_interval = heartbeat_interval
        self._sock: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._heartbeat_thread: threading.Thread | None = None
        self._addr: Tuple[str, int] | None = None
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

        self._addr = addr
        self._sock = socket.create_connection(addr)
        self._running = True
        self._thread = threading.Thread(target=self._listen, daemon=True)
        self._thread.start()
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat, daemon=True
        )
        self._heartbeat_thread.start()

    def _listen(self) -> None:
        while self._running:
            sock = self._sock
            if sock is None:
                if not self._addr:
                    break
                try:
                    self._sock = socket.create_connection(self._addr)
                    continue
                except OSError:
                    if not self._running:
                        break
                    time.sleep(self.heartbeat_interval)
                    continue
            try:
                header = sock.recv(4)
                if not header:
                    raise OSError
                length = int.from_bytes(header, "big")
                data = b""
                while len(data) < length:
                    chunk = sock.recv(length - len(data))
                    if not chunk:
                        raise OSError
                    data += chunk
                message = self.protocol.decrypt(data).decode()
                self.handle_task(message)
            except OSError:
                try:
                    sock.close()
                except Exception:
                    pass
                self._sock = None
                if not self._running:
                    break
                time.sleep(self.heartbeat_interval)

    def stop(self) -> None:
        self._running = False
        try:
            if self._sock:
                self._sock.close()
        except Exception:
            pass
        if self._thread:
            self._thread.join(timeout=1)
        if self._heartbeat_thread:
            self._heartbeat_thread.join(timeout=1)

    def _heartbeat(self) -> None:
        while self._running:
            time.sleep(self.heartbeat_interval)
            if not self._running:
                break
            sock = self._sock
            if sock is None:
                continue
            try:
                message = self.protocol.encrypt(b"HB")
                packet = len(message).to_bytes(4, "big") + message
                sock.sendall(packet)
            except OSError:
                pass
