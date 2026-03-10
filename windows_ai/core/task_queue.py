"""Background task queue system with Redis/in-memory support"""

import asyncio
import logging
import json
import time
import uuid
from typing import Any, Callable, Dict, Optional, List
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
from collections import deque
import traceback

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRY = "retry"


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class QueueTask:
    """Task in the queue"""
    id: str
    name: str
    func_name: str
    args: tuple
    kwargs: dict
    priority: TaskPriority
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retries: int = 0
    max_retries: int = 3
    result: Any = None
    error: Optional[str] = None
    timeout: Optional[int] = None  # seconds

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'func_name': self.func_name,
            'priority': self.priority.value,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'retries': self.retries,
            'max_retries': self.max_retries,
            'result': str(self.result) if self.result else None,
            'error': self.error,
            'timeout': self.timeout
        }


class TaskQueue:
    """
    Background task queue for async task execution

    Features:
    - Priority-based execution
    - Retry mechanism with exponential backoff
    - Task timeout handling
    - Task cancellation
    - Progress tracking
    - Concurrent worker pool
    """

    def __init__(
        self,
        max_workers: int = 4,
        max_queue_size: int = 1000,
        enable_persistence: bool = False
    ):
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size
        self.enable_persistence = enable_persistence

        # Task storage
        self.tasks: Dict[str, QueueTask] = {}
        self.pending_queue: deque = deque()
        self.running_tasks: Dict[str, asyncio.Task] = {}

        # Registered task functions
        self.task_registry: Dict[str, Callable] = {}

        # Worker management
        self.workers: List[asyncio.Task] = []
        self.running = False
        self.shutdown_event = asyncio.Event()

        # Statistics
        self.stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'cancelled_tasks': 0,
            'total_retries': 0
        }

        logger.info(f"Task queue initialized with {max_workers} workers")

    def register_task(self, name: str, func: Callable):
        """Register a task function"""
        self.task_registry[name] = func
        logger.debug(f"Registered task function: {name}")

    async def start(self):
        """Start the task queue workers"""
        if self.running:
            logger.warning("Task queue already running")
            return

        self.running = True
        self.shutdown_event.clear()

        # Start worker coroutines
        self.workers = [
            asyncio.create_task(self._worker(i))
            for i in range(self.max_workers)
        ]

        logger.info(f"Started {len(self.workers)} task queue workers")

    async def stop(self, wait_for_completion: bool = True):
        """Stop the task queue workers"""
        if not self.running:
            return

        logger.info("Stopping task queue...")
        self.running = False
        self.shutdown_event.set()

        if wait_for_completion:
            # Wait for all workers to finish
            if self.workers:
                await asyncio.gather(*self.workers, return_exceptions=True)

            # Wait for running tasks
            if self.running_tasks:
                logger.info(f"Waiting for {len(self.running_tasks)} running tasks...")
                await asyncio.gather(*self.running_tasks.values(), return_exceptions=True)

        logger.info("Task queue stopped")

    async def _worker(self, worker_id: int):
        """Worker coroutine that processes tasks from the queue"""
        logger.debug(f"Worker {worker_id} started")

        while self.running or self.pending_queue:
            try:
                # Get next task from queue
                task = await self._get_next_task()

                if task is None:
                    # No tasks available, wait a bit
                    await asyncio.sleep(0.1)
                    continue

                # Execute task
                await self._execute_task(task, worker_id)

            except asyncio.CancelledError:
                logger.debug(f"Worker {worker_id} cancelled")
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}", exc_info=True)

        logger.debug(f"Worker {worker_id} stopped")

    async def _get_next_task(self) -> Optional[QueueTask]:
        """Get next task from queue based on priority"""
        if not self.pending_queue:
            return None

        # Find highest priority pending task
        best_task = None
        best_priority = -1

        for task_id in list(self.pending_queue):
            task = self.tasks.get(task_id)
            if not task:
                self.pending_queue.remove(task_id)
                continue

            if task.status != TaskStatus.PENDING:
                self.pending_queue.remove(task_id)
                continue

            if task.priority.value > best_priority:
                best_task = task
                best_priority = task.priority.value

        if best_task:
            self.pending_queue.remove(best_task.id)
            return best_task

        return None

    async def _execute_task(self, task: QueueTask, worker_id: int):
        """Execute a single task"""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()

        logger.info(f"Worker {worker_id} executing task: {task.name} ({task.id})")

        try:
            # Get task function
            func = self.task_registry.get(task.func_name)
            if not func:
                raise ValueError(f"Task function not registered: {task.func_name}")

            # Execute with timeout if specified
            if task.timeout:
                result = await asyncio.wait_for(
                    func(*task.args, **task.kwargs),
                    timeout=task.timeout
                )
            else:
                result = await func(*task.args, **task.kwargs)

            # Task succeeded
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.completed_at = datetime.utcnow()
            self.stats['completed_tasks'] += 1

            logger.info(f"Task completed: {task.name} ({task.id})")

        except asyncio.TimeoutError:
            logger.error(f"Task timeout: {task.name} ({task.id})")
            await self._handle_task_failure(task, "Task timeout exceeded")

        except asyncio.CancelledError:
            logger.warning(f"Task cancelled: {task.name} ({task.id})")
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.utcnow()
            self.stats['cancelled_tasks'] += 1

        except Exception as e:
            logger.error(f"Task failed: {task.name} ({task.id}): {e}", exc_info=True)
            await self._handle_task_failure(task, str(e))

        finally:
            # Remove from running tasks
            if task.id in self.running_tasks:
                del self.running_tasks[task.id]

    async def _handle_task_failure(self, task: QueueTask, error: str):
        """Handle task failure with retry logic"""
        task.error = error

        # Check if we should retry
        if task.retries < task.max_retries:
            task.retries += 1
            task.status = TaskStatus.RETRY
            self.stats['total_retries'] += 1

            # Calculate backoff delay (exponential)
            delay = min(2 ** task.retries, 60)  # Max 60 seconds
            logger.info(f"Retrying task {task.name} in {delay}s (attempt {task.retries}/{task.max_retries})")

            # Re-queue after delay
            await asyncio.sleep(delay)
            task.status = TaskStatus.PENDING
            self.pending_queue.append(task.id)

        else:
            # Max retries exceeded
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.utcnow()
            self.stats['failed_tasks'] += 1
            logger.error(f"Task failed permanently: {task.name} ({task.id})")

    async def enqueue(
        self,
        func_name: str,
        *args,
        task_name: Optional[str] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        max_retries: int = 3,
        timeout: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Enqueue a task for execution

        Args:
            func_name: Name of registered task function
            *args: Positional arguments for the function
            task_name: Optional task name (uses func_name if not provided)
            priority: Task priority
            max_retries: Maximum retry attempts
            timeout: Task timeout in seconds
            **kwargs: Keyword arguments for the function

        Returns:
            Task ID
        """
        # Check queue size
        if len(self.pending_queue) >= self.max_queue_size:
            raise RuntimeError(f"Task queue full ({self.max_queue_size} tasks)")

        # Verify function is registered
        if func_name not in self.task_registry:
            raise ValueError(f"Task function not registered: {func_name}")

        # Create task
        task_id = str(uuid.uuid4())
        task = QueueTask(
            id=task_id,
            name=task_name or func_name,
            func_name=func_name,
            args=args,
            kwargs=kwargs,
            priority=priority,
            status=TaskStatus.PENDING,
            created_at=datetime.utcnow(),
            max_retries=max_retries,
            timeout=timeout
        )

        # Store and queue task
        self.tasks[task_id] = task
        self.pending_queue.append(task_id)
        self.stats['total_tasks'] += 1

        logger.debug(f"Enqueued task: {task.name} ({task_id})")

        return task_id

    def get_task(self, task_id: str) -> Optional[QueueTask]:
        """Get task by ID"""
        return self.tasks.get(task_id)

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or running task"""
        task = self.tasks.get(task_id)
        if not task:
            return False

        if task.status == TaskStatus.PENDING:
            # Remove from queue
            if task_id in self.pending_queue:
                self.pending_queue.remove(task_id)
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.utcnow()
            self.stats['cancelled_tasks'] += 1
            return True

        elif task.status == TaskStatus.RUNNING:
            # Cancel running task
            if task_id in self.running_tasks:
                self.running_tasks[task_id].cancel()
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.utcnow()
            self.stats['cancelled_tasks'] += 1
            return True

        return False

    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        return {
            **self.stats,
            'pending_tasks': len(self.pending_queue),
            'running_tasks': len(self.running_tasks),
            'total_stored_tasks': len(self.tasks),
            'workers': self.max_workers,
            'queue_running': self.running
        }

    def get_all_tasks(
        self,
        status: Optional[TaskStatus] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get all tasks with optional status filter"""
        tasks = list(self.tasks.values())

        if status:
            tasks = [t for t in tasks if t.status == status]

        # Sort by created_at descending
        tasks.sort(key=lambda t: t.created_at, reverse=True)

        # Limit results
        tasks = tasks[:limit]

        return [t.to_dict() for t in tasks]


# Global task queue instance
_global_queue: Optional[TaskQueue] = None


def get_task_queue() -> TaskQueue:
    """Get or create global task queue"""
    global _global_queue
    if _global_queue is None:
        _global_queue = TaskQueue()
    return _global_queue


async def start_task_queue():
    """Start the global task queue"""
    queue = get_task_queue()
    await queue.start()


async def stop_task_queue():
    """Stop the global task queue"""
    queue = get_task_queue()
    await queue.stop()
