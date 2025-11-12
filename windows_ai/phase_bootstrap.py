"""Phase bootstrap utilities for Windows AI."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

try:  # pragma: no cover - optional dependency may be missing in tests
    from windows_ai.folder_watcher import EXAMPLE_WATCHERS, WatcherConfig
    _HAS_FOLDER_WATCHER = True
except Exception:  # pragma: no cover - fallback for minimal environments
    _HAS_FOLDER_WATCHER = False

    @dataclass
    class WatcherConfig:  # type: ignore[override]
        id: str
        name: str
        path: str
        patterns: list[str]
        events: list[str]
        action: str
        custom_prompt: Optional[str] = None
        enabled: bool = True
        recursive: bool = True
        created_at: Optional[str] = None

        def to_dict(self) -> Dict[str, object]:
            return {
                "id": self.id,
                "name": self.name,
                "path": self.path,
                "patterns": list(self.patterns),
                "events": list(self.events),
                "action": self.action,
                "custom_prompt": self.custom_prompt,
                "enabled": self.enabled,
                "recursive": self.recursive,
                "created_at": self.created_at,
            }

        @classmethod
        def from_dict(cls, data: Dict[str, object]) -> "WatcherConfig":
            return cls(**data)  # type: ignore[arg-type]

    EXAMPLE_WATCHERS = [
        {
            "id": "downloads-organizer",
            "name": "Downloads Organizer",
            "path": str(Path.home() / "Downloads"),
            "patterns": ["*.pdf", "*.docx", "*.xlsx", "*.pptx"],
            "events": ["created"],
            "action": "organize",
            "custom_prompt": "Organize this file into an appropriate folder based on its content and filename",
            "enabled": False,
            "recursive": False,
        },
        {
            "id": "documents-summarizer",
            "name": "Document Summarizer",
            "path": str(Path.home() / "Documents"),
            "patterns": ["*.pdf", "*.txt", "*.md"],
            "events": ["created", "modified"],
            "action": "summarize",
            "custom_prompt": "Create a brief summary of this document",
            "enabled": False,
            "recursive": True,
        },
        {
            "id": "source-control-analyzer",
            "name": "Source Control Analyzer",
            "path": str(Path.home() / "Projects"),
            "patterns": ["*.py", "*.ts", "*.rs"],
            "events": ["modified"],
            "action": "analyze",
            "custom_prompt": "Review the code diff and highlight risky changes",
            "enabled": False,
            "recursive": True,
        },
    ]

from windows_ai.scheduler import EXAMPLE_TASKS, ScheduledTask

logger = logging.getLogger(__name__)


class PhaseBootstrapper:
    """Ensure that each roadmap phase has a runnable baseline."""

    def __init__(
        self,
        folder_watcher_manager: Optional[object] = None,
        task_scheduler: Optional[object] = None,
    ) -> None:
        self._folder_watcher_manager = folder_watcher_manager
        self._task_scheduler = task_scheduler

    def ensure_defaults(self) -> Dict[str, int]:
        """Seed automation configs with curated defaults when missing."""
        return {
            "watchers_added": self._ensure_default_watchers(),
            "tasks_added": self._ensure_default_tasks(),
        }

    # watcher helpers -------------------------------------------------
    def _ensure_default_watchers(self) -> int:
        manager = self._folder_watcher_manager
        if not manager:
            return 0

        watchers = getattr(manager, "watchers", None)
        if watchers is None:
            logger.debug("Folder watcher manager missing 'watchers' attribute")
            return 0
        if watchers:
            return 0

        config_file: Optional[Path] = getattr(manager, "config_file", None)
        added = 0
        timestamp = datetime.now().isoformat()

        for entry in EXAMPLE_WATCHERS:
            config = WatcherConfig.from_dict({**entry, "enabled": False, "created_at": timestamp})
            watchers[config.id] = replace(config)
            added += 1

        if added:
            logger.info("Seeding %s default folder watchers", added)
            if config_file:
                config_file.parent.mkdir(parents=True, exist_ok=True)
            save_config = getattr(manager, "save_config", None)
            if callable(save_config):
                save_config()
            else:
                if config_file:
                    with config_file.open("w", encoding="utf-8") as fh:
                        json.dump({wid: cfg.to_dict() for wid, cfg in watchers.items()}, fh, indent=2)

        return added

    # scheduler helpers -----------------------------------------------
    def _ensure_default_tasks(self) -> int:
        scheduler = self._task_scheduler
        if not scheduler:
            return 0

        tasks = getattr(scheduler, "tasks", None)
        if tasks is None:
            logger.debug("Task scheduler missing 'tasks' attribute")
            return 0
        if tasks:
            return 0

        config_file: Optional[Path] = getattr(scheduler, "config_file", None)
        added = 0
        timestamp = datetime.now().isoformat()

        for entry in EXAMPLE_TASKS:
            task = ScheduledTask.from_dict({**entry, "enabled": False, "created_at": timestamp, "next_run": None, "last_run": None})
            tasks[task.id] = task
            added += 1

        if added:
            logger.info("Seeding %s default scheduled tasks", added)
            if config_file:
                config_file.parent.mkdir(parents=True, exist_ok=True)
            save_config = getattr(scheduler, "save_config", None)
            if callable(save_config):
                save_config()
            else:
                if config_file:
                    with config_file.open("w", encoding="utf-8") as fh:
                        json.dump({tid: task.to_dict() for tid, task in tasks.items()}, fh, indent=2)

        return added


__all__ = ["PhaseBootstrapper"]
