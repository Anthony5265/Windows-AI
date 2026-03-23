"""
Question Answering module for Windows AI.

Implements extractive QA using TF-IDF retrieval:
1. Split context into sentences / passages
2. Build TF-IDF vectors for passages and query
3. Rank passages by cosine similarity to question
4. Extract best answer span from top-ranked passage
5. Score confidence based on similarity gap and coverage

Supports document-based and knowledge-base QA.
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
# Text helpers
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

_SENT_RE = re.compile(r'(?<=[.!?])\s+')


def _tokenize(text: str) -> List[str]:
    return [t for t in re.findall(r"[a-z0-9]+", text.lower())
            if t not in _STOP_WORDS and len(t) > 1]


def _split_sentences(text: str) -> List[str]:
    parts = _SENT_RE.split(text)
    sents = [p.strip() for p in parts if p.strip()]
    if not sents:
        for line in text.split("\n"):
            line = line.strip()
            if line:
                sents.append(line)
    return sents if sents else [text]


# ---------------------------------------------------------------------------
# TF-IDF + cosine
# ---------------------------------------------------------------------------
class _TfIdf:
    def __init__(self) -> None:
        self.idf: Dict[str, float] = {}

    def fit(self, docs: List[List[str]]) -> None:
        n = len(docs)
        df: Dict[str, int] = collections.defaultdict(int)
        for doc in docs:
            for t in set(doc):
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
# Built-in knowledge base
# ---------------------------------------------------------------------------
_KNOWLEDGE_BASE: List[str] = [
    "Python is a high-level programming language created by Guido van Rossum in 1991.",
    "The Earth orbits the Sun at an average distance of about 93 million miles.",
    "Water boils at 100 degrees Celsius at standard atmospheric pressure.",
    "The speed of light in a vacuum is approximately 299792458 meters per second.",
    "Artificial intelligence is a branch of computer science focused on building smart machines.",
    "The human brain contains approximately 86 billion neurons.",
    "Mount Everest is the tallest mountain on Earth at 8849 meters above sea level.",
    "The Pacific Ocean is the largest and deepest ocean on Earth.",
    "DNA stands for deoxyribonucleic acid and carries genetic instructions.",
    "The Great Wall of China is over 21000 kilometers long.",
    "Shakespeare wrote 37 plays and 154 sonnets during his lifetime.",
    "The Mona Lisa was painted by Leonardo da Vinci in the early 16th century.",
    "Oxygen makes up about 21 percent of the Earth's atmosphere.",
    "The Amazon River is the largest river by volume of water flow.",
    "Albert Einstein published his theory of general relativity in 1915.",
]


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------
@dataclass
class QuestionAnsweringResult:
    result_id: str
    input_text: str
    output_text: str
    confidence: float


# ---------------------------------------------------------------------------
# Answer extractor
# ---------------------------------------------------------------------------
class _AnswerExtractor:
    """Extract the most relevant span from a passage given a question."""

    @staticmethod
    def extract(passage: str, question: str) -> Tuple[str, float]:
        q_tokens = set(_tokenize(question))
        q_type = _AnswerExtractor._question_type(question)

        sentences = _split_sentences(passage)
        if len(sentences) == 1:
            return _AnswerExtractor._extract_span(sentences[0], q_tokens, q_type)

        scored: List[Tuple[float, str]] = []
        for sent in sentences:
            s_tokens = set(_tokenize(sent))
            overlap = len(q_tokens & s_tokens) / max(len(q_tokens), 1)
            type_bonus = _AnswerExtractor._type_bonus(sent, q_type)
            scored.append((overlap + type_bonus, sent))
        scored.sort(reverse=True)
        best_sent = scored[0][1]
        best_score = scored[0][0]
        span, _ = _AnswerExtractor._extract_span(best_sent, q_tokens, q_type)
        return span, min(best_score, 1.0)

    @staticmethod
    def _question_type(question: str) -> str:
        first = question.lower().split()[0] if question.split() else ""
        if first in ("who", "whom"):
            return "person"
        if first == "where":
            return "location"
        if first == "when":
            return "date"
        if first == "how" and "many" in question.lower():
            return "number"
        if first == "how" and "much" in question.lower():
            return "number"
        return "general"

    @staticmethod
    def _type_bonus(sentence: str, q_type: str) -> float:
        if q_type == "date" and re.search(r'\b\d{4}\b|\b\d{1,2}[/-]\d{1,2}', sentence):
            return 0.2
        if q_type == "number" and re.search(r'\b\d+(?:\.\d+)?\b', sentence):
            return 0.15
        if q_type == "person" and re.search(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', sentence):
            return 0.2
        if q_type == "location" and re.search(r'\b[A-Z][a-z]{2,}\b', sentence):
            return 0.1
        return 0.0

    @staticmethod
    def _extract_span(sentence: str, q_tokens: set, q_type: str) -> Tuple[str, float]:
        if len(sentence.split()) <= 8:
            return sentence, 0.7

        clauses = re.split(r'[,;]', sentence)
        if len(clauses) > 1:
            best_clause = ""
            best_score = -1.0
            for clause in clauses:
                c_tokens = set(_tokenize(clause))
                new_info = len(c_tokens - q_tokens)
                overlap = len(c_tokens & q_tokens)
                score = new_info * 0.6 + overlap * 0.4
                if score > best_score:
                    best_score = score
                    best_clause = clause.strip()
            if best_clause:
                return best_clause, 0.6
        return sentence, 0.5


# ---------------------------------------------------------------------------
# Main system
# ---------------------------------------------------------------------------
class QuestionAnsweringSystem:
    """Extractive QA using TF-IDF passage retrieval.

    Supports document-based QA (provide context) and knowledge-base QA
    (uses built-in knowledge base when no context given).
    """

    def __init__(self, data_dir) -> None:
        self.data_dir = Path(data_dir) if not isinstance(data_dir, Path) else data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[QuestionAnsweringResult] = []
        self._knowledge_base: List[str] = list(_KNOWLEDGE_BASE)
        self._documents: List[str] = []
        logger.info("QuestionAnswering initialized")

    def add_knowledge(self, facts: List[str]) -> None:
        """Add facts to the knowledge base."""
        self._knowledge_base.extend(facts)

    def add_documents(self, documents: List[str]) -> None:
        """Add documents for retrieval."""
        self._documents.extend(documents)

    def process(self, text: str) -> QuestionAnsweringResult:
        """Answer a question. Format: 'question' or 'question ||| context'."""
        if "|||" in text:
            question, context = text.split("|||", 1)
            question = question.strip()
            context = context.strip()
        else:
            question = text.strip()
            context = ""

        if context:
            answer, confidence = self._answer_from_context(question, context)
        elif self._documents:
            answer, confidence = self._answer_from_documents(question)
        else:
            answer, confidence = self._answer_from_kb(question)

        result = QuestionAnsweringResult(
            result_id=str(uuid.uuid4()),
            input_text=text,
            output_text=answer,
            confidence=round(confidence, 4),
        )
        self.results.append(result)
        logger.info("QA conf=%.4f", confidence)
        return result

    def ask(self, question: str, context: str = "") -> QuestionAnsweringResult:
        """Convenience: ask with explicit context."""
        if context:
            return self.process(f"{question} ||| {context}")
        return self.process(question)

    def _answer_from_context(self, question: str, context: str) -> Tuple[str, float]:
        return self._rank_and_extract(question, _split_sentences(context))

    def _answer_from_documents(self, question: str) -> Tuple[str, float]:
        all_sents: List[str] = []
        for doc in self._documents:
            all_sents.extend(_split_sentences(doc))
        return self._rank_and_extract(question, all_sents)

    def _answer_from_kb(self, question: str) -> Tuple[str, float]:
        return self._rank_and_extract(question, self._knowledge_base)

    def _rank_and_extract(
        self, question: str, passages: List[str]
    ) -> Tuple[str, float]:
        if not passages:
            return "No information available to answer this question.", 0.0

        q_tokens = _tokenize(question)
        p_tokenized = [_tokenize(p) for p in passages]
        all_docs = [q_tokens] + p_tokenized

        tfidf = _TfIdf()
        tfidf.fit(all_docs)
        q_vec = tfidf.transform(q_tokens)
        p_vecs = [tfidf.transform(pt) for pt in p_tokenized]

        scored: List[Tuple[float, int]] = []
        for idx, pv in enumerate(p_vecs):
            scored.append((_cosine(q_vec, pv), idx))
        scored.sort(reverse=True)

        if scored[0][0] < 0.01:
            return "No relevant information found for this question.", 0.0

        best_passage = passages[scored[0][1]]
        best_sim = scored[0][0]

        answer, span_conf = _AnswerExtractor.extract(best_passage, question)
        confidence = min(best_sim * 0.6 + span_conf * 0.4, 1.0)
        return answer, confidence


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_question_answering: Optional[QuestionAnsweringSystem] = None

def get_question_answering() -> Optional[QuestionAnsweringSystem]:
    return _question_answering

def initialize_question_answering(data_dir) -> QuestionAnsweringSystem:
    global _question_answering
    _question_answering = QuestionAnsweringSystem(data_dir)
    return _question_answering
