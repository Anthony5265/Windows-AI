"""
Proactive Task Prediction Engine
Predicts user tasks and offers proactive assistance based on patterns
"""
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
import json
from collections import defaultdict, deque
import threading
import time

logger = logging.getLogger(__name__)


@dataclass
class TaskPrediction:
    """Predicted task for the user"""
    task_id: str
    task_name: str
    task_type: str  # 'workflow', 'command', 'automation', 'reminder'
    confidence: float  # 0-1
    predicted_time: str
    reasoning: str
    suggested_action: str
    workflow_id: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    priority: int = 5  # 1-10


@dataclass
class UserPattern:
    """Detected user behavior pattern"""
    pattern_id: str
    pattern_type: str  # 'time_based', 'sequence_based', 'context_based'
    description: str
    frequency: int  # times observed
    last_observed: str
    conditions: Dict[str, Any]
    action: str
    confidence: float


class ProactiveAssistant:
    """
    Proactive Task Prediction Engine

    Features:
    - Time-based task prediction (e.g., daily standup at 9am)
    - Context-based suggestions (e.g., open IDE -> suggest running tests)
    - Sequence prediction (e.g., git add -> suggest git commit)
    - Habit learning and reinforcement
    - Proactive workflow initiation
    - Smart reminders based on context
    """

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.patterns_file = data_dir / "user_patterns.json"
        self.predictions_file = data_dir / "predictions_history.json"

        # Learned patterns
        self.patterns: List[UserPattern] = []

        # Prediction history
        self.predictions: deque = deque(maxlen=1000)

        # Active predictions
        self.active_predictions: List[TaskPrediction] = []

        # Pattern detection
        self.action_history: deque = deque(maxlen=500)
        self.time_patterns: Dict[str, List] = defaultdict(list)
        self.sequence_patterns: Dict[str, int] = defaultdict(int)

        # Feedback tracking
        self.prediction_feedback: Dict[str, bool] = {}

        # Monitoring
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None

        # Load data
        self._load_patterns()

    def start_monitoring(self, interval: int = 60):
        """Start proactive monitoring and prediction"""
        if self._monitoring:
            return

        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self._monitor_thread.start()
        logger.info(f"Started proactive assistant (interval: {interval}s)")

    def stop_monitoring(self):
        """Stop proactive monitoring"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2)
        logger.info("Stopped proactive assistant")

    def _monitor_loop(self, interval: int):
        """Background monitoring loop"""
        while self._monitoring:
            try:
                # Generate predictions
                self.generate_predictions()

                # Learn from patterns
                self._learn_patterns()

                time.sleep(interval)
            except Exception as e:
                logger.error(f"Error in proactive monitoring: {e}")
                time.sleep(interval)

    def record_action(self, action_type: str, action_data: Dict[str, Any], context: Dict[str, Any] = None):
        """
        Record user action for pattern learning

        Args:
            action_type: Type of action (e.g., 'file_open', 'command_run')
            action_data: Details of the action
            context: Current context (time, app, etc.)
        """
        action_record = {
            'timestamp': datetime.now().isoformat(),
            'action_type': action_type,
            'action_data': action_data,
            'context': context or {},
            'day_of_week': datetime.now().strftime('%A'),
            'hour': datetime.now().hour,
            'minute': datetime.now().minute
        }

        self.action_history.append(action_record)

        # Update time patterns
        time_key = f"{action_record['day_of_week']}_{action_record['hour']}"
        self.time_patterns[time_key].append(action_record)

        # Detect sequences
        if len(self.action_history) >= 2:
            prev_action = self.action_history[-2]
            sequence_key = f"{prev_action['action_type']}->{action_type}"
            self.sequence_patterns[sequence_key] += 1

        logger.debug(f"Recorded action: {action_type}")

    def generate_predictions(self) -> List[TaskPrediction]:
        """
        Generate proactive task predictions based on learned patterns

        Returns:
            List of predicted tasks
        """
        predictions = []
        now = datetime.now()

        # Time-based predictions
        time_predictions = self._predict_time_based(now)
        predictions.extend(time_predictions)

        # Context-based predictions
        context_predictions = self._predict_context_based()
        predictions.extend(context_predictions)

        # Sequence-based predictions
        sequence_predictions = self._predict_sequence_based()
        predictions.extend(sequence_predictions)

        # Filter by confidence threshold
        predictions = [p for p in predictions if p.confidence >= 0.3]

        # Sort by priority and confidence
        predictions.sort(key=lambda x: (x.priority, x.confidence), reverse=True)

        # Update active predictions
        self.active_predictions = predictions[:10]  # Top 10

        # Save to history
        for pred in self.active_predictions:
            self.predictions.append(asdict(pred))

        return self.active_predictions

    def _predict_time_based(self, now: datetime) -> List[TaskPrediction]:
        """Predict tasks based on time patterns"""
        predictions = []

        day_of_week = now.strftime('%A')
        current_hour = now.hour
        time_key = f"{day_of_week}_{current_hour}"

        # Check if there are patterns for this time
        if time_key in self.time_patterns:
            actions = self.time_patterns[time_key]

            if len(actions) >= 3:  # Need at least 3 observations
                # Most common action at this time
                action_counts = defaultdict(int)
                for action in actions:
                    action_type = action['action_type']
                    action_counts[action_type] += 1

                if action_counts:
                    most_common = max(action_counts, key=action_counts.get)
                    frequency = action_counts[most_common]
                    confidence = min(frequency / len(actions), 0.95)

                    if confidence >= 0.3:
                        import uuid
                        pred = TaskPrediction(
                            task_id=str(uuid.uuid4()),
                            task_name=f"Typical {most_common} task",
                            task_type='time_based',
                            confidence=confidence,
                            predicted_time=now.isoformat(),
                            reasoning=f"You typically perform '{most_common}' on {day_of_week} at {current_hour}:00 ({frequency}/{len(actions)} times)",
                            suggested_action=f"Would you like to {most_common}?",
                            priority=7
                        )
                        predictions.append(pred)

        return predictions

    def _predict_context_based(self) -> List[TaskPrediction]:
        """Predict tasks based on current context"""
        predictions = []

        # Would integrate with context_manager here
        # For now, check recent actions

        if len(self.action_history) >= 1:
            recent_action = self.action_history[-1]
            action_type = recent_action['action_type']

            # Context-based rules
            if action_type == 'file_edit' and 'test' not in recent_action.get('action_data', {}).get('path', ''):
                import uuid
                pred = TaskPrediction(
                    task_id=str(uuid.uuid4()),
                    task_name="Run tests",
                    task_type='context_based',
                    confidence=0.7,
                    predicted_time=datetime.now().isoformat(),
                    reasoning="You just edited code. Consider running tests.",
                    suggested_action="Run test suite",
                    priority=8
                )
                predictions.append(pred)

            elif action_type == 'git_add':
                import uuid
                pred = TaskPrediction(
                    task_id=str(uuid.uuid4()),
                    task_name="Git commit",
                    task_type='context_based',
                    confidence=0.9,
                    predicted_time=datetime.now().isoformat(),
                    reasoning="You staged files. Next step is usually commit.",
                    suggested_action="Create git commit",
                    priority=9
                )
                predictions.append(pred)

        return predictions

    def _predict_sequence_based(self) -> List[TaskPrediction]:
        """Predict next action based on action sequences"""
        predictions = []

        if len(self.action_history) >= 1:
            last_action = self.action_history[-1]['action_type']

            # Find common next actions
            matching_sequences = {
                seq: count for seq, count in self.sequence_patterns.items()
                if seq.startswith(last_action + '->')
            }

            if matching_sequences:
                # Get most common next action
                most_common_seq = max(matching_sequences, key=matching_sequences.get)
                next_action = most_common_seq.split('->')[1]
                frequency = matching_sequences[most_common_seq]

                # Calculate confidence based on frequency
                total_sequences = sum(matching_sequences.values())
                confidence = min(frequency / total_sequences, 0.95)

                if confidence >= 0.4:
                    import uuid
                    pred = TaskPrediction(
                        task_id=str(uuid.uuid4()),
                        task_name=f"Next: {next_action}",
                        task_type='sequence_based',
                        confidence=confidence,
                        predicted_time=datetime.now().isoformat(),
                        reasoning=f"After '{last_action}', you usually do '{next_action}' ({frequency}/{total_sequences} times)",
                        suggested_action=f"Proceed with {next_action}",
                        priority=6
                    )
                    predictions.append(pred)

        return predictions

    def _learn_patterns(self):
        """Learn patterns from action history"""
        # Time-based pattern learning
        for time_key, actions in self.time_patterns.items():
            if len(actions) >= 5:  # Minimum observations
                # Check if this is a strong pattern
                action_types = [a['action_type'] for a in actions]
                from collections import Counter
                most_common = Counter(action_types).most_common(1)[0]

                if most_common[1] / len(actions) >= 0.6:  # 60% consistency
                    # This is a pattern
                    pattern_id = f"time_{time_key}_{most_common[0]}"

                    # Check if already exists
                    existing = next((p for p in self.patterns if p.pattern_id == pattern_id), None)

                    if existing:
                        existing.frequency = most_common[1]
                        existing.last_observed = datetime.now().isoformat()
                        existing.confidence = most_common[1] / len(actions)
                    else:
                        pattern = UserPattern(
                            pattern_id=pattern_id,
                            pattern_type='time_based',
                            description=f"User typically performs {most_common[0]} at {time_key}",
                            frequency=most_common[1],
                            last_observed=datetime.now().isoformat(),
                            conditions={'time_key': time_key},
                            action=most_common[0],
                            confidence=most_common[1] / len(actions)
                        )
                        self.patterns.append(pattern)

        # Save patterns periodically
        if len(self.patterns) > 0:
            self._save_patterns()

    def provide_feedback(self, prediction_id: str, accepted: bool, executed: bool = False):
        """
        Provide feedback on a prediction

        Args:
            prediction_id: ID of the prediction
            accepted: Whether user accepted the suggestion
            executed: Whether the action was executed
        """
        self.prediction_feedback[prediction_id] = accepted

        # Adjust pattern confidence based on feedback
        # Find the prediction
        pred_dict = next((p for p in self.predictions if p['task_id'] == prediction_id), None)

        if pred_dict:
            # Update pattern confidence
            if accepted:
                logger.info(f"Positive feedback for prediction: {pred_dict['task_name']}")
                # Increase confidence for this pattern
            else:
                logger.info(f"Negative feedback for prediction: {pred_dict['task_name']}")
                # Decrease confidence for this pattern

    def get_active_predictions(self) -> List[Dict]:
        """Get current active predictions"""
        return [asdict(p) for p in self.active_predictions]

    def get_patterns(self) -> List[Dict]:
        """Get learned patterns"""
        return [asdict(p) for p in self.patterns]

    def _save_patterns(self):
        """Save learned patterns"""
        try:
            patterns_data = [asdict(p) for p in self.patterns]
            with open(self.patterns_file, 'w') as f:
                json.dump(patterns_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving patterns: {e}")

    def _load_patterns(self):
        """Load learned patterns"""
        try:
            if self.patterns_file.exists():
                with open(self.patterns_file, 'r') as f:
                    patterns_data = json.load(f)
                    self.patterns = [UserPattern(**p) for p in patterns_data]
                logger.info(f"Loaded {len(self.patterns)} patterns")
        except Exception as e:
            logger.error(f"Error loading patterns: {e}")


# Global instance
_proactive_assistant: Optional[ProactiveAssistant] = None


def get_proactive_assistant(data_dir: Path = None) -> ProactiveAssistant:
    """Get or create global proactive assistant"""
    global _proactive_assistant

    if _proactive_assistant is None:
        if data_dir is None:
            data_dir = Path.home() / ".windows-ai" / "proactive"
        _proactive_assistant = ProactiveAssistant(data_dir)

    return _proactive_assistant


def initialize_proactive_assistant(data_dir: Path = None, start_monitoring: bool = True):
    """Initialize the proactive assistant"""
    assistant = get_proactive_assistant(data_dir)

    if start_monitoring:
        assistant.start_monitoring(interval=60)

    logger.info("Proactive assistant initialized")
    return assistant
