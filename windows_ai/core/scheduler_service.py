"""Advanced scheduler service for periodic and scheduled tasks"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Callable, Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
import uuid
from croniter import croniter

logger = logging.getLogger(__name__)


class ScheduleType(Enum):
    """Type of schedule"""
    ONCE = "once"  # Run once at specific time
    INTERVAL = "interval"  # Run every N seconds
    CRON = "cron"  # Run based on cron expression
    DAILY = "daily"  # Run daily at specific time
    WEEKLY = "weekly"  # Run weekly on specific day/time


class TaskState(Enum):
    """Scheduled task state"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ScheduledTask:
    """Scheduled task definition"""
    id: str
    name: str
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    schedule_type: ScheduleType = ScheduleType.INTERVAL
    interval_seconds: Optional[int] = None
    cron_expression: Optional[str] = None
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None
    run_count: int = 0
    state: TaskState = TaskState.PENDING
    enabled: bool = True
    max_runs: Optional[int] = None  # None = unlimited
    created_at: datetime = field(default_factory=datetime.utcnow)
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'schedule_type': self.schedule_type.value,
            'interval_seconds': self.interval_seconds,
            'cron_expression': self.cron_expression,
            'next_run': self.next_run.isoformat() if self.next_run else None,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'run_count': self.run_count,
            'state': self.state.value,
            'enabled': self.enabled,
            'max_runs': self.max_runs,
            'created_at': self.created_at.isoformat(),
            'error': self.error
        }


class Scheduler:
    """
    Advanced task scheduler

    Features:
    - Interval-based scheduling
    - Cron expression support
    - One-time scheduled tasks
    - Task enable/disable
    - Maximum run limits
    - Error handling and retry
    - Concurrent task execution
    """

    def __init__(self, max_concurrent_tasks: int = 10):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.tasks: Dict[str, ScheduledTask] = {}
        self.running = False
        self.scheduler_task: Optional[asyncio.Task] = None
        self.running_tasks: Dict[str, asyncio.Task] = {}

        logger.info("Scheduler initialized")

    async def start(self):
        """Start the scheduler"""
        if self.running:
            logger.warning("Scheduler already running")
            return

        self.running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Scheduler started")

    async def stop(self, wait_for_tasks: bool = True):
        """Stop the scheduler"""
        if not self.running:
            return

        logger.info("Stopping scheduler...")
        self.running = False

        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass

        if wait_for_tasks and self.running_tasks:
            logger.info(f"Waiting for {len(self.running_tasks)} running tasks...")
            await asyncio.gather(*self.running_tasks.values(), return_exceptions=True)

        logger.info("Scheduler stopped")

    async def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                await self._check_and_run_tasks()
                await asyncio.sleep(1)  # Check every second
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}", exc_info=True)

    async def _check_and_run_tasks(self):
        """Check tasks and run those that are due"""
        now = datetime.utcnow()

        for task in list(self.tasks.values()):
            if not task.enabled or task.state == TaskState.CANCELLED:
                continue

            # Check if max runs reached
            if task.max_runs and task.run_count >= task.max_runs:
                task.enabled = False
                task.state = TaskState.COMPLETED
                logger.info(f"Task {task.name} reached max runs ({task.max_runs})")
                continue

            # Check if task is due
            if task.next_run and now >= task.next_run:
                # Check concurrent task limit
                if len(self.running_tasks) >= self.max_concurrent_tasks:
                    logger.warning(f"Max concurrent tasks reached ({self.max_concurrent_tasks})")
                    continue

                # Run task
                await self._run_task(task)

    async def _run_task(self, task: ScheduledTask):
        """Execute a scheduled task"""
        if task.state == TaskState.RUNNING:
            logger.warning(f"Task {task.name} already running, skipping")
            return

        task.state = TaskState.RUNNING
        task.last_run = datetime.utcnow()

        logger.info(f"Running scheduled task: {task.name}")

        # Create task coroutine
        async def task_wrapper():
            try:
                if asyncio.iscoroutinefunction(task.func):
                    await task.func(*task.args, **task.kwargs)
                else:
                    # Run sync function in executor
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, task.func, *task.args, **task.kwargs)

                task.run_count += 1
                task.error = None
                logger.info(f"Task {task.name} completed successfully (run {task.run_count})")

            except Exception as e:
                task.error = str(e)
                logger.error(f"Task {task.name} failed: {e}", exc_info=True)

            finally:
                task.state = TaskState.PENDING
                if task.id in self.running_tasks:
                    del self.running_tasks[task.id]

                # Calculate next run time
                self._schedule_next_run(task)

        # Start task
        self.running_tasks[task.id] = asyncio.create_task(task_wrapper())

    def _schedule_next_run(self, task: ScheduledTask):
        """Calculate next run time for a task"""
        if not task.enabled:
            return

        now = datetime.utcnow()

        if task.schedule_type == ScheduleType.ONCE:
            # One-time task, disable after running
            task.enabled = False
            task.next_run = None

        elif task.schedule_type == ScheduleType.INTERVAL:
            # Interval-based scheduling
            if task.interval_seconds:
                task.next_run = now + timedelta(seconds=task.interval_seconds)

        elif task.schedule_type == ScheduleType.CRON:
            # Cron expression scheduling
            if task.cron_expression:
                try:
                    cron = croniter(task.cron_expression, now)
                    task.next_run = cron.get_next(datetime)
                except Exception as e:
                    logger.error(f"Invalid cron expression for task {task.name}: {e}")
                    task.enabled = False

        elif task.schedule_type == ScheduleType.DAILY:
            # Daily at specific time
            if task.next_run:
                task.next_run = task.next_run + timedelta(days=1)

        elif task.schedule_type == ScheduleType.WEEKLY:
            # Weekly at specific day/time
            if task.next_run:
                task.next_run = task.next_run + timedelta(weeks=1)

    def schedule_interval(
        self,
        func: Callable,
        seconds: int,
        *args,
        task_name: Optional[str] = None,
        max_runs: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Schedule a task to run every N seconds

        Args:
            func: Function to execute
            seconds: Interval in seconds
            *args: Function arguments
            task_name: Optional task name
            max_runs: Maximum number of runs (None = unlimited)
            **kwargs: Function keyword arguments

        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())
        task = ScheduledTask(
            id=task_id,
            name=task_name or func.__name__,
            func=func,
            args=args,
            kwargs=kwargs,
            schedule_type=ScheduleType.INTERVAL,
            interval_seconds=seconds,
            next_run=datetime.utcnow() + timedelta(seconds=seconds),
            max_runs=max_runs
        )

        self.tasks[task_id] = task
        logger.info(f"Scheduled interval task: {task.name} every {seconds}s")

        return task_id

    def schedule_cron(
        self,
        func: Callable,
        cron_expression: str,
        *args,
        task_name: Optional[str] = None,
        max_runs: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Schedule a task using cron expression

        Args:
            func: Function to execute
            cron_expression: Cron expression (e.g., "0 */6 * * *" for every 6 hours)
            *args: Function arguments
            task_name: Optional task name
            max_runs: Maximum number of runs
            **kwargs: Function keyword arguments

        Returns:
            Task ID
        """
        # Validate cron expression
        try:
            cron = croniter(cron_expression, datetime.utcnow())
            next_run = cron.get_next(datetime)
        except Exception as e:
            raise ValueError(f"Invalid cron expression: {e}")

        task_id = str(uuid.uuid4())
        task = ScheduledTask(
            id=task_id,
            name=task_name or func.__name__,
            func=func,
            args=args,
            kwargs=kwargs,
            schedule_type=ScheduleType.CRON,
            cron_expression=cron_expression,
            next_run=next_run,
            max_runs=max_runs
        )

        self.tasks[task_id] = task
        logger.info(f"Scheduled cron task: {task.name} with expression '{cron_expression}'")

        return task_id

    def schedule_once(
        self,
        func: Callable,
        run_at: datetime,
        *args,
        task_name: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Schedule a task to run once at a specific time

        Args:
            func: Function to execute
            run_at: Datetime to run at
            *args: Function arguments
            task_name: Optional task name
            **kwargs: Function keyword arguments

        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())
        task = ScheduledTask(
            id=task_id,
            name=task_name or func.__name__,
            func=func,
            args=args,
            kwargs=kwargs,
            schedule_type=ScheduleType.ONCE,
            next_run=run_at,
            max_runs=1
        )

        self.tasks[task_id] = task
        logger.info(f"Scheduled one-time task: {task.name} at {run_at}")

        return task_id

    def schedule_daily(
        self,
        func: Callable,
        hour: int,
        minute: int = 0,
        *args,
        task_name: Optional[str] = None,
        max_runs: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Schedule a task to run daily at specific time

        Args:
            func: Function to execute
            hour: Hour (0-23)
            minute: Minute (0-59)
            *args: Function arguments
            task_name: Optional task name
            max_runs: Maximum number of runs
            **kwargs: Function keyword arguments

        Returns:
            Task ID
        """
        now = datetime.utcnow()
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # If time has passed today, schedule for tomorrow
        if next_run <= now:
            next_run += timedelta(days=1)

        task_id = str(uuid.uuid4())
        task = ScheduledTask(
            id=task_id,
            name=task_name or func.__name__,
            func=func,
            args=args,
            kwargs=kwargs,
            schedule_type=ScheduleType.DAILY,
            next_run=next_run,
            max_runs=max_runs
        )

        self.tasks[task_id] = task
        logger.info(f"Scheduled daily task: {task.name} at {hour:02d}:{minute:02d}")

        return task_id

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a scheduled task"""
        task = self.tasks.get(task_id)
        if not task:
            return False

        task.enabled = False
        task.state = TaskState.CANCELLED

        # Cancel if currently running
        if task_id in self.running_tasks:
            self.running_tasks[task_id].cancel()

        logger.info(f"Cancelled task: {task.name}")
        return True

    def enable_task(self, task_id: str) -> bool:
        """Enable a task"""
        task = self.tasks.get(task_id)
        if not task:
            return False

        task.enabled = True
        task.state = TaskState.PENDING
        self._schedule_next_run(task)

        logger.info(f"Enabled task: {task.name}")
        return True

    def disable_task(self, task_id: str) -> bool:
        """Disable a task"""
        task = self.tasks.get(task_id)
        if not task:
            return False

        task.enabled = False
        logger.info(f"Disabled task: {task.name}")
        return True

    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """Get task by ID"""
        return self.tasks.get(task_id)

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Get all tasks"""
        return [task.to_dict() for task in self.tasks.values()]

    def get_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics"""
        return {
            'total_tasks': len(self.tasks),
            'enabled_tasks': sum(1 for t in self.tasks.values() if t.enabled),
            'running_tasks': len(self.running_tasks),
            'running': self.running,
            'max_concurrent_tasks': self.max_concurrent_tasks
        }


# Global scheduler instance
_global_scheduler: Optional[Scheduler] = None


def get_scheduler() -> Scheduler:
    """Get or create global scheduler"""
    global _global_scheduler
    if _global_scheduler is None:
        _global_scheduler = Scheduler()
    return _global_scheduler


async def start_scheduler():
    """Start the global scheduler"""
    scheduler = get_scheduler()
    await scheduler.start()


async def stop_scheduler():
    """Stop the global scheduler"""
    scheduler = get_scheduler()
    await scheduler.stop()
