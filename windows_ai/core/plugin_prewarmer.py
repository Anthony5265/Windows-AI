"""Plugin Pre-Warming — Background pre-loading of popular plugins.

Loads frequently-used plugins ahead of time so that first-request latency
is minimized. Pre-warming runs as a background task on server startup.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class PreWarmResult:
    """Result of pre-warming a single plugin."""
    plugin_id: str
    success: bool
    load_time_ms: float = 0.0
    error: Optional[str] = None


@dataclass
class PreWarmStats:
    """Aggregate statistics for a pre-warm cycle."""
    total: int = 0
    succeeded: int = 0
    failed: int = 0
    skipped: int = 0
    total_time_ms: float = 0.0
    results: List[PreWarmResult] = field(default_factory=list)


class PluginPreWarmer:
    """Background plugin pre-loader.

    Usage::

        warmer = PluginPreWarmer(plugin_manager)
        stats = await warmer.warm_popular(top_k=20)
        print(f"Pre-warmed {stats.succeeded}/{stats.total} plugins")
    """

    def __init__(
        self,
        plugin_manager=None,
        max_concurrent: int = 5,
        timeout_seconds: float = 10.0,
    ):
        self._pm = plugin_manager
        self._max_concurrent = max_concurrent
        self._timeout = timeout_seconds
        self._warmed: Set[str] = set()
        self._usage_counts: Dict[str, int] = {}
        self._last_warm_stats: Optional[PreWarmStats] = None
        logger.info("PluginPreWarmer initialized (concurrency=%d, timeout=%.1fs)",
                     max_concurrent, timeout_seconds)

    # ------------------------------------------------------------------
    # Usage tracking
    # ------------------------------------------------------------------

    def record_usage(self, plugin_id: str) -> None:
        """Record that *plugin_id* was used (for popularity ranking)."""
        self._usage_counts[plugin_id] = self._usage_counts.get(plugin_id, 0) + 1

    def get_popular(self, top_k: int = 20) -> List[str]:
        """Return the *top_k* most-used plugin IDs."""
        sorted_ids = sorted(self._usage_counts, key=self._usage_counts.get, reverse=True)
        return sorted_ids[:top_k]

    # ------------------------------------------------------------------
    # Pre-warming
    # ------------------------------------------------------------------

    async def warm_plugin(self, plugin_id: str) -> PreWarmResult:
        """Pre-warm a single plugin by importing/initializing it."""
        if plugin_id in self._warmed:
            return PreWarmResult(plugin_id=plugin_id, success=True, load_time_ms=0.0)

        start = time.perf_counter()
        try:
            if self._pm is not None:
                # Use the real plugin manager's load mechanism
                plugin = self._pm.get_plugin(plugin_id)
                if plugin and hasattr(plugin, "initialize"):
                    if asyncio.iscoroutinefunction(plugin.initialize):
                        await asyncio.wait_for(plugin.initialize(), timeout=self._timeout)
                    else:
                        plugin.initialize()

            elapsed = (time.perf_counter() - start) * 1000
            self._warmed.add(plugin_id)
            logger.debug("Pre-warmed plugin %s in %.1fms", plugin_id, elapsed)
            return PreWarmResult(plugin_id=plugin_id, success=True, load_time_ms=round(elapsed, 2))

        except asyncio.TimeoutError:
            elapsed = (time.perf_counter() - start) * 1000
            logger.warning("Pre-warm timeout for plugin %s", plugin_id)
            return PreWarmResult(plugin_id=plugin_id, success=False,
                                load_time_ms=round(elapsed, 2), error="Timeout")
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            logger.warning("Pre-warm failed for plugin %s: %s", plugin_id, e)
            return PreWarmResult(plugin_id=plugin_id, success=False,
                                load_time_ms=round(elapsed, 2), error=str(e))

    async def warm_popular(self, top_k: int = 20) -> PreWarmStats:
        """Pre-warm the most popular plugins concurrently."""
        plugin_ids = self.get_popular(top_k)
        return await self.warm_plugins(plugin_ids)

    async def warm_plugins(self, plugin_ids: List[str]) -> PreWarmStats:
        """Pre-warm a list of plugins with concurrency control."""
        stats = PreWarmStats(total=len(plugin_ids))
        start = time.perf_counter()

        sem = asyncio.Semaphore(self._max_concurrent)

        async def _warm_one(pid: str):
            async with sem:
                return await self.warm_plugin(pid)

        tasks = [_warm_one(pid) for pid in plugin_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for r in results:
            if isinstance(r, Exception):
                stats.failed += 1
                stats.results.append(PreWarmResult(
                    plugin_id="unknown", success=False, error=str(r),
                ))
            elif isinstance(r, PreWarmResult):
                stats.results.append(r)
                if r.success:
                    stats.succeeded += 1
                else:
                    stats.failed += 1

        stats.total_time_ms = round((time.perf_counter() - start) * 1000, 2)
        self._last_warm_stats = stats
        logger.info("Pre-warm complete: %d/%d succeeded in %.1fms",
                     stats.succeeded, stats.total, stats.total_time_ms)
        return stats

    async def warm_all(self) -> PreWarmStats:
        """Pre-warm every registered plugin (use with caution)."""
        if self._pm is None:
            return PreWarmStats()
        all_ids = []
        if hasattr(self._pm, "list_plugins"):
            for p in self._pm.list_plugins():
                pid = p.get("id") if isinstance(p, dict) else getattr(p, "id", None)
                if pid:
                    all_ids.append(pid)
        return await self.warm_plugins(all_ids)

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def is_warmed(self, plugin_id: str) -> bool:
        return plugin_id in self._warmed

    def get_stats(self) -> Dict[str, Any]:
        """Return pre-warm statistics."""
        return {
            "warmed_count": len(self._warmed),
            "usage_tracked": len(self._usage_counts),
            "last_warm": {
                "total": self._last_warm_stats.total if self._last_warm_stats else 0,
                "succeeded": self._last_warm_stats.succeeded if self._last_warm_stats else 0,
                "failed": self._last_warm_stats.failed if self._last_warm_stats else 0,
                "time_ms": self._last_warm_stats.total_time_ms if self._last_warm_stats else 0,
            },
        }

    def reset(self) -> None:
        """Clear all pre-warm state."""
        self._warmed.clear()
        self._usage_counts.clear()
        self._last_warm_stats = None
