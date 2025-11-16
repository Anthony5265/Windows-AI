"""
Conversation Memory Plugin
Maintains conversation history for chatbots and agents
"""

from typing import Dict, Any, Optional, List
from collections import deque


class ConversationMemoryPlugin:
    """Plugin for conversation memory management"""

    name = "conversation_memory"
    version = "1.0.0"
    description = "Store and retrieve conversation history with context windows"
    author = "Windows AI Team"

    def __init__(self):
        self.conversations = {}
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Conversation Memory plugin"""
        try:
            self.max_history = config.get("max_history", 10) if config else 10
            self._initialized = True
            return True
        except Exception as e:
            print(f"Error initializing Conversation Memory plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a conversation memory action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "add_message":
                return self._add_message(params)
            elif action == "get_history":
                return self._get_history(params)
            elif action == "clear":
                return self._clear(params)
            elif action == "summarize":
                return self._summarize(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _add_message(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add message to conversation history"""
        session_id = params.get("session_id", "default")
        role = params.get("role", "user")
        content = params.get("content", "")
        metadata = params.get("metadata", {})

        if session_id not in self.conversations:
            self.conversations[session_id] = deque(maxlen=self.max_history)

        message = {
            "role": role,
            "content": content,
            "metadata": metadata,
            "timestamp": params.get("timestamp")
        }

        self.conversations[session_id].append(message)

        return {
            "success": True,
            "session_id": session_id,
            "message_count": len(self.conversations[session_id])
        }

    def _get_history(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get conversation history"""
        session_id = params.get("session_id", "default")
        limit = params.get("limit", None)

        if session_id not in self.conversations:
            return {
                "success": True,
                "history": [],
                "count": 0
            }

        history = list(self.conversations[session_id])
        if limit:
            history = history[-limit:]

        return {
            "success": True,
            "history": history,
            "count": len(history)
        }

    def _clear(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Clear conversation history"""
        session_id = params.get("session_id", "default")

        if session_id in self.conversations:
            self.conversations[session_id].clear()

        return {
            "success": True,
            "session_id": session_id
        }

    def _summarize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize conversation for compression"""
        session_id = params.get("session_id", "default")

        if session_id not in self.conversations:
            return {"success": False, "error": "Session not found"}

        history = list(self.conversations[session_id])
        summary = f"Conversation with {len(history)} messages"

        return {
            "success": True,
            "summary": summary,
            "message_count": len(history)
        }

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.conversations = {}
        return True
