#!/usr/bin/env python3
"""
Search Orchestrator

Lightweight orchestration layer that wires optimizer, coordinator, analyzer,
profiler, monitoring, and caching into a single async entrypoint.

Created: 2025-11-15
Part of: Windows-AI Roadmap Implementation
"""

import asyncio
import hashlib
import json
import logging
import time
from typing import Any, Dict, List, Optional

from .search_analyzer import SearchAnalyzer
from .search_coordinator import SearchCoordinator, SearchResult
from .search_optimizer import SearchOptimizer
from .search_monitor import SearchMonitor
from .semantic_index.embedding_cache import EmbeddingCache
from .semantic_index.query_profiler import QueryProfiler

logger = logging.getLogger(__name__)


class SearchOrchestrator:
    """Coordinate end-to-end search with optimization, monitoring, and caching."""

    def __init__(
        self,
        coordinator: Optional[SearchCoordinator] = None,
        optimizer: Optional[SearchOptimizer] = None,
        analyzer: Optional[SearchAnalyzer] = None,
        monitor: Optional[SearchMonitor] = None,
        cache: Optional[EmbeddingCache] = None,
        profiler: Optional[QueryProfiler] = None,
        cache_ttl_seconds: int = 900,
        cache_strategy: str = "hybrid",
    ):
        self.coordinator = coordinator or SearchCoordinator()
        self.optimizer = optimizer or SearchOptimizer()
        self.analyzer = analyzer or SearchAnalyzer()
        self.monitor = monitor or SearchMonitor()
        self.cache = cache or EmbeddingCache(ttl_seconds=cache_ttl_seconds, strategy=cache_strategy)
        self.profiler = profiler or QueryProfiler()
        self.initialized = False

    async def setup(self) -> bool:
        """Initialize all sub-systems."""
        if self.initialized:
            logger.warning("SearchOrchestrator already initialized")
            return True

        coord_ok = await self.coordinator.setup()
        opt_ok = self.optimizer.setup()
        analyzer_ok = self.analyzer.setup()
        monitor_ok = await self.monitor.setup()
        cache_ok = self.cache.setup()
        profiler_ok = await self.profiler.initialize()

        self.initialized = all([coord_ok, opt_ok, analyzer_ok, monitor_ok, cache_ok, profiler_ok])
        if not self.initialized:
            logger.error(
                "SearchOrchestrator setup failed",
                extra={
                    "coord_ok": coord_ok,
                    "opt_ok": opt_ok,
                    "analyzer_ok": analyzer_ok,
                    "monitor_ok": monitor_ok,
                    "cache_ok": cache_ok,
                    "profiler_ok": profiler_ok,
                },
            )
        else:
            logger.info("SearchOrchestrator ready")
        return self.initialized

    async def search(
        self,
        query_text: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        offset: int = 0,
        backends: Optional[List[str]] = None,
        timeout: int = 30,
        expected_results: Optional[List[str]] = None,
        persist_cache: bool = False,
    ) -> List[Dict[str, Any]]:
        """Execute a full search flow with optimization, coordination, monitoring, and caching."""
        if not self.initialized:
            raise RuntimeError("SearchOrchestrator not initialized. Call setup() first.")

        filters = filters or {}
        cache_key = self._make_cache_key(query_text, filters)
        start_time = time.perf_counter()

        async with self.profiler.profile_query(query_text, metadata={"filters": filters}) as profile:
            # Cache lookup
            cache_phase = profile.add_phase("cache_lookup", {"key": cache_key})
            cached = self.cache.execute(operation="get", key=cache_key)
            cache_phase.complete()
            if cached.get("status") == "success" and cached.get("data", {}).get("hit"):
                results = cached["data"].get("value") or []
                profile.cache_hit = True
                profile.complete(result_count=len(results))
                latency_ms = (time.perf_counter() - start_time) * 1000
                await self._track_metrics(query_text, results, latency_ms, expected_results)
                return results

            # Optimize query
            optimize_phase = profile.add_phase("optimize_query")
            optimized_query = query_text
            try:
                opt_resp = await self.optimizer.execute(action="optimize_query", query=query_text)
                opt_data = opt_resp.get("data", {}) if isinstance(opt_resp, dict) else {}
                optimized_query = opt_data.get("optimized_query", query_text)
                optimize_phase.metadata.update({"improvement_score": opt_data.get("improvement_score", 0)})
            finally:
                optimize_phase.complete()

            # Coordinate search
            search_phase = profile.add_phase("coordinated_search", {"backends": backends})
            results: List[SearchResult] = await self.coordinator.execute(
                optimized_query,
                filters=filters,
                limit=limit,
                offset=offset,
                backends=backends,
                timeout=timeout,
            )
            search_phase.metadata["results"] = len(results)
            search_phase.complete()

            payload = [self._result_to_dict(r) for r in results]
            latency_ms = (time.perf_counter() - start_time) * 1000

            # Analyzer and monitor hooks best-effort
            analyze_phase = profile.add_phase("analyze")
            try:
                await self.analyzer.execute(
                    action="track_performance",
                    metrics={"latency_ms": latency_ms, "result_count": len(payload)},
                )
            finally:
                analyze_phase.complete()

            monitor_phase = profile.add_phase("monitor")
            try:
                await self.monitor.execute(
                    action="track_query",
                    query=optimized_query,
                    results=payload,
                    latency_ms=latency_ms,
                    expected_results=expected_results,
                )
            finally:
                monitor_phase.complete()

            # Cache results
            cache_set_phase = profile.add_phase("cache_store")
            self.cache.execute(
                operation="set",
                key=cache_key,
                value=payload,
                persist=persist_cache,
            )
            cache_set_phase.complete()

            profile.complete(result_count=len(payload))

        return payload

    async def _track_metrics(
        self,
        query_text: str,
        results: List[Dict[str, Any]],
        latency_ms: float,
        expected_results: Optional[List[str]] = None,
    ) -> None:
        """Track metrics for cache hits and fresh searches without raising."""
        try:
            await self.monitor.execute(
                action="track_query",
                query=query_text,
                results=results,
                latency_ms=latency_ms,
                expected_results=expected_results,
            )
        except Exception as e:
            logger.debug(f"Monitor tracking skipped: {e}")

        try:
            await self.analyzer.execute(
                action="track_performance",
                metrics={"latency_ms": latency_ms, "result_count": len(results)},
            )
        except Exception as e:
            logger.debug(f"Analyzer tracking skipped: {e}")

    def _make_cache_key(self, query_text: str, filters: Dict[str, Any]) -> str:
        serialized = json.dumps({"q": query_text, "f": filters}, sort_keys=True)
        return hashlib.sha1(serialized.encode("utf-8")).hexdigest()

    @staticmethod
    def _result_to_dict(result: SearchResult) -> Dict[str, Any]:
        return {
            "id": result.id,
            "title": result.title,
            "content": result.content,
            "score": result.score,
            "source_backend": result.source_backend,
            "metadata": result.metadata,
            "timestamp": result.timestamp,
        }


async def main():
    orchestrator = SearchOrchestrator()
    await orchestrator.setup()
    results = await orchestrator.search("test query")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
