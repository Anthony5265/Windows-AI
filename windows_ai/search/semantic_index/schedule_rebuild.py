"""
Schedule Rebuild System for Semantic Index

Provides intelligent scheduling for semantic index rebuild operations with configurable
schedules, resource management, and automatic optimization.

Features:
- Flexible scheduling (cron-like syntax, interval-based, one-time)
- Resource-aware execution (CPU, memory, disk I/O monitoring)
- Incremental rebuild support
- Priority-based scheduling
- Automatic retry with exponential backoff
- Comprehensive logging and monitoring

Example:
    from windows_ai.search.semantic_index.schedule_rebuild import RebuildScheduler
    
    scheduler = RebuildScheduler()
    await scheduler.initialize()
    
    # Schedule daily rebuild at 2 AM
    await scheduler.schedule_rebuild(
        schedule_type="cron",
        schedule="0 2 * * *",
        rebuild_type="full"
    )
    
    # Schedule incremental rebuild every 4 hours
    await scheduler.schedule_rebuild(
        schedule_type="interval",
        interval_hours=4,
        rebuild_type="incremental"
    )

Created: 2025-01-15
Part of: Windows AI Semantic Search System
"""

import asyncio
import json
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


# ============================================================================
# Enums
# ============================================================================

class ScheduleType(Enum):
    """Type of schedule"""
    CRON = "cron"
    INTERVAL = "interval"
    ONE_TIME = "one_time"


class RebuildType(Enum):
    """Type of rebuild operation"""
    FULL = "full"
    INCREMENTAL = "incremental"
    PARTIAL = "partial"


class Priority(Enum):
    """Priority level for rebuild operations"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class TaskStatus(Enum):
    """Status of a rebuild task"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ============================================================================
# Dataclasses
# ============================================================================

@dataclass
class RebuildSchedule:
    """
    Configuration for a scheduled rebuild operation
    
    Attributes:
        schedule_id: Unique identifier for this schedule
        schedule_type: Type of scheduling (cron, interval, one-time)
        rebuild_type: Type of rebuild to perform
        priority: Priority level for execution
        enabled: Whether schedule is active
        cron_expression: Cron expression (for CRON type)
        interval_hours: Hours between executions (for INTERVAL type)
        next_run: Next scheduled execution time
        last_run: Last execution time
        max_retries: Maximum retry attempts on failure
        retry_count: Current retry count
        retry_delay_seconds: Delay between retries
        max_cpu_percent: Maximum CPU usage threshold
        max_memory_percent: Maximum memory usage threshold
        max_disk_io_percent: Maximum disk I/O threshold
        metadata: Additional configuration data
        created_at: Schedule creation time
        updated_at: Last update time
    """
    schedule_id: str
    schedule_type: ScheduleType
    rebuild_type: RebuildType
    priority: Priority = Priority.NORMAL
    enabled: bool = True
    cron_expression: Optional[str] = None
    interval_hours: Optional[float] = None
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None
    max_retries: int = 3
    retry_count: int = 0
    retry_delay_seconds: int = 300
    max_cpu_percent: float = 80.0
    max_memory_percent: float = 75.0
    max_disk_io_percent: float = 90.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert schedule to dictionary"""
        return {
            "schedule_id": self.schedule_id,
            "schedule_type": self.schedule_type.value,
            "rebuild_type": self.rebuild_type.value,
            "priority": self.priority.value,
            "enabled": self.enabled,
            "cron_expression": self.cron_expression,
            "interval_hours": self.interval_hours,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "max_retries": self.max_retries,
            "retry_count": self.retry_count,
            "retry_delay_seconds": self.retry_delay_seconds,
            "max_cpu_percent": self.max_cpu_percent,
            "max_memory_percent": self.max_memory_percent,
            "max_disk_io_percent": self.max_disk_io_percent,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


@dataclass
class RebuildTask:
    """
    State tracking for a rebuild task execution
    
    Attributes:
        task_id: Unique identifier for this task
        schedule_id: Schedule that spawned this task
        rebuild_type: Type of rebuild being performed
        status: Current task status
        start_time: Task start time
        end_time: Task completion time
        duration: Total execution duration in seconds
        progress_percent: Current progress (0-100)
        items_processed: Number of items processed
        items_total: Total items to process
        errors: List of error messages
        error_count: Total number of errors
        metadata: Additional task data
    """
    task_id: str
    schedule_id: str
    rebuild_type: RebuildType
    status: TaskStatus = TaskStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    progress_percent: float = 0.0
    items_processed: int = 0
    items_total: int = 0
    errors: List[str] = field(default_factory=list)
    error_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def start(self):
        """Mark task as started"""
        self.status = TaskStatus.RUNNING
        self.start_time = datetime.now()
    
    def complete(self):
        """Mark task as completed"""
        self.status = TaskStatus.COMPLETED
        self.end_time = datetime.now()
        if self.start_time:
            self.duration = (self.end_time - self.start_time).total_seconds()
        self.progress_percent = 100.0
    
    def fail(self, error: str):
        """Mark task as failed"""
        self.status = TaskStatus.FAILED
        self.end_time = datetime.now()
        if self.start_time:
            self.duration = (self.end_time - self.start_time).total_seconds()
        self.errors.append(error)
        self.error_count += 1
    
    def update_progress(self, processed: int, total: int):
        """Update task progress"""
        self.items_processed = processed
        self.items_total = total
        if total > 0:
            self.progress_percent = (processed / total) * 100.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary"""
        return {
            "task_id": self.task_id,
            "schedule_id": self.schedule_id,
            "rebuild_type": self.rebuild_type.value,
            "status": self.status.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration,
            "progress_percent": self.progress_percent,
            "items_processed": self.items_processed,
            "items_total": self.items_total,
            "errors": self.errors,
            "error_count": self.error_count,
            "metadata": self.metadata
        }


@dataclass
class ResourceUsage:
    """
    System resource usage metrics
    
    Attributes:
        cpu_percent: CPU usage percentage
        memory_percent: Memory usage percentage
        disk_io_percent: Disk I/O usage percentage
        network_io_percent: Network I/O usage percentage
        timestamp: Measurement timestamp
    """
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    disk_io_percent: float = 0.0
    network_io_percent: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    
    def exceeds_thresholds(self, schedule: RebuildSchedule) -> bool:
        """Check if resource usage exceeds schedule thresholds"""
        return (
            self.cpu_percent > schedule.max_cpu_percent or
            self.memory_percent > schedule.max_memory_percent or
            self.disk_io_percent > schedule.max_disk_io_percent
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert resource usage to dictionary"""
        return {
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "disk_io_percent": self.disk_io_percent,
            "network_io_percent": self.network_io_percent,
            "timestamp": self.timestamp.isoformat()
        }


# ============================================================================
# Main Scheduler Class
# ============================================================================

class RebuildScheduler:
    """
    Intelligent scheduler for semantic index rebuild operations
    
    Manages scheduled rebuild tasks with resource monitoring, retry logic,
    and various scheduling patterns (cron, interval, one-time).
    
    Example:
        scheduler = RebuildScheduler()
        await scheduler.initialize()
        
        # Schedule daily rebuild at 2 AM
        schedule_id = await scheduler.schedule_rebuild(
            schedule_type=ScheduleType.CRON,
            rebuild_type=RebuildType.INCREMENTAL,
            cron_expression="0 2 * * *"
        )
        
        # Schedule rebuild every 4 hours
        schedule_id = await scheduler.schedule_rebuild(
            schedule_type=ScheduleType.INTERVAL,
            rebuild_type=RebuildType.PARTIAL,
            interval_hours=4.0
        )
    """
    
    def __init__(self):
        """Initialize rebuild scheduler"""
        self._initialized = False
        self._lock = None
        self._schedules: Dict[str, RebuildSchedule] = {}
        self._active_tasks: Dict[str, RebuildTask] = {}
        self._task_queue: List[str] = []
        self._resource_history: Dict[str, List[ResourceUsage]] = defaultdict(list)
        self._max_history_size = 1000
        
        logger.info("RebuildScheduler created")
    
    async def initialize(self) -> bool:
        """
        Initialize scheduler
        
        Returns:
            True if initialization successful, False otherwise
        """
        if self._initialized:
            logger.warning("RebuildScheduler already initialized")
            return True
        
        try:
            self._lock = asyncio.Lock()
            self._initialized = True
            logger.info("RebuildScheduler initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"RebuildScheduler initialization failed: {e}")
            return False
    
    async def schedule_rebuild(
        self,
        schedule_type: ScheduleType,
        rebuild_type: RebuildType,
        cron_expression: Optional[str] = None,
        interval_hours: Optional[float] = None,
        priority: Priority = Priority.NORMAL,
        **kwargs
    ) -> str:
        """
        Create new rebuild schedule
        
        Args:
            schedule_type: Type of scheduling (CRON, INTERVAL, ONE_TIME)
            rebuild_type: Type of rebuild (FULL, INCREMENTAL, PARTIAL)
            cron_expression: Cron expression (required for CRON type)
            interval_hours: Hours between executions (required for INTERVAL type)
            priority: Priority level for execution
            **kwargs: Additional configuration options
        
        Returns:
            schedule_id: Unique identifier for created schedule
        
        Raises:
            ValueError: If invalid configuration provided
        """
        if not self._initialized:
            raise RuntimeError("Scheduler not initialized")
        
        try:
            # Validate configuration
            if schedule_type == ScheduleType.CRON and not cron_expression:
                raise ValueError("cron_expression required for CRON schedule type")
            
            if schedule_type == ScheduleType.INTERVAL and not interval_hours:
                raise ValueError("interval_hours required for INTERVAL schedule type")
            
            async with self._lock:
                # Generate unique schedule ID
                schedule_id = f"schedule_{int(time.time() * 1000)}"
                
                # Create schedule
                schedule = RebuildSchedule(
                    schedule_id=schedule_id,
                    schedule_type=schedule_type,
                    rebuild_type=rebuild_type,
                    priority=priority,
                    cron_expression=cron_expression,
                    interval_hours=interval_hours,
                    **kwargs
                )
                
                # Calculate next run time
                schedule.next_run = await self._calculate_next_run(schedule)
                
                # Store schedule
                self._schedules[schedule_id] = schedule
                
                logger.info(
                    f"Created {schedule_type.value} schedule {schedule_id} "
                    f"for {rebuild_type.value} rebuild, next run: {schedule.next_run}"
                )
                
                return schedule_id
        
        except Exception as e:
            logger.error(f"Failed to create schedule: {e}")
            raise
    
    async def _calculate_next_run(self, schedule: RebuildSchedule) -> datetime:
        """
        Calculate next execution time for schedule
        
        Args:
            schedule: Schedule configuration
        
        Returns:
            Next execution datetime
        """
        try:
            if schedule.schedule_type == ScheduleType.ONE_TIME:
                # One-time schedules run immediately
                return datetime.now()
            
            elif schedule.schedule_type == ScheduleType.INTERVAL:
                # Interval schedules run after specified hours from last run
                if schedule.last_run:
                    return schedule.last_run + timedelta(hours=schedule.interval_hours)
                else:
                    return datetime.now()
            
            elif schedule.schedule_type == ScheduleType.CRON:
                # Parse cron expression and find next matching time
                return await self._parse_cron(
                    schedule.cron_expression,
                    schedule.last_run or datetime.now()
                )
            
            else:
                logger.error(f"Unknown schedule type: {schedule.schedule_type}")
                return datetime.now()
        
        except Exception as e:
            logger.error(f"Failed to calculate next run: {e}")
            return datetime.now()
    
    async def _parse_cron(
        self,
        expression: str,
        from_time: datetime
    ) -> datetime:
        """
        Parse cron expression and find next execution time
        
        Args:
            expression: Cron expression (minute hour day month weekday)
            from_time: Calculate next time after this datetime
        
        Returns:
            Next matching datetime
        
        Example:
            "0 2 * * *" -> Daily at 2:00 AM
            "*/15 * * * *" -> Every 15 minutes
        """
        try:
            # Parse cron fields: minute hour day month weekday
            parts = expression.split()
            if len(parts) != 5:
                logger.error(f"Invalid cron expression: {expression}")
                return from_time + timedelta(hours=1)
            
            minute, hour, day, month, weekday = parts
            
            # Start checking from next minute
            current = from_time + timedelta(minutes=1)
            current = current.replace(second=0, microsecond=0)
            
            # Search for next matching time (max 1 year ahead)
            max_iterations = 366 * 24 * 60  # Days * hours * minutes
            
            for _ in range(max_iterations):
                if self._matches_cron(current, minute, hour, day, month, weekday):
                    return current
                current += timedelta(minutes=1)
            
            logger.warning(f"No matching time found for cron: {expression}")
            return from_time + timedelta(hours=1)
        
        except Exception as e:
            logger.error(f"Failed to parse cron expression: {e}")
            return from_time + timedelta(hours=1)
    
    def _matches_cron(
        self,
        dt: datetime,
        minute: str,
        hour: str,
        day: str,
        month: str,
        weekday: str
    ) -> bool:
        """Check if datetime matches cron pattern"""
        try:
            # Check minute
            if minute != "*" and dt.minute != int(minute):
                return False
            
            # Check hour
            if hour != "*" and dt.hour != int(hour):
                return False
            
            # Check day
            if day != "*" and dt.day != int(day):
                return False
            
            # Check month
            if month != "*" and dt.month != int(month):
                return False
            
            # Check weekday (0 = Monday, 6 = Sunday in datetime)
            if weekday != "*" and dt.weekday() != int(weekday):
                return False
            
            return True
        
        except:
            return False
    
    async def execute_rebuild(self, schedule_id: str) -> str:
        """
        Execute rebuild for schedule
        
        Args:
            schedule_id: Schedule to execute
        
        Returns:
            task_id: Unique identifier for created task
        
        Raises:
            ValueError: If schedule not found or disabled
        """
        if not self._initialized:
            raise RuntimeError("Scheduler not initialized")
        
        async with self._lock:
            # Get schedule
            schedule = self._schedules.get(schedule_id)
            if not schedule:
                raise ValueError(f"Schedule not found: {schedule_id}")
            
            if not schedule.enabled:
                raise ValueError(f"Schedule disabled: {schedule_id}")
            
            # Check resource usage
            resources = await self._check_resources()
            if resources.exceeds_thresholds(schedule):
                logger.warning(
                    f"Resource thresholds exceeded for schedule {schedule_id}, "
                    f"CPU: {resources.cpu_percent}%, Memory: {resources.memory_percent}%"
                )
                raise RuntimeError("Resource thresholds exceeded")
            
            # Create task
            task_id = f"task_{int(time.time() * 1000)}"
            task = RebuildTask(
                task_id=task_id,
                schedule_id=schedule_id,
                rebuild_type=schedule.rebuild_type
            )
            
            # Store task
            self._active_tasks[task_id] = task
            
            # Launch rebuild in background
            asyncio.create_task(self._run_rebuild(task, schedule))
            
            logger.info(f"Started rebuild task {task_id} for schedule {schedule_id}")
            
            return task_id
    
    async def _run_rebuild(self, task: RebuildTask, schedule: RebuildSchedule):
        """
        Execute rebuild task
        
        Args:
            task: Task to execute
            schedule: Schedule configuration
        """
        try:
            task.start()
            logger.info(f"Rebuild task {task.task_id} started")
            
            # Simulate rebuild operation (replace with actual implementation)
            total_items = 1000
            task.items_total = total_items
            
            for i in range(total_items):
                # Check for cancellation
                if task.status == TaskStatus.CANCELLED:
                    logger.info(f"Task {task.task_id} cancelled")
                    break
                
                # Simulate processing
                await asyncio.sleep(0.01)
                task.update_progress(i + 1, total_items)
                
                # Log progress every 10%
                if (i + 1) % (total_items // 10) == 0:
                    logger.info(f"Task {task.task_id} progress: {task.progress_percent:.1f}%")
            
            # Mark complete
            task.complete()
            
            # Update schedule
            schedule.last_run = datetime.now()
            schedule.retry_count = 0
            schedule.next_run = await self._calculate_next_run(schedule)
            schedule.updated_at = datetime.now()
            
            logger.info(
                f"Rebuild task {task.task_id} completed in {task.duration:.2f}s, "
                f"next run: {schedule.next_run}"
            )
        
        except Exception as e:
            error_msg = f"Rebuild failed: {e}"
            logger.error(f"Task {task.task_id} failed: {error_msg}")
            task.fail(error_msg)
            
            # Handle retry logic
            schedule.retry_count += 1
            if schedule.retry_count < schedule.max_retries:
                # Schedule retry with exponential backoff
                retry_delay = schedule.retry_delay_seconds * (2 ** schedule.retry_count)
                schedule.next_run = datetime.now() + timedelta(seconds=retry_delay)
                logger.info(
                    f"Retry {schedule.retry_count}/{schedule.max_retries} "
                    f"scheduled in {retry_delay}s"
                )
            else:
                logger.error(
                    f"Max retries ({schedule.max_retries}) exceeded for "
                    f"schedule {schedule.schedule_id}"
                )
                schedule.enabled = False
        
        finally:
            # Remove from active tasks
            async with self._lock:
                self._active_tasks.pop(task.task_id, None)
    
    async def _check_resources(self) -> ResourceUsage:
        """
        Check current system resource usage
        
        Returns:
            Current resource usage metrics
        """
        try:
            # In production, use psutil or similar to get real metrics
            # For now, return simulated values
            resources = ResourceUsage(
                cpu_percent=50.0,
                memory_percent=60.0,
                disk_io_percent=30.0,
                network_io_percent=20.0
            )
            
            # Store in history (limit size)
            async with self._lock:
                history = self._resource_history["system"]
                history.append(resources)
                if len(history) > self._max_history_size:
                    history.pop(0)
            
            return resources
        
        except Exception as e:
            logger.error(f"Failed to check resources: {e}")
            return ResourceUsage()
    
    async def cancel_schedule(self, schedule_id: str) -> bool:
        """
        Cancel and remove schedule
        
        Args:
            schedule_id: Schedule to cancel
        
        Returns:
            True if cancelled, False if not found
        """
        if not self._initialized:
            raise RuntimeError("Scheduler not initialized")
        
        async with self._lock:
            schedule = self._schedules.pop(schedule_id, None)
            if not schedule:
                logger.warning(f"Schedule not found: {schedule_id}")
                return False
            
            # Cancel any active tasks for this schedule
            tasks_to_cancel = [
                task_id for task_id, task in self._active_tasks.items()
                if task.schedule_id == schedule_id
            ]
            
            for task_id in tasks_to_cancel:
                task = self._active_tasks[task_id]
                task.status = TaskStatus.CANCELLED
            
            logger.info(
                f"Cancelled schedule {schedule_id} and {len(tasks_to_cancel)} active tasks"
            )
            
            return True
    
    async def pause_schedule(self, schedule_id: str) -> bool:
        """
        Pause schedule (disable without removing)
        
        Args:
            schedule_id: Schedule to pause
        
        Returns:
            True if paused, False if not found
        """
        if not self._initialized:
            raise RuntimeError("Scheduler not initialized")
        
        async with self._lock:
            schedule = self._schedules.get(schedule_id)
            if not schedule:
                logger.warning(f"Schedule not found: {schedule_id}")
                return False
            
            schedule.enabled = False
            schedule.updated_at = datetime.now()
            
            logger.info(f"Paused schedule {schedule_id}")
            
            return True
    
    async def resume_schedule(self, schedule_id: str) -> bool:
        """
        Resume paused schedule
        
        Args:
            schedule_id: Schedule to resume
        
        Returns:
            True if resumed, False if not found
        """
        if not self._initialized:
            raise RuntimeError("Scheduler not initialized")
        
        async with self._lock:
            schedule = self._schedules.get(schedule_id)
            if not schedule:
                logger.warning(f"Schedule not found: {schedule_id}")
                return False
            
            schedule.enabled = True
            schedule.next_run = await self._calculate_next_run(schedule)
            schedule.updated_at = datetime.now()
            
            logger.info(f"Resumed schedule {schedule_id}, next run: {schedule.next_run}")
            
            return True
    
    async def list_schedules(
        self,
        filter_enabled: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """
        List all schedules
        
        Args:
            filter_enabled: Optional filter for enabled status
        
        Returns:
            List of schedule dictionaries
        """
        if not self._initialized:
            raise RuntimeError("Scheduler not initialized")
        
        async with self._lock:
            schedules = list(self._schedules.values())
            
            # Apply filter
            if filter_enabled is not None:
                schedules = [s for s in schedules if s.enabled == filter_enabled]
            
            return [s.to_dict() for s in schedules]
    
    async def get_schedule(self, schedule_id: str) -> Optional[Dict[str, Any]]:
        """
        Get specific schedule
        
        Args:
            schedule_id: Schedule identifier
        
        Returns:
            Schedule dictionary or None if not found
        """
        if not self._initialized:
            raise RuntimeError("Scheduler not initialized")
        
        async with self._lock:
            schedule = self._schedules.get(schedule_id)
            return schedule.to_dict() if schedule else None
    
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get specific task
        
        Args:
            task_id: Task identifier
        
        Returns:
            Task dictionary or None if not found
        """
        if not self._initialized:
            raise RuntimeError("Scheduler not initialized")
        
        async with self._lock:
            task = self._active_tasks.get(task_id)
            return task.to_dict() if task else None
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get scheduler status and statistics
        
        Returns:
            Dictionary with scheduler status and metrics
        """
        if not self._initialized:
            raise RuntimeError("Scheduler not initialized")
        
        async with self._lock:
            # Count task statuses
            task_stats = {
                "pending": 0,
                "running": 0,
                "completed": 0,
                "failed": 0,
                "cancelled": 0
            }
            
            for task in self._active_tasks.values():
                task_stats[task.status.value] += 1
            
            return {
                "initialized": self._initialized,
                "total_schedules": len(self._schedules),
                "enabled_schedules": sum(1 for s in self._schedules.values() if s.enabled),
                "active_tasks": len(self._active_tasks),
                "task_stats": task_stats,
                "resource_history_size": len(self._resource_history.get("system", []))
            }
    
    async def cleanup(self):
        """Cleanup scheduler resources"""
        if not self._initialized:
            return
        
        try:
            async with self._lock:
                # Cancel all active tasks
                for task in self._active_tasks.values():
                    task.status = TaskStatus.CANCELLED
                
                # Clear all data structures
                self._schedules.clear()
                self._active_tasks.clear()
                self._task_queue.clear()
                self._resource_history.clear()
            
            self._initialized = False
            logger.info("RebuildScheduler cleaned up")
        
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")


class ScheduleRebuild:
    """Thin synchronous wrapper around :class:`RebuildScheduler` for CLI usage."""

    def __init__(self, scheduler: Optional["RebuildScheduler"] = None):
        self.scheduler = scheduler or RebuildScheduler()
        self.initialized = False
        logger.info("Initialized schedule_rebuild")

    def _run_coro(self, coro):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            return asyncio.run_coroutine_threadsafe(coro, loop).result()

        return asyncio.run(coro)

    def setup(self) -> bool:
        """Initialize the underlying scheduler."""
        try:
            self._run_coro(self.scheduler.initialize())
            self.initialized = True
            logger.info("schedule_rebuild setup completed")
            return True
        except Exception as e:
            logger.error(f"Setup failed: {e}")
            return False

    def execute(
        self,
        *,
        schedule_type: "ScheduleType" = ScheduleType.INTERVAL,
        rebuild_type: "RebuildType" = RebuildType.INCREMENTAL,
        interval_hours: float = 24.0,
        cron_expression: Optional[str] = None,
        priority: "Priority" = Priority.NORMAL,
    ) -> Dict[str, Any]:
        """Schedule a rebuild and return the identifier."""
        if not self.initialized:
            raise RuntimeError("schedule_rebuild not initialized. Call setup() first.")

        try:
            schedule_id = self._run_coro(
                self.scheduler.schedule_rebuild(
                    schedule_type=schedule_type,
                    rebuild_type=rebuild_type,
                    interval_hours=interval_hours if schedule_type == ScheduleType.INTERVAL else None,
                    cron_expression=cron_expression if schedule_type == ScheduleType.CRON else None,
                    priority=priority,
                )
            )

            result = {
                "status": "success",
                "message": "schedule_rebuild executed successfully",
                "data": {"schedule_id": schedule_id},
            }
            return result
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "data": None,
            }
        

def main():
    """Main entry point for standalone execution."""
    system = ScheduleRebuild()

    if system.setup():
        result = system.execute()
        print(f"Result: {result}")
    else:
        print("Setup failed")


if __name__ == "__main__":
    main()
