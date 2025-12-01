"""
State Synchronization
Synchronize state across mesh nodes
"""
from typing import Dict, Any, Set
import logging
import time
import threading
import json
import hashlib

logger = logging.getLogger(__name__)


class StateSync:
    """
    Distributed state synchronization with eventual consistency
    """
    
    def __init__(self, mesh_node):
        self.mesh_node = mesh_node
        self.state = {}
        self.version = 0
        self.sync_interval = 10
        self.running = False
        self.sync_thread = None
        self.state_lock = threading.Lock()
    
    def start(self) -> Dict[str, Any]:
        """Start state synchronization"""
        self.running = True
        
        # Start sync thread
        self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.sync_thread.start()
        
        # Register message handlers
        self.mesh_node.register_handler('state_sync_request', self._handle_sync_request)
        self.mesh_node.register_handler('state_sync_response', self._handle_sync_response)
        self.mesh_node.register_handler('state_update', self._handle_state_update)
        
        logger.info("State synchronization started")
        
        return {
            "status": "success",
            "message": "State sync started"
        }
    
    def stop(self) -> Dict[str, Any]:
        """Stop state synchronization"""
        self.running = False
        
        logger.info("State synchronization stopped")
        
        return {
            "status": "success",
            "message": "State sync stopped"
        }
    
    def set(self, key: str, value: Any) -> Dict[str, Any]:
        """Set state value"""
        with self.state_lock:
            self.state[key] = {
                "value": value,
                "version": self.version + 1,
                "timestamp": time.time(),
                "node_id": self.mesh_node.node_id
            }
            self.version += 1
        
        # Broadcast update to peers
        self._broadcast_update(key)
        
        return {
            "status": "success",
            "key": key,
            "version": self.version
        }
    
    def get(self, key: str) -> Dict[str, Any]:
        """Get state value"""
        with self.state_lock:
            if key in self.state:
                return {
                    "status": "success",
                    "value": self.state[key]["value"],
                    "version": self.state[key]["version"]
                }
            else:
                return {
                    "status": "error",
                    "message": f"Key not found: {key}"
                }
    
    def delete(self, key: str) -> Dict[str, Any]:
        """Delete state value"""
        with self.state_lock:
            if key in self.state:
                del self.state[key]
                self.version += 1
                
                # Broadcast deletion
                self._broadcast_delete(key)
                
                return {
                    "status": "success",
                    "message": f"Key deleted: {key}"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Key not found: {key}"
                }
    
    def get_all(self) -> Dict[str, Any]:
        """Get all state"""
        with self.state_lock:
            return {
                "status": "success",
                "state": {k: v["value"] for k, v in self.state.items()},
                "version": self.version
            }
    
    def _broadcast_update(self, key: str):
        """Broadcast state update to peers"""
        with self.state_lock:
            state_entry = self.state.get(key)
        
        if not state_entry:
            return
        
        message = {
            "type": "state_update",
            "key": key,
            "value": state_entry["value"],
            "version": state_entry["version"],
            "timestamp": state_entry["timestamp"],
            "node_id": self.mesh_node.node_id
        }
        
        for peer_id, peer in self.mesh_node.peers.items():
            try:
                self.mesh_node.send_to_peer(peer.address, peer.port, message)
            except Exception as e:
                logger.debug(f"Failed to send update to {peer_id}: {e}")
    
    def _broadcast_delete(self, key: str):
        """Broadcast state deletion to peers"""
        message = {
            "type": "state_delete",
            "key": key,
            "version": self.version,
            "node_id": self.mesh_node.node_id
        }
        
        for peer_id, peer in self.mesh_node.peers.items():
            try:
                self.mesh_node.send_to_peer(peer.address, peer.port, message)
            except Exception as e:
                logger.debug(f"Failed to send delete to {peer_id}: {e}")
    
    def _sync_loop(self):
        """Periodic state synchronization"""
        while self.running:
            try:
                # Request state from peers
                for peer_id, peer in list(self.mesh_node.peers.items()):
                    self._sync_with_peer(peer.address, peer.port)
                
                time.sleep(self.sync_interval)
                
            except Exception as e:
                logger.error(f"Sync loop error: {e}")
    
    def _sync_with_peer(self, address: str, port: int):
        """Synchronize state with a peer"""
        try:
            message = {
                "type": "state_sync_request",
                "version": self.version,
                "node_id": self.mesh_node.node_id
            }
            
            response = self.mesh_node.send_to_peer(address, port, message)
            
            if response.get('status') == 'success':
                peer_state = response.get('state', {})
                self._merge_state(peer_state)
                
        except Exception as e:
            logger.debug(f"Sync with peer error: {e}")
    
    def _merge_state(self, peer_state: Dict[str, Any]):
        """Merge peer state with local state"""
        with self.state_lock:
            for key, entry in peer_state.items():
                # Use last-write-wins strategy based on version
                if key not in self.state:
                    self.state[key] = entry
                elif entry["version"] > self.state[key]["version"]:
                    self.state[key] = entry
                elif entry["version"] == self.state[key]["version"]:
                    # Same version, use timestamp
                    if entry["timestamp"] > self.state[key]["timestamp"]:
                        self.state[key] = entry
    
    def _handle_sync_request(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle state sync request"""
        with self.state_lock:
            return {
                "status": "success",
                "type": "state_sync_response",
                "state": self.state.copy(),
                "version": self.version
            }
    
    def _handle_sync_response(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle state sync response"""
        peer_state = message.get('state', {})
        self._merge_state(peer_state)
        
        return {"status": "success"}
    
    def _handle_state_update(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle state update from peer"""
        key = message.get('key')
        value = message.get('value')
        version = message.get('version')
        timestamp = message.get('timestamp')
        node_id = message.get('node_id')
        
        with self.state_lock:
            # Apply update if newer
            if key not in self.state or version > self.state[key]["version"]:
                self.state[key] = {
                    "value": value,
                    "version": version,
                    "timestamp": timestamp,
                    "node_id": node_id
                }
        
        return {"status": "success"}
    
    def get_status(self) -> Dict[str, Any]:
        """Get sync status"""
        with self.state_lock:
            return {
                "status": "success",
                "state_keys": len(self.state),
                "version": self.version,
                "running": self.running
            }
