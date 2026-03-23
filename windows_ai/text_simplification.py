"""
Text Simplification module for Windows AI.

Implements rule-based text simplification:
- Long-sentence splitting at conjunctions and relative clauses
- Vocabulary simplification via complex->simple word mapping
- Passive-to-active voice conversion heuristics
- Readability scoring (Flesch-Kincaid Grade Level & Reading Ease)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import logging
import math
import re
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Complex -> simple vocabulary map
# ---------------------------------------------------------------------------
_SIMPLE_WORDS: Dict[str, str] = {
    "accomplish": "do", "accumulate": "gather", "administer": "manage",
    "advantageous": "helpful", "amalgamate": "combine", "ameliorate": "improve",
    "approximately": "about", "ascertain": "find out", "assistance": "help",
    "commence": "start", "communicate": "talk", "compensate": "pay",
    "component": "part", "comprehend": "understand", "concerning": "about",
    "consequently": "so", "considerable": "big", "constitute": "make up",
    "demonstrate": "show", "determine": "find out", "diminish": "reduce",
    "discontinue": "stop", "disseminate": "spread", "economical": "cheap",
    "elaborate": "detailed", "eliminate": "remove", "employ": "use",
    "encounter": "meet", "endeavor": "try", "enquire": "ask",
    "establish": "set up", "evaluate": "check", "evidently": "clearly",
    "exclusively": "only", "expedite": "speed up", "facilitate": "help",
    "fluctuate": "change", "forthcoming": "upcoming", "frequently": "often",
    "fundamental": "basic", "furthermore": "also", "however": "but",
    "illustrate": "show", "immediately": "now", "implement": "do",
    "in addition": "also", "in order to": "to", "in regard to": "about",
    "in the event that": "if", "inadequate": "not enough", "inaugurate": "start",
    "incorporate": "include", "indicate": "show", "individual": "person",
    "initiate": "start", "inquire": "ask", "insufficient": "not enough",
    "magnitude": "size", "maintain": "keep", "methodology": "method",
    "modification": "change", "moreover": "also", "necessitate": "need",
    "nevertheless": "still", "notify": "tell", "numerous": "many",
    "objective": "goal", "obtain": "get", "operate": "run",
    "opportunity": "chance", "participate": "join", "perceive": "see",
    "permit": "let", "pertaining to": "about", "possess": "have",
    "preceding": "before", "predominantly": "mainly", "previously": "before",
    "principal": "main", "prioritize": "rank", "probability": "chance",
    "proceed": "go", "proficient": "skilled", "prohibit": "ban",
    "provide": "give", "purchase": "buy", "regarding": "about",
    "reimburse": "pay back", "remainder": "rest", "remuneration": "pay",
    "request": "ask", "require": "need", "residence": "home",
    "retain": "keep", "satisfactory": "good enough", "scrutinize": "examine",
    "significant": "important", "solely": "only", "straightforward": "simple",
    "subsequent": "next", "subsequently": "later", "sufficient": "enough",
    "terminate": "end", "therefore": "so", "transmit": "send",
    "ultimately": "finally", "undertake": "do", "utilize": "use",
    "whereas": "while", "with respect to": "about",
}

# ---------------------------------------------------------------------------
# Sentence splitting patterns
# ---------------------------------------------------------------------------
_SPLIT_CONJUNCTIONS = re.compile(
    r',?\s+\b(and|but|however|moreover|furthermore|nevertheless|'
    r'consequently|therefore|although|whereas|while)\b\s+',
    re.IGNORECASE,
)

_RELATIVE_CLAUSE = re.compile(r',\s+(which|who|that)\s+', re.IGNORECASE)

_PASSIVE_RE = re.compile(
    r'\b(was|were|is|are|been|being|be)\s+(\w+ed)\b', re.IGNORECASE,
)

_SENT_SPLIT_RE = re.compile(r'(?<=[.!?])\s+')


def _count_syllables(word: str) -> int:
    """Estimate syllable count using a vowel-group heuristic."""
    word = word.lower().rstrip("e")
    if not word:
        return 1
    count = len(re.findall(r'[aeiouy]+', word))
    return max(count, 1)


def _split_sentences(text: str) -> List[str]:
    parts = _SENT_SPLIT_RE.split(text)
    return [p.strip() for p in parts if p.strip()]


# ---------------------------------------------------------------------------
# Readability metrics
# ---------------------------------------------------------------------------
def _flesch_kincaid_grade(text: str) -> float:
    """Compute Flesch-Kincaid Grade Level."""
    sentences = _split_sentences(text) or [text]
    words = re.findall(r"[a-zA-Z']+", text)
    if not words or not sentences:
        return 0.0
    syllables = sum(_count_syllables(w) for w in words)
    n_words = len(words)
    n_sents = len(sentences)
    grade = 0.39 * (n_words / n_sents) + 11.8 * (syllables / n_words) - 15.59
    return round(max(grade, 0.0), 2)


def _flesch_reading_ease(text: str) -> float:
    """Compute Flesch Reading Ease score (0-100, higher = easier)."""
    sentences = _split_sentences(text) or [text]
    words = re.findall(r"[a-zA-Z']+", text)
    if not words or not sentences:
        return 100.0
    syllables = sum(_count_syllables(w) for w in words)
    n_words = len(words)
    n_sents = len(sentences)
    ease = 206.835 - 1.015 * (n_words / n_sents) - 84.6 * (syllables / n_words)
    return round(max(min(ease, 100.0), 0.0), 2)


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------
@dataclass
class TextSimplificationResult:
    result_id: str
    input_text: str
    output_text: str
    confidence: float


# ---------------------------------------------------------------------------
# Main system
# ---------------------------------------------------------------------------
class TextSimplificationSystem:
    """Rule-based text simplification with readability scoring.

    Pipeline:
        1. Vocabulary simplification (complex -> simple words)
        2. Sentence splitting at conjunctions / relative clauses
        3. Passive-to-active heuristic conversion
        4. Readability scoring (Flesch-Kincaid)
    """

    def __init__(self, data_dir) -> None:
        self.data_dir = Path(data_dir) if not isinstance(data_dir, Path) else data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[TextSimplificationResult] = []
        self._word_map: Dict[str, str] = dict(_SIMPLE_WORDS)
        self._max_sentence_words: int = 20
        logger.info("TextSimplification initialized")

    def add_word_mapping(self, mapping: Dict[str, str]) -> None:
        """Extend vocabulary simplification map."""
        self._word_map.update({k.lower(): v.lower() for k, v in mapping.items()})

    def readability(self, text: str) -> Dict[str, float]:
        """Return readability metrics for *text*."""
        return {
            "flesch_kincaid_grade": _flesch_kincaid_grade(text),
            "flesch_reading_ease": _flesch_reading_ease(text),
        }

    def process(self, text: str) -> TextSimplificationResult:
        """Simplify *text* and return structured result."""
        original_grade = _flesch_kincaid_grade(text)

        simplified = text
        simplified = self._simplify_vocabulary(simplified)
        simplified = self._split_long_sentences(simplified)
        simplified = self._passive_to_active(simplified)
        simplified = self._clean_whitespace(simplified)

        new_grade = _flesch_kincaid_grade(simplified)

        if original_grade > 0:
            improvement = max(original_grade - new_grade, 0.0)
            confidence = min(improvement / max(original_grade, 1.0) + 0.5, 1.0)
        else:
            confidence = 0.9

        result = TextSimplificationResult(
            result_id=str(uuid.uuid4()),
            input_text=text,
            output_text=simplified,
            confidence=round(confidence, 4),
        )
        self.results.append(result)
        logger.info("Simplified grade %.1f->%.1f (conf=%.4f)", original_grade, new_grade, confidence)
        return result

    def _simplify_vocabulary(self, text: str) -> str:
        """Replace complex words/phrases with simpler equivalents."""
        result = text
        # Multi-word phrases first (longest first)
        phrases = sorted(
            ((k, v) for k, v in self._word_map.items() if " " in k),
            key=lambda x: -len(x[0]),
        )
        for phrase, simple in phrases:
            pat = re.compile(r'\b' + re.escape(phrase) + r'\b', re.IGNORECASE)
            result = pat.sub(simple, result)

        def _replace_word(m: re.Match) -> str:
            word = m.group(0)
            lower = word.lower()
            if lower in self._word_map:
                replacement = self._word_map[lower]
                return replacement.capitalize() if word[0].isupper() else replacement
            return word

        result = re.sub(r"\b[a-zA-Z']+\b", _replace_word, result)
        return result

    def _split_long_sentences(self, text: str) -> str:
        """Split sentences exceeding the max word threshold."""
        sentences = _split_sentences(text) or [text]
        output: List[str] = []

        _CONJ_SET = {
            "and", "but", "however", "moreover", "furthermore",
            "nevertheless", "consequently", "therefore",
            "although", "whereas", "while",
        }

        for sent in sentences:
            words = sent.split()
            if len(words) <= self._max_sentence_words:
                output.append(sent)
                continue

            parts = _SPLIT_CONJUNCTIONS.split(sent)
            if len(parts) >= 2:
                for part in parts:
                    part = part.strip()
                    if not part or part.lower() in _CONJ_SET:
                        continue
                    part = part[0].upper() + part[1:] if part else part
                    if part and not part.endswith((".", "!", "?")):
                        part += "."
                    output.append(part)
            else:
                rel_parts = _RELATIVE_CLAUSE.split(sent)
                if len(rel_parts) >= 2:
                    for rp in rel_parts:
                        rp = rp.strip()
                        if rp.lower() in ("which", "who", "that"):
                            continue
                        if rp:
                            rp = rp[0].upper() + rp[1:]
                            if not rp.endswith((".", "!", "?")):
                                rp += "."
                            output.append(rp)
                else:
                    output.append(sent)

        return " ".join(output)

    def _passive_to_active(self, text: str) -> str:
        """Heuristic passive->active conversion for simple cases."""
        def _convert(m: re.Match) -> str:
            aux = m.group(1).lower()
            verb = m.group(2)
            if aux in ("is", "are"):
                base = verb[:-2] if verb.endswith("ed") else verb
                return base + "s"
            if aux in ("was", "were"):
                return verb
            return m.group(0)
        return _PASSIVE_RE.sub(_convert, text)

    @staticmethod
    def _clean_whitespace(text: str) -> str:
        text = re.sub(r'\s+', ' ', text).strip()
        text = re.sub(r'\s+([.!?,;:])', r'\1', text)
        return text


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_text_simplification: Optional[TextSimplificationSystem] = None

def get_text_simplification() -> Optional[TextSimplificationSystem]:
    return _text_simplification

def initialize_text_simplification(data_dir) -> TextSimplificationSystem:
    global _text_simplification
    _text_simplification = TextSimplificationSystem(data_dir)
    return _text_simplification
