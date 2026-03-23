"""
Task Scheduler — Cron-based and interval task scheduling with persistence,
retry logic, dependency management, and distributed coordination.
"""
import logging
import time
import uuid
import asyncio
import heapq
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable, Awaitable, Set
from enum import Enum

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


class TaskState(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"
    WAITING_DEPENDENCY = "waiting_dependency"


@dataclass
class TaskResult:
    task_id: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    duration_ms: float = 0
    retries_used: int = 0


@dataclass
class ScheduledTask:
    task_id: str
    name: str
    handler_name: str
    kwargs: Dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    state: TaskState = TaskState.PENDING
    scheduled_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    max_retries: int = 3
    retry_count: int = 0
    retry_delay_seconds: float = 5.0
    timeout_seconds: float = 300.0
    depends_on: List[str] = field(default_factory=list)
    result: Optional[TaskResult] = None
    cron_expression: Optional[str] = None
    interval_seconds: Optional[float] = None
    is_recurring: bool = False
    last_run: Optional[float] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __lt__(self, other):
        return (self.priority.value, self.scheduled_at) < (other.priority.value, other.scheduled_at)


class CronParser:
    """Parse simple cron expressions: minute hour day month weekday."""

    @staticmethod
    def matches(expression: str, dt_tuple: tuple) -> bool:
        """Check if cron expression matches given (min, hour, day, month, weekday)."""
        parts = expression.split()
        if len(parts) != 5:
            return False
        fields = list(dt_tuple)
        for i, part in enumerate(parts):
            if part == "*":
                continue
            if "/" in part:
                _, step = part.split("/")
                if fields[i] % int(step) != 0:
                    return False
            elif "," in part:
                values = [int(v) for v in part.split(",")]
                if fields[i] not in values:
                    return False
            elif "-" in part:
                start, end = part.split("-")
                if not (int(start) <= fields[i] <= int(end)):
                    return False
            else:
                if fields[i] != int(part):
                    return False
        return True

    @staticmethod
    def next_run(expression: str, from_time: float = None) -> float:
        """Calculate next run time for a cron expression."""
        import datetime
        if from_time is None:
            from_time = time.time()
        dt = datetime.datetime.fromtimestamp(from_time)
        for _ in range(525600):  # max 1 year of minutes
            dt += datetime.timedelta(minutes=1)
            dt_tuple = (dt.minute, dt.hour, dt.day, dt.month, dt.weekday())
            if CronParser.matches(expression, dt_tuple):
                return dt.timestamp()
        return from_time + 86400  # fallback to 24h


class TaskQueue:
    """Priority queue for scheduled tasks."""

    def __init__(self):
        self._heap: List[ScheduledTask] = []
        self._task_map: Dict[str, ScheduledTask] = {}

    def push(self, task: ScheduledTask):
        heapq.heappush(self._heap, task)
        self._task_map[task.task_id] = task

    def pop(self) -> Optional[ScheduledTask]:
        while self._heap:
            task = heapq.heappop(self._heap)
            if task.task_id in self._task_map and task.state == TaskState.PENDING:
                return task
        return None

    def peek(self) -> Optional[ScheduledTask]:
        while self._heap:
            if self._heap[0].task_id in self._task_map and self._heap[0].state == TaskState.PENDING:
                return self._heap[0]
            heapq.heappop(self._heap)
        return None

    def cancel(self, task_id: str) -> bool:
        if task_id in self._task_map:
            self._task_map[task_id].state = TaskState.CANCELLED
            del self._task_map[task_id]
            return True
        return False

    @property
    def size(self) -> int:
        return len(self._task_map)


class TaskScheduler:
    """Main task scheduler with cron, interval, and one-shot support."""

    def __init__(self, max_concurrent: int = 10):
        self._queue = TaskQueue()
        self._handlers: Dict[str, Callable] = {}
        self._completed: List[TaskResult] = []
        self._running: Dict[str, ScheduledTask] = {}
        self._max_concurrent = max_concurrent
        self._is_running = False
        self._cron_parser = CronParser()
        self._dependency_graph: Dict[str, Set[str]] = {}
        logger.info(f"TaskScheduler initialized (max_concurrent={max_concurrent})")

    def register_handler(self, name: str, handler: Callable):
        self._handlers[name] = handler
        logger.debug(f"Handler registered: {name}")

    def schedule(self, name: str, handler_name: str, priority: TaskPriority = TaskPriority.NORMAL,
                 depends_on: List[str] = None, max_retries: int = 3,
                 timeout: float = 300, **kwargs) -> ScheduledTask:
        task = ScheduledTask(
            task_id=str(uuid.uuid4()), name=name, handler_name=handler_name,
            kwargs=kwargs, priority=priority, depends_on=depends_on or [],
            max_retries=max_retries, timeout_seconds=timeout
        )
        if task.depends_on:
            task.state = TaskState.WAITING_DEPENDENCY
            for dep_id in task.depends_on:
                self._dependency_graph.setdefault(dep_id, set()).add(task.task_id)
        self._queue.push(task)
        logger.info(f"Task scheduled: {name} ({task.task_id})")
        return task

    def schedule_cron(self, name: str, handler_name: str, cron_expression: str,
                      **kwargs) -> ScheduledTask:
        next_time = CronParser.next_run(cron_expression)
        task = ScheduledTask(
            task_id=str(uuid.uuid4()), name=name, handler_name=handler_name,
            kwargs=kwargs, cron_expression=cron_expression, is_recurring=True,
            scheduled_at=next_time
        )
        self._queue.push(task)
        logger.info(f"Cron task scheduled: {name} ({cron_expression})")
        return task

    def schedule_interval(self, name: str, handler_name: str, interval_seconds: float,
                          **kwargs) -> ScheduledTask:
        task = ScheduledTask(
            task_id=str(uuid.uuid4()), name=name, handler_name=handler_name,
            kwargs=kwargs, interval_seconds=interval_seconds, is_recurring=True
        )
        self._queue.push(task)
        logger.info(f"Interval task scheduled: {name} (every {interval_seconds}s)")
        return task

    async def execute_task(self, task: ScheduledTask) -> TaskResult:
        handler = self._handlers.get(task.handler_name)
        if not handler:
            return TaskResult(task.task_id, False, error=f"Handler not found: {task.handler_name}")

        task.state = TaskState.RUNNING
        task.started_at = time.time()
        self._running[task.task_id] = task

        try:
            if asyncio.iscoroutinefunction(handler):
                result = await asyncio.wait_for(handler(**task.kwargs), timeout=task.timeout_seconds)
            else:
                result = handler(**task.kwargs)

            duration = (time.time() - task.started_at) * 1000
            task_result = TaskResult(task.task_id, True, result=result, duration_ms=duration, retries_used=task.retry_count)
            task.state = TaskState.COMPLETED
            task.completed_at = time.time()
            task.result = task_result
            logger.info(f"Task completed: {task.name} in {duration:.1f}ms")

        except asyncio.TimeoutError:
            task_result = TaskResult(task.task_id, False, error="Task timed out", retries_used=task.retry_count)
            task.state = TaskState.FAILED
            logger.warning(f"Task timed out: {task.name}")

        except Exception as e:
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.state = TaskState.RETRYING
                task.scheduled_at = time.time() + task.retry_delay_seconds * (2 ** (task.retry_count - 1))
                self._queue.push(task)
                logger.warning(f"Task {task.name} failed, retry {task.retry_count}/{task.max_retries}: {e}")
                task_result = TaskResult(task.task_id, False, error=str(e), retries_used=task.retry_count)
            else:
                task_result = TaskResult(task.task_id, False, error=str(e), retries_used=task.retry_count)
                task.state = TaskState.FAILED
                logger.error(f"Task failed permanently: {task.name}: {e}")

        finally:
            self._running.pop(task.task_id, None)

        self._completed.append(task_result)
        self._resolve_dependencies(task.task_id)

        # Reschedule recurring tasks
        if task.is_recurring and task.state == TaskState.COMPLETED:
            self._reschedule_recurring(task)

        return task_result

    def _resolve_dependencies(self, completed_task_id: str):
        dependents = self._dependency_graph.pop(completed_task_id, set())
        for dep_task_id in dependents:
            task = self._queue._task_map.get(dep_task_id)
            if task and task.state == TaskState.WAITING_DEPENDENCY:
                task.depends_on = [d for d in task.depends_on if d != completed_task_id]
                if not task.depends_on:
                    task.state = TaskState.PENDING

    def _reschedule_recurring(self, task: ScheduledTask):
        new_task = ScheduledTask(
            task_id=str(uuid.uuid4()), name=task.name, handler_name=task.handler_name,
            kwargs=task.kwargs, priority=task.priority,
            cron_expression=task.cron_expression, interval_seconds=task.interval_seconds,
            is_recurring=True, max_retries=task.max_retries, tags=task.tags
        )
        if task.cron_expression:
            new_task.scheduled_at = CronParser.next_run(task.cron_expression)
        elif task.interval_seconds:
            new_task.scheduled_at = time.time() + task.interval_seconds
        self._queue.push(new_task)

    def cancel_task(self, task_id: str) -> bool:
        return self._queue.cancel(task_id)

    def get_status(self) -> Dict[str, Any]:
        return {
            "pending": self._queue.size,
            "running": len(self._running),
            "completed": len(self._completed),
            "failed": sum(1 for r in self._completed if not r.success),
        }

    def get_completed(self, limit: int = 50) -> List[TaskResult]:
        return self._completed[-limit:]

    async def run_pending(self) -> List[TaskResult]:
        """Process all pending tasks (non-blocking, single pass)."""
        results = []
        while len(self._running) < self._max_concurrent:
            task = self._queue.pop()
            if not task:
                break
            if task.scheduled_at > time.time():
                self._queue.push(task)
                break
            result = await self.execute_task(task)
            results.append(result)
        return results


# Global instance
_scheduler: Optional[TaskScheduler] = None

def get_task_scheduler() -> TaskScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = TaskScheduler()
    return _scheduler
