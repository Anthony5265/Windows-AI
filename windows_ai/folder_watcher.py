"""
Windows AI - Folder Watcher System

Monitors specified directories for file changes and triggers AI actions.
Supports:
- File creation, modification, deletion events
- Pattern-based filtering (e.g., *.pdf, *.txt)
- Custom AI actions on events
- Multiple watcher configurations
"""

import os
import time
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
import json

logger = logging.getLogger(__name__)


@dataclass
class WatcherConfig:
    """Configuration for a folder watcher"""
    id: str
    name: str
    path: str
    patterns: List[str]  # File patterns to watch (e.g., ['*.pdf', '*.txt'])
    events: List[str]  # Events to watch: created, modified, deleted, moved
    action: str  # AI action to perform: 'organize', 'summarize', 'analyze', 'custom'
    custom_prompt: Optional[str] = None
    enabled: bool = True
    recursive: bool = True
    created_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WatcherConfig':
        return cls(**data)


class AIFileEventHandler(FileSystemEventHandler):
    """Handles file system events and triggers AI actions"""

    def __init__(self, config: WatcherConfig, callback: Callable):
        super().__init__()
        self.config = config
        self.callback = callback
        self.last_events: Dict[str, float] = {}  # Debounce duplicate events
        self.debounce_seconds = 1.0

    def _should_process(self, src_path: str) -> bool:
        """Check if file matches patterns and debounce duplicate events"""
        # Check patterns
        if self.config.patterns:
            matches = any(
                Path(src_path).match(pattern)
                for pattern in self.config.patterns
            )
            if not matches:
                return False

        # Debounce duplicate events
        now = time.time()
        last_time = self.last_events.get(src_path, 0)
        if now - last_time < self.debounce_seconds:
            return False

        self.last_events[src_path] = now
        return True

    def _trigger_action(self, event: FileSystemEvent, event_type: str):
        """Trigger AI action for the event"""
        if not self._should_process(event.src_path):
            return

        if event_type not in self.config.events:
            return

        logger.info(f"Watcher '{self.config.name}': {event_type} - {event.src_path}")

        # Call async callback
        try:
            asyncio.create_task(
                self.callback(
                    watcher_id=self.config.id,
                    watcher_name=self.config.name,
                    event_type=event_type,
                    file_path=event.src_path,
                    action=self.config.action,
                    custom_prompt=self.config.custom_prompt
                )
            )
        except Exception as e:
            logger.error(f"Error triggering action: {e}")

    def on_created(self, event):
        if not event.is_directory:
            self._trigger_action(event, 'created')

    def on_modified(self, event):
        if not event.is_directory:
            self._trigger_action(event, 'modified')

    def on_deleted(self, event):
        if not event.is_directory:
            self._trigger_action(event, 'deleted')

    def on_moved(self, event):
        if not event.is_directory:
            self._trigger_action(event, 'moved')


class FolderWatcherManager:
    """Manages multiple folder watchers"""

    def __init__(self, config_file: Path):
        self.config_file = config_file
        self.watchers: Dict[str, WatcherConfig] = {}
        self.observers: Dict[str, Observer] = {}
        self.event_callback: Optional[Callable] = None
        self.load_config()

    def load_config(self):
        """Load watcher configurations from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self.watchers = {
                        wid: WatcherConfig.from_dict(wdata)
                        for wid, wdata in data.items()
                    }
                logger.info(f"Loaded {len(self.watchers)} watcher configs")
            except Exception as e:
                logger.error(f"Error loading watcher config: {e}")
        else:
            self.watchers = {}

    def save_config(self):
        """Save watcher configurations to file"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                data = {wid: w.to_dict() for wid, w in self.watchers.items()}
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(self.watchers)} watcher configs")
        except Exception as e:
            logger.error(f"Error saving watcher config: {e}")

    def set_event_callback(self, callback: Callable):
        """Set callback for file events"""
        self.event_callback = callback

    async def add_watcher(self, config: WatcherConfig) -> bool:
        """Add a new folder watcher"""
        # Validate path
        if not os.path.exists(config.path):
            logger.error(f"Path does not exist: {config.path}")
            return False

        if not os.path.isdir(config.path):
            logger.error(f"Path is not a directory: {config.path}")
            return False

        # Add timestamp
        if not config.created_at:
            config.created_at = datetime.now().isoformat()

        # Save config
        self.watchers[config.id] = config
        self.save_config()

        # Start watching if enabled
        if config.enabled:
            await self.start_watcher(config.id)

        logger.info(f"Added watcher: {config.name} ({config.id})")
        return True

    async def remove_watcher(self, watcher_id: str) -> bool:
        """Remove a folder watcher"""
        if watcher_id not in self.watchers:
            return False

        # Stop if running
        await self.stop_watcher(watcher_id)

        # Remove config
        del self.watchers[watcher_id]
        self.save_config()

        logger.info(f"Removed watcher: {watcher_id}")
        return True

    async def start_watcher(self, watcher_id: str) -> bool:
        """Start a folder watcher"""
        if watcher_id not in self.watchers:
            return False

        config = self.watchers[watcher_id]

        # Stop if already running
        if watcher_id in self.observers:
            await self.stop_watcher(watcher_id)

        # Create observer
        try:
            observer = Observer()
            event_handler = AIFileEventHandler(config, self.event_callback)
            observer.schedule(
                event_handler,
                config.path,
                recursive=config.recursive
            )
            observer.start()

            self.observers[watcher_id] = observer
            logger.info(f"Started watcher: {config.name} on {config.path}")
            return True
        except Exception as e:
            logger.error(f"Error starting watcher {watcher_id}: {e}")
            return False

    async def stop_watcher(self, watcher_id: str) -> bool:
        """Stop a folder watcher"""
        if watcher_id not in self.observers:
            return False

        try:
            observer = self.observers[watcher_id]
            observer.stop()
            observer.join(timeout=2.0)
            del self.observers[watcher_id]
            logger.info(f"Stopped watcher: {watcher_id}")
            return True
        except Exception as e:
            logger.error(f"Error stopping watcher {watcher_id}: {e}")
            return False

    async def start_all(self):
        """Start all enabled watchers"""
        for watcher_id, config in self.watchers.items():
            if config.enabled:
                await self.start_watcher(watcher_id)

    async def stop_all(self):
        """Stop all running watchers"""
        for watcher_id in list(self.observers.keys()):
            await self.stop_watcher(watcher_id)

    def get_watcher(self, watcher_id: str) -> Optional[WatcherConfig]:
        """Get watcher configuration"""
        return self.watchers.get(watcher_id)

    def list_watchers(self) -> List[Dict[str, Any]]:
        """List all watchers with their status"""
        result = []
        for wid, config in self.watchers.items():
            result.append({
                **config.to_dict(),
                'running': wid in self.observers
            })
        return result

    async def update_watcher(self, watcher_id: str, updates: Dict[str, Any]) -> bool:
        """Update watcher configuration"""
        if watcher_id not in self.watchers:
            return False

        config = self.watchers[watcher_id]
        was_enabled = config.enabled

        # Update fields
        for key, value in updates.items():
            if hasattr(config, key):
                setattr(config, key, value)

        self.save_config()

        # Restart if needed
        if config.enabled and watcher_id in self.observers:
            await self.stop_watcher(watcher_id)
            await self.start_watcher(watcher_id)
        elif config.enabled and not was_enabled:
            await self.start_watcher(watcher_id)
        elif not config.enabled and was_enabled:
            await self.stop_watcher(watcher_id)

        return True


# Example watcher configurations
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
        "recursive": False
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
        "recursive": True
    }
]
