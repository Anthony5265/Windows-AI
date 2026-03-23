"""
Rate Limiter — Token bucket, sliding window, and fixed window rate limiting.
Supports per-user, per-endpoint, and global rate limits with burst handling.
"""
import logging
import time
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class RateLimitAlgorithm(Enum):
    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"
    LEAKY_BUCKET = "leaky_bucket"


@dataclass
class RateLimitConfig:
    requests_per_second: float = 10.0
    requests_per_minute: float = 600.0
    burst_size: int = 20
    algorithm: RateLimitAlgorithm = RateLimitAlgorithm.TOKEN_BUCKET
    enabled: bool = True


@dataclass
class RateLimitResult:
    allowed: bool
    remaining: int
    limit: int
    reset_at: float
    retry_after: float = 0
    headers: Dict[str, str] = field(default_factory=dict)


class TokenBucket:
    """Token bucket rate limiter."""

    def __init__(self, rate: float, capacity: int):
        self.rate = rate
        self.capacity = capacity
        self.tokens = float(capacity)
        self.last_refill = time.time()
        self._lock = threading.Lock()

    def consume(self, tokens: int = 1) -> Tuple[bool, float]:
        with self._lock:
            now = time.time()
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_refill = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True, self.tokens
            else:
                wait_time = (tokens - self.tokens) / self.rate
                return False, wait_time


class SlidingWindow:
    """Sliding window rate limiter."""

    def __init__(self, max_requests: int, window_seconds: float):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: list = []
        self._lock = threading.Lock()

    def consume(self) -> Tuple[bool, int]:
        with self._lock:
            now = time.time()
            cutoff = now - self.window_seconds
            self._requests = [t for t in self._requests if t > cutoff]

            if len(self._requests) < self.max_requests:
                self._requests.append(now)
                remaining = self.max_requests - len(self._requests)
                return True, remaining
            else:
                return False, 0


class FixedWindow:
    """Fixed window rate limiter."""

    def __init__(self, max_requests: int, window_seconds: float):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._count = 0
        self._window_start = time.time()
        self._lock = threading.Lock()

    def consume(self) -> Tuple[bool, int, float]:
        with self._lock:
            now = time.time()
            if now - self._window_start >= self.window_seconds:
                self._count = 0
                self._window_start = now

            if self._count < self.max_requests:
                self._count += 1
                remaining = self.max_requests - self._count
                reset_at = self._window_start + self.window_seconds
                return True, remaining, reset_at
            else:
                reset_at = self._window_start + self.window_seconds
                return False, 0, reset_at


class LeakyBucket:
    """Leaky bucket rate limiter for smooth output."""

    def __init__(self, rate: float, capacity: int):
        self.rate = rate
        self.capacity = capacity
        self._water = 0.0
        self._last_leak = time.time()
        self._lock = threading.Lock()

    def consume(self, amount: int = 1) -> Tuple[bool, float]:
        with self._lock:
            now = time.time()
            elapsed = now - self._last_leak
            self._water = max(0, self._water - elapsed * self.rate)
            self._last_leak = now

            if self._water + amount <= self.capacity:
                self._water += amount
                return True, self.capacity - self._water
            else:
                overflow = self._water + amount - self.capacity
                wait_time = overflow / self.rate
                return False, wait_time


class RateLimiter:
    """Main rate limiter with per-key tracking."""

    def __init__(self, default_config: RateLimitConfig = None):
        self._config = default_config or RateLimitConfig()
        self._limiters: Dict[str, any] = {}
        self._endpoint_configs: Dict[str, RateLimitConfig] = {}
        self._blocked_keys: set = set()
        self._stats: Dict[str, Dict[str, int]] = {}
        logger.info(f"RateLimiter initialized (algorithm={self._config.algorithm.value})")

    def set_endpoint_config(self, endpoint: str, config: RateLimitConfig):
        self._endpoint_configs[endpoint] = config

    def block_key(self, key: str):
        self._blocked_keys.add(key)

    def unblock_key(self, key: str):
        self._blocked_keys.discard(key)

    def _get_limiter(self, key: str, config: RateLimitConfig):
        if key not in self._limiters:
            if config.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
                self._limiters[key] = TokenBucket(config.requests_per_second, config.burst_size)
            elif config.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
                self._limiters[key] = SlidingWindow(int(config.requests_per_minute), 60.0)
            elif config.algorithm == RateLimitAlgorithm.FIXED_WINDOW:
                self._limiters[key] = FixedWindow(int(config.requests_per_minute), 60.0)
            elif config.algorithm == RateLimitAlgorithm.LEAKY_BUCKET:
                self._limiters[key] = LeakyBucket(config.requests_per_second, config.burst_size)
        return self._limiters[key]

    def check(self, key: str, endpoint: str = "", tokens: int = 1) -> RateLimitResult:
        if not self._config.enabled:
            return RateLimitResult(True, 999, 999, 0)

        if key in self._blocked_keys:
            return RateLimitResult(False, 0, 0, 0, retry_after=3600,
                                    headers={"X-RateLimit-Blocked": "true"})

        config = self._endpoint_configs.get(endpoint, self._config)
        composite_key = f"{key}:{endpoint}" if endpoint else key
        limiter = self._get_limiter(composite_key, config)

        self._stats.setdefault(composite_key, {"allowed": 0, "denied": 0})

        if isinstance(limiter, TokenBucket):
            allowed, remaining = limiter.consume(tokens)
            limit = config.burst_size
            reset_at = time.time() + 1.0 / config.requests_per_second
            retry = 0 if allowed else remaining
        elif isinstance(limiter, SlidingWindow):
            allowed, remaining = limiter.consume()
            limit = int(config.requests_per_minute)
            reset_at = time.time() + 60
            retry = 0 if allowed else 1.0
        elif isinstance(limiter, FixedWindow):
            allowed, remaining, reset_at = limiter.consume()
            limit = int(config.requests_per_minute)
            retry = 0 if allowed else reset_at - time.time()
        else:
            allowed, remaining_or_wait = limiter.consume(tokens)
            limit = config.burst_size
            reset_at = time.time() + 1.0
            retry = 0 if allowed else remaining_or_wait
            remaining = int(remaining_or_wait) if allowed else 0

        if allowed:
            self._stats[composite_key]["allowed"] += 1
        else:
            self._stats[composite_key]["denied"] += 1

        headers = {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(max(0, int(remaining) if isinstance(remaining, (int, float)) else 0)),
            "X-RateLimit-Reset": str(int(reset_at)),
        }
        if not allowed:
            headers["Retry-After"] = str(int(retry) + 1)

        return RateLimitResult(
            allowed=allowed, remaining=max(0, int(remaining) if isinstance(remaining, (int, float)) else 0),
            limit=limit, reset_at=reset_at, retry_after=retry, headers=headers
        )

    def get_stats(self, key: str = None) -> Dict[str, Any]:
        if key:
            return self._stats.get(key, {"allowed": 0, "denied": 0})
        total_allowed = sum(s["allowed"] for s in self._stats.values())
        total_denied = sum(s["denied"] for s in self._stats.values())
        return {
            "total_keys": len(self._stats),
            "total_allowed": total_allowed,
            "total_denied": total_denied,
            "denial_rate": total_denied / (total_allowed + total_denied) if (total_allowed + total_denied) > 0 else 0,
        }

    def cleanup(self, max_age_seconds: float = 3600):
        """Remove stale limiters."""
        now = time.time()
        stale = []
        for key, limiter in self._limiters.items():
            if hasattr(limiter, 'last_refill') and now - limiter.last_refill > max_age_seconds:
                stale.append(key)
            elif hasattr(limiter, '_last_leak') and now - limiter._last_leak > max_age_seconds:
                stale.append(key)
        for key in stale:
            del self._limiters[key]
        logger.debug(f"Cleaned up {len(stale)} stale limiters")


# Global instance
_limiter: Optional[RateLimiter] = None

def get_rate_limiter() -> RateLimiter:
    global _limiter
    if _limiter is None:
        _limiter = RateLimiter()
    return _limiter
