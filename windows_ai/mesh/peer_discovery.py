"""
Peer Discovery for Mesh Network
Discovers other Windows-AI instances on local network
"""
from typing import Dict, Any, List, Callable
import logging
import socket
import threading
import json
import time

logger = logging.getLogger(__name__)


class PeerDiscovery:
    """
    Discover mesh peers on local network using UDP multicast
    """
    
    MULTICAST_GROUP = '239.255.43.21'
    MULTICAST_PORT = 5007
    
    def __init__(self, node_id: str, node_port: int, **kwargs):
        self.node_id = node_id
        self.node_port = node_port
        self.capabilities = kwargs.get('capabilities', [])
        
        self.sock = None
        self.running = False
        self.discovered_peers = {}
        self.discovery_callbacks = []
        
    def start(self) -> Dict[str, Any]:
        """Start peer discovery"""
        try:
            # Create multicast socket
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind to multicast port
            self.sock.bind(('', self.MULTICAST_PORT))
            
            # Join multicast group
            mreq = socket.inet_aton(self.MULTICAST_GROUP) + socket.inet_aton('0.0.0.0')
            self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            
            self.running = True
            
            # Start listener thread
            listener_thread = threading.Thread(target=self._listen_loop, daemon=True)
            listener_thread.start()
            
            # Start announcement thread
            announce_thread = threading.Thread(target=self._announce_loop, daemon=True)
            announce_thread.start()
            
            logger.info(f"Peer discovery started for node {self.node_id}")
            
            return {
                "status": "success",
                "message": "Peer discovery started"
            }
            
        except Exception as e:
            logger.error(f"Peer discovery start error: {e}")
            return {"status": "error", "message": str(e)}
    
    def stop(self) -> Dict[str, Any]:
        """Stop peer discovery"""
        self.running = False
        
        if self.sock:
            self.sock.close()
        
        logger.info("Peer discovery stopped")
        
        return {
            "status": "success",
            "message": "Peer discovery stopped"
        }
    
    def _listen_loop(self):
        """Listen for peer announcements"""
        while self.running:
            try:
                self.sock.settimeout(1.0)
                data, addr = self.sock.recvfrom(1024)
                
                # Parse announcement
                announcement = json.loads(data.decode('utf-8'))
                
                # Ignore own announcements
                if announcement.get('node_id') == self.node_id:
                    continue
                
                # Process peer announcement
                self._process_announcement(announcement, addr)
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    logger.debug(f"Listen loop error: {e}")
    
    def _announce_loop(self):
        """Announce presence to network"""
        while self.running:
            try:
                announcement = {
                    "node_id": self.node_id,
                    "port": self.node_port,
                    "capabilities": self.capabilities,
                    "timestamp": time.time()
                }
                
                # Send to multicast group
                message = json.dumps(announcement).encode('utf-8')
                self.sock.sendto(message, (self.MULTICAST_GROUP, self.MULTICAST_PORT))
                
                # Announce every 5 seconds
                time.sleep(5)
                
            except Exception as e:
                if self.running:
                    logger.error(f"Announce loop error: {e}")
    
    def _process_announcement(self, announcement: Dict[str, Any], addr: tuple):
        """Process peer announcement"""
        node_id = announcement.get('node_id')
        port = announcement.get('port')
        capabilities = announcement.get('capabilities', [])
        
        # Get IP address from socket address
        ip_address = addr[0]
        
        # Store/update peer
        peer = {
            "node_id": node_id,
            "address": ip_address,
            "port": port,
            "capabilities": capabilities,
            "last_seen": time.time()
        }
        
        is_new = node_id not in self.discovered_peers
        self.discovered_peers[node_id] = peer
        
        # Call callbacks for new peers
        if is_new:
            logger.info(f"Discovered peer: {node_id} at {ip_address}:{port}")
            
            for callback in self.discovery_callbacks:
                try:
                    callback(peer)
                except Exception as e:
                    logger.error(f"Discovery callback error: {e}")
    
    def add_discovery_callback(self, callback: Callable):
        """Add callback for new peer discoveries"""
        self.discovery_callbacks.append(callback)
    
    def get_peers(self, max_age: int = 30) -> Dict[str, Any]:
        """Get discovered peers"""
        now = time.time()
        
        # Filter out stale peers
        active_peers = {
            node_id: peer
            for node_id, peer in self.discovered_peers.items()
            if now - peer['last_seen'] < max_age
        }
        
        return {
            "status": "success",
            "peers": list(active_peers.values()),
            "count": len(active_peers)
        }
