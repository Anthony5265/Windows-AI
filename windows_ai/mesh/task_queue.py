"""
Distributed Task Queue
Queue tasks across mesh network with load balancing
"""
from typing import Dict, Any, List, Optional, Callable
import logging
import time
import uuid
import threading
from enum import Enum
from dataclasses import dataclass, asdict
from queue import Queue, Empty

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task status"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    """Distributed task"""
    task_id: str
    task_type: str
    payload: Dict[str, Any]
    priority: int = 0
    status: str = TaskStatus.PENDING.value
    assigned_node: Optional[str] = None
    created_at: float = 0.0
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at == 0.0:
            self.created_at = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DistributedTaskQueue:
    """
    Distributed task queue with load balancing
    """
    
    def __init__(self, mesh_node):
        self.mesh_node = mesh_node
        self.tasks = {}
        self.local_queue = Queue()
        self.task_handlers = {}
        self.worker_thread = None
        self.running = False
    
    def start(self) -> Dict[str, Any]:
        """Start task queue"""
        self.running = True
        
        # Start worker thread
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        
        # Register mesh message handler
        self.mesh_node.register_handler('task_request', self._handle_task_request)
        self.mesh_node.register_handler('task_result', self._handle_task_result)
        
        logger.info("Distributed task queue started")
        
        return {
            "status": "success",
            "message": "Task queue started"
        }
    
    def stop(self) -> Dict[str, Any]:
        """Stop task queue"""
        self.running = False
        
        logger.info("Distributed task queue stopped")
        
        return {
            "status": "success",
            "message": "Task queue stopped"
        }
    
    def submit_task(self, task_type: str, payload: Dict[str, Any],
                   priority: int = 0) -> Dict[str, Any]:
        """Submit task to queue"""
        try:
            # Create task
            task = Task(
                task_id=str(uuid.uuid4()),
                task_type=task_type,
                payload=payload,
                priority=priority
            )
            
            self.tasks[task.task_id] = task
            
            # Assign task to best node
            assigned_node = self._assign_task(task)
            
            if assigned_node == self.mesh_node.node_id:
                # Execute locally
                self.local_queue.put(task)
            else:
                # Send to remote node
                self._send_task_to_node(task, assigned_node)
            
            logger.info(f"Task {task.task_id} submitted to node {assigned_node}")
            
            return {
                "status": "success",
                "task_id": task.task_id,
                "assigned_node": assigned_node
            }
            
        except Exception as e:
            logger.error(f"Task submission error: {e}")
            return {"status": "error", "message": str(e)}
    
    def _assign_task(self, task: Task) -> str:
        """Assign task to best available node"""
        # Simple load balancing: choose node with lowest load
        best_node = self.mesh_node.node_id
        lowest_load = self._get_local_load()
        
        for peer_id, peer in self.mesh_node.peers.items():
            if peer.load < lowest_load:
                best_node = peer_id
                lowest_load = peer.load
        
        task.assigned_node = best_node
        task.status = TaskStatus.ASSIGNED.value
        
        return best_node
    
    def _get_local_load(self) -> float:
        """Get local node load (0.0 to 1.0)"""
        # Simple metric: queue size / 100
        return min(1.0, self.local_queue.qsize() / 100.0)
    
    def _send_task_to_node(self, task: Task, node_id: str):
        """Send task to remote node"""
        if node_id not in self.mesh_node.peers:
            logger.error(f"Node {node_id} not found in peers")
            return
        
        peer = self.mesh_node.peers[node_id]
        
        message = {
            "type": "task_request",
            "task": task.to_dict()
        }
        
        try:
            self.mesh_node.send_to_peer(peer.address, peer.port, message)
        except Exception as e:
            logger.error(f"Failed to send task to {node_id}: {e}")
            # Reassign task
            task.assigned_node = None
            task.status = TaskStatus.PENDING.value
            self.local_queue.put(task)
    
    def _handle_task_request(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming task request"""
        task_data = message.get('task', {})
        task = Task(**task_data)
        
        self.tasks[task.task_id] = task
        self.local_queue.put(task)
        
        return {"status": "success", "message": "Task queued"}
    
    def _handle_task_result(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle task result from remote node"""
        task_id = message.get('task_id')
        result = message.get('result')
        error = message.get('error')
        
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.result = result
            task.error = error
            task.status = TaskStatus.COMPLETED.value if not error else TaskStatus.FAILED.value
            task.completed_at = time.time()
        
        return {"status": "success"}
    
    def _worker_loop(self):
        """Process tasks from local queue"""
        while self.running:
            try:
                # Get task from queue
                task = self.local_queue.get(timeout=1)
                
                # Execute task
                self._execute_task(task)
                
            except Empty:
                continue
            except Exception as e:
                logger.error(f"Worker loop error: {e}")
    
    def _execute_task(self, task: Task):
        """Execute task"""
        task.status = TaskStatus.RUNNING.value
        task.started_at = time.time()
        
        try:
            # Get handler for task type
            handler = self.task_handlers.get(task.task_type)
            
            if handler:
                result = handler(task.payload)
                task.result = result
                task.status = TaskStatus.COMPLETED.value
            else:
                raise Exception(f"No handler for task type: {task.task_type}")
            
        except Exception as e:
            logger.error(f"Task execution error: {e}")
            task.error = str(e)
            task.status = TaskStatus.FAILED.value
        
        finally:
            task.completed_at = time.time()
            
            # Send result back if task was from remote node
            if task.assigned_node != self.mesh_node.node_id:
                self._send_result_back(task)
    
    def _send_result_back(self, task: Task):
        """Send task result back to origin node"""
        # Find origin node in peers
        for peer_id, peer in self.mesh_node.peers.items():
            message = {
                "type": "task_result",
                "task_id": task.task_id,
                "result": task.result,
                "error": task.error
            }
            
            try:
                self.mesh_node.send_to_peer(peer.address, peer.port, message)
                break
            except Exception as e:
                logger.debug(f"Failed to send result to {peer_id}: {e}")
    
    def register_handler(self, task_type: str, handler: Callable):
        """Register task handler"""
        self.task_handlers[task_type] = handler
        logger.info(f"Registered handler for task type: {task_type}")
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get task status"""
        if task_id not in self.tasks:
            return {
                "status": "error",
                "message": f"Task not found: {task_id}"
            }
        
        task = self.tasks[task_id]
        return {
            "status": "success",
            "task": task.to_dict()
        }
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get queue status"""
        pending = sum(1 for t in self.tasks.values() if t.status == TaskStatus.PENDING.value)
        running = sum(1 for t in self.tasks.values() if t.status == TaskStatus.RUNNING.value)
        completed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED.value)
        failed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED.value)
        
        return {
            "status": "success",
            "total_tasks": len(self.tasks),
            "pending": pending,
            "running": running,
            "completed": completed,
            "failed": failed,
            "local_queue_size": self.local_queue.qsize()
        }
