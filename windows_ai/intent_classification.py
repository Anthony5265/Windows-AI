"""
Intent Classification module for Windows AI.

Implements intent classification via keyword extraction, TF-IDF weighting,
and cosine similarity against intent templates. Ships with built-in intent
categories (greeting, farewell, help, search, create, delete, update,
navigate, confirm, cancel, info) and supports custom intents.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Set
import logging
import math
import re
import uuid
import collections
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Built-in intent templates
# ---------------------------------------------------------------------------
_BUILTIN_INTENTS: Dict[str, List[str]] = {
    "greeting": [
        "hello", "hi", "hey", "good morning", "good afternoon",
        "good evening", "howdy", "greetings", "hi there", "what's up",
    ],
    "farewell": [
        "goodbye", "bye", "see you later", "take care", "good night",
        "farewell", "catch you later", "see you", "bye bye", "so long",
    ],
    "help": [
        "help", "help me", "i need help", "can you help", "assist me",
        "support", "how do i", "what should i do", "instructions",
        "guide me", "show me how", "i'm stuck",
    ],
    "search": [
        "search", "find", "look up", "look for", "search for",
        "where is", "locate", "google", "query", "show me",
        "can you find", "i'm looking for",
    ],
    "create": [
        "create", "make", "build", "generate", "new", "add",
        "start a new", "compose", "set up", "initialize",
        "create a new", "make a",
    ],
    "delete": [
        "delete", "remove", "erase", "destroy", "discard",
        "get rid of", "clear", "trash", "drop", "eliminate",
    ],
    "update": [
        "update", "edit", "modify", "change", "revise",
        "alter", "adjust", "fix", "correct", "amend",
        "rename", "replace",
    ],
    "navigate": [
        "go to", "open", "navigate", "show", "take me to",
        "switch to", "go back", "forward", "return to",
        "visit", "launch", "load", "display",
    ],
    "confirm": [
        "yes", "confirm", "approve", "accept", "agree",
        "sure", "okay", "ok", "right", "correct", "absolutely",
        "affirmative", "definitely", "of course",
    ],
    "cancel": [
        "no", "cancel", "stop", "abort", "nevermind",
        "never mind", "don't", "do not", "reject", "decline",
        "dismiss", "forget it", "nope",
    ],
    "info": [
        "what is", "tell me about", "explain", "describe",
        "information", "details", "who is", "define",
        "what are", "how does", "why is",
    ],
}

_STOP_WORDS: Set[str] = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been",
    "have", "has", "had", "do", "does", "did", "will", "would",
    "shall", "should", "may", "might", "must", "can", "could",
    "to", "of", "in", "for", "on", "with", "at", "by", "from",
    "as", "into", "through", "during", "before", "after",
    "and", "but", "or", "not", "so", "yet", "it", "its",
    "this", "that", "these", "those", "i", "me", "my",
    "we", "our", "you", "your", "he", "him", "she", "her",
    "they", "them", "their",
}


def _tokenize(text: str) -> List[str]:
    tokens = re.findall(r"[a-z']+", text.lower())
    return [t for t in tokens if len(t) > 1]


def _tokenize_no_stop(text: str) -> List[str]:
    return [t for t in _tokenize(text) if t not in _STOP_WORDS]


# ---------------------------------------------------------------------------
# TF-IDF + cosine (lightweight)
# ---------------------------------------------------------------------------
class _TfIdf:
    def __init__(self) -> None:
        self.idf: Dict[str, float] = {}

    def fit(self, docs: List[List[str]]) -> None:
        n = len(docs)
        df: Dict[str, int] = collections.defaultdict(int)
        for d in docs:
            for t in set(d):
                df[t] += 1
        for t, c in df.items():
            self.idf[t] = math.log((n + 1) / (c + 1)) + 1.0

    def transform(self, tokens: List[str]) -> Dict[str, float]:
        tf = collections.Counter(tokens)
        total = max(len(tokens), 1)
        return {t: (c / total) * self.idf.get(t, 1.0) for t, c in tf.items()}


def _cosine(v1: Dict[str, float], v2: Dict[str, float]) -> float:
    common = set(v1) & set(v2)
    if not common:
        return 0.0
    dot = sum(v1[k] * v2[k] for k in common)
    m1 = math.sqrt(sum(x * x for x in v1.values()))
    m2 = math.sqrt(sum(x * x for x in v2.values()))
    return dot / (m1 * m2) if m1 and m2 else 0.0


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------
@dataclass
class IntentClassificationResult:
    result_id: str
    input_text: str
    output_text: str
    confidence: float


# ---------------------------------------------------------------------------
# Main system
# ---------------------------------------------------------------------------
class IntentClassificationSystem:
    """Intent classifier using keyword + TF-IDF + cosine similarity.

    Ships with built-in intents and supports custom intent registration.
    """

    def __init__(self, data_dir) -> None:
        self.data_dir = Path(data_dir) if not isinstance(data_dir, Path) else data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[IntentClassificationResult] = []
        self._intents: Dict[str, List[str]] = dict(_BUILTIN_INTENTS)
        self._tfidf = _TfIdf()
        self._intent_vectors: Dict[str, Dict[str, float]] = {}
        self._build_model()
        logger.info("IntentClassification initialized")

    def add_intent(self, label: str, examples: List[str]) -> None:
        """Register (or extend) a custom intent."""
        if label in self._intents:
            self._intents[label].extend(examples)
        else:
            self._intents[label] = list(examples)
        self._build_model()

    def remove_intent(self, label: str) -> bool:
        """Remove an intent category."""
        if label in self._intents:
            del self._intents[label]
            self._build_model()
            return True
        return False

    def get_intents(self) -> List[str]:
        """Return list of registered intent labels."""
        return sorted(self._intents.keys())

    def process(self, text: str) -> IntentClassificationResult:
        """Classify the intent of *text*."""
        tokens = _tokenize(text)
        if not tokens:
            return self._make_result(text, "unknown", 0.0)

        input_vec = self._tfidf.transform(tokens)
        input_set = set(_tokenize_no_stop(text))

        best_label = "unknown"
        best_score = 0.0

        for label, intent_vec in self._intent_vectors.items():
            cos_sim = _cosine(input_vec, intent_vec)

            intent_keywords: Set[str] = set()
            for ex in self._intents[label]:
                intent_keywords.update(_tokenize_no_stop(ex))
            overlap = (
                len(input_set & intent_keywords) / max(len(input_set), 1)
                if intent_keywords else 0.0
            )

            score = cos_sim * 0.65 + overlap * 0.35
            if score > best_score:
                best_score = score
                best_label = label

        confidence = round(min(best_score, 1.0), 4)
        if confidence < 0.1:
            best_label = "unknown"
            confidence = round(1.0 - confidence, 4)

        return self._make_result(text, best_label, confidence)

    def _build_model(self) -> None:
        """Build TF-IDF model and intent centroid vectors."""
        all_docs: List[List[str]] = []
        for examples in self._intents.values():
            for ex in examples:
                all_docs.append(_tokenize(ex))

        self._tfidf = _TfIdf()
        self._tfidf.fit(all_docs)

        self._intent_vectors = {}
        for label, examples in self._intents.items():
            centroid: Dict[str, float] = collections.defaultdict(float)
            for ex in examples:
                vec = self._tfidf.transform(_tokenize(ex))
                for t, v in vec.items():
                    centroid[t] += v
            n = max(len(examples), 1)
            self._intent_vectors[label] = {t: v / n for t, v in centroid.items()}

    def _make_result(
        self, text: str, label: str, confidence: float
    ) -> IntentClassificationResult:
        result = IntentClassificationResult(
            result_id=str(uuid.uuid4()),
            input_text=text,
            output_text=label,
            confidence=confidence,
        )
        self.results.append(result)
        logger.info("Intent '%s' (conf=%.4f)", label, confidence)
        return result


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_intent_classification: Optional[IntentClassificationSystem] = None

def get_intent_classification() -> Optional[IntentClassificationSystem]:
    return _intent_classification

def initialize_intent_classification(data_dir) -> IntentClassificationSystem:
    global _intent_classification
    _intent_classification = IntentClassificationSystem(data_dir)
    return _intent_classification
