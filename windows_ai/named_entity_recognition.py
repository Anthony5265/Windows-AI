"""
Named Entity Recognition module for Windows AI.

Implements rule-based + statistical NER combining:
- Regex patterns for DATE, MONEY, EMAIL, URL, PHONE entities
- Gazetteers for PERSON, ORGANIZATION, LOCATION
- Contextual clues (title words, capitalisation, suffixes)
- Span extraction with character offsets and confidence scoring
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Set
import logging
import re
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

# Entity type constants
PERSON = "PERSON"
ORGANIZATION = "ORGANIZATION"
LOCATION = "LOCATION"
DATE = "DATE"
MONEY = "MONEY"
EMAIL = "EMAIL"
URL = "URL"
PHONE = "PHONE"

# ---------------------------------------------------------------------------
# Gazetteers
# ---------------------------------------------------------------------------
_PERSON_TITLES: Set[str] = {
    "mr", "mrs", "ms", "dr", "prof", "sir", "lord", "lady",
    "president", "senator", "governor", "mayor", "captain",
    "general", "judge", "justice", "officer", "detective",
}

_FIRST_NAMES: Set[str] = {
    "james", "john", "robert", "michael", "william", "david", "richard",
    "joseph", "thomas", "charles", "mary", "patricia", "jennifer",
    "linda", "elizabeth", "barbara", "susan", "jessica", "sarah", "karen",
    "daniel", "matthew", "anthony", "mark", "donald", "steven", "paul",
    "andrew", "joshua", "kenneth", "nancy", "betty", "margaret", "sandra",
    "ashley", "emily", "donna", "michelle", "dorothy", "carol", "amanda",
    "alice", "bob", "charlie", "diana", "edward", "frank", "george",
    "helen", "ivan", "jack", "kate", "lisa", "peter", "sam", "tom",
}

_LAST_NAMES: Set[str] = {
    "smith", "johnson", "williams", "brown", "jones", "garcia", "miller",
    "davis", "rodriguez", "martinez", "hernandez", "lopez", "gonzalez",
    "wilson", "anderson", "thomas", "taylor", "moore", "jackson", "martin",
    "lee", "perez", "thompson", "white", "harris", "sanchez", "clark",
    "lewis", "robinson", "walker", "young", "allen", "king", "wright",
    "scott", "torres", "nguyen", "hill", "flores", "green", "adams",
    "nelson", "baker", "hall", "rivera", "campbell", "mitchell", "carter",
    "roberts", "gomez", "phillips", "evans", "turner", "diaz", "parker",
    "cruz", "edwards", "collins", "reyes", "stewart", "morris", "morales",
}

_ORGANIZATIONS: Set[str] = {
    "google", "microsoft", "apple", "amazon", "facebook", "meta", "tesla",
    "netflix", "twitter", "ibm", "intel", "nvidia", "oracle", "cisco",
    "samsung", "sony", "toyota", "boeing", "nasa", "fbi", "cia", "nsa",
    "who", "nato", "unesco", "unicef", "opec",
}

_ORG_SUFFIXES: Set[str] = {
    "inc", "corp", "ltd", "llc", "co", "company", "corporation",
    "group", "institute", "foundation", "association", "university",
    "college", "bank", "hospital", "agency", "department",
}

_LOCATIONS: Set[str] = {
    "africa", "antarctica", "asia", "australia", "europe",
    "london", "paris", "tokyo", "berlin", "madrid", "rome", "moscow",
    "beijing", "sydney", "toronto", "chicago", "boston", "miami",
    "california", "texas", "florida", "york", "angeles",
    "france", "germany", "spain", "italy", "japan", "china", "india",
    "brazil", "canada", "mexico", "russia", "korea", "england",
    "pacific", "atlantic", "mediterranean", "amazon", "nile", "thames",
    "alps", "himalayas", "sahara", "manhattan", "brooklyn", "queens",
    "washington", "philadelphia", "seattle", "denver", "atlanta",
}

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------
_DATE_PATTERNS = [
    re.compile(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'),
    re.compile(r'\b(?:January|February|March|April|May|June|July|August|'
               r'September|October|November|December)\s+\d{1,2}(?:,?\s+\d{4})?\b', re.I),
    re.compile(r'\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|'
               r'September|October|November|December)(?:\s+\d{4})?\b', re.I),
    re.compile(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}'
               r'(?:,?\s+\d{4})?\b', re.I),
    re.compile(r'\b\d{4}[/-]\d{2}[/-]\d{2}\b'),
]

_MONEY_PATTERNS = [
    re.compile(r'\$\s?\d[\d,]*(?:\.\d{1,2})?(?:\s?(?:million|billion|thousand|hundred))?\b', re.I),
    re.compile(r'\b\d[\d,]*(?:\.\d{1,2})?\s?(?:dollars|euros|pounds|yen|USD|EUR|GBP|JPY)\b', re.I),
    re.compile(r'[EUR_GBP_YEN]\s?\d[\d,]*(?:\.\d{1,2})?\b'),
]

_EMAIL_RE = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
_URL_RE = re.compile(r'https?://[^\s<>"]+|www\.[^\s<>"]+', re.I)
_PHONE_RE = re.compile(r'(?:\+\d{1,3}[\s-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b')


# ---------------------------------------------------------------------------
# Entity span helper
# ---------------------------------------------------------------------------
@dataclass
class _EntitySpan:
    text: str
    label: str
    start: int
    end: int
    confidence: float


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------
@dataclass
class NamedEntityRecognitionResult:
    result_id: str
    input_text: str
    output_text: str
    confidence: float


# ---------------------------------------------------------------------------
# Main system
# ---------------------------------------------------------------------------
class NamedEntityRecognitionSystem:
    """Rule-based + statistical NER.

    Detects: PERSON, ORGANIZATION, LOCATION, DATE, MONEY, EMAIL, URL, PHONE.
    Uses gazetteers, regex patterns, and contextual heuristics.
    """

    def __init__(self, data_dir) -> None:
        self.data_dir = Path(data_dir) if not isinstance(data_dir, Path) else data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[NamedEntityRecognitionResult] = []
        self._custom_gazetteers: Dict[str, Set[str]] = {}
        logger.info("NamedEntityRecognition initialized")

    def add_gazetteer(self, label: str, entries: List[str]) -> None:
        """Add custom gazetteer entries for a given label."""
        key = label.upper()
        if key not in self._custom_gazetteers:
            self._custom_gazetteers[key] = set()
        self._custom_gazetteers[key].update(e.lower() for e in entries)

    def process(self, text: str) -> NamedEntityRecognitionResult:
        """Extract named entities from *text*."""
        entities = self._extract_all(text)
        entities = self._resolve_overlaps(entities)

        if entities:
            parts = [f"{e.text} [{e.label}:{e.confidence:.2f}]" for e in entities]
            output_text = "; ".join(parts)
        else:
            output_text = "No entities found"

        avg_conf = (
            sum(e.confidence for e in entities) / len(entities) if entities else 0.0
        )

        result = NamedEntityRecognitionResult(
            result_id=str(uuid.uuid4()),
            input_text=text,
            output_text=output_text,
            confidence=round(avg_conf, 4),
        )
        self.results.append(result)
        logger.info("Found %d entities (avg_conf=%.4f)", len(entities), avg_conf)
        return result

    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Return structured entity list."""
        entities = self._extract_all(text)
        entities = self._resolve_overlaps(entities)
        return [
            {"text": e.text, "label": e.label, "start": e.start,
             "end": e.end, "confidence": e.confidence}
            for e in entities
        ]

    # -- extraction pipeline --------------------------------------------------
    def _extract_all(self, text: str) -> List[_EntitySpan]:
        entities: List[_EntitySpan] = []
        entities.extend(self._regex_entities(text))
        entities.extend(self._gazetteer_entities(text))
        entities.extend(self._contextual_entities(text))
        entities.extend(self._custom_gazetteer_entities(text))
        return entities

    def _regex_entities(self, text: str) -> List[_EntitySpan]:
        spans: List[_EntitySpan] = []
        for pat in _DATE_PATTERNS:
            for m in pat.finditer(text):
                spans.append(_EntitySpan(m.group(), DATE, m.start(), m.end(), 0.95))
        for pat in _MONEY_PATTERNS:
            for m in pat.finditer(text):
                spans.append(_EntitySpan(m.group(), MONEY, m.start(), m.end(), 0.95))
        for m in _EMAIL_RE.finditer(text):
            spans.append(_EntitySpan(m.group(), EMAIL, m.start(), m.end(), 0.99))
        for m in _URL_RE.finditer(text):
            spans.append(_EntitySpan(m.group(), URL, m.start(), m.end(), 0.99))
        for m in _PHONE_RE.finditer(text):
            spans.append(_EntitySpan(m.group(), PHONE, m.start(), m.end(), 0.85))
        return spans

    def _gazetteer_entities(self, text: str) -> List[_EntitySpan]:
        spans: List[_EntitySpan] = []
        for m in re.finditer(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text):
            chunk = m.group()
            words = chunk.lower().split()
            if len(words) == 1:
                w = words[0]
                if w in _LOCATIONS:
                    spans.append(_EntitySpan(chunk, LOCATION, m.start(), m.end(), 0.80))
                elif w in _ORGANIZATIONS:
                    spans.append(_EntitySpan(chunk, ORGANIZATION, m.start(), m.end(), 0.80))
                elif w in _FIRST_NAMES:
                    spans.append(_EntitySpan(chunk, PERSON, m.start(), m.end(), 0.55))
            elif len(words) >= 2:
                if words[0] in _FIRST_NAMES or words[-1] in _LAST_NAMES:
                    spans.append(_EntitySpan(chunk, PERSON, m.start(), m.end(), 0.85))
                elif any(w in _LOCATIONS for w in words):
                    spans.append(_EntitySpan(chunk, LOCATION, m.start(), m.end(), 0.75))
                elif any(w in _ORG_SUFFIXES for w in words):
                    spans.append(_EntitySpan(chunk, ORGANIZATION, m.start(), m.end(), 0.80))
        return spans

    def _contextual_entities(self, text: str) -> List[_EntitySpan]:
        """Use context clues like title words and nearby keywords."""
        spans: List[_EntitySpan] = []
        title_pat = re.compile(
            r'\b(?:' + '|'.join(re.escape(t) for t in _PERSON_TITLES) +
            r')\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', re.I,
        )
        for m in title_pat.finditer(text):
            spans.append(_EntitySpan(m.group(), PERSON, m.start(), m.end(), 0.92))

        loc_ctx = re.compile(
            r'\b(?:in|from|to|at|near|visited)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
        )
        for m in loc_ctx.finditer(text):
            candidate = m.group(1)
            if candidate.lower().split()[0] not in _FIRST_NAMES:
                spans.append(_EntitySpan(
                    candidate, LOCATION, m.start(1), m.end(1), 0.75,
                ))

        org_suf = re.compile(
            r'\b([A-Z][\w]*(?:\s+[A-Z][\w]*)*\s+(?:' +
            '|'.join(re.escape(s) for s in _ORG_SUFFIXES) +
            r'))\b', re.I,
        )
        for m in org_suf.finditer(text):
            spans.append(_EntitySpan(m.group(), ORGANIZATION, m.start(), m.end(), 0.85))
        return spans

    def _custom_gazetteer_entities(self, text: str) -> List[_EntitySpan]:
        spans: List[_EntitySpan] = []
        for label, entries in self._custom_gazetteers.items():
            for entry in entries:
                pat = re.compile(r'\b' + re.escape(entry) + r'\b', re.I)
                for m in pat.finditer(text):
                    spans.append(_EntitySpan(m.group(), label, m.start(), m.end(), 0.90))
        return spans

    @staticmethod
    def _resolve_overlaps(entities: List[_EntitySpan]) -> List[_EntitySpan]:
        """Remove overlapping spans, keeping the one with highest confidence."""
        entities.sort(key=lambda e: (-e.confidence, e.start))
        used: List[Tuple[int, int]] = []
        kept: List[_EntitySpan] = []
        for ent in entities:
            overlap = any(not (ent.end <= s or ent.start >= e) for s, e in used)
            if not overlap:
                kept.append(ent)
                used.append((ent.start, ent.end))
        kept.sort(key=lambda e: e.start)
        return kept


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_named_entity_recognition: Optional[NamedEntityRecognitionSystem] = None

def get_named_entity_recognition() -> Optional[NamedEntityRecognitionSystem]:
    return _named_entity_recognition

def initialize_named_entity_recognition(data_dir) -> NamedEntityRecognitionSystem:
    global _named_entity_recognition
    _named_entity_recognition = NamedEntityRecognitionSystem(data_dir)
    return _named_entity_recognition
