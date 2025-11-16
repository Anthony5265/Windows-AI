"""
Episodic Memory Plugin
Store and retrieve specific events and experiences
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import hashlib


class EpisodicMemoryPlugin:
    """Plugin for episodic memory (event-based memory)"""

    name = "episodic_memory"
    version = "1.0.0"
    description = "Store and retrieve specific events and experiences"
    author = "Windows AI Team"

    def __init__(self):
        self.episodes = {}
        self.timeline = []
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Episodic Memory plugin"""
        try:
            self._initialized = True
            return True
        except Exception as e:
            print(f"Error initializing Episodic Memory plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an Episodic Memory action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "store_episode":
                return self._store_episode(params)
            elif action == "recall_episode":
                return self._recall_episode(params)
            elif action == "recall_by_time":
                return self._recall_by_time(params)
            elif action == "recall_by_context":
                return self._recall_by_context(params)
            elif action == "get_timeline":
                return self._get_timeline(params)
            elif action == "consolidate":
                return self._consolidate(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _store_episode(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Store an episodic memory"""
        event = params.get("event", "")
        context = params.get("context", {})
        emotional_valence = params.get("emotional_valence", 0.0)  # -1 to 1
        importance = params.get("importance", 0.5)  # 0 to 1

        episode_id = hashlib.md5(f"{event}{datetime.now().isoformat()}".encode()).hexdigest()[:12]

        episode = {
            "id": episode_id,
            "event": event,
            "context": context,
            "timestamp": datetime.now().isoformat(),
            "emotional_valence": emotional_valence,
            "importance": importance,
            "recall_count": 0,
            "related_episodes": []
        }

        self.episodes[episode_id] = episode
        self.timeline.append(episode_id)

        return {
            "success": True,
            "episode_id": episode_id,
            "episode": episode
        }

    def _recall_episode(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Recall a specific episode by ID"""
        episode_id = params.get("episode_id", "")

        if episode_id not in self.episodes:
            return {"success": False, "error": f"Episode {episode_id} not found"}

        episode = self.episodes[episode_id]
        episode["recall_count"] += 1

        return {
            "success": True,
            "episode": episode
        }

    def _recall_by_time(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Recall episodes from a time period"""
        start_time = params.get("start_time")
        end_time = params.get("end_time")
        limit = params.get("limit", 10)

        matched_episodes = []

        for episode_id in self.timeline:
            episode = self.episodes[episode_id]
            ep_time = episode["timestamp"]

            # Check time range
            in_range = True
            if start_time and ep_time < start_time:
                in_range = False
            if end_time and ep_time > end_time:
                in_range = False

            if in_range:
                matched_episodes.append(episode)

            if len(matched_episodes) >= limit:
                break

        return {
            "success": True,
            "episodes": matched_episodes,
            "count": len(matched_episodes)
        }

    def _recall_by_context(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Recall episodes matching context cues"""
        context_cues = params.get("context", {})
        limit = params.get("limit", 10)

        matched_episodes = []

        for episode_id in reversed(self.timeline):  # Recent first
            episode = self.episodes[episode_id]
            ep_context = episode.get("context", {})

            # Check context match
            match_score = 0
            for key, value in context_cues.items():
                if key in ep_context and ep_context[key] == value:
                    match_score += 1

            if match_score > 0:
                episode_copy = episode.copy()
                episode_copy["match_score"] = match_score
                matched_episodes.append(episode_copy)

            if len(matched_episodes) >= limit:
                break

        # Sort by match score
        matched_episodes.sort(key=lambda x: x["match_score"], reverse=True)

        return {
            "success": True,
            "episodes": matched_episodes,
            "count": len(matched_episodes)
        }

    def _get_timeline(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get chronological timeline of episodes"""
        limit = params.get("limit", 50)
        reverse = params.get("reverse", False)  # Recent first if True

        timeline_ids = self.timeline[-limit:] if not reverse else list(reversed(self.timeline[-limit:]))

        timeline_episodes = [
            self.episodes[ep_id] for ep_id in timeline_ids
        ]

        return {
            "success": True,
            "timeline": timeline_episodes,
            "total_episodes": len(self.timeline)
        }

    def _consolidate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Consolidate related episodes (sleep-like process)"""
        similarity_threshold = params.get("threshold", 0.5)

        # Find related episodes
        consolidation_groups = []

        for i, ep1_id in enumerate(self.timeline):
            ep1 = self.episodes[ep1_id]

            group = [ep1_id]

            for ep2_id in self.timeline[i+1:]:
                ep2 = self.episodes[ep2_id]

                # Calculate similarity
                similarity = self._calculate_similarity(ep1, ep2)

                if similarity > similarity_threshold:
                    group.append(ep2_id)
                    # Link episodes
                    if ep2_id not in ep1["related_episodes"]:
                        ep1["related_episodes"].append(ep2_id)
                    if ep1_id not in ep2["related_episodes"]:
                        ep2["related_episodes"].append(ep1_id)

            if len(group) > 1:
                consolidation_groups.append(group)

        return {
            "success": True,
            "consolidation_groups": consolidation_groups,
            "groups_formed": len(consolidation_groups)
        }

    def _calculate_similarity(self, ep1: Dict[str, Any], ep2: Dict[str, Any]) -> float:
        """Calculate similarity between two episodes"""
        similarity = 0.0

        # Context similarity
        ctx1 = ep1.get("context", {})
        ctx2 = ep2.get("context", {})

        if ctx1 and ctx2:
            common_keys = set(ctx1.keys()) & set(ctx2.keys())
            matching_values = sum(1 for k in common_keys if ctx1[k] == ctx2[k])
            similarity += (matching_values / max(len(ctx1), len(ctx2))) * 0.5

        # Emotional similarity
        val1 = ep1.get("emotional_valence", 0)
        val2 = ep2.get("emotional_valence", 0)
        emotion_sim = 1.0 - abs(val1 - val2) / 2.0
        similarity += emotion_sim * 0.3

        # Event content similarity (simplified)
        event1_words = set(ep1.get("event", "").lower().split())
        event2_words = set(ep2.get("event", "").lower().split())
        if event1_words and event2_words:
            word_overlap = len(event1_words & event2_words) / len(event1_words | event2_words)
            similarity += word_overlap * 0.2

        return min(similarity, 1.0)

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.episodes = {}
        self.timeline = []
        return True
