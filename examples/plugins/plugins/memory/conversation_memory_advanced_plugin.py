"""
Conversation Memory Advanced Plugin
Track and manage multi-turn conversations with context retention
"""

from typing import Dict, Any, Optional, List
from collections import deque


class ConversationMemoryAdvancedPlugin:
    """Plugin for advanced conversation memory management"""

    name = "conversation_memory_advanced"
    version = "1.0.0"
    description = "Advanced conversation tracking with context windows and summarization"
    author = "Windows AI Team"

    def __init__(self):
        self.conversations = {}
        self.context_windows = {}
        self.summaries = {}
        self.max_window_size = 10
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Conversation Memory plugin"""
        try:
            if config:
                self.max_window_size = config.get("max_window_size", 10)
            self._initialized = True
            return True
        except Exception as e:
            print(f"Error initializing Conversation Memory plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Conversation Memory action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "create_conversation":
                return self._create_conversation(params)
            elif action == "add_turn":
                return self._add_turn(params)
            elif action == "get_context":
                return self._get_context(params)
            elif action == "summarize":
                return self._summarize(params)
            elif action == "search_conversation":
                return self._search_conversation(params)
            elif action == "merge_conversations":
                return self._merge_conversations(params)
            elif action == "get_statistics":
                return self._get_statistics(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _create_conversation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new conversation"""
        conv_id = params.get("conversation_id", f"conv_{len(self.conversations)}")
        participants = params.get("participants", ["user", "assistant"])
        metadata = params.get("metadata", {})

        conversation = {
            "id": conv_id,
            "participants": participants,
            "turns": [],
            "metadata": metadata,
            "created_at": "now",
            "last_updated": "now"
        }

        self.conversations[conv_id] = conversation
        self.context_windows[conv_id] = deque(maxlen=self.max_window_size)
        self.summaries[conv_id] = []

        return {
            "success": True,
            "conversation_id": conv_id,
            "conversation": conversation
        }

    def _add_turn(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add a turn to a conversation"""
        conv_id = params.get("conversation_id", "")
        speaker = params.get("speaker", "user")
        message = params.get("message", "")
        metadata = params.get("metadata", {})

        if conv_id not in self.conversations:
            return {"success": False, "error": f"Conversation {conv_id} not found"}

        turn = {
            "turn_number": len(self.conversations[conv_id]["turns"]),
            "speaker": speaker,
            "message": message,
            "metadata": metadata,
            "timestamp": "now"
        }

        self.conversations[conv_id]["turns"].append(turn)
        self.conversations[conv_id]["last_updated"] = "now"

        # Update context window
        self.context_windows[conv_id].append(turn)

        # Auto-summarize if conversation gets long
        if len(self.conversations[conv_id]["turns"]) % 20 == 0:
            self._auto_summarize(conv_id)

        return {
            "success": True,
            "turn": turn,
            "total_turns": len(self.conversations[conv_id]["turns"]),
            "context_window_size": len(self.context_windows[conv_id])
        }

    def _get_context(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get conversation context (recent turns + summary)"""
        conv_id = params.get("conversation_id", "")
        window_size = params.get("window_size", self.max_window_size)
        include_summary = params.get("include_summary", True)

        if conv_id not in self.conversations:
            return {"success": False, "error": f"Conversation {conv_id} not found"}

        conversation = self.conversations[conv_id]

        # Get recent turns
        recent_turns = list(self.context_windows[conv_id])[-window_size:]

        context = {
            "conversation_id": conv_id,
            "recent_turns": recent_turns,
            "window_size": len(recent_turns)
        }

        if include_summary and self.summaries.get(conv_id):
            context["summary"] = self.summaries[conv_id][-1] if self.summaries[conv_id] else None
            context["total_summaries"] = len(self.summaries[conv_id])

        return {
            "success": True,
            "context": context,
            "total_turns": len(conversation["turns"])
        }

    def _summarize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of the conversation"""
        conv_id = params.get("conversation_id", "")
        start_turn = params.get("start_turn", 0)
        end_turn = params.get("end_turn", None)

        if conv_id not in self.conversations:
            return {"success": False, "error": f"Conversation {conv_id} not found"}

        conversation = self.conversations[conv_id]
        turns = conversation["turns"][start_turn:end_turn]

        # Create summary
        summary = {
            "conversation_id": conv_id,
            "turn_range": f"{start_turn}-{end_turn or len(conversation['turns'])}",
            "num_turns": len(turns),
            "participants": conversation["participants"],
            "key_points": self._extract_key_points(turns),
            "topics": self._extract_topics(turns),
            "created_at": "now"
        }

        self.summaries[conv_id].append(summary)

        return {
            "success": True,
            "summary": summary,
            "total_summaries": len(self.summaries[conv_id])
        }

    def _auto_summarize(self, conv_id: str):
        """Automatically summarize conversation at intervals"""
        if conv_id not in self.conversations:
            return

        conversation = self.conversations[conv_id]
        num_turns = len(conversation["turns"])

        # Summarize last 20 turns
        start_turn = max(0, num_turns - 20)
        self._summarize({
            "conversation_id": conv_id,
            "start_turn": start_turn,
            "end_turn": num_turns
        })

    def _extract_key_points(self, turns: List[Dict[str, Any]]) -> List[str]:
        """Extract key points from turns"""
        key_points = []

        for turn in turns:
            message = turn["message"]

            # Simple heuristics for key points
            if len(message) > 100:
                key_points.append(f"{turn['speaker']}: {message[:100]}...")
            elif "?" in message:
                key_points.append(f"Question by {turn['speaker']}: {message}")
            elif any(word in message.lower() for word in ["important", "key", "note", "remember"]):
                key_points.append(f"Important from {turn['speaker']}: {message}")

        return key_points[:5]  # Top 5 key points

    def _extract_topics(self, turns: List[Dict[str, Any]]) -> List[str]:
        """Extract topics discussed in turns"""
        topics = set()

        # Simple topic extraction based on common nouns
        for turn in turns:
            message = turn["message"].lower()

            # Extract potential topics (simplified)
            words = message.split()
            for word in words:
                if len(word) > 5 and word.isalpha():
                    topics.add(word)

        return list(topics)[:10]  # Top 10 topics

    def _search_conversation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search within a conversation"""
        conv_id = params.get("conversation_id", "")
        query = params.get("query", "")
        search_type = params.get("type", "keyword")  # keyword, speaker, metadata

        if conv_id not in self.conversations:
            return {"success": False, "error": f"Conversation {conv_id} not found"}

        conversation = self.conversations[conv_id]
        results = []

        for turn in conversation["turns"]:
            if search_type == "keyword":
                if query.lower() in turn["message"].lower():
                    results.append(turn)
            elif search_type == "speaker":
                if turn["speaker"] == query:
                    results.append(turn)
            elif search_type == "metadata":
                if query in turn.get("metadata", {}):
                    results.append(turn)

        return {
            "success": True,
            "query": query,
            "search_type": search_type,
            "results": results,
            "num_results": len(results)
        }

    def _merge_conversations(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Merge multiple conversations into one"""
        conv_ids = params.get("conversation_ids", [])
        new_conv_id = params.get("new_conversation_id", f"merged_{len(self.conversations)}")

        if len(conv_ids) < 2:
            return {"success": False, "error": "Need at least 2 conversations to merge"}

        # Validate all conversations exist
        for conv_id in conv_ids:
            if conv_id not in self.conversations:
                return {"success": False, "error": f"Conversation {conv_id} not found"}

        # Create merged conversation
        merged = {
            "id": new_conv_id,
            "participants": [],
            "turns": [],
            "metadata": {"merged_from": conv_ids},
            "created_at": "now",
            "last_updated": "now"
        }

        # Merge participants
        all_participants = set()
        for conv_id in conv_ids:
            all_participants.update(self.conversations[conv_id]["participants"])
        merged["participants"] = list(all_participants)

        # Merge turns (chronologically)
        for conv_id in conv_ids:
            merged["turns"].extend(self.conversations[conv_id]["turns"])

        # Re-number turns
        for i, turn in enumerate(merged["turns"]):
            turn["turn_number"] = i

        self.conversations[new_conv_id] = merged
        self.context_windows[new_conv_id] = deque(merged["turns"][-self.max_window_size:],
                                                   maxlen=self.max_window_size)

        return {
            "success": True,
            "merged_conversation_id": new_conv_id,
            "total_turns": len(merged["turns"]),
            "participants": merged["participants"]
        }

    def _get_statistics(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get conversation statistics"""
        conv_id = params.get("conversation_id", "")

        if conv_id not in self.conversations:
            return {"success": False, "error": f"Conversation {conv_id} not found"}

        conversation = self.conversations[conv_id]

        # Calculate statistics
        speaker_counts = {}
        total_words = 0

        for turn in conversation["turns"]:
            speaker = turn["speaker"]
            speaker_counts[speaker] = speaker_counts.get(speaker, 0) + 1
            total_words += len(turn["message"].split())

        stats = {
            "conversation_id": conv_id,
            "total_turns": len(conversation["turns"]),
            "participants": conversation["participants"],
            "speaker_distribution": speaker_counts,
            "total_words": total_words,
            "avg_words_per_turn": total_words / len(conversation["turns"]) if conversation["turns"] else 0,
            "total_summaries": len(self.summaries.get(conv_id, [])),
            "duration": "calculated based on timestamps"
        }

        return {
            "success": True,
            "statistics": stats
        }

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.conversations = {}
        self.context_windows = {}
        self.summaries = {}
        return True
