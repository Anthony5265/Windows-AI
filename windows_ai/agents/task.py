"""Task representation for agent orchestration"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime
import uuid

class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class Task:
    """Represents a task to be executed by an agent"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: Optional[str] = None
    description: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.NORMAL
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    assigned_agent: Optional[str] = None
    required_plugins: List[str] = field(default_factory=list)
    required_capabilities: List[str] = field(default_factory=list)  # Required agent capabilities
    dependencies: List[str] = field(default_factory=list)  # Task IDs this depends on
    subtasks: List['Task'] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timeout: Optional[float] = None  # Task timeout in seconds (None = use agent default)
    
    def __post_init__(self):
        """Map name to description if name provided"""
        if self.name and not self.description:
            self.description = self.name

    def start(self):
        """Mark task as started"""
        self.status = TaskStatus.IN_PROGRESS
        self.started_at = datetime.utcnow()

    def complete(self, result: Any):
        """Mark task as completed"""
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.completed_at = datetime.utcnow()

    def fail(self, error: str):
        """Mark task as failed"""
        self.status = TaskStatus.FAILED
        self.error = error
        self.completed_at = datetime.utcnow()

    def cancel(self):
        """Cancel task"""
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary"""
        return {
            'id': self.id,
            'description': self.description,
            'parameters': self.parameters,
            'status': self.status.value,
            'priority': self.priority.value,
            'result': self.result,
            'error': self.error,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'assigned_agent': self.assigned_agent,
            'required_plugins': self.required_plugins,
            'dependencies': self.dependencies,
            'metadata': self.metadata
        }
