"""
Contextual Awareness & Memory System
Tracks user context, active applications, and provides persistent memory
"""
import json
import logging
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from collections import deque
import threading

logger = logging.getLogger(__name__)


@dataclass
class UserContext:
    """Current user context snapshot"""
    timestamp: str
    active_application: Optional[str]
    active_window_title: Optional[str]
    recent_files: List[str]
    clipboard_content: Optional[str]
    cpu_usage: float
    memory_usage: float
    focus_duration: int  # seconds on current application
    task_category: Optional[str]  # inferred task type


@dataclass
class MemoryEntry:
    """Persistent memory entry"""
    timestamp: str
    event_type: str  # 'interaction', 'preference', 'task', 'learning'
    content: str
    metadata: Dict[str, Any]
    importance: int  # 1-10 scale


class ContextualAwarenessSystem:
    """
    Manages contextual awareness and persistent memory

    Features:
    - Tracks active applications and windows
    - Monitors user focus patterns
    - Stores persistent user context
    - Provides context for AI decision-making
    - Learns user preferences over time
    """

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.context_file = data_dir / "user_context.json"
        self.memory_file = data_dir / "persistent_memory.json"

        # Short-term context (recent N actions)
        self.temporal_context: deque = deque(maxlen=100)

        # Persistent memory
        self.persistent_memory: List[MemoryEntry] = []

        # Current context
        self.current_context: Optional[UserContext] = None

        # Application tracking
        self.active_app_start_time: Optional[float] = None
        self.last_active_app: Optional[str] = None

        # User preferences learned over time
        self.user_preferences: Dict[str, Any] = {}

        # Load existing data
        self._load_memory()
        self._load_preferences()

        # Start monitoring thread
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None

    def start_monitoring(self, interval: int = 5):
        """Start background monitoring of user context"""
        if self._monitoring:
            logger.warning("Context monitoring already running")
            return

        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self._monitor_thread.start()
        logger.info(f"Started context monitoring (interval: {interval}s)")

    def stop_monitoring(self):
        """Stop background monitoring"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2)
        logger.info("Stopped context monitoring")

    def _monitor_loop(self, interval: int):
        """Background monitoring loop"""
        while self._monitoring:
            try:
                self.update_context()
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Error in context monitoring: {e}")
                time.sleep(interval)

    def update_context(self):
        """Update current user context"""
        try:
            # Get active application
            active_app, window_title = self._get_active_application()

            # Calculate focus duration
            focus_duration = 0
            if active_app == self.last_active_app and self.active_app_start_time:
                focus_duration = int(time.time() - self.active_app_start_time)
            else:
                self.last_active_app = active_app
                self.active_app_start_time = time.time()

            # Get system metrics
            cpu_usage = psutil.cpu_percent(interval=0.1)
            memory_usage = psutil.virtual_memory().percent

            # Get recent files (would integrate with file watcher)
            recent_files = self._get_recent_files()

            # Infer task category
            task_category = self._infer_task_category(active_app, window_title)

            # Create context snapshot
            context = UserContext(
                timestamp=datetime.now().isoformat(),
                active_application=active_app,
                active_window_title=window_title,
                recent_files=recent_files,
                clipboard_content=None,  # Would use pyperclip
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                focus_duration=focus_duration,
                task_category=task_category
            )

            self.current_context = context
            self.temporal_context.append(asdict(context))

            # Save periodically
            if len(self.temporal_context) % 20 == 0:
                self._save_context()

        except Exception as e:
            logger.error(f"Error updating context: {e}")

    def _get_active_application(self) -> tuple[Optional[str], Optional[str]]:
        """Get currently active application and window title"""
        try:
            # For Windows, would use win32gui
            # For now, get foreground process
            import platform
            if platform.system() == "Windows":
                try:
                    import win32gui
                    import win32process

                    hwnd = win32gui.GetForegroundWindow()
                    window_title = win32gui.GetWindowText(hwnd)
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)

                    process = psutil.Process(pid)
                    app_name = process.name()

                    return app_name, window_title
                except ImportError:
                    logger.warning("win32gui not available, using fallback")
                except Exception as e:
                    logger.debug(f"Error getting active window: {e}")

            # Fallback: just return None
            return None, None

        except Exception as e:
            logger.error(f"Error getting active application: {e}")
            return None, None

    def _get_recent_files(self, limit: int = 10) -> List[str]:
        """Get recently accessed files"""
        # Would integrate with file watcher or OS recent files
        # For now, return empty
        return []

    def _infer_task_category(self, app: Optional[str], window_title: Optional[str]) -> Optional[str]:
        """Infer what type of task user is doing"""
        if not app:
            return None

        app_lower = app.lower()
        title_lower = (window_title or "").lower()

        # Development
        if any(x in app_lower for x in ['code', 'visual studio', 'pycharm', 'intellij', 'sublime']):
            return "development"

        # Communication
        if any(x in app_lower for x in ['outlook', 'thunderbird', 'slack', 'teams', 'discord']):
            return "communication"

        # Browsing
        if any(x in app_lower for x in ['chrome', 'firefox', 'edge', 'safari', 'brave']):
            if any(x in title_lower for x in ['youtube', 'netflix', 'twitch']):
                return "entertainment"
            elif any(x in title_lower for x in ['github', 'stackoverflow', 'docs']):
                return "research"
            return "browsing"

        # Office work
        if any(x in app_lower for x in ['word', 'excel', 'powerpoint', 'libreoffice']):
            return "office_work"

        # Media
        if any(x in app_lower for x in ['spotify', 'vlc', 'media player', 'photoshop', 'gimp']):
            return "media"

        return "general"

    def add_memory(self, event_type: str, content: str, metadata: Dict[str, Any] = None, importance: int = 5):
        """Add entry to persistent memory"""
        entry = MemoryEntry(
            timestamp=datetime.now().isoformat(),
            event_type=event_type,
            content=content,
            metadata=metadata or {},
            importance=importance
        )

        self.persistent_memory.append(entry)

        # Keep only important memories (importance >= 5) or recent ones
        self._prune_memory()

        # Save
        self._save_memory()

        logger.info(f"Added memory: {event_type} - {content[:50]}...")

    def _prune_memory(self, max_memories: int = 1000):
        """Remove old, low-importance memories"""
        if len(self.persistent_memory) <= max_memories:
            return

        # Sort by importance (desc) and timestamp (desc)
        sorted_memories = sorted(
            self.persistent_memory,
            key=lambda m: (m.importance, m.timestamp),
            reverse=True
        )

        # Keep top N
        self.persistent_memory = sorted_memories[:max_memories]

    def get_relevant_context(self, query: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
        """
        Get relevant context for AI decision-making

        Returns:
            - Current context
            - Recent temporal context
            - Relevant memories
            - User preferences
        """
        result = {
            "current_context": asdict(self.current_context) if self.current_context else None,
            "temporal_context": list(self.temporal_context)[-limit:],
            "recent_memories": [asdict(m) for m in self.persistent_memory[-limit:]],
            "user_preferences": self.user_preferences,
            "task_patterns": self._analyze_task_patterns()
        }

        return result

    def _analyze_task_patterns(self) -> Dict[str, Any]:
        """Analyze user task patterns from context history"""
        if not self.temporal_context:
            return {}

        # Count task categories
        task_counts: Dict[str, int] = {}
        app_usage: Dict[str, float] = {}

        for ctx in self.temporal_context:
            category = ctx.get("task_category")
            if category:
                task_counts[category] = task_counts.get(category, 0) + 1

            app = ctx.get("active_application")
            duration = ctx.get("focus_duration", 0)
            if app:
                app_usage[app] = app_usage.get(app, 0) + duration

        return {
            "task_distribution": task_counts,
            "app_usage_time": app_usage,
            "most_common_task": max(task_counts, key=task_counts.get) if task_counts else None
        }

    def learn_preference(self, key: str, value: Any):
        """Learn and store user preference"""
        self.user_preferences[key] = value
        self._save_preferences()
        logger.info(f"Learned preference: {key} = {value}")

    def _save_context(self):
        """Save temporal context to file"""
        try:
            with open(self.context_file, 'w') as f:
                json.dump(list(self.temporal_context), f, indent=2)
        except Exception as e:
            logger.error(f"Error saving context: {e}")

    def _save_memory(self):
        """Save persistent memory to file"""
        try:
            memories_dict = [asdict(m) for m in self.persistent_memory]
            with open(self.memory_file, 'w') as f:
                json.dump(memories_dict, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving memory: {e}")

    def _load_memory(self):
        """Load persistent memory from file"""
        try:
            if self.memory_file.exists():
                with open(self.memory_file, 'r') as f:
                    memories_dict = json.load(f)
                    self.persistent_memory = [
                        MemoryEntry(**m) for m in memories_dict
                    ]
                logger.info(f"Loaded {len(self.persistent_memory)} memories")
        except Exception as e:
            logger.error(f"Error loading memory: {e}")

    def _save_preferences(self):
        """Save user preferences"""
        try:
            prefs_file = self.data_dir / "user_preferences.json"
            with open(prefs_file, 'w') as f:
                json.dump(self.user_preferences, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving preferences: {e}")

    def _load_preferences(self):
        """Load user preferences"""
        try:
            prefs_file = self.data_dir / "user_preferences.json"
            if prefs_file.exists():
                with open(prefs_file, 'r') as f:
                    self.user_preferences = json.load(f)
                logger.info(f"Loaded {len(self.user_preferences)} preferences")
        except Exception as e:
            logger.error(f"Error loading preferences: {e}")


# Global instance
_context_manager: Optional[ContextualAwarenessSystem] = None


def get_context_manager(data_dir: Path = None) -> ContextualAwarenessSystem:
    """Get or create global context manager"""
    global _context_manager

    if _context_manager is None:
        if data_dir is None:
            data_dir = Path.home() / ".windows-ai" / "context"
        _context_manager = ContextualAwarenessSystem(data_dir)

    return _context_manager


def initialize_context_system(data_dir: Path = None, start_monitoring: bool = True):
    """Initialize the contextual awareness system"""
    manager = get_context_manager(data_dir)

    if start_monitoring:
        manager.start_monitoring(interval=5)

    logger.info("Contextual awareness system initialized")
    return manager
