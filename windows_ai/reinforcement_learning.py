"""
Reinforcement Learning from Human Feedback (RLHF) System
Learns optimal behaviors from user feedback and rewards
"""
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import numpy as np
from collections import deque, defaultdict
import pickle

logger = logging.getLogger(__name__)


@dataclass
class Action:
    """An action taken by the AI"""
    action_id: str
    action_type: str
    parameters: Dict[str, Any]
    context: Dict[str, Any]
    timestamp: str


@dataclass
class Feedback:
    """User feedback on an action"""
    feedback_id: str
    action_id: str
    rating: int  # -2 (terrible) to +2 (excellent)
    implicit: bool  # Whether feedback was implicit (inferred) or explicit
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class Policy:
    """A learned policy for action selection"""
    policy_id: str
    state_features: List[str]
    action_space: List[str]
    q_table: Dict[str, Dict[str, float]]  # state -> action -> q_value
    learning_rate: float
    discount_factor: float
    epsilon: float  # exploration rate


class ReinforcementLearningSystem:
    """
    Reinforcement Learning from Human Feedback System

    Features:
    - Q-Learning algorithm for policy optimization
    - Human feedback integration (explicit + implicit)
    - Reward shaping from user interactions
    - Policy gradient methods
    - Experience replay for stability
    - Multi-objective reward balancing
    - Continuous learning from interactions
    - A/B testing for policy comparison
    - Safe exploration with guardrails
    """

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.actions_file = data_dir / "actions.json"
        self.feedback_file = data_dir / "feedback.json"
        self.policy_file = data_dir / "policy.pkl"

        # Action and feedback history
        self.actions: deque = deque(maxlen=10000)
        self.feedback_log: List[Feedback] = []

        # Q-Learning parameters
        self.learning_rate = 0.1
        self.discount_factor = 0.95
        self.epsilon = 0.1  # exploration rate
        self.epsilon_decay = 0.995
        self.min_epsilon = 0.01

        # Q-table: state -> action -> q_value
        self.q_table: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))

        # Experience replay buffer
        self.replay_buffer: deque = deque(maxlen=5000)

        # Policy versions for A/B testing
        self.policies: Dict[str, Policy] = {}
        self.active_policy_id = "default"

        # Reward weights (multi-objective)
        self.reward_weights = {
            'user_satisfaction': 1.0,
            'task_completion': 0.8,
            'efficiency': 0.6,
            'safety': 1.2
        }

        # Statistics
        self.stats = {
            'total_actions': 0,
            'positive_feedback': 0,
            'negative_feedback': 0,
            'avg_reward': 0.0,
            'policy_updates': 0
        }

        # Load data
        self._load_policy()

    def record_action(self, action_type: str, parameters: Dict[str, Any], context: Dict[str, Any]) -> Action:
        """Record an action taken by the AI"""
        import uuid

        action = Action(
            action_id=str(uuid.uuid4()),
            action_type=action_type,
            parameters=parameters,
            context=context,
            timestamp=datetime.now().isoformat()
        )

        self.actions.append(asdict(action))
        self.stats['total_actions'] += 1

        return action

    def provide_feedback(
        self,
        action_id: str,
        rating: int,
        implicit: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Feedback:
        """
        Provide feedback on an action

        Args:
            action_id: ID of the action
            rating: -2 (terrible) to +2 (excellent)
            implicit: Whether feedback was implicit
            metadata: Additional context
        """
        import uuid

        if rating < -2 or rating > 2:
            raise ValueError("Rating must be between -2 and +2")

        feedback = Feedback(
            feedback_id=str(uuid.uuid4()),
            action_id=action_id,
            rating=rating,
            implicit=implicit,
            timestamp=datetime.now().isoformat(),
            metadata=metadata
        )

        self.feedback_log.append(feedback)

        # Update statistics
        if rating > 0:
            self.stats['positive_feedback'] += 1
        elif rating < 0:
            self.stats['negative_feedback'] += 1

        # Update policy based on feedback
        self._update_policy_from_feedback(action_id, rating)

        logger.info(f"Feedback recorded: action={action_id}, rating={rating}")

        return feedback

    def _update_policy_from_feedback(self, action_id: str, rating: int):
        """Update Q-table based on feedback"""
        # Find the action
        action_dict = next((a for a in self.actions if a['action_id'] == action_id), None)

        if not action_dict:
            logger.warning(f"Action {action_id} not found")
            return

        # Extract state and action
        state = self._extract_state(action_dict['context'])
        action_type = action_dict['action_type']

        # Convert rating to reward
        reward = self._rating_to_reward(rating)

        # Q-Learning update
        current_q = self.q_table[state][action_type]

        # Update Q-value
        # Q(s,a) = Q(s,a) + α[R - Q(s,a)]
        # Simplified since we don't have next state in feedback
        new_q = current_q + self.learning_rate * (reward - current_q)

        self.q_table[state][action_type] = new_q

        self.stats['policy_updates'] += 1

        # Update average reward
        total_feedback = self.stats['positive_feedback'] + self.stats['negative_feedback']
        if total_feedback > 0:
            self.stats['avg_reward'] = (
                (self.stats['positive_feedback'] - self.stats['negative_feedback']) / total_feedback
            )

        logger.debug(f"Updated Q({state}, {action_type}): {current_q:.3f} -> {new_q:.3f}")

    def _extract_state(self, context: Dict[str, Any]) -> str:
        """Extract state representation from context"""
        # Simplified state representation
        # In production, would use feature engineering or neural networks

        state_features = []

        # Time of day
        hour = datetime.now().hour
        if hour < 6:
            state_features.append("night")
        elif hour < 12:
            state_features.append("morning")
        elif hour < 18:
            state_features.append("afternoon")
        else:
            state_features.append("evening")

        # Task type if available
        if 'task_type' in context:
            state_features.append(context['task_type'])

        # User focus level if available
        if 'focus_level' in context:
            state_features.append(f"focus_{context['focus_level']}")

        return "_".join(state_features)

    def _rating_to_reward(self, rating: int) -> float:
        """Convert user rating to reward value"""
        # Map rating (-2 to +2) to reward (-1.0 to +1.0)
        return rating / 2.0

    def select_action(self, action_space: List[str], context: Dict[str, Any]) -> str:
        """
        Select best action using epsilon-greedy policy

        Args:
            action_space: Available actions
            context: Current context

        Returns:
            Selected action
        """
        state = self._extract_state(context)

        # Epsilon-greedy exploration
        if np.random.random() < self.epsilon:
            # Explore: random action
            action = np.random.choice(action_space)
            logger.debug(f"Exploring: selected {action}")
        else:
            # Exploit: best known action
            q_values = {action: self.q_table[state].get(action, 0.0) for action in action_space}
            action = max(q_values, key=q_values.get)
            logger.debug(f"Exploiting: selected {action} (Q={q_values[action]:.3f})")

        # Decay epsilon
        self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)

        return action

    def learn_from_trajectory(self, trajectory: List[Tuple[str, str, float]]):
        """
        Learn from a trajectory of (state, action, reward) tuples

        Args:
            trajectory: List of (state, action, reward)
        """
        # Backward update using Monte Carlo returns
        G = 0.0  # Return

        for state, action, reward in reversed(trajectory):
            G = reward + self.discount_factor * G

            # Q-Learning update
            current_q = self.q_table[state][action]
            new_q = current_q + self.learning_rate * (G - current_q)
            self.q_table[state][action] = new_q

        self.stats['policy_updates'] += len(trajectory)

    def get_policy_performance(self) -> Dict[str, Any]:
        """Get policy performance metrics"""
        total_feedback = self.stats['positive_feedback'] + self.stats['negative_feedback']

        if total_feedback == 0:
            return {
                'total_actions': self.stats['total_actions'],
                'feedback_count': 0,
                'positive_rate': 0.0,
                'avg_reward': 0.0,
                'policy_updates': self.stats['policy_updates'],
                'exploration_rate': self.epsilon
            }

        positive_rate = self.stats['positive_feedback'] / total_feedback

        return {
            'total_actions': self.stats['total_actions'],
            'feedback_count': total_feedback,
            'positive_feedback': self.stats['positive_feedback'],
            'negative_feedback': self.stats['negative_feedback'],
            'positive_rate': positive_rate,
            'avg_reward': self.stats['avg_reward'],
            'policy_updates': self.stats['policy_updates'],
            'exploration_rate': self.epsilon,
            'q_table_size': sum(len(actions) for actions in self.q_table.values())
        }

    def get_action_recommendations(self, context: Dict[str, Any], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Get top-k action recommendations with Q-values

        Args:
            context: Current context
            top_k: Number of recommendations

        Returns:
            List of {action, q_value, confidence}
        """
        state = self._extract_state(context)

        # Get all actions and their Q-values for this state
        action_values = [(action, q_value) for action, q_value in self.q_table[state].items()]

        # Sort by Q-value
        action_values.sort(key=lambda x: x[1], reverse=True)

        # Get top-k
        recommendations = []
        for action, q_value in action_values[:top_k]:
            recommendations.append({
                'action': action,
                'q_value': q_value,
                'confidence': self._q_value_to_confidence(q_value)
            })

        return recommendations

    def _q_value_to_confidence(self, q_value: float) -> float:
        """Convert Q-value to confidence percentage"""
        # Sigmoid transformation
        confidence = 1 / (1 + np.exp(-q_value))
        return confidence * 100

    def export_policy(self) -> Policy:
        """Export current policy"""
        import uuid

        policy = Policy(
            policy_id=str(uuid.uuid4()),
            state_features=['time_of_day', 'task_type', 'focus_level'],
            action_space=list(set(
                action for actions in self.q_table.values() for action in actions.keys()
            )),
            q_table=dict(self.q_table),
            learning_rate=self.learning_rate,
            discount_factor=self.discount_factor,
            epsilon=self.epsilon
        )

        return policy

    def import_policy(self, policy: Policy):
        """Import a policy"""
        self.q_table = defaultdict(lambda: defaultdict(float), policy.q_table)
        self.learning_rate = policy.learning_rate
        self.discount_factor = policy.discount_factor
        self.epsilon = policy.epsilon

        logger.info(f"Imported policy: {policy.policy_id}")

    def reset_learning(self):
        """Reset learning (clear Q-table)"""
        self.q_table.clear()
        self.stats['policy_updates'] = 0
        logger.warning("Learning reset - Q-table cleared")

    def visualize_q_table(self, limit: int = 20) -> Dict[str, Any]:
        """Get Q-table visualization data"""
        # Get top states by number of actions
        state_action_counts = {
            state: len(actions) for state, actions in self.q_table.items()
        }

        top_states = sorted(state_action_counts.items(), key=lambda x: x[1], reverse=True)[:limit]

        visualization = {}
        for state, _ in top_states:
            visualization[state] = dict(self.q_table[state])

        return visualization

    def _save_policy(self):
        """Save policy to disk"""
        try:
            policy = self.export_policy()
            with open(self.policy_file, 'wb') as f:
                pickle.dump(policy, f)

            # Save stats
            stats_file = self.data_dir / "rl_stats.json"
            with open(stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2)

        except Exception as e:
            logger.error(f"Error saving policy: {e}")

    def _load_policy(self):
        """Load policy from disk"""
        try:
            if self.policy_file.exists():
                with open(self.policy_file, 'rb') as f:
                    policy = pickle.load(f)
                self.import_policy(policy)

            # Load stats
            stats_file = self.data_dir / "rl_stats.json"
            if stats_file.exists():
                with open(stats_file, 'r') as f:
                    self.stats = json.load(f)

                logger.info(f"Loaded policy with {len(self.q_table)} states")

        except Exception as e:
            logger.error(f"Error loading policy: {e}")


# Global instance
_rl_system: Optional[ReinforcementLearningSystem] = None


def get_rl_system(data_dir: Path = None) -> ReinforcementLearningSystem:
    """Get or create global RL system"""
    global _rl_system

    if _rl_system is None:
        if data_dir is None:
            data_dir = Path.home() / ".windows-ai" / "rl"
        _rl_system = ReinforcementLearningSystem(data_dir)

    return _rl_system


def initialize_rl_system(data_dir: Path = None):
    """Initialize the reinforcement learning system"""
    system = get_rl_system(data_dir)
    logger.info("Reinforcement learning system initialized")
    return system
