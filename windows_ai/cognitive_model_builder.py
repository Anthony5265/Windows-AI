"""
Cognitive Model Builder

Develops sophisticated cognitive models of individual users, encompassing learning style,
decision-making patterns, emotional triggers, and information consumption preferences.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class CognitiveProfile:
    """User cognitive profile"""
    user_id: str
    learning_style: str  # visual, auditory, kinesthetic, reading
    decision_pattern: str  # analytical, intuitive, balanced
    attention_span: float  # minutes
    cognitive_load_tolerance: float  # 0-1 scale
    emotional_triggers: List[str]
    information_preferences: Dict[str, float]
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class CognitiveState:
    """Real-time cognitive state"""
    state_id: str
    user_id: str
    current_load: float  # 0-1 scale
    attention_level: float  # 0-1 scale
    emotional_state: str  # focused, stressed, relaxed, frustrated
    fatigue_level: float  # 0-1 scale
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class InteractionPattern:
    """User interaction pattern"""
    pattern_id: str
    user_id: str
    activity_type: str
    frequency: int
    duration_avg: float
    success_rate: float
    preferences: Dict[str, Any]


class CognitiveModelBuilder:
    """
    Cognitive Model Builder System

    Builds and maintains sophisticated cognitive models of users
    """

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.profiles: Dict[str, CognitiveProfile] = {}
        self.states: List[CognitiveState] = []
        self.patterns: List[InteractionPattern] = []

        self._load_state()
        logger.info("Cognitive Model Builder initialized")

    def create_profile(
        self,
        user_id: str,
        initial_preferences: Optional[Dict[str, Any]] = None
    ) -> CognitiveProfile:
        """Create new cognitive profile for user"""
        import uuid

        profile = CognitiveProfile(
            user_id=user_id,
            learning_style="balanced",
            decision_pattern="analytical",
            attention_span=25.0,  # Pomodoro default
            cognitive_load_tolerance=0.7,
            emotional_triggers=[],
            information_preferences=initial_preferences or {}
        )

        self.profiles[user_id] = profile
        self._save_state()

        logger.info(f"Created cognitive profile for user {user_id}")
        return profile

    def update_cognitive_state(
        self,
        user_id: str,
        activity_data: Dict[str, Any]
    ) -> CognitiveState:
        """Update real-time cognitive state"""
        import uuid

        # Analyze activity data to infer cognitive state
        cognitive_load = self._estimate_cognitive_load(activity_data)
        attention_level = self._estimate_attention(activity_data)
        emotional_state = self._detect_emotional_state(activity_data)
        fatigue_level = self._estimate_fatigue(activity_data)

        state = CognitiveState(
            state_id=str(uuid.uuid4()),
            user_id=user_id,
            current_load=cognitive_load,
            attention_level=attention_level,
            emotional_state=emotional_state,
            fatigue_level=fatigue_level
        )

        self.states.append(state)

        # Update profile based on state history
        if user_id in self.profiles:
            self._update_profile_from_state(user_id, state)

        logger.info(f"Updated cognitive state for {user_id}: {emotional_state}")
        return state

    def analyze_interaction_pattern(
        self,
        user_id: str,
        interactions: List[Dict[str, Any]]
    ) -> List[InteractionPattern]:
        """Analyze user interaction patterns"""
        import uuid
        from collections import defaultdict

        # Group by activity type
        activity_groups = defaultdict(list)
        for interaction in interactions:
            activity_type = interaction.get("type", "unknown")
            activity_groups[activity_type].append(interaction)

        patterns = []
        for activity_type, activity_list in activity_groups.items():
            pattern = InteractionPattern(
                pattern_id=str(uuid.uuid4()),
                user_id=user_id,
                activity_type=activity_type,
                frequency=len(activity_list),
                duration_avg=sum(a.get("duration", 0) for a in activity_list) / len(activity_list),
                success_rate=sum(1 for a in activity_list if a.get("success", False)) / len(activity_list),
                preferences=self._extract_preferences(activity_list)
            )
            patterns.append(pattern)

        self.patterns.extend(patterns)
        self._save_state()

        logger.info(f"Analyzed {len(patterns)} interaction patterns for {user_id}")
        return patterns

    def predict_cognitive_state(
        self,
        user_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Predict future cognitive state"""
        if user_id not in self.profiles:
            return {}

        profile = self.profiles[user_id]
        recent_states = [s for s in self.states if s.user_id == user_id][-10:]

        if not recent_states:
            return {
                "predicted_load": profile.cognitive_load_tolerance,
                "predicted_attention": 0.8,
                "predicted_emotional_state": "neutral",
                "confidence": 0.3
            }

        # Simple prediction based on recent trends
        avg_load = sum(s.current_load for s in recent_states) / len(recent_states)
        avg_attention = sum(s.attention_level for s in recent_states) / len(recent_states)

        return {
            "predicted_load": min(1.0, avg_load * 1.1),  # Slight increase expected
            "predicted_attention": max(0.0, avg_attention * 0.95),  # Slight decrease
            "predicted_emotional_state": recent_states[-1].emotional_state,
            "confidence": 0.7
        }

    def get_learning_recommendations(self, user_id: str) -> List[str]:
        """Get personalized learning recommendations"""
        if user_id not in self.profiles:
            return []

        profile = self.profiles[user_id]
        recommendations = []

        if profile.learning_style == "visual":
            recommendations.extend([
                "Use diagrams and charts for explanations",
                "Provide video tutorials",
                "Show visual progress indicators"
            ])
        elif profile.learning_style == "auditory":
            recommendations.extend([
                "Provide audio explanations",
                "Use voice feedback",
                "Enable text-to-speech for documentation"
            ])
        elif profile.learning_style == "kinesthetic":
            recommendations.extend([
                "Offer interactive demos",
                "Enable hands-on practice",
                "Provide step-by-step walkthroughs"
            ])

        return recommendations

    def _estimate_cognitive_load(self, activity_data: Dict[str, Any]) -> float:
        """Estimate cognitive load from activity data"""
        # Factors: number of active tasks, complexity, interruptions
        active_tasks = activity_data.get("active_tasks", 1)
        complexity = activity_data.get("task_complexity", 0.5)
        interruptions = activity_data.get("interruptions", 0)

        load = min(1.0, (active_tasks * 0.2 + complexity * 0.5 + interruptions * 0.1))
        return load

    def _estimate_attention(self, activity_data: Dict[str, Any]) -> float:
        """Estimate attention level"""
        focus_duration = activity_data.get("focus_duration", 0)
        context_switches = activity_data.get("context_switches", 0)

        attention = max(0.0, 1.0 - (context_switches * 0.1))
        if focus_duration > 25:  # Sustained focus
            attention = min(1.0, attention + 0.2)

        return attention

    def _detect_emotional_state(self, activity_data: Dict[str, Any]) -> str:
        """Detect emotional state from activity data"""
        errors = activity_data.get("errors", 0)
        productivity = activity_data.get("productivity_score", 0.5)

        if errors > 5:
            return "frustrated"
        elif productivity > 0.8:
            return "focused"
        elif productivity < 0.3:
            return "distracted"
        else:
            return "neutral"

    def _estimate_fatigue(self, activity_data: Dict[str, Any]) -> float:
        """Estimate fatigue level"""
        session_duration = activity_data.get("session_duration", 0)
        time_since_break = activity_data.get("time_since_break", 0)

        fatigue = min(1.0, (session_duration / 180 + time_since_break / 60) / 2)
        return fatigue

    def _update_profile_from_state(self, user_id: str, state: CognitiveState):
        """Update profile based on state history"""
        profile = self.profiles[user_id]

        # Update attention span if consistently different
        recent_states = [s for s in self.states if s.user_id == user_id][-20:]
        if len(recent_states) > 10:
            avg_attention_duration = sum(
                s.attention_level * 25 for s in recent_states
            ) / len(recent_states)
            profile.attention_span = avg_attention_duration

        profile.last_updated = datetime.now()

    def _extract_preferences(self, activity_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract preferences from activities"""
        preferences = {}

        # Common preference patterns
        if activity_list:
            preferences["preferred_time"] = self._find_peak_time(activity_list)
            preferences["preferred_duration"] = sum(
                a.get("duration", 0) for a in activity_list
            ) / len(activity_list)

        return preferences

    def _find_peak_time(self, activity_list: List[Dict[str, Any]]) -> str:
        """Find peak activity time"""
        from collections import Counter

        times = [a.get("time_of_day", "unknown") for a in activity_list]
        if not times:
            return "unknown"

        counter = Counter(times)
        return counter.most_common(1)[0][0]

    def get_profile(self, user_id: str) -> Optional[CognitiveProfile]:
        """Get user cognitive profile"""
        return self.profiles.get(user_id)

    def _save_state(self):
        """Save state to disk"""
        try:
            data = {
                "profiles_count": len(self.profiles),
                "states_count": len(self.states),
                "patterns_count": len(self.patterns)
            }
            with open(self.data_dir / "cognitive_state.json", "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cognitive state: {e}")

    def _load_state(self):
        """Load state from disk"""
        try:
            state_file = self.data_dir / "cognitive_state.json"
            if state_file.exists():
                with open(state_file, "r") as f:
                    data = json.load(f)
                logger.info(f"Loaded {data.get('profiles_count', 0)} cognitive profiles")
        except Exception as e:
            logger.error(f"Failed to load cognitive state: {e}")


# Global instance
_cognitive_builder: Optional[CognitiveModelBuilder] = None


def get_cognitive_builder() -> Optional[CognitiveModelBuilder]:
    """Get global cognitive builder instance"""
    return _cognitive_builder


def initialize_cognitive_builder(data_dir: Path) -> CognitiveModelBuilder:
    """Initialize cognitive builder"""
    global _cognitive_builder
    _cognitive_builder = CognitiveModelBuilder(data_dir)
    return _cognitive_builder
