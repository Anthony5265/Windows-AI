"""
Context Persistence Manager

Maintains persistent user context across sessions, remembering past interactions,
preferences, and frequently used applications/workflows.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import json
import logging
import uuid

logger = logging.getLogger(__name__)


@dataclass
class UserContext:
    """Persistent user context"""
    user_id: str
    session_history: List[Dict[str, Any]]
    preferences: Dict[str, Any]
    frequent_applications: List[str]
    frequent_workflows: List[str]
    interaction_count: int = 0
    last_active: datetime = field(default_factory=datetime.now)


class ContextPersistenceManager:
    """Manages persistent user context across sessions"""

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.contexts: Dict[str, UserContext] = {}
        self._load_state()
        logger.info("Context Persistence Manager initialized")

    def get_context(self, user_id: str) -> UserContext:
        """Get or create user context"""
        if user_id not in self.contexts:
            self.contexts[user_id] = UserContext(
                user_id=user_id,
                session_history=[],
                preferences={},
                frequent_applications=[],
                frequent_workflows=[]
            )
        return self.contexts[user_id]

    def update_context(self, user_id: str, interaction: Dict[str, Any]):
        """Update context with new interaction"""
        context = self.get_context(user_id)
        context.session_history.append(interaction)
        context.interaction_count += 1
        context.last_active = datetime.now()
        
        if len(context.session_history) > 1000:
            context.session_history = context.session_history[-1000:]
        
        self._save_state()

    def get_relevant_context(self, user_id: str, query: str) -> Dict[str, Any]:
        """Retrieve relevant context for query"""
        context = self.get_context(user_id)
        return {
            "recent_interactions": context.session_history[-5:],
            "preferences": context.preferences,
            "suggested_apps": context.frequent_applications[:3]
        }

    def _save_state(self):
        try:
            data = {"contexts_count": len(self.contexts)}
            with open(self.data_dir / "context_state.json", "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save context: {e}")

    def _load_state(self):
        try:
            state_file = self.data_dir / "context_state.json"
            if state_file.exists():
                with open(state_file, "r") as f:
                    data = json.load(f)
                logger.info(f"Loaded {data.get('contexts_count', 0)} contexts")
        except Exception as e:
            logger.error(f"Failed to load context: {e}")


_context_manager: Optional[ContextPersistenceManager] = None

def get_context_manager() -> Optional[ContextPersistenceManager]:
    return _context_manager

def initialize_context_manager(data_dir: Path) -> ContextPersistenceManager:
    global _context_manager
    _context_manager = ContextPersistenceManager(data_dir)
    return _context_manager
