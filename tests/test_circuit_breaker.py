"""Tests for circuit breaker pattern and provider failover."""
import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock

from windows_ai.core.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerError,
    CircuitBreakerRegistry,
    CircuitState,
    circuit_breaker,
)
from windows_ai.core.provider_failover import ProviderFailover


class TestCircuitBreaker:
    """Test circuit breaker functionality."""

    def test_initial_state_closed(self):
        """Circuit breaker starts in CLOSED state."""
        cb = CircuitBreaker("test")
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_stays_closed_on_success(self):
        """Circuit stays closed on successful calls."""
        cb = CircuitBreaker("test", failure_threshold=3)
        mock_fn = AsyncMock(return_value="ok")

        result = await cb.call(mock_fn)
        assert result == "ok"
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_opens_after_threshold(self):
        """Circuit opens after failure_threshold consecutive failures."""
        cb = CircuitBreaker("test", failure_threshold=3)
        mock_fn = AsyncMock(side_effect=ConnectionError("failed"))

        for _ in range(3):
            with pytest.raises(ConnectionError):
                await cb.call(mock_fn)

        assert cb.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_rejects_when_open(self):
        """Open circuit rejects calls with CircuitBreakerError."""
        cb = CircuitBreaker("test", failure_threshold=1)
        mock_fn = AsyncMock(side_effect=Exception("fail"))

        with pytest.raises(Exception):
            await cb.call(mock_fn)

        assert cb.state == CircuitState.OPEN

        with pytest.raises(CircuitBreakerError):
            await cb.call(mock_fn)

    @pytest.mark.asyncio
    async def test_transitions_to_half_open(self):
        """Circuit transitions to HALF_OPEN after recovery timeout."""
        cb = CircuitBreaker("test", failure_threshold=1, recovery_timeout=0.1)
        mock_fn = AsyncMock(side_effect=Exception("fail"))

        with pytest.raises(Exception):
            await cb.call(mock_fn)

        assert cb.state == CircuitState.OPEN

        # Wait for recovery timeout
        await asyncio.sleep(0.15)
        assert cb.state == CircuitState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_half_open_success_closes(self):
        """Successful call in HALF_OPEN transitions to CLOSED."""
        cb = CircuitBreaker("test", failure_threshold=1, recovery_timeout=0.1)

        # Trigger failure
        fail_fn = AsyncMock(side_effect=Exception("fail"))
        with pytest.raises(Exception):
            await cb.call(fail_fn)

        await asyncio.sleep(0.15)  # Wait for HALF_OPEN

        # Successful call should close circuit
        success_fn = AsyncMock(return_value="ok")
        result = await cb.call(success_fn)
        assert result == "ok"
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_half_open_failure_reopens(self):
        """Failed call in HALF_OPEN transitions back to OPEN."""
        cb = CircuitBreaker("test", failure_threshold=1, recovery_timeout=0.1)

        fail_fn = AsyncMock(side_effect=Exception("fail"))
        with pytest.raises(Exception):
            await cb.call(fail_fn)

        await asyncio.sleep(0.15)  # Wait for HALF_OPEN

        with pytest.raises(Exception):
            await cb.call(fail_fn)
        assert cb.state == CircuitState.OPEN

    def test_reset(self):
        """Manual reset returns to CLOSED."""
        cb = CircuitBreaker("test")
        cb._state = CircuitState.OPEN
        cb.reset()
        assert cb.state == CircuitState.CLOSED

    def test_stats(self):
        """Stats returns comprehensive info."""
        cb = CircuitBreaker("test")
        stats = cb.stats()
        assert stats["name"] == "test"
        assert stats["state"] == "closed"
        assert "failure_count" in stats
        assert "total_calls" in stats

    @pytest.mark.asyncio
    async def test_sync_function_support(self):
        """Circuit breaker works with sync functions."""
        cb = CircuitBreaker("test")
        mock_fn = MagicMock(return_value="sync_ok")

        result = await cb.call(mock_fn)
        assert result == "sync_ok"


class TestCircuitBreakerRegistry:
    """Test circuit breaker registry."""

    def test_register(self):
        """Can register circuit breakers."""
        registry = CircuitBreakerRegistry()
        cb = registry.register("service1")
        assert cb is not None
        assert cb.name == "service1"

    def test_get(self):
        """Can retrieve registered breakers."""
        registry = CircuitBreakerRegistry()
        registry.register("service1")
        cb = registry.get("service1")
        assert cb is not None
        assert cb.name == "service1"

    def test_get_nonexistent(self):
        """Returns None for unregistered breakers."""
        registry = CircuitBreakerRegistry()
        assert registry.get("nonexistent") is None

    def test_get_or_create(self):
        """get_or_create creates if not exists."""
        registry = CircuitBreakerRegistry()
        cb1 = registry.get_or_create("service1")
        cb2 = registry.get_or_create("service1")
        assert cb1 is cb2  # Same instance

    def test_all_stats(self):
        """all_stats returns stats for all breakers."""
        registry = CircuitBreakerRegistry()
        registry.register("s1")
        registry.register("s2")
        stats = registry.all_stats()
        assert "s1" in stats
        assert "s2" in stats

    def test_reset_all(self):
        """reset_all resets all breakers."""
        registry = CircuitBreakerRegistry()
        cb1 = registry.register("s1")
        cb1._state = CircuitState.OPEN
        registry.reset_all()
        assert cb1.state == CircuitState.CLOSED


class TestProviderFailover:
    """Test provider failover functionality."""

    @pytest.mark.asyncio
    async def test_single_provider_success(self):
        """Single provider succeeds."""
        failover = ProviderFailover()
        mock_fn = AsyncMock(return_value="response")
        failover.add_provider("openai", mock_fn, priority=1)

        result = await failover.call(prompt="hello")
        assert result == "response"

    @pytest.mark.asyncio
    async def test_failover_to_second_provider(self):
        """Falls over to second provider when first fails."""
        failover = ProviderFailover()
        fail_fn = AsyncMock(side_effect=Exception("provider down"))
        success_fn = AsyncMock(return_value="backup response")

        failover.add_provider("openai", fail_fn, priority=1)
        failover.add_provider("anthropic", success_fn, priority=2)

        result = await failover.call(prompt="hello")
        assert result == "backup response"

    @pytest.mark.asyncio
    async def test_all_providers_fail(self):
        """Raises RuntimeError when all providers fail."""
        failover = ProviderFailover()
        fail_fn1 = AsyncMock(side_effect=Exception("fail1"))
        fail_fn2 = AsyncMock(side_effect=Exception("fail2"))

        failover.add_provider("openai", fail_fn1, priority=1)
        failover.add_provider("anthropic", fail_fn2, priority=2)

        with pytest.raises(RuntimeError, match="All providers failed"):
            await failover.call(prompt="hello")

    @pytest.mark.asyncio
    async def test_preferred_provider(self):
        """Preferred provider is tried first."""
        failover = ProviderFailover()
        fn1 = AsyncMock(return_value="openai")
        fn2 = AsyncMock(return_value="anthropic")

        failover.add_provider("openai", fn1, priority=1)
        failover.add_provider("anthropic", fn2, priority=2)

        result = await failover.call(preferred_provider="anthropic")
        assert result == "anthropic"
        fn2.assert_called_once()
        fn1.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_providers_raises(self):
        """Raises RuntimeError when no providers registered."""
        failover = ProviderFailover()
        with pytest.raises(RuntimeError, match="No providers registered"):
            await failover.call()

    def test_provider_status(self):
        """get_provider_status returns status dict."""
        failover = ProviderFailover()
        failover.add_provider("openai", AsyncMock(), priority=1)
        status = failover.get_provider_status()
        assert "openai" in status
        assert status["openai"]["priority"] == 1

    def test_stats(self):
        """stats returns comprehensive info."""
        failover = ProviderFailover()
        failover.add_provider("openai", AsyncMock(), priority=1)
        stats = failover.stats()
        assert stats["total_providers"] == 1
        assert stats["total_failovers"] == 0

    @pytest.mark.asyncio
    async def test_priority_ordering(self):
        """Providers are tried in priority order."""
        failover = ProviderFailover()
        call_order = []

        async def fn1():
            call_order.append("p3")
            raise Exception("fail")

        async def fn2():
            call_order.append("p1")
            return "success"

        async def fn3():
            call_order.append("p2")
            raise Exception("fail")

        failover.add_provider("low", fn1, priority=3)
        failover.add_provider("high", fn2, priority=1)
        failover.add_provider("mid", fn3, priority=2)

        result = await failover.call()
        assert result == "success"
        assert call_order[0] == "p1"  # Highest priority tried first


class TestCircuitBreakerDecorator:
    """Test the @circuit_breaker decorator."""

    @pytest.mark.asyncio
    async def test_decorator_wraps_function(self):
        """Decorator wraps function with circuit breaker."""
        @circuit_breaker("test_decorator", failure_threshold=3)
        async def my_api_call(prompt: str) -> str:
            return f"response to: {prompt}"

        result = await my_api_call("hello")
        assert result == "response to: hello"
        assert hasattr(my_api_call, "circuit_breaker")
