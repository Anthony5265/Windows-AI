"""
Circuit Breaker Pattern for External API Calls

Prevents cascading failures when external services are unavailable.
Implements the standard circuit breaker states: CLOSED → OPEN → HALF_OPEN.
"""

import asyncio
import logging
import time
from enum import Enum
from typing import Any, Callable, Dict, Optional, TypeVar
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"       # Normal operation — requests pass through
    OPEN = "open"           # Failing — requests rejected immediately
    HALF_OPEN = "half_open" # Testing — limited requests allowed


class CircuitBreakerError(Exception):
    """Raised when circuit is open and request is rejected."""
    pass


class CircuitBreaker:
    """
    Circuit breaker for external API calls.
    
    Usage:
        breaker = CircuitBreaker(name="openai", failure_threshold=5, recovery_timeout=30)
        
        try:
            result = await breaker.call(some_api_function, *args, **kwargs)
        except CircuitBreakerError:
            # Circuit is open — use fallback
            result = fallback_response()
    
    States:
        CLOSED  — Normal. Requests pass through. Failures counted.
                  After `failure_threshold` consecutive failures → OPEN.
        OPEN    — Tripped. All requests rejected with CircuitBreakerError.
                  After `recovery_timeout` seconds → HALF_OPEN.
        HALF_OPEN — Testing. One request allowed through.
                    If it succeeds → CLOSED. If it fails → OPEN.
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        expected_exceptions: tuple = (Exception,),
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exceptions = expected_exceptions
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._last_state_change: float = time.time()
        self._total_calls = 0
        self._total_failures = 0
        self._total_rejections = 0

    @property
    def state(self) -> CircuitState:
        """Get current state, auto-transitioning OPEN → HALF_OPEN if timeout elapsed."""
        if self._state == CircuitState.OPEN:
            if self._last_failure_time and (
                time.time() - self._last_failure_time >= self.recovery_timeout
            ):
                self._transition_to(CircuitState.HALF_OPEN)
        return self._state

    def _transition_to(self, new_state: CircuitState):
        """Transition to a new state."""
        old_state = self._state
        self._state = new_state
        self._last_state_change = time.time()
        logger.info(
            f"Circuit breaker '{self.name}': {old_state.value} → {new_state.value}"
        )

    def _on_success(self):
        """Handle a successful call."""
        self._failure_count = 0
        self._success_count += 1
        if self._state == CircuitState.HALF_OPEN:
            self._transition_to(CircuitState.CLOSED)

    def _on_failure(self):
        """Handle a failed call."""
        self._failure_count += 1
        self._total_failures += 1
        self._last_failure_time = time.time()
        
        if self._state == CircuitState.HALF_OPEN:
            self._transition_to(CircuitState.OPEN)
        elif self._failure_count >= self.failure_threshold:
            self._transition_to(CircuitState.OPEN)

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function through the circuit breaker.
        
        Raises CircuitBreakerError if the circuit is open.
        """
        self._total_calls += 1
        current_state = self.state  # May auto-transition OPEN→HALF_OPEN
        
        if current_state == CircuitState.OPEN:
            self._total_rejections += 1
            raise CircuitBreakerError(
                f"Circuit breaker '{self.name}' is OPEN — service unavailable"
            )
        
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exceptions as e:
            self._on_failure()
            raise

    def reset(self):
        """Manually reset the circuit breaker to CLOSED."""
        self._transition_to(CircuitState.CLOSED)
        self._failure_count = 0

    def stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "total_calls": self._total_calls,
            "total_failures": self._total_failures,
            "total_rejections": self._total_rejections,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
            "last_failure_time": self._last_failure_time,
            "last_state_change": self._last_state_change,
        }


class CircuitBreakerRegistry:
    """
    Registry for managing multiple circuit breakers.
    
    Usage:
        registry = CircuitBreakerRegistry()
        registry.register("openai", failure_threshold=5, recovery_timeout=30)
        registry.register("anthropic", failure_threshold=3, recovery_timeout=60)
        
        breaker = registry.get("openai")
        result = await breaker.call(openai_api_call, prompt="hello")
    """

    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}

    def register(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        expected_exceptions: tuple = (Exception,),
    ) -> CircuitBreaker:
        """Register a new circuit breaker."""
        breaker = CircuitBreaker(
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exceptions=expected_exceptions,
        )
        self._breakers[name] = breaker
        return breaker

    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Get a circuit breaker by name."""
        return self._breakers.get(name)

    def get_or_create(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
    ) -> CircuitBreaker:
        """Get existing or create new circuit breaker."""
        if name not in self._breakers:
            return self.register(name, failure_threshold, recovery_timeout)
        return self._breakers[name]

    def all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get stats for all circuit breakers."""
        return {name: cb.stats() for name, cb in self._breakers.items()}

    def reset_all(self):
        """Reset all circuit breakers to CLOSED."""
        for breaker in self._breakers.values():
            breaker.reset()


# Global registry instance
_registry = CircuitBreakerRegistry()


def get_circuit_breaker_registry() -> CircuitBreakerRegistry:
    """Get the global circuit breaker registry."""
    return _registry


def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 30.0,
):
    """
    Decorator to wrap an async function with a circuit breaker.
    
    Each unique `name` creates one circuit breaker in the global registry.
    If the same name is used on multiple functions, they share a circuit
    breaker (i.e., failures in one affect the other).
    
    Usage:
        @circuit_breaker("openai", failure_threshold=5, recovery_timeout=30)
        async def call_openai(prompt: str) -> str:
            ...
    """
    def decorator(func: Callable):
        breaker = _registry.get_or_create(name, failure_threshold, recovery_timeout)
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await breaker.call(func, *args, **kwargs)
        
        wrapper.circuit_breaker = breaker
        return wrapper
    
    return decorator
