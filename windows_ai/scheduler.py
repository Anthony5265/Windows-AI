"""
Windows AI - Task Scheduler System

Schedules and executes AI tasks at specific times or intervals.
Supports:
- Cron-style scheduling (e.g., "0 9 * * *" for 9 AM daily)
- Interval-based scheduling (e.g., every 2 hours)
- One-time scheduled tasks
- Task history and logging
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from croniter import croniter
import json

logger = logging.getLogger(__name__)


@dataclass
class ScheduledTask:
    """Configuration for a scheduled task"""
    id: str
    name: str
    description: str
    schedule_type: str  # 'cron', 'interval', 'once'
    schedule: str  # Cron expression, interval string, or datetime
    action: str  # AI action to perform
    prompt: str  # Prompt for the AI
    enabled: bool = True
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    run_count: int = 0
    created_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScheduledTask':
        return cls(**data)


class TaskScheduler:
    """Manages scheduled AI tasks"""

    def __init__(self, config_file: Path):
        self.config_file = config_file
        self.tasks: Dict[str, ScheduledTask] = {}
        self.task_callback: Optional[Callable] = None
        self.running = False
        self._scheduler_task: Optional[asyncio.Task] = None
        self.load_config()

    def load_config(self):
        """Load scheduled tasks from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self.tasks = {
                        tid: ScheduledTask.from_dict(tdata)
                        for tid, tdata in data.items()
                    }
                logger.info(f"Loaded {len(self.tasks)} scheduled tasks")
            except Exception as e:
                logger.error(f"Error loading scheduler config: {e}")
        else:
            self.tasks = {}

    def save_config(self):
        """Save scheduled tasks to file"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                data = {tid: t.to_dict() for tid, t in self.tasks.items()}
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(self.tasks)} scheduled tasks")
        except Exception as e:
            logger.error(f"Error saving scheduler config: {e}")

    def set_task_callback(self, callback: Callable):
        """Set callback for task execution"""
        self.task_callback = callback

    def _calculate_next_run(self, task: ScheduledTask) -> Optional[datetime]:
        """Calculate next run time for a task"""
        now = datetime.now()

        try:
            if task.schedule_type == 'cron':
                # Parse cron expression
                cron = croniter(task.schedule, now)
                next_run = cron.get_next(datetime)
                return next_run

            elif task.schedule_type == 'interval':
                # Parse interval (e.g., "2h", "30m", "1d")
                interval = task.schedule.strip().lower()

                # Extract number and unit
                import re
                match = re.match(r'^(\d+)([smhd])$', interval)
                if not match:
                    logger.error(f"Invalid interval format: {interval}")
                    return None

                amount, unit = match.groups()
                amount = int(amount)

                # Calculate delta
                if unit == 's':
                    delta = timedelta(seconds=amount)
                elif unit == 'm':
                    delta = timedelta(minutes=amount)
                elif unit == 'h':
                    delta = timedelta(hours=amount)
                elif unit == 'd':
                    delta = timedelta(days=amount)
                else:
                    return None

                # Calculate next run from last run or now
                if task.last_run:
                    last_run = datetime.fromisoformat(task.last_run)
                    next_run = last_run + delta
                    # If next_run is in the past, calculate from now
                    if next_run < now:
                        next_run = now + delta
                else:
                    next_run = now + delta

                return next_run

            elif task.schedule_type == 'once':
                # Parse datetime string
                scheduled_time = datetime.fromisoformat(task.schedule)
                if scheduled_time > now:
                    return scheduled_time
                else:
                    # Already past, don't reschedule
                    return None

        except Exception as e:
            logger.error(f"Error calculating next run for task {task.id}: {e}")
            return None

        return None

    async def add_task(self, task: ScheduledTask) -> bool:
        """Add a new scheduled task"""
        # Add timestamp
        if not task.created_at:
            task.created_at = datetime.now().isoformat()

        # Calculate next run
        next_run = self._calculate_next_run(task)
        if next_run:
            task.next_run = next_run.isoformat()
        else:
            logger.error(f"Could not calculate next run for task: {task.name}")
            return False

        # Save task
        self.tasks[task.id] = task
        self.save_config()

        logger.info(f"Added scheduled task: {task.name} ({task.id})")
        logger.info(f"Next run: {task.next_run}")
        return True

    async def remove_task(self, task_id: str) -> bool:
        """Remove a scheduled task"""
        if task_id not in self.tasks:
            return False

        del self.tasks[task_id]
        self.save_config()

        logger.info(f"Removed scheduled task: {task_id}")
        return True

    async def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """Update a scheduled task"""
        if task_id not in self.tasks:
            return False

        task = self.tasks[task_id]

        # Update fields
        for key, value in updates.items():
            if hasattr(task, key):
                setattr(task, key, value)

        # Recalculate next run if schedule changed
        if 'schedule' in updates or 'schedule_type' in updates:
            next_run = self._calculate_next_run(task)
            if next_run:
                task.next_run = next_run.isoformat()

        self.save_config()
        return True

    async def execute_task(self, task: ScheduledTask):
        """Execute a scheduled task"""
        if not self.task_callback:
            logger.error("No task callback set")
            return

        logger.info(f"Executing scheduled task: {task.name}")

        try:
            # Call callback
            await self.task_callback(
                task_id=task.id,
                task_name=task.name,
                action=task.action,
                prompt=task.prompt
            )

            # Update task
            task.last_run = datetime.now().isoformat()
            task.run_count += 1

            # Calculate next run (unless it's a one-time task)
            if task.schedule_type != 'once':
                next_run = self._calculate_next_run(task)
                if next_run:
                    task.next_run = next_run.isoformat()
                    logger.info(f"Next run for {task.name}: {task.next_run}")
                else:
                    task.enabled = False
                    logger.warning(f"Could not schedule next run for {task.name}, disabling")
            else:
                # One-time task, disable after execution
                task.enabled = False
                task.next_run = None
                logger.info(f"One-time task {task.name} completed, disabling")

            self.save_config()

        except Exception as e:
            logger.error(f"Error executing task {task.name}: {e}")

    async def _scheduler_loop(self):
        """Main scheduler loop"""
        logger.info("Task scheduler started")

        while self.running:
            now = datetime.now()

            # Check each enabled task
            for task_id, task in list(self.tasks.items()):
                if not task.enabled:
                    continue

                if not task.next_run:
                    continue

                try:
                    next_run = datetime.fromisoformat(task.next_run)
                    if now >= next_run:
                        # Execute task in background
                        asyncio.create_task(self.execute_task(task))
                except Exception as e:
                    logger.error(f"Error checking task {task_id}: {e}")

            # Sleep for a bit
            await asyncio.sleep(10)  # Check every 10 seconds

        logger.info("Task scheduler stopped")

    async def start(self):
        """Start the task scheduler"""
        if self.running:
            return

        self.running = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Task scheduler starting...")

    async def stop(self):
        """Stop the task scheduler"""
        if not self.running:
            return

        self.running = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        logger.info("Task scheduler stopped")

    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """Get scheduled task"""
        return self.tasks.get(task_id)

    def list_tasks(self) -> List[Dict[str, Any]]:
        """List all scheduled tasks"""
        return [task.to_dict() for task in self.tasks.values()]


# Example scheduled tasks
EXAMPLE_TASKS = [
    {
        "id": "daily-summary",
        "name": "Daily Summary",
        "description": "Generate a daily summary of tasks and events",
        "schedule_type": "cron",
        "schedule": "0 9 * * *",  # 9 AM every day
        "action": "summarize",
        "prompt": "Generate a summary of today's tasks, calendar events, and important notifications",
        "enabled": False
    },
    {
        "id": "hourly-check",
        "name": "Hourly System Check",
        "description": "Check system status every hour",
        "schedule_type": "interval",
        "schedule": "1h",  # Every hour
        "action": "system_check",
        "prompt": "Check system resources, running processes, and report any issues",
        "enabled": False
    },
    {
        "id": "weekly-cleanup",
        "name": "Weekly Cleanup",
        "description": "Clean up temporary files and organize downloads",
        "schedule_type": "cron",
        "schedule": "0 10 * * 0",  # 10 AM every Sunday
        "action": "cleanup",
        "prompt": "Clean up temporary files, organize downloads folder, and report what was cleaned",
        "enabled": False
    }
]
