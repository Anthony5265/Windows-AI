"""
Text Summarization module for Windows AI.

Implements extractive summarization using a TextRank-inspired algorithm:
sentence tokenization, TF-IDF vectors, cosine-similarity graph,
iterative PageRank scoring, and top-N sentence selection.
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
# Lightweight NLP helpers
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
    "we", "our", "you", "your", "he", "him", "his", "she", "her",
    "they", "them", "their", "what", "which", "who", "whom", "when",
    "where", "why", "how", "if", "then", "there", "here",
}

_SENT_SPLIT_RE = re.compile(r'(?<=[.!?])\s+(?=[A-Z])')
_ABBREV_RE = re.compile(r'\b(?:Mr|Mrs|Ms|Dr|Prof|Inc|Ltd|Jr|Sr|vs|etc)\.\s', re.I)


def _split_sentences(text: str) -> List[str]:
    """Split text into sentences with basic abbreviation handling."""
    protected = _ABBREV_RE.sub(lambda m: m.group().replace(". ", ".<PROT> "), text)
    parts = _SENT_SPLIT_RE.split(protected)
    sentences: List[str] = []
    for part in parts:
        s = part.replace("<PROT>", "").strip()
        if s:
            sentences.append(s)
    if len(sentences) <= 1 and "\n" in text:
        for line in text.split("\n"):
            line = line.strip()
            if line:
                sentences.append(line)
    return sentences


def _tokenize(text: str) -> List[str]:
    tokens = re.findall(r"[a-z]+", text.lower())
    return [t for t in tokens if t not in _STOP_WORDS and len(t) > 1]


# ---------------------------------------------------------------------------
# TF-IDF helpers
# ---------------------------------------------------------------------------
class _TfIdf:
    """Build TF-IDF vectors for a collection of sentences."""

    def __init__(self) -> None:
        self.idf: Dict[str, float] = {}
        self.doc_count: int = 0

    def fit(self, docs: List[List[str]]) -> None:
        self.doc_count = len(docs)
        df: Dict[str, int] = collections.defaultdict(int)
        for doc in docs:
            for term in set(doc):
                df[term] += 1
        for term, count in df.items():
            self.idf[term] = math.log((self.doc_count + 1) / (count + 1)) + 1.0

    def transform(self, tokens: List[str]) -> Dict[str, float]:
        tf: Dict[str, int] = collections.Counter(tokens)
        total = max(len(tokens), 1)
        return {t: (c / total) * self.idf.get(t, 1.0) for t, c in tf.items()}


def _cosine_similarity(v1: Dict[str, float], v2: Dict[str, float]) -> float:
    common = set(v1) & set(v2)
    if not common:
        return 0.0
    dot = sum(v1[k] * v2[k] for k in common)
    mag1 = math.sqrt(sum(val * val for val in v1.values()))
    mag2 = math.sqrt(sum(val * val for val in v2.values()))
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot / (mag1 * mag2)


# ---------------------------------------------------------------------------
# TextRank scorer
# ---------------------------------------------------------------------------
def _textrank(
    similarity_matrix: List[List[float]],
    damping: float = 0.85,
    max_iter: int = 50,
    tol: float = 1e-5,
) -> List[float]:
    """Compute PageRank-style scores over a sentence similarity graph."""
    n = len(similarity_matrix)
    if n == 0:
        return []
    scores = [1.0 / n] * n
    row_sums = [sum(row) or 1.0 for row in similarity_matrix]

    for _ in range(max_iter):
        new_scores = [0.0] * n
        for i in range(n):
            rank_sum = 0.0
            for j in range(n):
                if i != j:
                    rank_sum += (similarity_matrix[j][i] / row_sums[j]) * scores[j]
            new_scores[i] = (1 - damping) / n + damping * rank_sum
        diff = sum(abs(new_scores[k] - scores[k]) for k in range(n))
        scores = new_scores
        if diff < tol:
            break
    return scores


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------
@dataclass
class TextSummarizationResult:
    result_id: str
    input_text: str
    output_text: str
    confidence: float


# ---------------------------------------------------------------------------
# Main system
# ---------------------------------------------------------------------------
class TextSummarizationSystem:
    """Extractive summarization using TextRank (graph-based sentence ranking).

    Pipeline: sentence tokenisation -> TF-IDF vectorisation ->
    cosine-similarity adjacency matrix -> PageRank scoring ->
    top-N sentence selection (preserving original order).
    """

    def __init__(self, data_dir) -> None:
        self.data_dir = Path(data_dir) if not isinstance(data_dir, Path) else data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[TextSummarizationResult] = []
        self.ratio: float = 0.3
        self.min_sentences: int = 1
        self.max_sentences: int = 10
        self.damping: float = 0.85
        logger.info("TextSummarization initialized")

    def set_ratio(self, ratio: float) -> None:
        """Set the fraction of sentences to retain (0.0 – 1.0)."""
        self.ratio = max(0.05, min(ratio, 1.0))

    def process(self, text: str) -> TextSummarizationResult:
        """Summarise *text* via TextRank extractive approach."""
        sentences = _split_sentences(text)

        if len(sentences) <= 2:
            return self._build_result(text, text, confidence=0.95)

        tokenized = [_tokenize(s) for s in sentences]
        tfidf = _TfIdf()
        tfidf.fit(tokenized)
        vectors = [tfidf.transform(tok) for tok in tokenized]

        n = len(sentences)
        sim_matrix: List[List[float]] = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(i + 1, n):
                sim = _cosine_similarity(vectors[i], vectors[j])
                sim_matrix[i][j] = sim
                sim_matrix[j][i] = sim

        scores = _textrank(sim_matrix, damping=self.damping)

        k = max(self.min_sentences,
                min(self.max_sentences, int(math.ceil(n * self.ratio))))
        ranked_indices = sorted(range(n), key=lambda idx: scores[idx], reverse=True)
        selected = sorted(ranked_indices[:k])

        summary = " ".join(sentences[idx] for idx in selected)
        avg_conf = sum(scores[idx] for idx in selected) / max(len(selected), 1)
        max_possible = max(scores) if scores else 1.0
        confidence = round(min(avg_conf / max(max_possible, 1e-9), 1.0), 4)

        return self._build_result(text, summary, confidence=confidence)

    def process_with_length(self, text: str, *, num_sentences: int = 3) -> TextSummarizationResult:
        """Summarise requesting a specific number of output sentences."""
        old_min, old_max, old_ratio = self.min_sentences, self.max_sentences, self.ratio
        self.min_sentences = num_sentences
        self.max_sentences = num_sentences
        self.ratio = 1.0
        result = self.process(text)
        self.min_sentences, self.max_sentences, self.ratio = old_min, old_max, old_ratio
        return result

    def _build_result(
        self, input_text: str, summary: str, *, confidence: float
    ) -> TextSummarizationResult:
        result = TextSummarizationResult(
            result_id=str(uuid.uuid4()),
            input_text=input_text,
            output_text=summary,
            confidence=confidence,
        )
        self.results.append(result)
        logger.info(
            "Summarised %d chars -> %d chars (conf=%.4f)",
            len(input_text), len(summary), confidence,
        )
        return result


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_text_summarization: Optional[TextSummarizationSystem] = None

def get_text_summarization() -> Optional[TextSummarizationSystem]:
    return _text_summarization

def initialize_text_summarization(data_dir) -> TextSummarizationSystem:
    global _text_summarization
    _text_summarization = TextSummarizationSystem(data_dir)
    return _text_summarization
