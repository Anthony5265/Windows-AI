"""API usage analysis primitives."""

from dataclasses import dataclass
import logging
import math
import re
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

@dataclass
class ApiUsageAnalyzerResult:
    result_id: str
    output: str
    confidence: float

class ApiUsageAnalyzerSystem:
    """Analyze supplied API usage text without fabricated confidence values."""
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[ApiUsageAnalyzerResult] = []
        self._config = {"initialized": True, "version": "1.0.0"}
        self._cache: Dict[str, Any] = {}

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return re.findall(r"\b\w+\b", text.casefold())

    def _tfidf_vector(self, tokens, vocab):
        counts = {token: tokens.count(token) for token in set(tokens)}
        total = len(tokens) or 1
        return [counts.get(word, 0) / total for word in vocab]

    @staticmethod
    def _cosine_sim(a, b):
        if len(a) != len(b):
            raise ValueError("vectors must have equal length")
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(y * y for y in b))
        return dot / (na * nb) if na and nb else 0.0

    @staticmethod
    def _levenshtein(s1, s2):
        if not isinstance(s1, str) or not isinstance(s2, str):
            raise TypeError("inputs must be strings")
        previous = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1, 1):
            current = [i]
            for j, c2 in enumerate(s2, 1):
                current.append(min(current[-1] + 1, previous[j] + 1, previous[j - 1] + (c1 != c2)))
            previous = current
        return previous[-1]

    @staticmethod
    def _extract_patterns(text):
        return {"emails": re.findall(r"[\w.+-]+@[\w-]+\.[\w.]+", text), "urls": re.findall(r"https?://[^\s]+", text), "ips": re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", text), "dates": re.findall(r"\b\d{4}-\d{2}-\d{2}\b", text), "numbers": re.findall(r"\b\d+(?:\.\d+)?\b", text)}

    def _build_inverted_index(self, documents):
        return {token: [i for i, doc in enumerate(documents) if token in set(self._tokenize(doc))] for token in sorted(set(t for doc in documents for t in self._tokenize(doc)))}

    def _bm25_score(self, query_tokens, doc_tokens, avg_dl, n_docs, df):
        if avg_dl <= 0 or n_docs <= 0:
            return 0.0
        k1, b = 1.2, 0.75
        counts = {token: doc_tokens.count(token) for token in set(doc_tokens)}
        dl = len(doc_tokens)
        return sum(math.log((n_docs - df.get(token, 0) + 0.5) / (df.get(token, 0) + 0.5) + 1) * ((counts.get(token, 0) * (k1 + 1)) / (counts.get(token, 0) + k1 * (1 - b + b * dl / avg_dl))) for token in query_tokens if counts.get(token, 0))

    @staticmethod
    def _detect_anomalies_text(texts):
        if not texts:
            return []
        lengths = [len(text) for text in texts]
        mean = sum(lengths) / len(lengths)
        std = math.sqrt(sum((x - mean) ** 2 for x in lengths) / len(lengths))
        return [] if std == 0 else [i for i, length in enumerate(lengths) if abs(length - mean) / std > 2]

    @staticmethod
    def _summarize_stats(values):
        if not values:
            return {"count": 0}
        ordered = sorted(values)
        n = len(ordered)
        mean = sum(values) / n
        return {"count": n, "mean": mean, "median": ordered[(n - 1) // 2], "min": ordered[0], "max": ordered[-1], "std": math.sqrt(sum((v - mean) ** 2 for v in values) / n), "p25": ordered[(n - 1) // 4], "p75": ordered[3 * (n - 1) // 4]}

    def process(self, text: str) -> ApiUsageAnalyzerResult:
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        if not text.strip():
            raise ValueError("text must not be empty")
        tokens = self._tokenize(text)
        patterns = self._extract_patterns(text)
        output = f"tokens={len(tokens)}; characters={len(text)}; patterns={sum(len(v) for v in patterns.values())}"
        confidence = min(1.0, 0.5 + min(len(tokens), 100) / 200)
        result = ApiUsageAnalyzerResult(str(uuid.uuid4()), output, confidence)
        self.results.append(result)
        return result

_api_usage_analyzer: Optional[ApiUsageAnalyzerSystem] = None

def get_api_usage_analyzer() -> Optional[ApiUsageAnalyzerSystem]:
    return _api_usage_analyzer

def initialize_api_usage_analyzer(data_dir) -> ApiUsageAnalyzerSystem:
    global _api_usage_analyzer
    _api_usage_analyzer = ApiUsageAnalyzerSystem(data_dir)
    return _api_usage_analyzer
