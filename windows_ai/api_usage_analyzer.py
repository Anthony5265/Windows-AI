"""Deterministic API usage analysis primitives."""

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import math
import re
import uuid

logger = logging.getLogger(__name__)


@dataclass
class ApiUsageAnalyzerResult:
    result_id: str
    output: str
    confidence: float
    created_at: str


class ApiUsageAnalyzerSystem:
    """Analyze API usage text without fabricated/random confidence scores."""

    STATE_VERSION = 1

    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[ApiUsageAnalyzerResult] = []
        self._config = {"initialized": True, "version": "1.0.0"}
        self._cache: Dict[str, Any] = {}
        self._load_state()

    def _tokenize(self, text):
        return re.findall(r"\b\w+\b", text.casefold())

    def _tfidf_vector(self, tokens, vocab):
        tf = {}
        for token in tokens:
            tf[token] = tf.get(token, 0) + 1
        total = len(tokens) or 1
        return [tf.get(word, 0) / total for word in vocab]

    def _cosine_sim(self, a, b):
        if len(a) != len(b):
            raise ValueError("vectors must have equal dimensions")
        dot = sum(ai * bi for ai, bi in zip(a, b))
        na = math.sqrt(sum(ai * ai for ai in a))
        nb = math.sqrt(sum(bi * bi for bi in b))
        return dot / (na * nb) if na and nb else 0.0

    def _levenshtein(self, s1, s2):
        previous = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1, 1):
            current = [i]
            for j, c2 in enumerate(s2, 1):
                current.append(min(current[-1] + 1, previous[j] + 1, previous[j - 1] + (c1 != c2)))
            previous = current
        return previous[-1]

    def _extract_patterns(self, text):
        return {
            "emails": re.findall(r"[\w.+-]+@[\w-]+\.[\w.]+", text),
            "urls": re.findall(r"https?://[^\s]+", text),
            "ips": re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", text),
            "dates": re.findall(r"\b\d{4}-\d{2}-\d{2}\b", text),
            "numbers": re.findall(r"\b\d+(?:\.\d+)?\b", text),
        }

    def _build_inverted_index(self, documents):
        index = {}
        for doc_id, doc in enumerate(documents):
            for token in set(self._tokenize(doc)):
                index.setdefault(token, []).append(doc_id)
        return index

    def _bm25_score(self, query_tokens, doc_tokens, avg_dl, n_docs, df):
        if avg_dl <= 0 or n_docs <= 0:
            return 0.0
        k1, b = 1.2, 0.75
        dl = len(doc_tokens)
        tf_map = {}
        for token in doc_tokens:
            tf_map[token] = tf_map.get(token, 0) + 1
        score = 0.0
        for token in query_tokens:
            tf = tf_map.get(token, 0)
            if not tf:
                continue
            doc_freq = df.get(token, 0)
            idf = math.log((n_docs - doc_freq + 0.5) / (doc_freq + 0.5) + 1)
            score += idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl / avg_dl))
        return score

    def _detect_anomalies_text(self, texts):
        if not texts:
            return []
        lengths = [len(t) for t in texts]
        mean = sum(lengths) / len(lengths)
        std = math.sqrt(sum((length - mean) ** 2 for length in lengths) / len(lengths))
        if std == 0:
            return []
        return [i for i, length in enumerate(lengths) if abs(length - mean) / std > 2]

    def _summarize_stats(self, values):
        if not values:
            return {"count": 0}
        values = sorted(values)
        n = len(values)
        mean = sum(values) / n
        return {"count": n, "mean": mean, "median": values[(n - 1) // 2], "min": values[0], "max": values[-1], "std": math.sqrt(sum((v - mean) ** 2 for v in values) / n), "p25": values[(n - 1) // 4], "p75": values[3 * (n - 1) // 4]}

    def process(self, text: str) -> ApiUsageAnalyzerResult:
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        text = text.strip()
        if not text:
            raise ValueError("text must not be empty")
        tokens = self._tokenize(text)
        patterns = self._extract_patterns(text)
        pattern_count = sum(len(values) for values in patterns.values())
        token_quality = min(1.0, len(set(tokens)) / max(1, len(tokens)))
        pattern_quality = min(1.0, pattern_count / max(1, len(tokens)))
        confidence = max(0.0, min(1.0, 0.7 * token_quality + 0.3 * pattern_quality))
        output = f"Processed {len(tokens)} tokens; detected {pattern_count} structured API patterns."
        result = ApiUsageAnalyzerResult(str(uuid.uuid4()), output, confidence, datetime.now(timezone.utc).isoformat())
        self.results.append(result)
        self._save_state()
        return result

    def _save_state(self):
        target = self.data_dir / "api_usage_analyzer_state.json"
        temp = target.with_suffix(".tmp")
        state = {"version": self.STATE_VERSION, "results": [asdict(result) for result in self.results]}
        temp.write_text(json.dumps(state, indent=2), encoding="utf-8")
        temp.replace(target)

    def _load_state(self):
        target = self.data_dir / "api_usage_analyzer_state.json"
        if not target.exists():
            return
        try:
            state = json.loads(target.read_text(encoding="utf-8"))
            if state.get("version") != self.STATE_VERSION:
                return
            self.results = [ApiUsageAnalyzerResult(**item) for item in state.get("results", [])]
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
            logger.warning("Ignoring invalid API usage analyzer state")


_api_usage_analyzer: Optional[ApiUsageAnalyzerSystem] = None


def get_api_usage_analyzer() -> Optional[ApiUsageAnalyzerSystem]:
    return _api_usage_analyzer


def initialize_api_usage_analyzer(data_dir) -> ApiUsageAnalyzerSystem:
    global _api_usage_analyzer
    _api_usage_analyzer = ApiUsageAnalyzerSystem(data_dir)
    return _api_usage_analyzer
