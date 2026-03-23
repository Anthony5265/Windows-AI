"""Automatic Crash Recovery for Windows AI.

Monitors the health of the application and automatically restarts failed
components. Uses a heartbeat mechanism to detect unresponsive services.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class ComponentStatus(Enum):
    """Health status for a monitored component."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    RECOVERING = "recovering"
    UNKNOWN = "unknown"


@dataclass
class ComponentState:
    """Tracked state of a monitored component."""
    name: str
    status: ComponentStatus = ComponentStatus.UNKNOWN
    last_heartbeat: float = 0.0
    failure_count: int = 0
    recovery_count: int = 0
    last_error: Optional[str] = None
    restart_fn: Optional[Callable] = None


class CrashRecoveryManager:
    """Monitor components and automatically recover from failures.

    Features
    --------
    * **Heartbeat monitoring** — components report heartbeats; if silent
      for longer than the timeout, they are marked failed.
    * **Automatic restart** — registered restart functions are invoked
      when a component fails.
    * **Backoff** — increasing delays between restart attempts.
    * **Recovery limits** — stop retrying after a configurable number
      of consecutive failures.

    Example
    -------
    >>> mgr = CrashRecoveryManager()
    >>> async def restart_api():
    ...     # restart logic
    ...     pass
    >>> mgr.register("api_server", restart_fn=restart_api)
    >>> mgr.heartbeat("api_server")
    """

    def __init__(
        self,
        heartbeat_timeout: float = 30.0,
        max_retries: int = 5,
        base_backoff: float = 2.0,
    ) -> None:
        self.heartbeat_timeout = heartbeat_timeout
        self.max_retries = max_retries
        self.base_backoff = base_backoff

        self._components: Dict[str, ComponentState] = {}
        self._running = False
        self._check_task: Optional[asyncio.Task] = None
        self._history: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(
        self,
        name: str,
        *,
        restart_fn: Optional[Callable] = None,
    ) -> None:
        """Register a component for monitoring."""
        self._components[name] = ComponentState(
            name=name,
            status=ComponentStatus.HEALTHY,
            last_heartbeat=time.time(),
            restart_fn=restart_fn,
        )
        logger.info("Registered component for recovery: %s", name)

    def unregister(self, name: str) -> bool:
        """Unregister a component."""
        return self._components.pop(name, None) is not None

    # ------------------------------------------------------------------
    # Heartbeat
    # ------------------------------------------------------------------

    def heartbeat(self, name: str) -> None:
        """Report that a component is alive."""
        if name in self._components:
            comp = self._components[name]
            comp.last_heartbeat = time.time()
            if comp.status == ComponentStatus.RECOVERING:
                comp.status = ComponentStatus.HEALTHY
                comp.failure_count = 0
                logger.info("Component '%s' recovered successfully", name)
            elif comp.status != ComponentStatus.HEALTHY:
                comp.status = ComponentStatus.HEALTHY

    # ------------------------------------------------------------------
    # Manual reporting
    # ------------------------------------------------------------------

    def report_failure(self, name: str, error: str) -> None:
        """Manually report a component failure."""
        if name not in self._components:
            return
        comp = self._components[name]
        comp.status = ComponentStatus.FAILED
        comp.failure_count += 1
        comp.last_error = error
        self._history.append({
            "event": "failure_reported",
            "component": name,
            "error": error,
            "timestamp": time.time(),
        })
        logger.error("Component '%s' reported failure: %s", name, error)

    # ------------------------------------------------------------------
    # Health checking
    # ------------------------------------------------------------------

    async def check_health(self) -> Dict[str, ComponentStatus]:
        """Check health of all components based on heartbeat freshness."""
        now = time.time()
        statuses: Dict[str, ComponentStatus] = {}

        for name, comp in self._components.items():
            elapsed = now - comp.last_heartbeat
            if comp.status == ComponentStatus.FAILED:
                statuses[name] = ComponentStatus.FAILED
            elif elapsed > self.heartbeat_timeout:
                comp.status = ComponentStatus.FAILED
                comp.failure_count += 1
                comp.last_error = f"Heartbeat timeout ({elapsed:.1f}s)"
                statuses[name] = ComponentStatus.FAILED
                logger.warning(
                    "Component '%s' heartbeat timeout (%.1fs > %.1fs)",
                    name, elapsed, self.heartbeat_timeout,
                )
            elif elapsed > self.heartbeat_timeout * 0.7:
                comp.status = ComponentStatus.DEGRADED
                statuses[name] = ComponentStatus.DEGRADED
            else:
                statuses[name] = comp.status

        return statuses

    async def recover_failed(self) -> Dict[str, bool]:
        """Attempt to recover all failed components.

        Returns a dict mapping component name → success boolean.
        """
        results: Dict[str, bool] = {}

        for name, comp in self._components.items():
            if comp.status != ComponentStatus.FAILED:
                continue

            if comp.failure_count > self.max_retries:
                logger.error(
                    "Component '%s' exceeded max retries (%d), skipping",
                    name, self.max_retries,
                )
                results[name] = False
                continue

            if comp.restart_fn is None:
                logger.warning("No restart function for '%s'", name)
                results[name] = False
                continue

            comp.status = ComponentStatus.RECOVERING
            backoff = self.base_backoff ** min(comp.failure_count, 5)
            logger.info(
                "Recovering '%s' (attempt %d, backoff %.1fs)",
                name, comp.failure_count, backoff,
            )

            try:
                await asyncio.sleep(backoff)
                if asyncio.iscoroutinefunction(comp.restart_fn):
                    await comp.restart_fn()
                else:
                    comp.restart_fn()

                comp.status = ComponentStatus.HEALTHY
                comp.last_heartbeat = time.time()
                comp.recovery_count += 1
                results[name] = True

                self._history.append({
                    "event": "recovery_success",
                    "component": name,
                    "attempt": comp.failure_count,
                    "timestamp": time.time(),
                })
                logger.info("Component '%s' recovered", name)

            except Exception as e:
                comp.status = ComponentStatus.FAILED
                comp.last_error = str(e)
                results[name] = False

                self._history.append({
                    "event": "recovery_failed",
                    "component": name,
                    "error": str(e),
                    "timestamp": time.time(),
                })
                logger.error("Recovery failed for '%s': %s", name, e)

        return results

    # ------------------------------------------------------------------
    # Background monitoring loop
    # ------------------------------------------------------------------

    async def start_monitoring(self, check_interval: float = 10.0) -> None:
        """Start the background health check loop."""
        if self._running:
            return
        self._running = True

        async def _loop():
            while self._running:
                try:
                    statuses = await self.check_health()
                    failed = [n for n, s in statuses.items() if s == ComponentStatus.FAILED]
                    if failed:
                        await self.recover_failed()
                except Exception as e:
                    logger.error("Health check loop error: %s", e)
                await asyncio.sleep(check_interval)

        self._check_task = asyncio.create_task(_loop())
        logger.info("Crash recovery monitoring started (interval=%.1fs)", check_interval)

    async def stop_monitoring(self) -> None:
        """Stop the background monitoring loop."""
        self._running = False
        if self._check_task:
            self._check_task.cancel()
            try:
                await self._check_task
            except asyncio.CancelledError:
                pass
            self._check_task = None
        logger.info("Crash recovery monitoring stopped")

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    @property
    def history(self) -> List[Dict[str, Any]]:
        return list(self._history)

    def stats(self) -> Dict[str, Any]:
        """Return recovery statistics."""
        return {
            "monitored_components": len(self._components),
            "healthy": sum(
                1 for c in self._components.values()
                if c.status == ComponentStatus.HEALTHY
            ),
            "failed": sum(
                1 for c in self._components.values()
                if c.status == ComponentStatus.FAILED
            ),
            "total_recoveries": sum(
                c.recovery_count for c in self._components.values()
            ),
            "history_events": len(self._history),
        }

    def get_component_status(self, name: str) -> Optional[Dict[str, Any]]:
        """Get detailed status for a component."""
        comp = self._components.get(name)
        if comp is None:
            return None
        return {
            "name": comp.name,
            "status": comp.status.value,
            "last_heartbeat": comp.last_heartbeat,
            "failure_count": comp.failure_count,
            "recovery_count": comp.recovery_count,
            "last_error": comp.last_error,
        }
