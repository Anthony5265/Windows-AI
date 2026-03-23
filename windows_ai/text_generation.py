"""
Text Generation module for Windows AI.

Implements an N-gram language model with Markov-chain text generation.
Supports training on arbitrary corpora, temperature-controlled sampling,
configurable N-gram order, and vocabulary tracking.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import logging
import math
import random
import re
import uuid
import collections
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default seed corpus
# ---------------------------------------------------------------------------
_DEFAULT_CORPUS: str = (
    "The quick brown fox jumps over the lazy dog. "
    "Artificial intelligence is transforming the way we interact with technology. "
    "Machine learning models learn patterns from data and make predictions. "
    "Natural language processing enables computers to understand human language. "
    "Deep learning uses neural networks with many layers to learn representations. "
    "The future of technology lies in seamless human computer interaction. "
    "Data science combines statistics and programming to extract insights. "
    "Automation helps businesses improve efficiency and reduce errors. "
    "Cloud computing provides scalable resources for modern applications. "
    "Open source software drives innovation across the technology industry. "
    "The development of intelligent systems requires careful design and testing. "
    "Algorithms process information step by step to solve complex problems. "
    "Software engineering practices ensure reliable and maintainable code. "
    "The advancement of science depends on collaboration and shared knowledge. "
    "Technology companies invest heavily in research and development efforts. "
    "Programming languages provide the tools to build powerful software systems. "
    "Computers process vast amounts of data at incredible speeds today. "
)


def _tokenize_for_lm(text: str) -> List[str]:
    """Tokenise text preserving sentence boundaries as <S> / </S>."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    tokens: List[str] = []
    for sent in sentences:
        words = re.findall(r"[a-zA-Z']+|[.!?,;:]", sent)
        if words:
            tokens.append("<S>")
            tokens.extend(w.lower() for w in words)
            tokens.append("</S>")
    return tokens


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------
@dataclass
class TextGenerationResult:
    result_id: str
    input_text: str
    output_text: str
    confidence: float


# ---------------------------------------------------------------------------
# N-gram Language Model
# ---------------------------------------------------------------------------
class _NgramModel:
    """Variable-order N-gram model with Laplace smoothing."""

    def __init__(self, n: int = 3, smoothing: float = 0.01) -> None:
        self.n = n
        self.smoothing = smoothing
        self.ngrams: Dict[Tuple[str, ...], Dict[str, int]] = collections.defaultdict(
            lambda: collections.defaultdict(int)
        )
        self.vocab: set = set()
        self.total_tokens: int = 0

    def train(self, tokens: List[str]) -> None:
        """Train model on a token sequence."""
        self.vocab.update(tokens)
        self.total_tokens += len(tokens)
        for i in range(len(tokens) - self.n + 1):
            context = tuple(tokens[i : i + self.n - 1])
            target = tokens[i + self.n - 1]
            self.ngrams[context][target] += 1

    def _get_distribution(self, context: Tuple[str, ...]) -> Dict[str, float]:
        """Return smoothed probability distribution for a given context."""
        counts = self.ngrams.get(context, {})
        total = sum(counts.values()) + self.smoothing * len(self.vocab)
        if total == 0:
            uniform = 1.0 / max(len(self.vocab), 1)
            return {w: uniform for w in self.vocab}
        return {
            word: (counts.get(word, 0) + self.smoothing) / total
            for word in self.vocab
        }

    def generate_next(
        self, context: Tuple[str, ...], temperature: float = 1.0
    ) -> Tuple[str, float]:
        """Sample the next token given a context with temperature scaling."""
        dist = self._get_distribution(context)
        if not dist:
            word = random.choice(list(self.vocab)) if self.vocab else "."
            return word, 0.0

        if temperature <= 0.01:
            best = max(dist, key=dist.get)  # type: ignore[arg-type]
            return best, dist[best]

        words = list(dist.keys())
        logits = [math.log(max(p, 1e-12)) / temperature for p in dist.values()]
        max_logit = max(logits)
        exp_logits = [math.exp(l - max_logit) for l in logits]
        total = sum(exp_logits)
        probs = [e / total for e in exp_logits]

        r = random.random()
        cumulative = 0.0
        for word, prob in zip(words, probs):
            cumulative += prob
            if r <= cumulative:
                return word, prob
        return words[-1], probs[-1]

    def sequence_prob(self, tokens: List[str]) -> float:
        """Log-probability of a token sequence under the model."""
        log_prob = 0.0
        for i in range(len(tokens) - self.n + 1):
            context = tuple(tokens[i : i + self.n - 1])
            target = tokens[i + self.n - 1]
            dist = self._get_distribution(context)
            p = dist.get(target, self.smoothing / max(len(self.vocab), 1))
            log_prob += math.log(max(p, 1e-15))
        return log_prob


# ---------------------------------------------------------------------------
# Main system
# ---------------------------------------------------------------------------
class TextGenerationSystem:
    """N-gram Markov-chain text generation system.

    Supports training on arbitrary text, temperature-controlled sampling,
    configurable generation length, and vocabulary statistics.
    """

    def __init__(self, data_dir) -> None:
        self.data_dir = Path(data_dir) if not isinstance(data_dir, Path) else data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[TextGenerationResult] = []
        self._order: int = 3
        self._model = _NgramModel(n=self._order)
        self._temperature: float = 0.8
        self._max_tokens: int = 60
        self._trained: bool = False
        self.train(_DEFAULT_CORPUS)
        logger.info("TextGeneration initialized")

    def train(self, corpus: str) -> None:
        """Train (or continue training) on a text corpus."""
        tokens = _tokenize_for_lm(corpus)
        if len(tokens) < self._order:
            logger.warning("Corpus too short for n=%d model", self._order)
            return
        self._model.train(tokens)
        self._trained = True
        logger.info("Trained on %d tokens, vocab=%d", len(tokens), len(self._model.vocab))

    def set_temperature(self, temperature: float) -> None:
        """Set sampling temperature (0=greedy, >1=creative)."""
        self._temperature = max(0.0, temperature)

    def set_max_tokens(self, n: int) -> None:
        self._max_tokens = max(1, n)

    def get_vocab_size(self) -> int:
        return len(self._model.vocab)

    def process(self, text: str) -> TextGenerationResult:
        """Generate text continuing from the given prompt."""
        if not self._trained:
            self.train(_DEFAULT_CORPUS)

        prompt_tokens = _tokenize_for_lm(text)
        if len(prompt_tokens) < self._order - 1:
            prompt_tokens = ["<S>"] + prompt_tokens

        context = tuple(prompt_tokens[-(self._order - 1) :])

        generated: List[str] = []
        total_prob = 0.0
        for _ in range(self._max_tokens):
            word, prob = self._model.generate_next(context, self._temperature)
            if word == "</S>":
                break
            generated.append(word)
            total_prob += prob
            context = (*context[1:], word)

        output = self._detokenize(generated)
        confidence = round(
            total_prob / max(len(generated), 1), 4
        ) if generated else 0.0
        confidence = min(confidence, 1.0)

        result = TextGenerationResult(
            result_id=str(uuid.uuid4()),
            input_text=text,
            output_text=output,
            confidence=confidence,
        )
        self.results.append(result)
        logger.info("Generated %d tokens (conf=%.4f)", len(generated), confidence)
        return result

    @staticmethod
    def _detokenize(tokens: List[str]) -> str:
        """Join tokens into readable text."""
        if not tokens:
            return ""
        text = tokens[0]
        for tok in tokens[1:]:
            if tok in {".", ",", "!", "?", ";", ":"}:
                text += tok
            else:
                text += " " + tok
        result = re.sub(
            r'(^|[.!?]\s+)([a-z])',
            lambda m: m.group(1) + m.group(2).upper(),
            text,
        )
        return result


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_text_generation: Optional[TextGenerationSystem] = None

def get_text_generation() -> Optional[TextGenerationSystem]:
    return _text_generation

def initialize_text_generation(data_dir) -> TextGenerationSystem:
    global _text_generation
    _text_generation = TextGenerationSystem(data_dir)
    return _text_generation
