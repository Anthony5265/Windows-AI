"""
Search Coordinator - Multi-backend search orchestration
Handles parallel searches across multiple backends with result merging and deduplication.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Set
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class SearchBackend(Enum):
    """Available search backends"""
    ELASTICSEARCH = "elasticsearch"
    VECTOR_DB = "vector_db"
    SQL_DATABASE = "sql_database"
    HYBRID = "hybrid"


class LoadBalancingStrategy(Enum):
    """Load balancing strategies for backend selection"""
    ROUND_ROBIN = "round_robin"
    LEAST_LOADED = "least_loaded"
    WEIGHTED = "weighted"
    RANDOM = "random"


@dataclass
class SearchBackendConfig:
    """Configuration for a search backend"""
    name: str
    backend_type: SearchBackend
    endpoint: str
    timeout: int = 30
    weight: float = 1.0
    enabled: bool = True
    retry_count: int = 3


@dataclass
class SearchResult:
    """Single search result"""
    id: str
    title: str
    content: str
    score: float
    source_backend: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class SearchQuery:
    """Parsed search query"""
    query_id: str
    text: str
    filters: Dict[str, Any] = field(default_factory=dict)
    limit: int = 10
    offset: int = 0
    backends: List[str] = field(default_factory=list)
    timeout: int = 30


class SearchCoordinator:
    """
    Multi-backend search coordinator with parallel search orchestration.
    
    Handles orchestrating searches across multiple backends, merging results,
    deduplicating, normalizing scores, and load balancing across backends.
    
    Features:
    - Parallel async searches across multiple backends
    - Intelligent result merging with score aggregation
    - Deduplication with configurable similarity threshold
    - Score normalization to 0-1 range
    - 4 load balancing strategies (round-robin, least-loaded, weighted, random)
    - Backend health tracking and statistics
    - Comprehensive logging and error handling
    
    Example:
        coordinator = SearchCoordinator(config)
        await coordinator.setup()
        results = await coordinator.execute("query text")
        stats = coordinator.get_backend_stats()
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the search coordinator.
        
        Args:
            config: Configuration dictionary with:
                - strategy: LoadBalancingStrategy enum (default: ROUND_ROBIN)
                - max_parallel: Max parallel searches (default: 5)
                - dedup_threshold: Similarity threshold 0-1 (default: 0.85)
                - score_window: Scoring window size (default: 100)
                - backends: List of SearchBackendConfig objects
        """
        self.config = config or {}
        self._initialized = False
        self.strategy = self.config.get("strategy", LoadBalancingStrategy.ROUND_ROBIN)
        self.max_parallel = self.config.get("max_parallel", 5)
        self.dedup_threshold = self.config.get("dedup_threshold", 0.85)
        self.score_window = self.config.get("score_window", 100)
        
        self.backends: Dict[str, SearchBackendConfig] = {}
        self.backend_stats: Dict[str, Dict[str, int]] = {}
        self.backend_health: Dict[str, bool] = {}
        self._current_backend_index = 0
        
        logger.debug(f"SearchCoordinator initialized with strategy={self.strategy.value}")
    
    async def setup(self) -> bool:
        """
        Set up the search coordinator and validate backend configurations.
        
        Returns:
            bool: True if setup successful, False otherwise
        """
        if self._initialized:
            logger.warning("SearchCoordinator already initialized")
            return True
        
        try:
            logger.info("Starting SearchCoordinator setup")
            
            # Initialize backends from config
            backends_config = self.config.get("backends", [])
            for backend_config in backends_config:
                if isinstance(backend_config, dict):
                    backend_config = SearchBackendConfig(**backend_config)
                
                self.backends[backend_config.name] = backend_config
                self.backend_stats[backend_config.name] = {
                    "requests": 0,
                    "successes": 0,
                    "failures": 0
                }
                self.backend_health[backend_config.name] = backend_config.enabled
                
                logger.debug(f"Registered backend: {backend_config.name} ({backend_config.backend_type.value})")
            
            if not self.backends:
                logger.warning("No backends configured, coordinator will have limited functionality")
            
            self._initialized = True
            logger.info(f"SearchCoordinator setup complete with {len(self.backends)} backends")
            return True
            
        except Exception as e:
            logger.error(f"SearchCoordinator setup failed: {e}", exc_info=True)
            self._initialized = False
            return False
    
    async def execute(
        self,
        query_text: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        offset: int = 0,
        backends: Optional[List[str]] = None,
        timeout: int = 30
    ) -> List[SearchResult]:
        """
        Execute a search across configured backends.
        
        Args:
            query_text: The search query text
            filters: Optional filter dictionary
            limit: Maximum results to return (default: 10)
            offset: Result offset for pagination (default: 0)
            backends: List of backend names to search (default: all enabled)
            timeout: Search timeout in seconds (default: 30)
        
        Returns:
            List of SearchResult objects sorted by relevance score
        
        Raises:
            RuntimeError: If coordinator not initialized
            ValueError: If query_text is empty
        """
        if not self._initialized:
            raise RuntimeError("SearchCoordinator not initialized. Call setup() first.")
        
        if not query_text or not query_text.strip():
            raise ValueError("query_text cannot be empty")
        
        try:
            logger.info(f"Executing search: '{query_text}' (limit={limit}, offset={offset})")
            
            # Create search query object
            query = SearchQuery(
                query_id=str(uuid.uuid4()),
                text=query_text.strip(),
                filters=filters or {},
                limit=limit,
                offset=offset,
                backends=backends or list(self.backends.keys()),
                timeout=timeout
            )
            
            # Route query to backends using load balancing strategy
            target_backends = await self._route_query(query)
            logger.debug(f"Routed to backends: {target_backends}")
            
            # Execute parallel searches
            results_by_backend = await self._parallel_search(query, target_backends)
            logger.debug(f"Received results from {len(results_by_backend)} backends")
            
            # Merge and process results
            merged_results = await self._merge_results(results_by_backend, query)
            logger.debug(f"Merged {len(merged_results)} results")
            
            # Deduplicate results
            deduped_results = await self._deduplicate(merged_results)
            logger.debug(f"Deduped to {len(deduped_results)} results (removed {len(merged_results) - len(deduped_results)})")
            
            # Normalize scores to 0-1 range
            normalized_results = await self._normalize_scores(deduped_results)
            
            # Apply offset and limit
            final_results = normalized_results[offset:offset + limit]
            
            logger.info(f"Search complete: {len(final_results)} results returned (from {len(normalized_results)} total)")
            return final_results
            
        except Exception as e:
            logger.error(f"Search execution failed: {e}", exc_info=True)
            raise
    
    async def _route_query(self, query: SearchQuery) -> List[str]:
        """
        Route query to appropriate backends using load balancing strategy.
        
        Args:
            query: SearchQuery object
        
        Returns:
            List of backend names to search
        """
        enabled_backends = [
            name for name, config in self.backends.items()
            if config.enabled and name in query.backends
        ]
        
        if not enabled_backends:
            logger.warning(f"No enabled backends available for query {query.query_id}")
            enabled_backends = list(self.backends.keys())
        
        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            selected = self._route_round_robin(enabled_backends)
        elif self.strategy == LoadBalancingStrategy.LEAST_LOADED:
            selected = self._route_least_loaded(enabled_backends)
        elif self.strategy == LoadBalancingStrategy.WEIGHTED:
            selected = self._route_weighted(enabled_backends)
        else:  # RANDOM
            selected = self._route_random(enabled_backends)
        
        logger.debug(f"Load balancing strategy={self.strategy.value}: selected {len(selected)} backends")
        return selected
    
    def _route_round_robin(self, backends: List[str]) -> List[str]:
        """
        Select backends using round-robin strategy.
        
        Args:
            backends: Available backend names
        
        Returns:
            Selected backend names
        """
        if not backends:
            return []
        
        selected = backends[self._current_backend_index % len(backends)]
        self._current_backend_index += 1
        return [selected]
    
    def _route_least_loaded(self, backends: List[str]) -> List[str]:
        """
        Select backends with least request load.
        
        Args:
            backends: Available backend names
        
        Returns:
            Selected backend name with least load
        """
        if not backends:
            return []
        
        least_loaded = min(
            backends,
            key=lambda b: self.backend_stats[b]["requests"]
        )
        return [least_loaded]
    
    def _route_weighted(self, backends: List[str]) -> List[str]:
        """
        Select backend based on configured weights.
        
        Args:
            backends: Available backend names
        
        Returns:
            Selected backend name
        """
        if not backends:
            return []
        
        # Select backend with highest weight
        selected = max(
            backends,
            key=lambda b: self.backends[b].weight
        )
        return [selected]
    
    def _route_random(self, backends: List[str]) -> List[str]:
        """
        Select backend randomly.
        
        Args:
            backends: Available backend names
        
        Returns:
            Randomly selected backend name
        """
        import random
        if not backends:
            return []
        return [random.choice(backends)]
    
    async def _parallel_search(
        self,
        query: SearchQuery,
        backends: List[str]
    ) -> Dict[str, List[SearchResult]]:
        """
        Execute searches in parallel across backends with timeout handling.
        
        Args:
            query: SearchQuery object
            backends: List of backend names to search
        
        Returns:
            Dictionary mapping backend name to list of SearchResult objects
        """
        logger.debug(f"Starting parallel searches across {len(backends)} backends")
        
        results_by_backend = {}
        tasks = []
        
        for backend_name in backends:
            if backend_name not in self.backends:
                logger.warning(f"Backend {backend_name} not found in configuration")
                continue
            
            # Increment request counter
            self.backend_stats[backend_name]["requests"] += 1
            
            # Create task for this backend search
            task = asyncio.create_task(
                self._search_backend(query, backend_name)
            )
            tasks.append((backend_name, task))
        
        # Wait for all searches with timeout
        for backend_name, task in tasks:
            try:
                logger.debug(f"Waiting for search from {backend_name}")
                results = await asyncio.wait_for(task, timeout=query.timeout)
                results_by_backend[backend_name] = results
                self.backend_stats[backend_name]["successes"] += 1
                logger.debug(f"Received {len(results)} results from {backend_name}")
                
            except asyncio.TimeoutError:
                logger.error(f"Search timeout for backend {backend_name} after {query.timeout}s")
                self.backend_stats[backend_name]["failures"] += 1
                self.backend_health[backend_name] = False
                results_by_backend[backend_name] = []
                
            except Exception as e:
                logger.error(f"Search failed for backend {backend_name}: {e}", exc_info=True)
                self.backend_stats[backend_name]["failures"] += 1
                self.backend_health[backend_name] = False
                results_by_backend[backend_name] = []
        
        logger.debug(f"Parallel searches complete: {sum(len(r) for r in results_by_backend.values())} total results")
        return results_by_backend
    
    async def _search_backend(
        self,
        query: SearchQuery,
        backend_name: str
    ) -> List[SearchResult]:
        """
        Execute search on a specific backend (mock implementation).
        
        Args:
            query: SearchQuery object
            backend_name: Name of backend to search
        
        Returns:
            List of SearchResult objects from backend
        """
        logger.debug(f"Searching backend '{backend_name}' for query: {query.text}")
        
        # Simulate backend search with delay
        await asyncio.sleep(0.1)
        
        # Mock results - in production, would call actual backend
        mock_results = [
            SearchResult(
                id=f"{backend_name}-{i}",
                title=f"Result {i+1} from {backend_name}",
                content=f"Content for query '{query.text}' result {i+1}",
                score=1.0 - (i * 0.1),
                source_backend=backend_name,
                metadata={"rank": i+1, "backend": backend_name}
            )
            for i in range(min(5, query.limit))
        ]
        
        logger.debug(f"Backend {backend_name} returned {len(mock_results)} results")
        return mock_results
    
    async def _merge_results(
        self,
        results_by_backend: Dict[str, List[SearchResult]],
        query: SearchQuery
    ) -> List[SearchResult]:
        """
        Merge results from multiple backends and aggregate scores.
        
        Args:
            results_by_backend: Dictionary of backend results
            query: Original SearchQuery
        
        Returns:
            Merged and sorted list of SearchResult objects
        """
        logger.debug("Merging results from multiple backends")
        
        # Combine all results
        all_results = []
        for backend_name, results in results_by_backend.items():
            all_results.extend(results)
        
        if not all_results:
            logger.debug("No results to merge")
            return []
        
        # Group by result ID and aggregate scores
        result_map: Dict[str, SearchResult] = {}
        for result in all_results:
            if result.id not in result_map:
                result_map[result.id] = result
            else:
                # Aggregate score (average of all backends)
                existing = result_map[result.id]
                existing.score = (existing.score + result.score) / 2
        
        # Sort by score descending
        merged = sorted(result_map.values(), key=lambda r: r.score, reverse=True)
        logger.debug(f"Merged {len(all_results)} raw results to {len(merged)} unique results")
        
        return merged
    
    async def _deduplicate(
        self,
        results: List[SearchResult]
    ) -> List[SearchResult]:
        """
        Remove duplicate results using similarity threshold.
        
        Args:
            results: List of SearchResult objects
        
        Returns:
            Deduplicated list of SearchResult objects
        """
        logger.debug(f"Deduplicating {len(results)} results with threshold={self.dedup_threshold}")
        
        if not results:
            return []
        
        deduped = [results[0]]
        
        for current in results[1:]:
            is_duplicate = False
            
            for kept in deduped:
                similarity = self._calculate_similarity(current.content, kept.content)
                
                if similarity >= self.dedup_threshold:
                    logger.debug(
                        f"Duplicate detected: {current.id} vs {kept.id} "
                        f"(similarity={similarity:.2f})"
                    )
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                deduped.append(current)
        
        logger.debug(f"Deduplicated to {len(deduped)} results (removed {len(results) - len(deduped)})")
        return deduped
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate Jaccard similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
        
        Returns:
            Similarity score between 0 and 1
        """
        # Tokenize texts
        tokens1 = set(text1.lower().split())
        tokens2 = set(text2.lower().split())
        
        if not tokens1 and not tokens2:
            return 1.0
        
        if not tokens1 or not tokens2:
            return 0.0
        
        # Jaccard similarity = intersection / union
        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)
        
        similarity = intersection / union if union > 0 else 0.0
        return similarity
    
    async def _normalize_scores(
        self,
        results: List[SearchResult]
    ) -> List[SearchResult]:
        """
        Normalize scores to 0-1 range using min-max normalization.
        
        Args:
            results: List of SearchResult objects
        
        Returns:
            Results with normalized scores
        """
        logger.debug(f"Normalizing scores for {len(results)} results")
        
        if not results:
            return []
        
        if len(results) == 1:
            results[0].score = 1.0
            return results
        
        # Find min and max scores
        scores = [r.score for r in results]
        min_score = min(scores)
        max_score = max(scores)
        
        # Normalize to 0-1 range
        for result in results:
            if max_score > min_score:
                result.score = (result.score - min_score) / (max_score - min_score)
            else:
                result.score = 1.0
        
        logger.debug(f"Score normalization complete (min={min_score:.2f}, max={max_score:.2f})")
        return results
    
    async def cleanup(self) -> None:
        """
        Clean up resources and reset the coordinator.
        """
        logger.info("SearchCoordinator cleanup starting")
        
        self._initialized = False
        self.backends.clear()
        self.backend_stats.clear()
        self.backend_health.clear()
        
        logger.info("SearchCoordinator cleanup complete")
    
    def get_backend_stats(self) -> Dict[str, Dict[str, int]]:
        """
        Get statistics for all backends.
        
        Returns:
            Dictionary mapping backend name to stats dict with:
                - requests: Total requests sent
                - successes: Successful requests
                - failures: Failed requests
        """
        return {
            name: stats.copy()
            for name, stats in self.backend_stats.items()
        }
    
    def get_health_status(self) -> Dict[str, bool]:
        """
        Get health status for all backends.
        
        Returns:
            Dictionary mapping backend name to health status (bool)
        """
        return {
            name: healthy
            for name, healthy in self.backend_health.items()
        }
            return {
                "status": "error",
                "message": str(e),
                "data": None
            }


def main():
    """Main entry point for standalone execution."""
    system = SearchCoordinator()
    
    if system.setup():
        result = system.execute()
        print(f"Result: {result}")
    else:
        print("Setup failed")


if __name__ == "__main__":
    main()
