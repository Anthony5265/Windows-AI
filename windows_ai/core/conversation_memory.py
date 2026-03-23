"""
Conversation Memory — Multi-session conversation management with context windows,
summarization, entity tracking, and long-term memory.
"""
import logging
import time
import uuid
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class MessageRole(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    FUNCTION = "function"


@dataclass
class Message:
    message_id: str
    role: MessageRole
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    token_count: int = 0
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = {"role": self.role.value, "content": self.content}
        if self.tool_calls:
            d["tool_calls"] = self.tool_calls
        return d


@dataclass
class Entity:
    name: str
    entity_type: str  # person, place, thing, concept, organization
    mentions: int = 1
    last_mentioned: float = field(default_factory=time.time)
    attributes: Dict[str, str] = field(default_factory=dict)
    sentiment: float = 0.0  # -1 to 1


@dataclass
class ConversationSummary:
    summary_id: str
    text: str
    topics: List[str]
    key_points: List[str]
    message_range: Tuple[int, int]  # start, end message indices
    created_at: float = field(default_factory=time.time)


@dataclass
class Conversation:
    conversation_id: str
    title: str = ""
    messages: List[Message] = field(default_factory=list)
    entities: Dict[str, Entity] = field(default_factory=dict)
    summaries: List[ConversationSummary] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    total_tokens: int = 0
    tags: List[str] = field(default_factory=list)

    def add_message(self, role: MessageRole, content: str, **kwargs) -> Message:
        msg = Message(
            message_id=str(uuid.uuid4()),
            role=role, content=content,
            token_count=len(content.split()),  # approximate
            **kwargs
        )
        self.messages.append(msg)
        self.total_tokens += msg.token_count
        self.updated_at = time.time()
        return msg

    def get_context_window(self, max_tokens: int = 4000) -> List[Message]:
        """Get recent messages that fit within token budget."""
        result = []
        tokens = 0
        for msg in reversed(self.messages):
            if tokens + msg.token_count > max_tokens:
                break
            result.insert(0, msg)
            tokens += msg.token_count
        return result


class EntityTracker:
    """Extracts and tracks entities across conversations."""

    PATTERNS = {
        "email": r"[\w.+-]+@[\w-]+\.[\w.]+",
        "url": r"https?://[^\s]+",
        "date": r"\b\d{4}-\d{2}-\d{2}\b",
        "money": r"\$[\d,]+\.?\d*",
        "phone": r"\b\d{3}[-.]\d{3}[-.]\d{4}\b",
    }

    def extract_entities(self, text: str) -> List[Entity]:
        entities = []
        # Pattern-based extraction
        for entity_type, pattern in self.PATTERNS.items():
            matches = re.findall(pattern, text)
            for match in matches:
                entities.append(Entity(name=match, entity_type=entity_type))
        # Capitalized word detection (simple NER)
        words = text.split()
        for i, word in enumerate(words):
            if word[0:1].isupper() and len(word) > 1 and i > 0:
                # Check it's not start of sentence
                prev = words[i-1] if i > 0 else ""
                if prev and not prev.endswith((".", "!", "?")):
                    entities.append(Entity(name=word, entity_type="proper_noun"))
        return entities

    def update_conversation_entities(self, conversation: Conversation, message: Message):
        extracted = self.extract_entities(message.content)
        for entity in extracted:
            if entity.name in conversation.entities:
                conversation.entities[entity.name].mentions += 1
                conversation.entities[entity.name].last_mentioned = time.time()
            else:
                conversation.entities[entity.name] = entity


class ConversationSummarizer:
    """Creates summaries of conversation segments."""

    def summarize(self, messages: List[Message], max_length: int = 200) -> ConversationSummary:
        if not messages:
            return ConversationSummary(
                summary_id=str(uuid.uuid4()), text="Empty conversation",
                topics=[], key_points=[], message_range=(0, 0)
            )
        # Extract key content
        all_text = " ".join(m.content for m in messages)
        words = all_text.split()
        # Extract topics using word frequency
        word_freq = {}
        stop_words = {"the","a","an","is","are","was","were","be","been","being","have","has","had",
                       "do","does","did","will","would","could","should","may","might","shall",
                       "can","need","dare","ought","used","to","of","in","for","on","with","at",
                       "by","from","as","into","through","during","before","after","above","below",
                       "between","out","off","over","under","again","further","then","once","i","me",
                       "my","we","our","you","your","he","she","it","they","them","his","her","its",
                       "this","that","these","those","and","but","or","nor","not","so","very","just"}
        for word in words:
            w = word.lower().strip(".,!?;:")
            if w and len(w) > 2 and w not in stop_words:
                word_freq[w] = word_freq.get(w, 0) + 1
        topics = sorted(word_freq, key=word_freq.get, reverse=True)[:5]
        # Extract key points (sentences with important words)
        sentences = re.split(r'[.!?]+', all_text)
        scored_sentences = []
        for s in sentences:
            s = s.strip()
            if len(s) < 10:
                continue
            score = sum(word_freq.get(w.lower(), 0) for w in s.split())
            scored_sentences.append((score, s))
        scored_sentences.sort(reverse=True)
        key_points = [s for _, s in scored_sentences[:3]]
        # Build summary text
        summary_text = ". ".join(key_points[:2])
        if len(summary_text) > max_length:
            summary_text = summary_text[:max_length-3] + "..."
        return ConversationSummary(
            summary_id=str(uuid.uuid4()), text=summary_text,
            topics=topics, key_points=key_points,
            message_range=(0, len(messages))
        )


class ConversationMemory:
    """Main conversation memory manager."""

    def __init__(self, max_conversations: int = 1000):
        self._conversations: Dict[str, Conversation] = {}
        self._max_conversations = max_conversations
        self.entity_tracker = EntityTracker()
        self.summarizer = ConversationSummarizer()
        self._search_index: Dict[str, List[str]] = {}  # word -> [conversation_ids]
        logger.info("ConversationMemory initialized")

    def create_conversation(self, title: str = "", system_prompt: str = "",
                            tags: List[str] = None) -> Conversation:
        conv = Conversation(
            conversation_id=str(uuid.uuid4()),
            title=title, tags=tags or []
        )
        if system_prompt:
            conv.add_message(MessageRole.SYSTEM, system_prompt)
        self._conversations[conv.conversation_id] = conv
        self._enforce_limit()
        return conv

    def add_message(self, conversation_id: str, role: MessageRole, content: str,
                    **kwargs) -> Optional[Message]:
        conv = self._conversations.get(conversation_id)
        if not conv:
            return None
        msg = conv.add_message(role, content, **kwargs)
        self.entity_tracker.update_conversation_entities(conv, msg)
        self._index_message(conversation_id, content)
        # Auto-summarize when conversation gets long
        if len(conv.messages) % 50 == 0 and len(conv.messages) > 0:
            self._auto_summarize(conv)
        return msg

    def get_context(self, conversation_id: str, max_tokens: int = 4000,
                    include_summary: bool = True) -> List[Dict[str, Any]]:
        conv = self._conversations.get(conversation_id)
        if not conv:
            return []
        messages = conv.get_context_window(max_tokens)
        context = [m.to_dict() for m in messages]
        if include_summary and conv.summaries:
            latest_summary = conv.summaries[-1]
            summary_msg = {"role": "system", "content": f"Previous conversation summary: {latest_summary.text}"}
            context.insert(0, summary_msg)
        return context

    def search_conversations(self, query: str, limit: int = 10) -> List[Conversation]:
        query_words = set(query.lower().split())
        scores: Dict[str, int] = {}
        for word in query_words:
            for conv_id in self._search_index.get(word, []):
                scores[conv_id] = scores.get(conv_id, 0) + 1
        sorted_ids = sorted(scores, key=scores.get, reverse=True)[:limit]
        return [self._conversations[cid] for cid in sorted_ids if cid in self._conversations]

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        return self._conversations.get(conversation_id)

    def list_conversations(self, limit: int = 50) -> List[Dict[str, Any]]:
        convs = sorted(self._conversations.values(), key=lambda c: c.updated_at, reverse=True)
        return [
            {
                "id": c.conversation_id, "title": c.title,
                "messages": len(c.messages), "tokens": c.total_tokens,
                "updated": c.updated_at, "tags": c.tags,
            }
            for c in convs[:limit]
        ]

    def delete_conversation(self, conversation_id: str) -> bool:
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            return True
        return False

    def get_entities(self, conversation_id: str) -> Dict[str, Entity]:
        conv = self._conversations.get(conversation_id)
        return conv.entities if conv else {}

    def _index_message(self, conversation_id: str, content: str):
        words = set(content.lower().split())
        for word in words:
            w = word.strip(".,!?;:")
            if len(w) > 2:
                self._search_index.setdefault(w, [])
                if conversation_id not in self._search_index[w]:
                    self._search_index[w].append(conversation_id)

    def _auto_summarize(self, conversation: Conversation):
        last_summarized = conversation.summaries[-1].message_range[1] if conversation.summaries else 0
        new_messages = conversation.messages[last_summarized:]
        if len(new_messages) >= 20:
            summary = self.summarizer.summarize(new_messages)
            conversation.summaries.append(summary)

    def _enforce_limit(self):
        if len(self._conversations) > self._max_conversations:
            oldest = min(self._conversations.values(), key=lambda c: c.updated_at)
            del self._conversations[oldest.conversation_id]

    def get_stats(self) -> Dict[str, Any]:
        total_msgs = sum(len(c.messages) for c in self._conversations.values())
        total_tokens = sum(c.total_tokens for c in self._conversations.values())
        return {
            "total_conversations": len(self._conversations),
            "total_messages": total_msgs,
            "total_tokens": total_tokens,
            "avg_messages_per_conversation": total_msgs / max(len(self._conversations), 1),
        }


# Global instance
_memory: Optional[ConversationMemory] = None

def get_conversation_memory() -> ConversationMemory:
    global _memory
    if _memory is None:
        _memory = ConversationMemory()
    return _memory
