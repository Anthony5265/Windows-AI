"""Mesh hub responsible for node discovery and task distribution."""

from __future__ import annotations

import socket
import threading
import time
from typing import Dict, List

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
        heartbeat_timeout: float = 10.0,
        prune_interval: float = 1.0,
    ) -> None:
        self.host = host
        self.port = port
        self.discovery_port = discovery_port
        self.protocol = SecureProtocol(key)
        self._nodes: List[socket.socket] = []
        self._last_heartbeat: Dict[socket.socket, float] = {}
        self._running = False
        self._lock = threading.Lock()
        self.heartbeat_timeout = heartbeat_timeout
        self.prune_interval = prune_interval

    # --------------------------------------------------------------- lifecycle
    def start(self) -> None:
        """Start TCP and UDP servers."""

        if self._running:
            return
        self._running = True

        # Discovery UDP socket
        self._discovery_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._discovery_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._discovery_sock.bind((self.host, self.discovery_port))
        self.discovery_port = self._discovery_sock.getsockname()[1]
        self._discovery_thread = threading.Thread(
            target=self._discovery_loop, daemon=True
        )
        self._discovery_thread.start()

        # TCP server for node connections
        self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_sock.bind((self.host, self.port))
        self.port = self._server_sock.getsockname()[1]
        self._server_sock.listen()
        self._server_thread = threading.Thread(
            target=self._server_loop, daemon=True
        )
        self._server_thread.start()

        self._prune_thread = threading.Thread(
            target=self._prune_loop, daemon=True
        )
        self._prune_thread.start()

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
            for node in list(self._nodes):
                try:
                    node.close()
                except Exception:
                    pass
            self._nodes.clear()
            self._last_heartbeat.clear()
        try:
            self._prune_thread.join(timeout=1)
        except Exception:
            pass

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
            conn.settimeout(self.prune_interval)
            with self._lock:
                self._nodes.append(conn)
                self._last_heartbeat[conn] = time.time()
            threading.Thread(target=self._node_loop, args=(conn,), daemon=True).start()

    def _node_loop(self, conn: socket.socket) -> None:
        while self._running:
            try:
                header = conn.recv(4)
                if not header:
                    break
                length = int.from_bytes(header, "big")
                data = b""
                while len(data) < length:
                    chunk = conn.recv(length - len(data))
                    if not chunk:
                        break
                    data += chunk
                if len(data) != length:
                    break
                with self._lock:
                    self._last_heartbeat[conn] = time.time()
            except socket.timeout:
                continue
            except OSError:
                break
        with self._lock:
            if conn in self._nodes:
                self._nodes.remove(conn)
            self._last_heartbeat.pop(conn, None)
        try:
            conn.close()
        except Exception:
            pass

    def _prune_loop(self) -> None:
        while self._running:
            time.sleep(self.prune_interval)
            now = time.time()
            with self._lock:
                for conn, ts in list(self._last_heartbeat.items()):
                    if now - ts > self.heartbeat_timeout:
                        try:
                            conn.close()
                        except Exception:
                            pass
                        if conn in self._nodes:
                            self._nodes.remove(conn)
                        self._last_heartbeat.pop(conn, None)

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
                    try:
                        conn.close()
                    except Exception:
                        pass
                    if conn in self._nodes:
                        self._nodes.remove(conn)
                    self._last_heartbeat.pop(conn, None)

