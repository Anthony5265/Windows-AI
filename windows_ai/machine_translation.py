"""
Machine Translation module for Windows AI.

Implements statistical phrase-based translation with:
- Bilingual word/phrase dictionaries (EN-ES, EN-FR)
- Phrase-table lookup with longest-match-first decoding
- Reverse dictionaries for bidirectional translation
- Coverage-based confidence scoring
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
# Built-in bilingual dictionaries
# ---------------------------------------------------------------------------
_EN_ES: Dict[str, str] = {
    "hello": "hola", "goodbye": "adios", "please": "por favor",
    "thank": "gracias", "thanks": "gracias", "you": "tu",
    "yes": "si", "no": "no", "good": "bueno", "bad": "malo",
    "morning": "manana", "night": "noche", "day": "dia",
    "the": "el", "a": "un", "is": "es", "are": "son",
    "i": "yo", "we": "nosotros", "they": "ellos", "he": "el",
    "she": "ella", "it": "eso", "my": "mi", "your": "tu",
    "what": "que", "where": "donde", "when": "cuando",
    "how": "como", "why": "por que", "who": "quien",
    "water": "agua", "food": "comida", "house": "casa",
    "car": "coche", "book": "libro", "dog": "perro", "cat": "gato",
    "big": "grande", "small": "pequeno", "new": "nuevo", "old": "viejo",
    "man": "hombre", "woman": "mujer", "child": "nino",
    "friend": "amigo", "family": "familia", "love": "amor",
    "time": "tiempo", "work": "trabajo", "world": "mundo",
    "name": "nombre", "city": "ciudad", "country": "pais",
    "have": "tener", "want": "querer", "need": "necesitar",
    "can": "poder", "know": "saber", "like": "gustar",
    "go": "ir", "come": "venir", "see": "ver", "eat": "comer",
    "drink": "beber", "speak": "hablar", "write": "escribir",
    "read": "leer", "think": "pensar", "live": "vivir",
    "very": "muy", "with": "con", "without": "sin",
    "today": "hoy", "tomorrow": "manana", "yesterday": "ayer",
    "here": "aqui", "there": "alli", "now": "ahora",
    "this": "esto", "that": "eso", "these": "estos",
    "and": "y", "or": "o", "but": "pero", "not": "no",
    "in": "en", "on": "en", "at": "en", "to": "a", "from": "de",
    "of": "de", "for": "para", "about": "sobre",
}

_EN_FR: Dict[str, str] = {
    "hello": "bonjour", "goodbye": "au revoir", "please": "s'il vous plait",
    "thank": "merci", "thanks": "merci", "you": "vous",
    "yes": "oui", "no": "non", "good": "bon", "bad": "mauvais",
    "morning": "matin", "night": "nuit", "day": "jour",
    "the": "le", "a": "un", "is": "est", "are": "sont",
    "i": "je", "we": "nous", "they": "ils", "he": "il",
    "she": "elle", "it": "il", "my": "mon", "your": "votre",
    "what": "quoi", "where": "ou", "when": "quand",
    "how": "comment", "why": "pourquoi", "who": "qui",
    "water": "eau", "food": "nourriture", "house": "maison",
    "car": "voiture", "book": "livre", "dog": "chien", "cat": "chat",
    "big": "grand", "small": "petit", "new": "nouveau", "old": "vieux",
    "man": "homme", "woman": "femme", "child": "enfant",
    "friend": "ami", "family": "famille", "love": "amour",
    "time": "temps", "work": "travail", "world": "monde",
    "name": "nom", "city": "ville", "country": "pays",
    "have": "avoir", "want": "vouloir", "need": "avoir besoin",
    "can": "pouvoir", "know": "savoir", "like": "aimer",
    "go": "aller", "come": "venir", "see": "voir", "eat": "manger",
    "drink": "boire", "speak": "parler", "write": "ecrire",
    "read": "lire", "think": "penser", "live": "vivre",
    "very": "tres", "with": "avec", "without": "sans",
    "today": "aujourd'hui", "tomorrow": "demain", "yesterday": "hier",
    "here": "ici", "there": "la", "now": "maintenant",
    "this": "ceci", "that": "cela", "these": "ces",
    "and": "et", "or": "ou", "but": "mais", "not": "ne pas",
    "in": "dans", "on": "sur", "at": "a", "to": "a", "from": "de",
    "of": "de", "for": "pour", "about": "sur",
}

# Multi-word phrase tables
_EN_ES_PHRASES: Dict[str, str] = {
    "good morning": "buenos dias", "good night": "buenas noches",
    "how are you": "como estas", "thank you": "gracias",
    "see you later": "hasta luego", "i love you": "te quiero",
    "excuse me": "disculpe", "i am sorry": "lo siento",
    "nice to meet you": "mucho gusto", "of course": "por supuesto",
    "i don't know": "no se", "i don't understand": "no entiendo",
}

_EN_FR_PHRASES: Dict[str, str] = {
    "good morning": "bonjour", "good night": "bonne nuit",
    "how are you": "comment allez-vous", "thank you": "merci beaucoup",
    "see you later": "a plus tard", "i love you": "je t'aime",
    "excuse me": "excusez-moi", "i am sorry": "je suis desole",
    "nice to meet you": "enchante", "of course": "bien sur",
    "i don't know": "je ne sais pas", "i don't understand": "je ne comprends pas",
}


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z']+|[.!?,;:]", text)


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------
@dataclass
class MachineTranslationResult:
    result_id: str
    input_text: str
    output_text: str
    confidence: float


# ---------------------------------------------------------------------------
# Translation engine
# ---------------------------------------------------------------------------
class _TranslationEngine:
    """Phrase-based statistical translation engine."""

    def __init__(
        self,
        word_table: Dict[str, str],
        phrase_table: Dict[str, str],
    ) -> None:
        self.word_table = word_table
        self.phrase_table = phrase_table

    def translate(self, tokens: List[str]) -> Tuple[List[str], float]:
        """Translate tokens using longest-phrase-first matching."""
        lower_tokens = [t.lower() for t in tokens]
        output: List[str] = []
        matched = 0
        total = 0
        i = 0
        while i < len(lower_tokens):
            found_phrase = False
            for length in range(min(5, len(lower_tokens) - i), 1, -1):
                phrase = " ".join(lower_tokens[i : i + length])
                if phrase in self.phrase_table:
                    output.append(self.phrase_table[phrase])
                    matched += length
                    total += length
                    i += length
                    found_phrase = True
                    break
            if not found_phrase:
                word = lower_tokens[i]
                if word in self.word_table:
                    output.append(self.word_table[word])
                    matched += 1
                elif re.match(r'[.!?,;:]', word):
                    output.append(word)
                    matched += 1
                else:
                    output.append(tokens[i])
                total += 1
                i += 1
        coverage = matched / max(total, 1)
        return output, round(coverage, 4)


# ---------------------------------------------------------------------------
# Main system
# ---------------------------------------------------------------------------
class MachineTranslationSystem:
    """Statistical phrase-based translation system.

    Supports EN->ES, EN->FR, ES->EN, FR->EN with bilingual dictionaries,
    phrase-table lookup, and coverage-based confidence scoring.
    """

    LANG_PAIRS: Dict[str, Tuple[Dict[str, str], Dict[str, str]]] = {
        "en-es": (_EN_ES, _EN_ES_PHRASES),
        "en-fr": (_EN_FR, _EN_FR_PHRASES),
    }

    def __init__(self, data_dir) -> None:
        self.data_dir = Path(data_dir) if not isinstance(data_dir, Path) else data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[MachineTranslationResult] = []
        self._target_lang: str = "es"
        self._engines: Dict[str, _TranslationEngine] = {}
        self._build_engines()
        logger.info("MachineTranslation initialized")

    def set_target_language(self, lang: str) -> None:
        """Set the target language code (es, fr)."""
        lang = lang.lower().strip()
        pair = f"en-{lang}"
        if pair not in self._engines and f"{lang}-en" not in self._engines:
            raise ValueError(f"Unsupported language '{lang}'. Choose from: es, fr")
        self._target_lang = lang

    def add_dictionary(
        self, pair: str, words: Dict[str, str],
        phrases: Optional[Dict[str, str]] = None,
    ) -> None:
        """Add or extend a bilingual dictionary."""
        if pair not in self._engines:
            self._engines[pair] = _TranslationEngine(words, phrases or {})
        else:
            self._engines[pair].word_table.update(words)
            if phrases:
                self._engines[pair].phrase_table.update(phrases)
        logger.info("Updated dictionary for %s (%d words)", pair, len(words))

    def process(self, text: str) -> MachineTranslationResult:
        """Translate *text* from English to the current target language."""
        pair = f"en-{self._target_lang}"
        engine = self._engines.get(pair)
        if engine is None:
            engine = self._engines.get(f"{self._target_lang}-en")
        if engine is None:
            return self._build_result(text, text, confidence=0.0)

        tokens = _tokenize(text)
        translated, confidence = engine.translate(tokens)
        output = self._detokenize(translated)

        return self._build_result(text, output, confidence=confidence)

    def translate(
        self, text: str, *, source: str = "en", target: str = "es"
    ) -> MachineTranslationResult:
        """Translate with explicit source/target."""
        old_target = self._target_lang
        self._target_lang = target
        result = self.process(text)
        self._target_lang = old_target
        return result

    def _build_engines(self) -> None:
        for pair, (words, phrases) in self.LANG_PAIRS.items():
            self._engines[pair] = _TranslationEngine(words, phrases)
            rev_pair = "-".join(reversed(pair.split("-")))
            rev_words = {v: k for k, v in words.items()}
            rev_phrases = {v: k for k, v in phrases.items()}
            self._engines[rev_pair] = _TranslationEngine(rev_words, rev_phrases)

    @staticmethod
    def _detokenize(tokens: List[str]) -> str:
        if not tokens:
            return ""
        parts: List[str] = [tokens[0]]
        for tok in tokens[1:]:
            if re.match(r'[.!?,;:]', tok):
                parts.append(tok)
            else:
                parts.append(" " + tok)
        text = "".join(parts)
        text = re.sub(
            r'(^|[.!?]\s+)([a-z])',
            lambda m: m.group(1) + m.group(2).upper(),
            text,
        )
        return text

    def _build_result(
        self, input_text: str, output_text: str, *, confidence: float
    ) -> MachineTranslationResult:
        result = MachineTranslationResult(
            result_id=str(uuid.uuid4()),
            input_text=input_text,
            output_text=output_text,
            confidence=confidence,
        )
        self.results.append(result)
        logger.info("Translated [en->%s] (conf=%.4f)", self._target_lang, confidence)
        return result


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_machine_translation: Optional[MachineTranslationSystem] = None

def get_machine_translation() -> Optional[MachineTranslationSystem]:
    return _machine_translation

def initialize_machine_translation(data_dir) -> MachineTranslationSystem:
    global _machine_translation
    _machine_translation = MachineTranslationSystem(data_dir)
    return _machine_translation
