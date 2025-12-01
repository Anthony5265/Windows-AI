"""
Mesh Node Implementation
Core node for mesh networking with leader election and secure communication
"""
from typing import Dict, Any, List, Optional, Callable
import logging
import socket
import threading
import time
import json
import hashlib
import ssl
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class NodeRole(Enum):
    """Node roles in mesh"""
    LEADER = "leader"
    FOLLOWER = "follower"
    CANDIDATE = "candidate"


@dataclass
class PeerInfo:
    """Information about a peer node"""
    node_id: str
    address: str
    port: int
    role: str
    capabilities: List[str]
    last_seen: float
    load: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MeshNode:
    """
    Mesh network node with leader election and distributed coordination
    """
    
    def __init__(self, node_id: str = None, port: int = 8765, **kwargs):
        self.node_id = node_id or self._generate_node_id()
        self.port = port
        self.role = NodeRole.FOLLOWER
        self.leader_id = None
        self.peers = {}
        self.capabilities = kwargs.get('capabilities', ['ai_inference', 'task_processing'])
        
        # Networking
        self.server_socket = None
        self.running = False
        self.server_thread = None
        
        # Leader election
        self.election_timeout = kwargs.get('election_timeout', 5)
        self.heartbeat_interval = kwargs.get('heartbeat_interval', 2)
        self.last_heartbeat = time.time()
        self.election_term = 0
        self.votes_received = set()
        
        # Callbacks
        self.message_handlers = {}
        
        # Security
        self.use_tls = kwargs.get('use_tls', False)
        self.ssl_context = None
        if self.use_tls:
            self._setup_ssl()
    
    def _generate_node_id(self) -> str:
        """Generate unique node ID"""
        hostname = socket.gethostname()
        timestamp = str(time.time())
        return hashlib.sha256(f"{hostname}{timestamp}".encode()).hexdigest()[:16]
    
    def _setup_ssl(self):
        """Setup SSL/TLS context"""
        self.ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        # In production, use proper certificates
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
    
    def start(self) -> Dict[str, Any]:
        """Start mesh node"""
        try:
            # Create server socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', self.port))
            self.server_socket.listen(10)
            
            # Wrap with TLS if enabled
            if self.use_tls and self.ssl_context:
                self.server_socket = self.ssl_context.wrap_socket(
                    self.server_socket,
                    server_side=True
                )
            
            self.running = True
            
            # Start server thread
            self.server_thread = threading.Thread(target=self._server_loop, daemon=True)
            self.server_thread.start()
            
            # Start heartbeat thread
            heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
            heartbeat_thread.start()
            
            # Start election timer
            election_thread = threading.Thread(target=self._election_timer, daemon=True)
            election_thread.start()
            
            logger.info(f"Mesh node {self.node_id} started on port {self.port}")
            
            return {
                "status": "success",
                "message": "Mesh node started",
                "node_id": self.node_id,
                "port": self.port
            }
            
        except Exception as e:
            logger.error(f"Error starting mesh node: {e}")
            return {"status": "error", "message": str(e)}
    
    def stop(self) -> Dict[str, Any]:
        """Stop mesh node"""
        self.running = False
        
        if self.server_socket:
            self.server_socket.close()
        
        logger.info(f"Mesh node {self.node_id} stopped")
        
        return {
            "status": "success",
            "message": "Mesh node stopped"
        }
    
    def _server_loop(self):
        """Main server loop"""
        while self.running:
            try:
                self.server_socket.settimeout(1.0)
                conn, addr = self.server_socket.accept()
                
                # Handle connection in separate thread
                thread = threading.Thread(
                    target=self._handle_connection,
                    args=(conn, addr),
                    daemon=True
                )
                thread.start()
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    logger.error(f"Server loop error: {e}")
    
    def _handle_connection(self, conn: socket.socket, addr: tuple):
        """Handle incoming connection"""
        try:
            # Receive data
            data = b""
            while True:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                data += chunk
                if len(data) > 1024 * 1024:  # 1MB limit
                    break
            
            if data:
                message = json.loads(data.decode('utf-8'))
                response = self._handle_message(message)
                
                # Send response
                conn.sendall(json.dumps(response).encode('utf-8'))
        
        except Exception as e:
            logger.error(f"Connection handler error: {e}")
        
        finally:
            conn.close()
    
    def _handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming message"""
        msg_type = message.get('type')
        
        if msg_type == 'heartbeat':
            return self._handle_heartbeat(message)
        elif msg_type == 'vote_request':
            return self._handle_vote_request(message)
        elif msg_type == 'vote_response':
            return self._handle_vote_response(message)
        elif msg_type == 'peer_info':
            return self._handle_peer_info(message)
        elif msg_type in self.message_handlers:
            return self.message_handlers[msg_type](message)
        else:
            return {"status": "error", "message": f"Unknown message type: {msg_type}"}
    
    def _handle_heartbeat(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle heartbeat from leader"""
        leader_id = message.get('node_id')
        term = message.get('term', 0)
        
        if term >= self.election_term:
            self.leader_id = leader_id
            self.election_term = term
            self.last_heartbeat = time.time()
            self.role = NodeRole.FOLLOWER
        
        return {"status": "success", "message": "Heartbeat received"}
    
    def _handle_vote_request(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle vote request during election"""
        candidate_id = message.get('node_id')
        term = message.get('term', 0)
        
        # Vote for candidate if term is higher
        if term > self.election_term:
            self.election_term = term
            self.leader_id = None
            
            return {
                "status": "success",
                "type": "vote_response",
                "vote_granted": True,
                "node_id": self.node_id,
                "term": self.election_term
            }
        
        return {
            "status": "success",
            "type": "vote_response",
            "vote_granted": False,
            "node_id": self.node_id,
            "term": self.election_term
        }
    
    def _handle_vote_response(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle vote response"""
        if message.get('vote_granted'):
            voter_id = message.get('node_id')
            self.votes_received.add(voter_id)
        
        return {"status": "success"}
    
    def _handle_peer_info(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle peer information"""
        peer = PeerInfo(**message.get('peer', {}))
        self.peers[peer.node_id] = peer
        
        return {"status": "success"}
    
    def _heartbeat_loop(self):
        """Send heartbeat if leader"""
        while self.running:
            try:
                if self.role == NodeRole.LEADER:
                    self._send_heartbeat_to_peers()
                
                time.sleep(self.heartbeat_interval)
            
            except Exception as e:
                logger.error(f"Heartbeat loop error: {e}")
    
    def _send_heartbeat_to_peers(self):
        """Send heartbeat to all peers"""
        message = {
            "type": "heartbeat",
            "node_id": self.node_id,
            "term": self.election_term
        }
        
        for peer_id, peer in list(self.peers.items()):
            try:
                self.send_to_peer(peer.address, peer.port, message)
            except Exception as e:
                logger.debug(f"Failed to send heartbeat to {peer_id}: {e}")
    
    def _election_timer(self):
        """Monitor for leader timeout and start election"""
        while self.running:
            try:
                # Check if we've heard from leader recently
                if self.role == NodeRole.FOLLOWER:
                    if time.time() - self.last_heartbeat > self.election_timeout:
                        self._start_election()
                
                time.sleep(1)
            
            except Exception as e:
                logger.error(f"Election timer error: {e}")
    
    def _start_election(self):
        """Start leader election"""
        logger.info(f"Node {self.node_id} starting election")
        
        self.role = NodeRole.CANDIDATE
        self.election_term += 1
        self.votes_received = {self.node_id}  # Vote for self
        self.leader_id = None
        
        # Request votes from peers
        message = {
            "type": "vote_request",
            "node_id": self.node_id,
            "term": self.election_term
        }
        
        for peer_id, peer in list(self.peers.items()):
            try:
                response = self.send_to_peer(peer.address, peer.port, message)
                if response.get('vote_granted'):
                    self.votes_received.add(peer_id)
            except Exception as e:
                logger.debug(f"Failed to request vote from {peer_id}: {e}")
        
        # Check if we won
        if len(self.votes_received) > len(self.peers) / 2:
            self._become_leader()
    
    def _become_leader(self):
        """Become leader"""
        logger.info(f"Node {self.node_id} became leader")
        self.role = NodeRole.LEADER
        self.leader_id = self.node_id
        self.last_heartbeat = time.time()
    
    def send_to_peer(self, address: str, port: int,
                    message: Dict[str, Any]) -> Dict[str, Any]:
        """Send message to peer"""
        try:
            # Create socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            
            # Wrap with TLS if enabled
            if self.use_tls and self.ssl_context:
                sock = self.ssl_context.wrap_socket(sock, server_hostname=address)
            
            # Connect and send
            sock.connect((address, port))
            sock.sendall(json.dumps(message).encode('utf-8'))
            
            # Receive response
            data = sock.recv(4096)
            response = json.loads(data.decode('utf-8'))
            
            sock.close()
            return response
        
        except Exception as e:
            logger.debug(f"Send to peer error: {e}")
            return {"status": "error", "message": str(e)}
    
    def add_peer(self, node_id: str, address: str, port: int,
                capabilities: List[str] = None) -> Dict[str, Any]:
        """Add peer to mesh"""
        peer = PeerInfo(
            node_id=node_id,
            address=address,
            port=port,
            role="unknown",
            capabilities=capabilities or [],
            last_seen=time.time()
        )
        
        self.peers[node_id] = peer
        
        logger.info(f"Added peer {node_id} at {address}:{port}")
        
        return {
            "status": "success",
            "message": "Peer added",
            "peer": peer.to_dict()
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get node status"""
        return {
            "status": "success",
            "node_id": self.node_id,
            "role": self.role.value,
            "leader_id": self.leader_id,
            "peer_count": len(self.peers),
            "port": self.port,
            "running": self.running,
            "election_term": self.election_term
        }
    
    def register_handler(self, message_type: str, handler: Callable):
        """Register custom message handler"""
        self.message_handlers[message_type] = handler
