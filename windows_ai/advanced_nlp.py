"""Advanced natural-language understanding primitives for Windows AI."""
import logging
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


@dataclass
class Intent:
    intent_name: str
    confidence: float
    slots: Dict[str, Any]


@dataclass
class Entity:
    entity_type: str
    value: str
    start: int
    end: int
    confidence: float


@dataclass
class SemanticAnalysis:
    sentiment: str
    sentiment_score: float
    topics: List[str]
    keywords: List[str]
    complexity: float
    formality: float


class AdvancedNLPEngine:
    """Lightweight deterministic NLP layer used when a model is unavailable."""

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.intent_patterns = self._initialize_intent_patterns()
        self.entity_patterns = self._initialize_entity_patterns()
        self.sentiment_lexicon = self._initialize_sentiment_lexicon()
        self.conversation_context: Dict[str, Any] = {}

    def _initialize_intent_patterns(self) -> Dict[str, List[str]]:
        return {
            "open_file": [r"open (the )?file", r"show me", r"display"],
            "save_file": [r"save (the )?file", r"write to"],
            "delete_file": [r"delete", r"remove", r"trash"],
            "copy_file": [r"copy", r"duplicate"],
            "move_file": [r"move", r"relocate"],
            "launch_app": [r"open", r"launch", r"start", r"run"],
            "close_app": [r"close", r"quit", r"exit", r"kill"],
            "switch_app": [r"switch to", r"go to", r"focus on"],
            "shutdown": [r"shutdown", r"power off", r"turn off"],
            "restart": [r"restart", r"reboot"],
            "sleep": [r"sleep", r"suspend", r"hibernate"],
            "lock": [r"lock (the )?screen", r"lock (the )?computer"],
            "search_web": [r"search (for|the web)", r"google", r"look up"],
            "search_files": [r"find (a )?file", r"locate", r"where is"],
            "send_email": [r"send (an )?email", r"email", r"compose"],
            "make_call": [r"call", r"phone", r"dial"],
            "send_message": [r"send (a )?message", r"text", r"sms"],
            "get_weather": [r"weather", r"temperature", r"forecast"],
            "get_time": [r"(what )?time", r"current time", r"what's the time"],
            "get_date": [r"(what )?date", r"today", r"what day"],
            "get_news": [r"news", r"headlines", r"latest"],
            "create_task": [r"create (a )?task", r"add (a )?todo", r"remind me"],
            "list_tasks": [r"(show|list) (my )?tasks", r"what do i need to do"],
            "complete_task": [r"complete", r"finish", r"done with"],
            "schedule_event": [r"schedule", r"create (an )?event", r"add to calendar"],
            "check_calendar": [r"(show|check) (my )?calendar", r"(what|any) meetings"],
            "write_code": [r"write (some )?code", r"implement", r"code"],
            "run_tests": [r"run tests", r"test", r"pytest"],
            "debug": [r"debug", r"fix", r"troubleshoot"],
            "commit_code": [r"commit", r"git commit", r"check in"],
            "explain": [r"explain", r"what is", r"define", r"how does"],
            "tutorial": [r"tutorial", r"how to", r"teach me", r"show me how"],
            "help": [r"help", r"assist", r"support"],
            "change_settings": [r"change settings", r"configure", r"set"],
            "adjust_volume": [r"volume", r"sound", r"audio"],
            "adjust_brightness": [r"brightness", r"screen"],
            "play_music": [r"play", r"music", r"song"],
            "pause_media": [r"pause", r"stop"],
            "next_track": [r"next", r"skip"],
            "previous_track": [r"previous", r"back"],
            "lights_on": [r"(turn )?lights on"],
            "lights_off": [r"(turn )?lights off"],
            "thermostat": [r"thermostat", r"heating"],
            "yes": [r"^yes$", r"^yeah$", r"^yep$", r"^sure$", r"^okay$", r"^ok$"],
            "no": [r"^no$", r"^nope$", r"^nah$"],
            "cancel": [r"cancel", r"nevermind", r"forget it"],
            "thanks": [r"thank", r"thanks", r"appreciate"],
        }

    def _initialize_entity_patterns(self) -> Dict[str, str]:
        return {
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
            "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
            "url": r"https?://[^\s]+",
            "date": r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",
            "time": r"\b\d{1,2}:\d{2}(?:\s?[AP]M)?\b",
            "number": r"\b\d+(?:\.\d+)?\b",
            "percentage": r"\b\d+(?:\.\d+)?%\b",
            "currency": r"\$\d+(?:\.\d{2})?",
            "file_path": r"[A-Za-z]:\\[\w\\. -]+|/[\w/.-]+",
        }

    def _initialize_sentiment_lexicon(self) -> Dict[str, float]:
        return {
            "good": 1.0, "great": 1.5, "excellent": 2.0, "amazing": 2.0,
            "awesome": 1.5, "fantastic": 1.5, "wonderful": 1.5, "perfect": 2.0,
            "love": 1.5, "like": 0.5, "enjoy": 1.0, "happy": 1.0,
            "pleased": 1.0, "satisfied": 1.0, "helpful": 1.0, "useful": 1.0,
            "bad": -1.0, "terrible": -2.0, "awful": -2.0, "horrible": -2.0,
            "poor": -1.0, "disappointing": -1.5, "useless": -1.5, "waste": -1.5,
            "hate": -2.0, "dislike": -1.0, "annoying": -1.0, "frustrating": -1.5,
            "broken": -1.0, "wrong": -0.5, "error": -0.5, "problem": -0.5,
            "fail": -1.5, "failed": -1.5, "slow": -0.5, "crash": -1.5,
        }

    def understand(self, text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        original_text = text.strip()
        if not original_text:
            raise ValueError("text must not be empty")
        if context is not None:
            if not isinstance(context, dict):
                raise TypeError("context must be a dictionary")
            self.conversation_context.update(context)
        normalized = original_text.lower()
        intent = self.recognize_intent(normalized)
        entities = self.extract_entities(original_text)
        semantic = self.semantic_analysis(normalized)
        return {
            "text": original_text,
            "intent": asdict(intent) if intent else None,
            "entities": [asdict(entity) for entity in entities],
            "sentiment": asdict(semantic),
            "semantic": asdict(semantic),
            "context": self.conversation_context.copy(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def recognize_intent(self, text: str) -> Optional[Intent]:
        if not isinstance(text, str) or not text.strip():
            return None
        best = None
        for intent_name, patterns in self.intent_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if not match:
                    continue
                matched = match.group(0)
                span_ratio = len(matched) / max(len(text), 1)
                confidence = min(0.5 + span_ratio * 0.5, 0.99)
                candidate = (confidence, len(matched), intent_name, self._extract_slots(text, intent_name))
                if best is None or candidate[:3] > best[:3]:
                    best = candidate
        if best is None:
            return None
        confidence, _, intent_name, slots = best
        return Intent(intent_name, confidence, slots)

    def _extract_slots(self, text: str, intent: str) -> Dict[str, Any]:
        slots: Dict[str, Any] = {}
        if "app" in intent or "launch" in intent:
            match = re.search(r"\b(?:open|launch|start|run|close|quit)\s+(.+)$", text, re.I)
            if match:
                slots["app_name"] = match.group(1).strip()
        if "file" in intent:
            match = re.search(r"\b(?:file|document)\s+(.+)$", text, re.I)
            if match:
                slots["file_name"] = match.group(1).strip()
        if "search" in intent:
            match = re.search(r"\b(?:search for|search|google|find|look up)\s+(.+)$", text, re.I)
            if match:
                slots["query"] = match.group(1).strip()
        return slots

    def extract_entities(self, text: str) -> List[Entity]:
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        entities: List[Entity] = []
        for entity_type, pattern in self.entity_patterns.items():
            for match in re.finditer(pattern, text):
                entities.append(Entity(entity_type, match.group(), match.start(), match.end(), 0.9))
        return sorted(entities, key=lambda entity: (entity.start, entity.end, entity.entity_type))

    def analyze_sentiment(self, text: str) -> SemanticAnalysis:
        words = re.findall(r"[A-Za-z']+", text.lower())
        scores = [self.sentiment_lexicon[word] for word in words if word in self.sentiment_lexicon]
        score = sum(scores) / len(scores) if scores else 0.0
        sentiment = "positive" if score > 0.3 else "negative" if score < -0.3 else "neutral"
        topics = self._extract_topics(words)
        keywords = self._extract_keywords(words)
        avg_word_length = sum(map(len, words)) / len(words) if words else 0.0
        complexity = min(avg_word_length / 10.0, 1.0)
        formal_words = {"please", "kindly", "would", "could", "sir", "madam"}
        formality = len(set(words) & formal_words) / max(len(words), 1)
        return SemanticAnalysis(sentiment, score, topics, keywords, complexity, formality)

    def semantic_analysis(self, text: str) -> SemanticAnalysis:
        return self.analyze_sentiment(text)

    def _extract_topics(self, words: List[str]) -> List[str]:
        topic_keywords = {
            "technology": ["computer", "software", "code", "program", "app", "tech"],
            "work": ["work", "job", "task", "project", "meeting", "deadline"],
            "communication": ["email", "message", "call", "chat", "talk"],
            "entertainment": ["music", "movie", "game", "play", "fun"],
            "health": ["health", "exercise", "sleep", "diet", "medical"],
        }
        return [topic for topic, keywords in topic_keywords.items() if any(k in words for k in keywords)][:3]

    def _extract_keywords(self, words: List[str]) -> List[str]:
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "is", "was", "are", "be", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should", "may", "might", "can", "i", "you", "he", "she", "it", "we", "they", "my", "your"}
        return list(dict.fromkeys(w for w in words if w not in stop_words and len(w) > 2))[:5]

    def calculate_similarity(self, text1: str, text2: str) -> float:
        if not isinstance(text1, str) or not isinstance(text2, str):
            raise TypeError("texts must be strings")
        words1, words2 = set(text1.lower().split()), set(text2.lower().split())
        union = words1 | words2
        return len(words1 & words2) / len(union) if union else 0.0


_nlp_engine: Optional[AdvancedNLPEngine] = None


def get_nlp_engine(data_dir: Optional[Path] = None) -> AdvancedNLPEngine:
    global _nlp_engine
    if _nlp_engine is None:
        _nlp_engine = AdvancedNLPEngine(data_dir or (Path.home() / ".windows-ai" / "nlp"))
    return _nlp_engine


def initialize_nlp_engine(data_dir: Optional[Path] = None) -> AdvancedNLPEngine:
    engine = get_nlp_engine(data_dir)
    logger.info("Advanced NLP engine initialized")
    return engine
