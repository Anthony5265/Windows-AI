"""
Text Classification module for Windows AI.

Implements TF-IDF feature extraction with Naive Bayes classification.
Supports training on labeled data, multi-class prediction with confidence
scores, and ships with built-in category sets (spam, sentiment, topic).
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import logging
import math
import re
import uuid
import collections
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Stop-words (compact set – no external deps)
# ---------------------------------------------------------------------------
_STOP_WORDS: set = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "shall",
    "should", "may", "might", "must", "can", "could", "to", "of", "in",
    "for", "on", "with", "at", "by", "from", "as", "into", "through",
    "during", "before", "after", "and", "but", "or", "nor", "not", "so",
    "yet", "both", "either", "neither", "each", "every", "all", "any",
    "few", "more", "most", "other", "some", "such", "no", "only", "own",
    "same", "than", "too", "very", "just", "because", "about", "between",
    "it", "its", "this", "that", "these", "those", "i", "me", "my",
    "myself", "we", "our", "ours", "you", "your", "he", "him", "his",
    "she", "her", "they", "them", "their", "what", "which", "who",
    "whom", "when", "where", "why", "how", "if", "then", "there", "here",
    "up", "out", "off", "over", "under", "again", "further", "once",
}

# ---------------------------------------------------------------------------
# Built-in training data for pre-loaded categories
# ---------------------------------------------------------------------------
_BUILTIN_SPAM: List[Tuple[str, str]] = [
    ("win free money now click here", "spam"),
    ("congratulations you have won a prize", "spam"),
    ("buy cheap pills online discount", "spam"),
    ("free gift card claim now limited offer", "spam"),
    ("earn money fast work from home", "spam"),
    ("click here for exclusive deal today only", "spam"),
    ("urgent action required verify your account", "spam"),
    ("meeting scheduled for tomorrow at 10am", "ham"),
    ("please review the attached document", "ham"),
    ("can we discuss the project timeline", "ham"),
    ("the quarterly report is ready for review", "ham"),
    ("looking forward to our lunch on friday", "ham"),
    ("thank you for your prompt response", "ham"),
    ("please find the updated spreadsheet attached", "ham"),
]

_BUILTIN_SENTIMENT: List[Tuple[str, str]] = [
    ("i love this product it is amazing", "positive"),
    ("great experience would recommend to everyone", "positive"),
    ("excellent quality and fast delivery", "positive"),
    ("wonderful service very happy customer", "positive"),
    ("best purchase i have ever made fantastic", "positive"),
    ("terrible experience never buying again", "negative"),
    ("worst product broken on arrival", "negative"),
    ("awful customer service very disappointed", "negative"),
    ("waste of money poor quality horrible", "negative"),
    ("hate this product completely useless junk", "negative"),
    ("the product arrived on time it works", "neutral"),
    ("it is okay nothing special average", "neutral"),
    ("standard quality meets basic expectations", "neutral"),
]

_BUILTIN_TOPIC: List[Tuple[str, str]] = [
    ("the stock market rallied today after fed announcement", "finance"),
    ("investors are watching quarterly earnings reports", "finance"),
    ("new study reveals breakthrough in cancer treatment", "health"),
    ("exercise and diet improve heart health significantly", "health"),
    ("the team won the championship game last night", "sports"),
    ("the player scored three goals in the match", "sports"),
    ("new smartphone released with advanced camera features", "technology"),
    ("artificial intelligence is transforming many industries", "technology"),
    ("the senator introduced a new bill in congress", "politics"),
    ("election results showed a clear winner emerging", "politics"),
]


def _tokenize(text: str) -> List[str]:
    """Lowercase, strip punctuation, remove stop-words."""
    tokens = re.findall(r"[a-z]+", text.lower())
    return [t for t in tokens if t not in _STOP_WORDS and len(t) > 1]


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------
@dataclass
class TextClassificationResult:
    result_id: str
    input_text: str
    output_text: str
    confidence: float


# ---------------------------------------------------------------------------
# TF-IDF helpers
# ---------------------------------------------------------------------------
class _TfIdf:
    """Minimal TF-IDF calculator."""

    def __init__(self) -> None:
        self.vocab: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.doc_count: int = 0

    def fit(self, documents: List[List[str]]) -> None:
        df: Dict[str, int] = collections.defaultdict(int)
        self.doc_count = len(documents)
        for doc in documents:
            seen: set = set()
            for token in doc:
                if token not in self.vocab:
                    self.vocab[token] = len(self.vocab)
                if token not in seen:
                    df[token] += 1
                    seen.add(token)
        for term, count in df.items():
            self.idf[term] = math.log((self.doc_count + 1) / (count + 1)) + 1

    def transform(self, tokens: List[str]) -> Dict[str, float]:
        tf: Dict[str, int] = collections.Counter(tokens)
        total = len(tokens) if tokens else 1
        return {t: (c / total) * self.idf.get(t, 1.0) for t, c in tf.items()}


# ---------------------------------------------------------------------------
# Naive Bayes classifier
# ---------------------------------------------------------------------------
class _NaiveBayes:
    """Multinomial Naive Bayes operating on TF-IDF-weighted features."""

    def __init__(self, alpha: float = 1.0) -> None:
        self.alpha = alpha
        self.class_log_prior: Dict[str, float] = {}
        self.feature_log_prob: Dict[str, Dict[str, float]] = {}
        self.classes: List[str] = []
        self.vocab: set = set()

    def fit(self, X: List[Dict[str, float]], y: List[str]) -> None:
        class_counts: Dict[str, int] = collections.Counter(y)
        total = len(y)
        self.classes = sorted(class_counts.keys())
        for cls in self.classes:
            self.class_log_prior[cls] = math.log(class_counts[cls] / total)

        for vec in X:
            self.vocab.update(vec.keys())
        vocab_size = len(self.vocab)

        class_feature_sum: Dict[str, Dict[str, float]] = {
            c: collections.defaultdict(float) for c in self.classes
        }
        class_total: Dict[str, float] = {c: 0.0 for c in self.classes}

        for vec, label in zip(X, y):
            for term, val in vec.items():
                class_feature_sum[label][term] += val
                class_total[label] += val

        self.feature_log_prob = {}
        for cls in self.classes:
            self.feature_log_prob[cls] = {}
            denom = class_total[cls] + self.alpha * vocab_size
            for term in self.vocab:
                num = class_feature_sum[cls].get(term, 0.0) + self.alpha
                self.feature_log_prob[cls][term] = math.log(num / denom)

    def predict(self, vec: Dict[str, float]) -> Tuple[str, float]:
        scores: Dict[str, float] = {}
        for cls in self.classes:
            score = self.class_log_prior[cls]
            for term, val in vec.items():
                if term in self.feature_log_prob[cls]:
                    score += val * self.feature_log_prob[cls][term]
            scores[cls] = score

        # Softmax to get probabilities
        max_score = max(scores.values()) if scores else 0.0
        exp_scores = {c: math.exp(s - max_score) for c, s in scores.items()}
        total_exp = sum(exp_scores.values()) or 1.0
        probs = {c: e / total_exp for c, e in exp_scores.items()}

        best_cls = max(probs, key=probs.get)  # type: ignore[arg-type]
        return best_cls, round(probs[best_cls], 4)


# ---------------------------------------------------------------------------
# Main system
# ---------------------------------------------------------------------------
class TextClassificationSystem:
    """Text classification using TF-IDF + Naive Bayes.

    Ships with built-in category sets (spam, sentiment, topic) and supports
    custom training data.
    """

    BUILTIN_DATASETS: Dict[str, List[Tuple[str, str]]] = {
        "spam": _BUILTIN_SPAM,
        "sentiment": _BUILTIN_SENTIMENT,
        "topic": _BUILTIN_TOPIC,
    }

    def __init__(self, data_dir) -> None:
        self.data_dir = Path(data_dir) if not isinstance(data_dir, Path) else data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[TextClassificationResult] = []
        self._tfidf = _TfIdf()
        self._clf = _NaiveBayes()
        self._trained = False
        self._active_dataset: str = "sentiment"
        self._train_builtin(self._active_dataset)
        logger.info("TextClassification initialized")

    def train(self, data: List[Tuple[str, str]], *, dataset_name: str = "custom") -> None:
        """Train classifier on list of (text, label) pairs."""
        if not data:
            logger.warning("Empty training data provided")
            return
        tokenized = [_tokenize(t) for t, _ in data]
        labels = [lbl for _, lbl in data]
        self._tfidf = _TfIdf()
        self._tfidf.fit(tokenized)
        vectors = [self._tfidf.transform(tok) for tok in tokenized]
        self._clf = _NaiveBayes()
        self._clf.fit(vectors, labels)
        self._trained = True
        self._active_dataset = dataset_name
        logger.info("Trained on %d samples for dataset '%s'", len(data), dataset_name)

    def set_category(self, category: str) -> None:
        """Switch to a built-in category set."""
        if category not in self.BUILTIN_DATASETS:
            raise ValueError(
                f"Unknown category '{category}'. Choose from {list(self.BUILTIN_DATASETS)}"
            )
        self._train_builtin(category)

    def process(self, text: str) -> TextClassificationResult:
        """Classify *text* and return a structured result."""
        if not self._trained:
            self._train_builtin(self._active_dataset)

        tokens = _tokenize(text)
        vec = self._tfidf.transform(tokens)
        label, confidence = self._clf.predict(vec)

        result = TextClassificationResult(
            result_id=str(uuid.uuid4()),
            input_text=text,
            output_text=label,
            confidence=confidence,
        )
        self.results.append(result)
        logger.info("Classified as '%s' (conf=%.4f)", label, confidence)
        return result

    def _train_builtin(self, name: str) -> None:
        data = self.BUILTIN_DATASETS.get(name, _BUILTIN_SENTIMENT)
        self.train(data, dataset_name=name)


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_text_classification: Optional[TextClassificationSystem] = None

def get_text_classification() -> Optional[TextClassificationSystem]:
    return _text_classification

def initialize_text_classification(data_dir) -> TextClassificationSystem:
    global _text_classification
    _text_classification = TextClassificationSystem(data_dir)
    return _text_classification
