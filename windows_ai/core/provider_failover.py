"""
Automatic Provider Failover

When an AI provider fails, automatically failover to the next available provider.
Integrates with the circuit breaker pattern to detect and avoid failing providers.
"""

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field

from windows_ai.core.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerError,
    CircuitBreakerRegistry,
    get_circuit_breaker_registry,
)

logger = logging.getLogger(__name__)


@dataclass
class ProviderConfig:
    """Configuration for a failover provider."""
    name: str
    priority: int = 0  # Lower = higher priority
    enabled: bool = True
    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class ProviderFailover:
    """
    Manages automatic failover between AI providers.
    
    When a primary provider fails (circuit breaker opens), automatically
    routes requests to the next available provider in priority order.
    
    Usage:
        failover = ProviderFailover()
        failover.add_provider("openai", priority=1, call_fn=call_openai)
        failover.add_provider("anthropic", priority=2, call_fn=call_anthropic)
        failover.add_provider("google", priority=3, call_fn=call_google)
        
        # Automatically tries openai first, then anthropic, then google
        result = await failover.call(prompt="hello")
    """

    def __init__(self):
        self._providers: Dict[str, ProviderConfig] = {}
        self._call_functions: Dict[str, Callable] = {}
        self._registry: CircuitBreakerRegistry = get_circuit_breaker_registry()
        self._total_failovers = 0

    def add_provider(
        self,
        name: str,
        call_fn: Callable,
        priority: int = 0,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        **metadata,
    ):
        """
        Register a provider for failover.
        
        Args:
            name: Provider name (e.g., "openai")
            call_fn: Async callable to invoke the provider
            priority: Lower = higher priority
            failure_threshold: Failures before circuit opens
            recovery_timeout: Seconds before retry after circuit opens
            **metadata: Additional provider metadata
        """
        config = ProviderConfig(
            name=name,
            priority=priority,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            metadata=metadata,
        )
        self._providers[name] = config
        self._call_functions[name] = call_fn
        
        # Register circuit breaker for this provider
        self._registry.get_or_create(
            f"provider:{name}",
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
        )
        
        logger.info(f"Provider '{name}' registered with priority {priority}")

    def remove_provider(self, name: str):
        """Remove a provider from failover."""
        self._providers.pop(name, None)
        self._call_functions.pop(name, None)

    def _get_ordered_providers(self) -> List[str]:
        """Get providers sorted by priority (enabled only)."""
        enabled = [
            (name, cfg)
            for name, cfg in self._providers.items()
            if cfg.enabled
        ]
        enabled.sort(key=lambda x: x[1].priority)
        return [name for name, _ in enabled]

    async def call(
        self,
        *args,
        preferred_provider: Optional[str] = None,
        **kwargs,
    ) -> Any:
        """
        Call a provider with automatic failover.
        
        Tries providers in priority order (or preferred_provider first).
        If a provider's circuit breaker is open, it's skipped.
        If a provider fails, the next one is tried.
        
        Returns the result from the first successful provider.
        Raises the last exception if all providers fail.
        """
        providers = self._get_ordered_providers()
        
        if not providers:
            raise RuntimeError("No providers registered for failover")
        
        # If preferred provider specified, try it first
        if preferred_provider and preferred_provider in providers:
            providers.remove(preferred_provider)
            providers.insert(0, preferred_provider)
        
        last_error = None
        attempted = []
        
        for provider_name in providers:
            call_fn = self._call_functions.get(provider_name)
            if not call_fn:
                continue
            
            breaker = self._registry.get(f"provider:{provider_name}")
            attempted.append(provider_name)
            
            try:
                if breaker:
                    result = await breaker.call(call_fn, *args, **kwargs)
                else:
                    if asyncio.iscoroutinefunction(call_fn):
                        result = await call_fn(*args, **kwargs)
                    else:
                        result = call_fn(*args, **kwargs)
                
                if len(attempted) > 1:
                    self._total_failovers += 1
                    logger.info(
                        f"Failover successful: {' → '.join(attempted)}"
                    )
                
                return result
                
            except CircuitBreakerError:
                logger.debug(
                    f"Provider '{provider_name}' circuit open — skipping"
                )
                continue
                
            except Exception as e:
                last_error = e
                logger.warning(
                    f"Provider '{provider_name}' failed: {e} — trying next"
                )
                continue
        
        # All providers failed
        error_msg = (
            f"All providers failed ({', '.join(attempted)}). "
            f"Last error: {last_error}"
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg) from last_error

    def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all providers including circuit breaker state."""
        status = {}
        for name, config in self._providers.items():
            breaker = self._registry.get(f"provider:{name}")
            status[name] = {
                "priority": config.priority,
                "enabled": config.enabled,
                "circuit_state": breaker.state.value if breaker else "unknown",
                "metadata": config.metadata,
            }
        return status

    def stats(self) -> Dict[str, Any]:
        """Get failover statistics."""
        return {
            "total_providers": len(self._providers),
            "enabled_providers": len(self._get_ordered_providers()),
            "total_failovers": self._total_failovers,
            "provider_status": self.get_provider_status(),
        }
