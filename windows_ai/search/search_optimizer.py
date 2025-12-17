#!/usr/bin/env python3
"""
Search Optimizer

Introduce `search/search_optimizer.py` optimizing pipelines to enhance semantic retrieval capabilities.

This module optimizes search pipelines through query rewriting, ranking tuning, caching,
and resource allocation to maximize search performance and relevance.

Created: 2025-11-15
Part of: Windows-AI Roadmap Implementation
"""

import asyncio
import json
import logging
import re
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class SearchOptimizer:
    """
    Optimizes search pipelines to enhance semantic retrieval capabilities.
    
    Provides query optimization, ranking tuning, caching strategies, and resource
    allocation to improve search performance and result quality.
    
    Features:
    - Query optimization and rewriting
    - Ranking algorithm tuning
    - Pipeline performance optimization
    - Result caching and invalidation
    - Query expansion
    - Performance analytics
    
    Usage:
        optimizer = SearchOptimizer(cache_size=10000, query_timeout=30)
        optimizer.setup()
        result = await optimizer.execute(action="optimize_query", query="machine learning")
    """
    
    def __init__(
        self,
        cache_size: int = 10000,
        query_timeout: float = 30.0,
        min_relevance_score: float = 0.5,
        enable_query_expansion: bool = True,
        enable_result_caching: bool = True,
        max_results: int = 100,
        parallel_searches: int = 5,
        log_level: str = "INFO"
    ):
        """
        Initialize the search optimizer.
        
        Args:
            cache_size: Maximum number of cached results
            query_timeout: Query execution timeout in seconds
            min_relevance_score: Minimum relevance score threshold
            enable_query_expansion: Enable query expansion feature
            enable_result_caching: Enable result caching
            max_results: Maximum results per query
            parallel_searches: Maximum parallel search operations
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        self.initialized = False
        self.cache_size = cache_size
        self.query_timeout = query_timeout
        self.min_relevance_score = min_relevance_score
        self.enable_query_expansion = enable_query_expansion
        self.enable_result_caching = enable_result_caching
        self.max_results = max_results
        self.parallel_searches = parallel_searches
        self.log_level = log_level
        
        # Query cache: query_hash -> (results, timestamp, metadata)
        self.query_cache: Dict[str, Tuple[List[Dict], datetime, Dict]] = {}
        
        # Optimization rules: rule_id -> rule_config
        self.optimization_rules: Dict[str, Dict[str, Any]] = {}
        
        # Performance history: metric_name -> values
        self.performance_history: Dict[str, List[float]] = defaultdict(list)
        
        # Ranking algorithms configuration
        self.ranking_algorithms: Dict[str, Dict[str, Any]] = {}
        
        # Query expansion dictionary: term -> expanded_terms
        self.expansion_dict: Dict[str, List[str]] = {}
        
        # Performance baselines
        self.performance_baselines: Dict[str, float] = {}
        
        # Cache statistics
        self.cache_hits = 0
        self.cache_misses = 0
        
        logger.setLevel(getattr(logging, log_level.upper()))
        logger.info(f"Initialized SearchOptimizer with cache_size={cache_size}, timeout={query_timeout}s")
    
    def setup(self) -> bool:
        """
        Set up the search optimizer and prepare for operation.
        
        Returns:
            bool: True if setup successful, False otherwise
        """
        try:
            logger.info("Starting SearchOptimizer setup")
            
            # Load optimization rules
            logger.debug("Loading optimization rules")
            self._load_optimization_rules()
            logger.debug(f"Loaded {len(self.optimization_rules)} optimization rules")
            
            # Initialize query cache
            logger.debug("Initializing query cache")
            self._init_cache()
            
            # Initialize ranking algorithms
            logger.debug("Initializing ranking algorithms")
            self._init_ranking_algorithms()
            logger.debug(f"Initialized {len(self.ranking_algorithms)} ranking algorithms")
            
            # Load performance baselines
            logger.debug("Loading performance baselines")
            self._load_performance_baselines()
            logger.debug(f"Loaded {len(self.performance_baselines)} performance baselines")
            
            # Initialize query expansion dictionary
            if self.enable_query_expansion:
                logger.debug("Initializing query expansion dictionary")
                self._init_expansion_dict()
                logger.debug(f"Loaded {len(self.expansion_dict)} expansion terms")
            
            self.initialized = True
            logger.info("SearchOptimizer setup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"SearchOptimizer setup failed: {e}", exc_info=True)
            return False
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute optimization operations.
        
        Args:
            action: Operation to perform (optimize_query, tune_ranking, optimize_pipeline,
                   cache_results, expand_query, get_optimizations)
            **kwargs: Action-specific parameters
        
        Returns:
            Dict containing:
                - status: "success" or "error"
                - data: Operation results
                - message: Status message
        """
        if not self.initialized:
            raise RuntimeError("SearchOptimizer not initialized. Call setup() first.")
        
        action = kwargs.get("action", "optimize_query")
        
        try:
            logger.debug(f"Executing action: {action}")
            
            if action == "optimize_query":
                result = await self._optimize_query(kwargs)
            elif action == "tune_ranking":
                result = await self._tune_ranking(kwargs)
            elif action == "optimize_pipeline":
                result = await self._optimize_pipeline(kwargs)
            elif action == "cache_results":
                result = await self._cache_results(kwargs)
            elif action == "expand_query":
                result = await self._expand_query(kwargs)
            elif action == "get_optimizations":
                result = await self._get_optimizations(kwargs)
            else:
                logger.warning(f"Unknown action: {action}")
                return {
                    "status": "error",
                    "message": f"Unknown action: {action}",
                    "data": None
                }
            
            logger.info(f"Action {action} completed successfully")
            return {
                "status": "success",
                "message": f"{action} executed successfully",
                "data": result
            }
            
        except Exception as e:
            logger.error(f"Execution failed for action {action}: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "data": None
            }
    
    async def _optimize_query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize a search query."""
        query = params.get("query", "")
        
        if not query:
            logger.warning("Empty query provided for optimization")
            return {"optimized_query": "", "improvements": []}
        
        logger.debug(f"Optimizing query: {query}")
        
        # Check cache first
        if self.enable_result_caching:
            query_hash = hash(query)
            if query_hash in self.query_cache:
                cached_result, timestamp, metadata = self.query_cache[query_hash]
                cache_age = (datetime.now() - timestamp).total_seconds()
                
                if cache_age < 3600:  # 1 hour cache validity
                    self.cache_hits += 1
                    logger.debug(f"Cache hit for query (age: {cache_age:.0f}s)")
                    return {
                        "optimized_query": query,
                        "cached": True,
                        "cache_age": cache_age,
                        "improvements": metadata.get("improvements", [])
                    }
        
        self.cache_misses += 1
        
        # Apply optimization rules
        optimized_query = query
        improvements = []
        
        for rule_id, rule in self.optimization_rules.items():
            result = self._apply_optimization_rule(optimized_query, rule)
            if result["changed"]:
                optimized_query = result["query"]
                improvements.append({
                    "rule": rule_id,
                    "description": rule.get("description", ""),
                    "impact": result.get("impact", "medium")
                })
                logger.debug(f"Applied rule {rule_id}: {rule.get('description', '')}")
        
        # Query expansion if enabled
        if self.enable_query_expansion:
            expanded = self._apply_query_expansion(optimized_query)
            if expanded != optimized_query:
                improvements.append({
                    "rule": "query_expansion",
                    "description": "Expanded query with synonyms and related terms",
                    "impact": "high"
                })
                optimized_query = expanded
        
        # Calculate improvement score
        improvement_score = self._calculate_improvement_score(improvements)
        
        logger.info(f"Query optimization complete: {len(improvements)} improvements, score: {improvement_score:.2f}")
        
        return {
            "optimized_query": optimized_query,
            "original_query": query,
            "improvements": improvements,
            "improvement_score": improvement_score,
            "cached": False
        }
    
    async def _tune_ranking(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Tune ranking algorithm for better results."""
        results = params.get("results", [])
        algorithm = params.get("algorithm", "default")
        
        if not results:
            logger.warning("No results provided for ranking tuning")
            return {"ranked_results": [], "algorithm": algorithm}
        
        logger.debug(f"Tuning ranking with algorithm: {algorithm}")
        
        # Apply relevance scoring
        scored_results = []
        for result in results:
            score = self._calculate_relevance_score(result, algorithm)
            if score >= self.min_relevance_score:
                result["relevance_score"] = score
                scored_results.append(result)
        
        # Sort by relevance score
        ranked_results = sorted(scored_results, key=lambda x: x["relevance_score"], reverse=True)
        
        # Apply result limit
        ranked_results = ranked_results[:self.max_results]
        
        logger.info(f"Ranked {len(ranked_results)} results using {algorithm} algorithm")
        
        return {
            "ranked_results": ranked_results,
            "algorithm": algorithm,
            "total_scored": len(scored_results),
            "filtered_count": len(results) - len(scored_results),
            "avg_score": statistics.mean([r["relevance_score"] for r in ranked_results]) if ranked_results else 0
        }
    
    async def _optimize_pipeline(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize search pipeline performance."""
        pipeline_config = params.get("config", {})
        
        logger.debug("Optimizing search pipeline")
        
        optimizations = []
        
        # Identify bottlenecks
        bottlenecks = self._identify_bottlenecks()
        if bottlenecks:
            optimizations.append({
                "type": "bottleneck_removal",
                "bottlenecks": bottlenecks,
                "priority": "high"
            })
        
        # Suggest parallelization opportunities
        parallel_ops = self._suggest_parallelization()
        if parallel_ops:
            optimizations.append({
                "type": "parallelization",
                "operations": parallel_ops,
                "priority": "medium"
            })
        
        # Resource allocation optimization
        resource_opts = self._optimize_resources()
        if resource_opts:
            optimizations.append({
                "type": "resource_allocation",
                "recommendations": resource_opts,
                "priority": "medium"
            })
        
        logger.info(f"Pipeline optimization complete: {len(optimizations)} recommendations")
        
        return {
            "optimizations": optimizations,
            "total_recommendations": len(optimizations),
            "estimated_improvement": self._estimate_pipeline_improvement(optimizations)
        }
    
    async def _cache_results(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Cache search results."""
        query = params.get("query", "")
        results = params.get("results", [])
        metadata = params.get("metadata", {})
        
        if not query or not results:
            logger.warning("Invalid cache parameters")
            return {"cached": False, "reason": "Invalid parameters"}
        
        query_hash = hash(query)
        
        # Check cache size and evict if necessary
        if len(self.query_cache) >= self.cache_size:
            self._evict_cache_entries()
        
        # Cache the results
        self.query_cache[query_hash] = (results, datetime.now(), metadata)
        
        logger.debug(f"Cached results for query (size: {len(results)})")
        
        return {
            "cached": True,
            "query_hash": str(query_hash),
            "result_count": len(results),
            "cache_size": len(self.query_cache)
        }
    
    async def _expand_query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Expand query with synonyms and related terms."""
        query = params.get("query", "")
        
        if not query or not self.enable_query_expansion:
            return {"expanded_query": query, "expansions": []}
        
        expanded_terms = []
        words = query.lower().split()
        
        for word in words:
            if word in self.expansion_dict:
                expanded_terms.extend(self.expansion_dict[word])
        
        # Build expanded query
        if expanded_terms:
            expanded_query = f"{query} {' '.join(set(expanded_terms))}"
        else:
            expanded_query = query
        
        logger.debug(f"Query expansion: added {len(set(expanded_terms))} terms")
        
        return {
            "expanded_query": expanded_query,
            "original_query": query,
            "expansions": list(set(expanded_terms)),
            "expansion_count": len(set(expanded_terms))
        }
    
    async def _get_optimizations(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get optimization statistics and recommendations."""
        return {
            "cache_stats": {
                "size": len(self.query_cache),
                "max_size": self.cache_size,
                "hits": self.cache_hits,
                "misses": self.cache_misses,
                "hit_rate": self._calculate_cache_hit_rate()
            },
            "performance_stats": {
                "avg_query_time": self._get_avg_query_time(),
                "baselines": self.performance_baselines
            },
            "configuration": {
                "query_timeout": self.query_timeout,
                "min_relevance_score": self.min_relevance_score,
                "max_results": self.max_results,
                "parallel_searches": self.parallel_searches
            },
            "optimization_rules_count": len(self.optimization_rules),
            "ranking_algorithms_count": len(self.ranking_algorithms)
        }
    
    # Helper methods
    
    def _apply_optimization_rule(self, query: str, rule: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a single optimization rule to a query."""
        changed = False
        optimized_query = query
        impact = rule.get("impact", "medium")
        
        rule_type = rule.get("type", "")
        
        if rule_type == "lowercase":
            optimized_query = query.lower()
            changed = optimized_query != query
        elif rule_type == "remove_stopwords":
            stopwords = rule.get("stopwords", [])
            words = query.split()
            filtered = [w for w in words if w.lower() not in stopwords]
            optimized_query = " ".join(filtered)
            changed = optimized_query != query
        elif rule_type == "normalize_whitespace":
            optimized_query = " ".join(query.split())
            changed = optimized_query != query
        
        return {
            "query": optimized_query,
            "changed": changed,
            "impact": impact
        }
    
    def _apply_query_expansion(self, query: str) -> str:
        """Apply query expansion using the expansion dictionary."""
        words = query.lower().split()
        expanded_terms = []
        
        for word in words:
            if word in self.expansion_dict:
                expanded_terms.extend(self.expansion_dict[word][:3])  # Top 3 expansions
        
        if expanded_terms:
            return f"{query} {' '.join(set(expanded_terms))}"
        return query
    
    def _calculate_improvement_score(self, improvements: List[Dict]) -> float:
        """Calculate overall improvement score from individual improvements."""
        if not improvements:
            return 0.0
        
        impact_weights = {"low": 0.3, "medium": 0.6, "high": 1.0}
        total_score = sum(impact_weights.get(imp.get("impact", "medium"), 0.6) for imp in improvements)
        return min(total_score / len(improvements), 1.0)
    
    def _calculate_relevance_score(self, result: Dict[str, Any], algorithm: str) -> float:
        """Calculate relevance score for a search result."""
        base_score = result.get("score", 0.5)
        
        # Apply algorithm-specific adjustments
        algo_config = self.ranking_algorithms.get(algorithm, {})
        
        # Boost for recency
        recency_boost = self._calculate_recency_boost(result, algo_config)
        
        # Boost for popularity
        popularity_boost = self._calculate_popularity_boost(result, algo_config)
        
        # Calculate final score
        final_score = base_score * (1 + recency_boost + popularity_boost)
        return min(final_score, 1.0)
    
    def _calculate_recency_boost(self, result: Dict[str, Any], config: Dict) -> float:
        """Calculate recency boost factor."""
        timestamp = result.get("timestamp")
        if not timestamp:
            return 0.0
        
        recency_weight = config.get("recency_weight", 0.1)
        age_days = (datetime.now() - timestamp).days if isinstance(timestamp, datetime) else 0
        
        if age_days < 7:
            return recency_weight * 1.0
        elif age_days < 30:
            return recency_weight * 0.5
        elif age_days < 90:
            return recency_weight * 0.25
        return 0.0
    
    def _calculate_popularity_boost(self, result: Dict[str, Any], config: Dict) -> float:
        """Calculate popularity boost factor."""
        popularity = result.get("popularity", 0)
        popularity_weight = config.get("popularity_weight", 0.1)
        
        if popularity > 1000:
            return popularity_weight * 1.0
        elif popularity > 100:
            return popularity_weight * 0.5
        elif popularity > 10:
            return popularity_weight * 0.25
        return 0.0
    
    def _identify_bottlenecks(self) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks in the search pipeline."""
        bottlenecks = []
        
        # Check query time
        avg_query_time = self._get_avg_query_time()
        if avg_query_time > self.query_timeout * 0.8:
            bottlenecks.append({
                "type": "slow_queries",
                "metric": "avg_query_time",
                "value": avg_query_time,
                "threshold": self.query_timeout * 0.8,
                "recommendation": "Optimize query execution or increase timeout"
            })
        
        # Check cache hit rate
        hit_rate = self._calculate_cache_hit_rate()
        if hit_rate < 0.5:
            bottlenecks.append({
                "type": "low_cache_hit_rate",
                "metric": "cache_hit_rate",
                "value": hit_rate,
                "threshold": 0.5,
                "recommendation": "Increase cache size or adjust caching strategy"
            })
        
        return bottlenecks
    
    def _suggest_parallelization(self) -> List[Dict[str, Any]]:
        """Suggest operations that can be parallelized."""
        suggestions = []
        
        if self.parallel_searches < 10:
            suggestions.append({
                "operation": "multi_backend_search",
                "current_parallelism": self.parallel_searches,
                "recommended_parallelism": 10,
                "estimated_improvement": "20-30%"
            })
        
        return suggestions
    
    def _optimize_resources(self) -> List[Dict[str, Any]]:
        """Suggest resource allocation optimizations."""
        recommendations = []
        
        # Cache size optimization
        cache_utilization = len(self.query_cache) / self.cache_size if self.cache_size > 0 else 0
        if cache_utilization > 0.9:
            recommendations.append({
                "resource": "cache_size",
                "current": self.cache_size,
                "recommended": self.cache_size * 2,
                "reason": "High cache utilization"
            })
        
        return recommendations
    
    def _estimate_pipeline_improvement(self, optimizations: List[Dict]) -> str:
        """Estimate overall pipeline improvement."""
        if not optimizations:
            return "0%"
        
        high_priority = sum(1 for opt in optimizations if opt.get("priority") == "high")
        medium_priority = sum(1 for opt in optimizations if opt.get("priority") == "medium")
        
        estimated = high_priority * 20 + medium_priority * 10
        return f"{min(estimated, 50)}%"
    
    def _evict_cache_entries(self):
        """Evict oldest cache entries to make room for new ones."""
        if not self.query_cache:
            return
        
        # Sort by timestamp and remove oldest 10%
        sorted_cache = sorted(
            self.query_cache.items(),
            key=lambda x: x[1][1]  # Sort by timestamp
        )
        
        evict_count = max(1, len(sorted_cache) // 10)
        for query_hash, _ in sorted_cache[:evict_count]:
            del self.query_cache[query_hash]
        
        logger.debug(f"Evicted {evict_count} cache entries")
    
    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / total if total > 0 else 0.0
    
    def _get_avg_query_time(self) -> float:
        """Get average query time from performance history."""
        query_times = self.performance_history.get("query_time", [])
        return statistics.mean(query_times) if query_times else 0.0
    
    def _load_optimization_rules(self):
        """Load optimization rules configuration."""
        self.optimization_rules = {
            "lowercase": {
                "type": "lowercase",
                "description": "Convert query to lowercase",
                "impact": "low"
            },
            "remove_stopwords": {
                "type": "remove_stopwords",
                "description": "Remove common stopwords",
                "stopwords": ["the", "a", "an", "and", "or", "but"],
                "impact": "medium"
            },
            "normalize_whitespace": {
                "type": "normalize_whitespace",
                "description": "Normalize whitespace",
                "impact": "low"
            }
        }
    
    def _init_cache(self):
        """Initialize the query cache."""
        self.query_cache.clear()
        self.cache_hits = 0
        self.cache_misses = 0
    
    def _init_ranking_algorithms(self):
        """Initialize ranking algorithm configurations."""
        self.ranking_algorithms = {
            "default": {
                "recency_weight": 0.1,
                "popularity_weight": 0.1
            },
            "recency_focused": {
                "recency_weight": 0.3,
                "popularity_weight": 0.05
            },
            "popularity_focused": {
                "recency_weight": 0.05,
                "popularity_weight": 0.3
            }
        }
    
    def _load_performance_baselines(self):
        """Load performance baseline metrics."""
        self.performance_baselines = {
            "avg_query_time": 1.0,
            "cache_hit_rate": 0.6,
            "result_quality_score": 0.75
        }
    
    def _init_expansion_dict(self):
        """Initialize query expansion dictionary."""
        self.expansion_dict = {
            "ai": ["artificial intelligence", "machine learning", "deep learning"],
            "ml": ["machine learning", "artificial intelligence"],
            "nlp": ["natural language processing", "text processing"],
            "cv": ["computer vision", "image processing"],
            "python": ["programming", "coding", "development"],
            "data": ["dataset", "information", "analytics"]
        }
    
    async def _optimize_query_structure(self, query: str) -> str:
        """
        Optimize query structure for better search performance.
        
        Args:
            query: Original query string
            
        Returns:
            Optimized query string
        """
        try:
            # Remove extra whitespace
            optimized = " ".join(query.split())
            
            # Normalize case for common terms
            optimized = self._normalize_query_case(optimized)
            
            # Remove special characters that don't add value
            optimized = re.sub(r'[^\w\s\-"\']', '', optimized)
            
            # Reorder query terms for better matching
            optimized = await self._reorder_query_terms(optimized)
            
            # Add proximity operators for phrase queries
            if '"' in optimized:
                optimized = self._optimize_phrase_queries(optimized)
            
            logger.debug(f"Optimized query structure: '{query}' -> '{optimized}'")
            return optimized
            
        except Exception as e:
            logger.error(f"Failed to optimize query structure: {e}")
            return query
    
    def _normalize_query_case(self, query: str) -> str:
        """Normalize query case based on term importance."""
        try:
            words = query.split()
            normalized = []
            
            for word in words:
                if word.isupper() and len(word) > 1:
                    normalized.append(word)  # Keep acronyms
                elif word.istitle() and len(word) > 3:
                    normalized.append(word)  # Keep proper nouns
                else:
                    normalized.append(word.lower())
            
            return " ".join(normalized)
            
        except Exception as e:
            logger.error(f"Failed to normalize query case: {e}")
            return query
    
    async def _reorder_query_terms(self, query: str) -> str:
        """Reorder query terms based on importance and selectivity."""
        try:
            words = query.split()
            
            # Calculate term selectivity scores
            scored_terms = []
            for word in words:
                score = await self._calculate_term_selectivity(word)
                scored_terms.append((word, score))
            
            # Sort by selectivity (higher selectivity first)
            scored_terms.sort(key=lambda x: x[1], reverse=True)
            
            # Reconstruct query
            reordered = " ".join([term for term, score in scored_terms])
            
            logger.debug(f"Reordered query terms: '{query}' -> '{reordered}'")
            return reordered
            
        except Exception as e:
            logger.error(f"Failed to reorder query terms: {e}")
            return query
    
    async def _calculate_term_selectivity(self, term: str) -> float:
        """
        Calculate selectivity score for a term.
        Higher score = more selective = better for filtering.
        
        Args:
            term: Query term
            
        Returns:
            Selectivity score (0.0 to 1.0)
        """
        try:
            # Check term frequency in historical queries
            term_freq = self.performance_history.get(f"term_{term.lower()}", {}).get("frequency", 0) if isinstance(self.performance_history.get(f"term_{term.lower()}"), dict) else 0
            
            # Rare terms are more selective
            if term_freq == 0:
                return 0.8  # Unknown term - assume moderately selective
            elif term_freq < 10:
                return 0.9  # Very rare - highly selective
            elif term_freq < 100:
                return 0.7  # Uncommon - moderately selective
            elif term_freq < 1000:
                return 0.5  # Common - less selective
            else:
                return 0.3  # Very common - low selectivity
                
        except Exception as e:
            logger.error(f"Failed to calculate term selectivity: {e}")
            return 0.5
    
    def _optimize_phrase_queries(self, query: str) -> str:
        """Optimize phrase queries with proximity operators."""
        try:
            # Extract phrases in quotes
            phrases = re.findall(r'"([^"]+)"', query)
            
            for phrase in phrases:
                # Add proximity operator for multi-word phrases
                if len(phrase.split()) > 1:
                    # Replace with proximity operator (e.g., NEAR/3)
                    optimized_phrase = f'({phrase.replace(" ", " NEAR/3 ")})'
                    query = query.replace(f'"{phrase}"', optimized_phrase)
            
            return query
            
        except Exception as e:
            logger.error(f"Failed to optimize phrase queries: {e}")
            return query
    
    async def _expand_synonyms(self, query: str) -> str:
        """
        Expand query with synonyms from expansion dictionary.
        
        Args:
            query: Original query
            
        Returns:
            Expanded query with synonyms
        """
        try:
            words = query.split()
            expanded_words = []
            
            for word in words:
                expanded_words.append(word)
                
                # Add synonyms if available
                word_lower = word.lower()
                if word_lower in self.expansion_dict:
                    synonyms = self.expansion_dict[word_lower]
                    # Add top 2 synonyms to avoid query explosion
                    expanded_words.extend(synonyms[:2])
                    
                    logger.debug(f"Expanded '{word}' with synonyms: {synonyms[:2]}")
            
            expanded = " ".join(expanded_words)
            logger.debug(f"Synonym expansion: '{query}' -> '{expanded}'")
            
            return expanded
            
        except Exception as e:
            logger.error(f"Failed to expand synonyms: {e}")
            return query
    
    async def _add_semantic_expansions(self, query: str) -> str:
        """
        Add semantic expansions using contextual understanding.
        
        Args:
            query: Original query
            
        Returns:
            Query with semantic expansions
        """
        try:
            # Detect query intent
            intent = await self._detect_query_intent(query)
            
            # Add intent-specific expansions
            if intent == "navigational":
                expanded = await self._expand_navigational(query)
            elif intent == "informational":
                expanded = await self._expand_informational(query)
            elif intent == "transactional":
                expanded = await self._expand_transactional(query)
            else:
                expanded = query
            
            logger.debug(f"Semantic expansion ({intent}): '{query}' -> '{expanded}'")
            return expanded
            
        except Exception as e:
            logger.error(f"Failed to add semantic expansions: {e}")
            return query
    
    async def _detect_query_intent(self, query: str) -> str:
        """Detect the intent behind a search query."""
        try:
            query_lower = query.lower()
            
            # Navigational intent indicators
            navigational_keywords = ["login", "homepage", "site", "website", "official"]
            if any(kw in query_lower for kw in navigational_keywords):
                return "navigational"
            
            # Transactional intent indicators
            transactional_keywords = ["buy", "purchase", "download", "install", "get", "price"]
            if any(kw in query_lower for kw in transactional_keywords):
                return "transactional"
            
            # Informational intent (default)
            informational_keywords = ["how", "what", "why", "when", "where", "tutorial", "guide"]
            if any(kw in query_lower for kw in informational_keywords):
                return "informational"
            
            return "general"
            
        except Exception as e:
            logger.error(f"Failed to detect query intent: {e}")
            return "general"
    
    async def _expand_navigational(self, query: str) -> str:
        """Expand navigational queries."""
        try:
            expansions = ["home", "main", "official", "site"]
            return f"{query} {' '.join(expansions)}"
        except Exception as e:
            logger.error(f"Failed to expand navigational query: {e}")
            return query
    
    async def _expand_informational(self, query: str) -> str:
        """Expand informational queries."""
        try:
            expansions = ["guide", "tutorial", "documentation", "overview"]
            return f"{query} {' '.join(expansions)}"
        except Exception as e:
            logger.error(f"Failed to expand informational query: {e}")
            return query
    
    async def _expand_transactional(self, query: str) -> str:
        """Expand transactional queries."""
        try:
            expansions = ["download", "install", "setup", "configure"]
            return f"{query} {' '.join(expansions)}"
        except Exception as e:
            logger.error(f"Failed to expand transactional query: {e}")
            return query
    
    async def _optimize_cache_distribution(self):
        """
        Optimize cache distribution based on query patterns.
        
        Analyzes cache hit rates and redistributes cached items
        based on access frequency and recency.
        """
        try:
            logger.debug("Optimizing cache distribution...")
            
            # Calculate cache statistics
            total_entries = len(self.query_cache)
            if total_entries == 0:
                logger.debug("Cache is empty, nothing to optimize")
                return
            
            # Analyze access patterns
            access_patterns = await self._analyze_cache_access_patterns()
            
            # Identify cold cache entries (rarely accessed)
            cold_entries = [
                key for key, pattern in access_patterns.items()
                if pattern["access_count"] < 2 and pattern["age_hours"] > 24
            ]
            
            # Remove cold entries if cache is full
            if total_entries >= self.cache_size * 0.9:  # 90% full
                for key in cold_entries[:len(cold_entries) // 2]:  # Remove half
                    self.query_cache.pop(key, None)
                    logger.debug(f"Evicted cold cache entry: {key}")
            
            # Warm cache with frequent queries
            await self._warm_cache_with_frequent_queries()
            
            logger.info(f"Cache optimization complete: {len(cold_entries)} cold entries processed")
            
        except Exception as e:
            logger.error(f"Failed to optimize cache distribution: {e}", exc_info=True)
    
    async def _analyze_cache_access_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Analyze cache access patterns."""
        try:
            patterns = {}
            current_time = datetime.now()
            
            for key, value in self.query_cache.items():
                # Extract metadata
                timestamp = value[1] if isinstance(value, tuple) and len(value) > 1 else current_time
                access_count = value[2] if isinstance(value, tuple) and len(value) > 2 else 1
                
                # Calculate age
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp)
                age_hours = (current_time - timestamp).total_seconds() / 3600
                
                patterns[key] = {
                    "access_count": access_count,
                    "age_hours": age_hours,
                    "last_access": timestamp
                }
            
            return patterns
            
        except Exception as e:
            logger.error(f"Failed to analyze cache access patterns: {e}")
            return {}
    
    async def _warm_cache_with_frequent_queries(self):
        """Pre-populate cache with frequently executed queries."""
        try:
            # Get most frequent queries from performance history
            frequent_queries = self._get_frequent_queries(limit=100)
            
            warmed_count = 0
            for query_data in frequent_queries:
                query = query_data.get("query", "")
                
                # Check if already cached
                cache_key = self._get_cache_key(query)
                if cache_key not in self.query_cache:
                    # Pre-cache the query
                    self.query_cache[cache_key] = (
                        query,
                        datetime.now(),
                        0,
                        True  # warmed flag
                    )
                    warmed_count += 1
            
            logger.info(f"Cache warming complete: {warmed_count} queries pre-cached")
            
        except Exception as e:
            logger.error(f"Failed to warm cache: {e}")
    
    def _get_frequent_queries(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get most frequently executed queries."""
        try:
            query_freqs = []
            
            for key, value in self.performance_history.items():
                if key.startswith("query_"):
                    query = key.replace("query_", "")
                    frequency = value.get("frequency", 0) if isinstance(value, dict) else 0
                    query_freqs.append({
                        "query": query,
                        "frequency": frequency
                    })
            
            # Sort by frequency and return top N
            query_freqs.sort(key=lambda x: x["frequency"], reverse=True)
            return query_freqs[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get frequent queries: {e}")
            return []
    
    async def _analyze_ab_test_results(self, test_id: str) -> Dict[str, Any]:
        """
        Analyze A/B test results for ranking algorithm comparison.
        
        Args:
            test_id: A/B test identifier
            
        Returns:
            Analysis results with statistical significance
        """
        try:
            logger.debug(f"Analyzing A/B test: {test_id}")
            
            # Retrieve test data
            test_data = self.performance_history.get(f"ab_test_{test_id}", {})
            
            if not test_data:
                logger.warning(f"No data found for A/B test: {test_id}")
                return {"error": "Test not found"}
            
            variant_a = test_data.get("variant_a", {})
            variant_b = test_data.get("variant_b", {})
            
            # Calculate metrics for both variants
            metrics_a = self._calculate_variant_metrics(variant_a)
            metrics_b = self._calculate_variant_metrics(variant_b)
            
            # Determine statistical significance
            significance = self._calculate_statistical_significance(metrics_a, metrics_b)
            
            # Determine winner
            winner = self._determine_ab_winner(metrics_a, metrics_b, significance)
            
            result = {
                "test_id": test_id,
                "variant_a": metrics_a,
                "variant_b": metrics_b,
                "winner": winner,
                "statistical_significance": significance,
                "recommendation": self._generate_ab_recommendation(winner, significance)
            }
            
            logger.info(f"A/B test analysis complete: {test_id} winner={winner}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to analyze A/B test results: {e}", exc_info=True)
            return {"error": str(e)}
    
    def _calculate_variant_metrics(self, variant_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate metrics for an A/B test variant."""
        try:
            metrics = {
                "queries": len(variant_data.get("queries", [])),
                "avg_latency": statistics.mean(variant_data.get("latencies", [1.0])),
                "avg_relevance": statistics.mean(variant_data.get("relevance_scores", [0.5])),
                "click_through_rate": variant_data.get("clicks", 0) / max(variant_data.get("impressions", 1), 1),
                "conversion_rate": variant_data.get("conversions", 0) / max(variant_data.get("clicks", 1), 1)
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to calculate variant metrics: {e}")
            return {}
    
    def _calculate_statistical_significance(
        self,
        metrics_a: Dict[str, float],
        metrics_b: Dict[str, float]
    ) -> Dict[str, Any]:
        """Calculate statistical significance between variants."""
        try:
            # Simple z-test for proportions (click-through rate)
            ctr_a = metrics_a.get("click_through_rate", 0)
            ctr_b = metrics_b.get("click_through_rate", 0)
            n_a = metrics_a.get("queries", 0)
            n_b = metrics_b.get("queries", 0)
            
            # Calculate pooled proportion
            pooled = ((ctr_a * n_a) + (ctr_b * n_b)) / max((n_a + n_b), 1)
            
            # Calculate standard error
            se = ((pooled * (1 - pooled)) * ((1 / max(n_a, 1)) + (1 / max(n_b, 1)))) ** 0.5
            
            # Calculate z-score
            z_score = abs(ctr_a - ctr_b) / max(se, 0.001)
            
            # Determine p-value (simplified)
            p_value = 0.05 if z_score > 1.96 else 0.10  # Simplified calculation
            
            return {
                "z_score": z_score,
                "p_value": p_value,
                "is_significant": z_score > 1.96,  # 95% confidence
                "confidence_level": 0.95 if z_score > 1.96 else 0.90
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate statistical significance: {e}")
            return {"is_significant": False}
    
    def _determine_ab_winner(
        self,
        metrics_a: Dict[str, float],
        metrics_b: Dict[str, float],
        significance: Dict[str, Any]
    ) -> str:
        """Determine the winner of an A/B test."""
        try:
            if not significance.get("is_significant", False):
                return "inconclusive"
            
            # Compare key metrics
            score_a = (
                metrics_a.get("avg_relevance", 0) * 0.4 +
                metrics_a.get("click_through_rate", 0) * 0.4 +
                (1.0 / max(metrics_a.get("avg_latency", 1.0), 0.1)) * 0.2
            )
            
            score_b = (
                metrics_b.get("avg_relevance", 0) * 0.4 +
                metrics_b.get("click_through_rate", 0) * 0.4 +
                (1.0 / max(metrics_b.get("avg_latency", 1.0), 0.1)) * 0.2
            )
            
            return "variant_a" if score_a > score_b else "variant_b"
            
        except Exception as e:
            logger.error(f"Failed to determine A/B winner: {e}")
            return "error"
    
    def _generate_ab_recommendation(self, winner: str, significance: Dict[str, Any]) -> str:
        """Generate recommendation based on A/B test results."""
        if winner == "inconclusive":
            return "Continue test to gather more data for statistical significance"
        elif winner == "error":
            return "Test analysis encountered errors, review test configuration"
        elif significance.get("is_significant", False):
            return f"Deploy {winner} - statistically significant improvement detected"
        else:
            return f"{winner} shows improvement but lacks statistical significance - consider longer test duration"
    
    async def _configure_load_balancing(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Configure load balancing for distributed search backends.
        
        Args:
            config: Load balancing configuration
            
        Returns:
            Configuration result
        """
        try:
            strategy = config.get("strategy", "round_robin")
            backends = config.get("backends", [])
            
            logger.info(f"Configuring load balancing: strategy={strategy}, backends={len(backends)}")
            
            # Validate strategy
            valid_strategies = ["round_robin", "least_connections", "weighted", "latency_based"]
            if strategy not in valid_strategies:
                raise ValueError(f"Invalid strategy: {strategy}. Must be one of {valid_strategies}")
            
            # Initialize load balancer state
            lb_state = {
                "strategy": strategy,
                "backends": backends,
                "current_index": 0,
                "connection_counts": {backend: 0 for backend in backends},
                "latencies": {backend: [] for backend in backends},
                "weights": config.get("weights", {backend: 1.0 for backend in backends})
            }
            
            # Store in performance history
            self.performance_history["load_balancer"] = lb_state
            
            logger.info(f"Load balancing configured successfully")
            
            return {
                "status": "configured",
                "strategy": strategy,
                "backend_count": len(backends),
                "config": lb_state
            }
            
        except Exception as e:
            logger.error(f"Failed to configure load balancing: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}
    
    async def _select_backend(self) -> Optional[str]:
        """Select a backend using the configured load balancing strategy."""
        try:
            lb_config = self.performance_history.get("load_balancer", {})
            
            if not lb_config:
                logger.warning("Load balancer not configured")
                return None
            
            strategy = lb_config.get("strategy", "round_robin")
            backends = lb_config.get("backends", [])
            
            if not backends:
                return None
            
            if strategy == "round_robin":
                selected = await self._round_robin_select(lb_config)
            elif strategy == "least_connections":
                selected = await self._least_connections_select(lb_config)
            elif strategy == "weighted":
                selected = await self._weighted_select(lb_config)
            elif strategy == "latency_based":
                selected = await self._latency_based_select(lb_config)
            else:
                selected = backends[0]
            
            logger.debug(f"Selected backend: {selected} (strategy={strategy})")
            return selected
            
        except Exception as e:
            logger.error(f"Failed to select backend: {e}")
            return None
    
    async def _round_robin_select(self, config: Dict[str, Any]) -> str:
        """Round-robin backend selection."""
        backends = config.get("backends", [])
        current_index = config.get("current_index", 0)
        
        selected = backends[current_index % len(backends)]
        config["current_index"] = (current_index + 1) % len(backends)
        
        return selected
    
    async def _least_connections_select(self, config: Dict[str, Any]) -> str:
        """Least connections backend selection."""
        connection_counts = config.get("connection_counts", {})
        
        # Select backend with fewest connections
        selected = min(connection_counts.items(), key=lambda x: x[1])[0]
        connection_counts[selected] += 1
        
        return selected
    
    async def _weighted_select(self, config: Dict[str, Any]) -> str:
        """Weighted backend selection."""
        import random
        
        backends = config.get("backends", [])
        weights = config.get("weights", {})
        
        # Use weights to select backend
        total_weight = sum(weights.get(b, 1.0) for b in backends)
        r = random.uniform(0, total_weight)
        
        cumsum = 0
        for backend in backends:
            cumsum += weights.get(backend, 1.0)
            if r <= cumsum:
                return backend
        
        return backends[0]
    
    async def _latency_based_select(self, config: Dict[str, Any]) -> str:
        """Latency-based backend selection."""
        latencies = config.get("latencies", {})
        
        # Calculate average latencies
        avg_latencies = {}
        for backend, lats in latencies.items():
            avg_latencies[backend] = statistics.mean(lats) if lats else float('inf')
        
        # Select backend with lowest latency
        selected = min(avg_latencies.items(), key=lambda x: x[1])[0]
        
        return selected
    
    async def _recommend_index_optimizations(
        self,
        query_patterns: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Recommend index optimizations based on query patterns.
        
        Args:
            query_patterns: List of query patterns to analyze
            
        Returns:
            Dictionary of index optimization recommendations
        """
        try:
            logger.info("Analyzing query patterns for index optimization...")
            
            recommendations = {
                "new_indexes": [],
                "composite_indexes": [],
                "remove_indexes": [],
                "rebuild_indexes": []
            }
            
            # Analyze field access patterns
            field_usage = await self._analyze_field_usage(query_patterns)
            
            # Recommend new single-field indexes
            for field, stats in field_usage.items():
                if stats["access_count"] > 100 and not stats["is_indexed"]:
                    recommendations["new_indexes"].append({
                        "field": field,
                        "type": "btree",
                        "reason": f"High access count ({stats['access_count']})",
                        "priority": "high" if stats["access_count"] > 1000 else "medium",
                        "estimated_improvement": self._estimate_index_improvement(stats)
                    })
            
            # Recommend composite indexes
            field_combinations = await self._analyze_field_combinations(query_patterns)
            for combo, stats in field_combinations.items():
                if stats["frequency"] > 50:
                    recommendations["composite_indexes"].append({
                        "fields": list(combo),
                        "order": stats["optimal_order"],
                        "reason": f"Frequent combination ({stats['frequency']} queries)",
                        "priority": "high" if stats["frequency"] > 200 else "medium",
                        "estimated_improvement": stats.get("estimated_improvement", "20%")
                    })
            
            # Identify unused indexes for removal
            unused_indexes = await self._identify_unused_indexes()
            recommendations["remove_indexes"].extend(unused_indexes)
            
            # Identify fragmented indexes for rebuild
            fragmented_indexes = await self._identify_fragmented_indexes()
            recommendations["rebuild_indexes"].extend(fragmented_indexes)
            
            logger.info(f"Index optimization analysis complete: {sum(len(v) for v in recommendations.values())} recommendations")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to recommend index optimizations: {e}", exc_info=True)
            return {
                "new_indexes": [],
                "composite_indexes": [],
                "remove_indexes": [],
                "rebuild_indexes": []
            }
    
    async def _analyze_field_usage(
        self,
        query_patterns: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """Analyze field usage patterns from queries."""
        try:
            field_stats = defaultdict(lambda: {
                "access_count": 0,
                "filter_count": 0,
                "sort_count": 0,
                "is_indexed": False,
                "avg_selectivity": 0.0
            })
            
            for pattern in query_patterns:
                query = pattern.get("query", {})
                
                # Analyze filters
                filters = query.get("filters", {})
                for field in filters.keys():
                    field_stats[field]["access_count"] += 1
                    field_stats[field]["filter_count"] += 1
                
                # Analyze sort fields
                sort_fields = query.get("sort", [])
                for field in sort_fields:
                    field_stats[field]["access_count"] += 1
                    field_stats[field]["sort_count"] += 1
                
                # Check existing indexes
                indexed_fields = query.get("indexed_fields", [])
                for field in indexed_fields:
                    field_stats[field]["is_indexed"] = True
            
            return dict(field_stats)
            
        except Exception as e:
            logger.error(f"Failed to analyze field usage: {e}")
            return {}
    
    async def _analyze_field_combinations(
        self,
        query_patterns: List[Dict[str, Any]]
    ) -> Dict[tuple, Dict[str, Any]]:
        """Analyze frequent field combinations for composite indexes."""
        try:
            combinations = defaultdict(lambda: {
                "frequency": 0,
                "optimal_order": [],
                "selectivity_order": []
            })
            
            for pattern in query_patterns:
                filters = pattern.get("query", {}).get("filters", {})
                
                if len(filters) > 1:
                    # Create combination tuple
                    fields = tuple(sorted(filters.keys()))
                    combinations[fields]["frequency"] += 1
                    
                    # Track selectivity for ordering
                    if not combinations[fields]["selectivity_order"]:
                        selectivities = []
                        for field in fields:
                            selectivity = await self._estimate_field_selectivity(field, filters[field])
                            selectivities.append((field, selectivity))
                        
                        # Sort by selectivity (highest first)
                        selectivities.sort(key=lambda x: x[1], reverse=True)
                        combinations[fields]["optimal_order"] = [f for f, s in selectivities]
                        combinations[fields]["selectivity_order"] = selectivities
            
            return dict(combinations)
            
        except Exception as e:
            logger.error(f"Failed to analyze field combinations: {e}")
            return {}
    
    async def _estimate_field_selectivity(self, field: str, value: Any) -> float:
        """Estimate selectivity of a field filter."""
        try:
            # Simplified selectivity estimation
            # In real implementation, would query actual data distribution
            
            if isinstance(value, (list, tuple)):
                # IN clause - less selective
                return 0.3
            elif isinstance(value, dict):
                # Range query - moderately selective
                return 0.5
            else:
                # Equality - highly selective
                return 0.9
                
        except Exception as e:
            logger.error(f"Failed to estimate field selectivity: {e}")
            return 0.5
    
    def _estimate_index_improvement(self, field_stats: Dict[str, Any]) -> str:
        """Estimate performance improvement from adding an index."""
        access_count = field_stats.get("access_count", 0)
        
        if access_count > 1000:
            return "50-80%"
        elif access_count > 500:
            return "30-50%"
        elif access_count > 100:
            return "20-30%"
        else:
            return "10-20%"
    
    async def _identify_unused_indexes(self) -> List[Dict[str, Any]]:
        """Identify indexes that are rarely or never used."""
        try:
            unused = []
            
            # Check index usage stats from performance history
            index_usage = self.performance_history.get("index_usage", {})
            
            for index_name, stats in index_usage.items():
                usage_count = stats.get("usage_count", 0)
                last_used = stats.get("last_used", None)
                
                # Consider unused if not used in 30 days or < 10 uses total
                if usage_count < 10:
                    unused.append({
                        "index": index_name,
                        "usage_count": usage_count,
                        "last_used": last_used,
                        "reason": "Low usage count",
                        "recommendation": "Consider removal to reduce maintenance overhead"
                    })
            
            return unused
            
        except Exception as e:
            logger.error(f"Failed to identify unused indexes: {e}")
            return []
    
    async def _identify_fragmented_indexes(self) -> List[Dict[str, Any]]:
        """Identify fragmented indexes that need rebuilding."""
        try:
            fragmented = []
            
            # Check fragmentation stats
            index_stats = self.performance_history.get("index_fragmentation", {})
            
            for index_name, stats in index_stats.items():
                fragmentation_pct = stats.get("fragmentation", 0)
                
                # Recommend rebuild if fragmentation > 30%
                if fragmentation_pct > 30:
                    fragmented.append({
                        "index": index_name,
                        "fragmentation": f"{fragmentation_pct}%",
                        "reason": "High fragmentation impacts query performance",
                        "priority": "high" if fragmentation_pct > 50 else "medium",
                        "recommendation": "Rebuild index to restore performance"
                    })
            
            return fragmented
            
        except Exception as e:
            logger.error(f"Failed to identify fragmented indexes: {e}")
            return []
    
    def _get_cache_key(self, query: str) -> str:
        """Generate cache key for a query."""
        import hashlib
        return hashlib.md5(query.encode()).hexdigest()


def main():
    """Main entry point for standalone execution."""
    logging.basicConfig(level=logging.DEBUG)
    
    optimizer = SearchOptimizer(
        cache_size=1000,
        query_timeout=30.0,
        enable_query_expansion=True
    )
    
    if optimizer.setup():
        # Test query optimization
        result = asyncio.run(optimizer.execute(
            action="optimize_query",
            query="AI machine learning"
        ))
        print(f"Optimization result: {json.dumps(result, indent=2)}")
    else:
        print("Setup failed")


if __name__ == "__main__":
    main()
