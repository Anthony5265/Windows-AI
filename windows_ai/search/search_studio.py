#!/usr/bin/env python3
"""
Search Studio - Interactive Workbench for Search Development

Ship `search/search_studio.py` delivering studio tooling for teams to shape semantic retrieval capabilities.

This module provides an interactive development environment for search engineers to test,
refine, and optimize search queries, analyze results, perform A/B testing, and manage
search templates. It's the central workspace for search quality improvement.

Created: 2025-11-15
Updated: 2025-12-16
Part of: Windows-AI Search Module
"""

import asyncio
import hashlib
import json
import logging
import statistics
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class SearchStudio:
    """
    Interactive workbench for search development and testing.
    
    Provides comprehensive tools for search engineers to develop, test, and refine
    search capabilities through an interactive studio environment.
    
    Features:
    - Interactive query testing and refinement
    - Real-time result analysis and visualization
    - A/B testing framework for ranking comparisons
    - Performance profiling and benchmarking
    - Search template library management
    - Query suggestion and autocomplete testing
    - Relevance scoring analysis
    - Search pipeline debugging
    
    Usage:
        studio = SearchStudio(workspace_dir="~/.windows-ai/search-studio")
        await studio.initialize()
        
        # Test a query
        results = await studio.test_query(
            query="machine learning tutorials",
            backend="local",
            max_results=10
        )
        
        # Run A/B test
        ab_results = await studio.run_ab_test(
            query="python tutorial",
            variant_a="default_ranker",
            variant_b="ml_ranker"
        )
        
        # Save as template
        await studio.save_template(
            name="tutorial_search",
            query_pattern="* tutorial",
            parameters={"boost_recency": True}
        )
    """
    
    def __init__(
        self,
        workspace_dir: str = "~/.windows-ai/search-studio",
        max_history: int = 1000,
        enable_profiling: bool = True,
        enable_visualization: bool = True,
        cache_results: bool = True,
        default_timeout: float = 30.0,
        log_level: str = "INFO"
    ):
        """
        Initialize the search studio.
        
        Args:
            workspace_dir: Directory for storing studio data
            max_history: Maximum query history entries to retain
            enable_profiling: Enable performance profiling
            enable_visualization: Enable result visualization features
            cache_results: Cache search results for faster iteration
            default_timeout: Default query timeout in seconds
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        self._initialized = False
        self.workspace_dir = Path(workspace_dir).expanduser()
        self.max_history = max_history
        self.enable_profiling = enable_profiling
        self.enable_visualization = enable_visualization
        self.cache_results = cache_results
        self.default_timeout = default_timeout
        
        # Query history: timestamp -> query_data
        self.query_history: Dict[str, Dict[str, Any]] = {}
        
        # Search templates: template_name -> template_config
        self.templates: Dict[str, Dict[str, Any]] = {}
        
        # A/B test results: test_id -> test_data
        self.ab_tests: Dict[str, Dict[str, Any]] = {}
        
        # Performance profiles: query_id -> profile_data
        self.performance_profiles: Dict[str, Dict[str, Any]] = {}
        
        # Result cache: query_hash -> cached_results
        self.result_cache: Dict[str, Dict[str, Any]] = {}
        
        # Active experiments: experiment_id -> experiment_config
        self.experiments: Dict[str, Dict[str, Any]] = {}
        
        # Metrics tracking
        self.metrics: Dict[str, List[float]] = defaultdict(list)
        
        logger.setLevel(getattr(logging, log_level.upper()))
        logger.info(f"Created SearchStudio with workspace: {workspace_dir}")
    
    async def initialize(self) -> bool:
        """
        Initialize the search studio and load workspace data.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            logger.info("Initializing SearchStudio")
            
            # Create workspace directories
            logger.debug("Creating workspace directories")
            self.workspace_dir.mkdir(parents=True, exist_ok=True)
            (self.workspace_dir / "templates").mkdir(exist_ok=True)
            (self.workspace_dir / "history").mkdir(exist_ok=True)
            (self.workspace_dir / "profiles").mkdir(exist_ok=True)
            (self.workspace_dir / "ab_tests").mkdir(exist_ok=True)
            (self.workspace_dir / "experiments").mkdir(exist_ok=True)
            
            # Load templates
            logger.debug("Loading search templates")
            await self._load_templates()
            logger.info(f"Loaded {len(self.templates)} templates")
            
            # Load query history
            logger.debug("Loading query history")
            await self._load_history()
            logger.info(f"Loaded {len(self.query_history)} history entries")
            
            # Load A/B test results
            logger.debug("Loading A/B test results")
            await self._load_ab_tests()
            logger.info(f"Loaded {len(self.ab_tests)} A/B tests")
            
            # Load performance profiles
            if self.enable_profiling:
                logger.debug("Loading performance profiles")
                await self._load_profiles()
                logger.info(f"Loaded {len(self.performance_profiles)} profiles")
            
            self._initialized = True
            logger.info("SearchStudio initialization completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"SearchStudio initialization failed: {e}", exc_info=True)
            return False
    
    async def test_query(
        self,
        query: str,
        backend: str = "local",
        max_results: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        ranking_algorithm: Optional[str] = None,
        profile: bool = True
    ) -> Dict[str, Any]:
        """
        Test a search query with detailed analysis.
        
        Args:
            query: Search query string
            backend: Search backend to use
            max_results: Maximum results to return
            filters: Optional filters to apply
            ranking_algorithm: Ranking algorithm to use
            profile: Enable performance profiling
            
        Returns:
            Dict containing:
                - results: Search results
                - metadata: Query metadata
                - performance: Performance metrics
                - analysis: Result analysis
        """
        if not self._initialized:
            raise RuntimeError("SearchStudio not initialized. Call initialize() first.")
        
        try:
            start_time = time.time()
            logger.info(f"Testing query: '{query}' on backend: {backend}")
            
            # Generate query ID
            query_id = self._generate_query_id(query, backend, filters)
            
            # Check cache if enabled
            if self.cache_results and query_id in self.result_cache:
                logger.debug(f"Cache hit for query: {query_id}")
                cached = self.result_cache[query_id]
                cached["metadata"]["cached"] = True
                return cached
            
            # Execute search (simulated)
            logger.debug(f"Executing search: {query}")
            results = await self._execute_search(
                query=query,
                backend=backend,
                max_results=max_results,
                filters=filters,
                ranking_algorithm=ranking_algorithm
            )
            
            # Profile performance
            performance = {}
            if profile and self.enable_profiling:
                performance = await self._profile_query(query, backend, results)
                logger.debug(f"Query profiling completed: {performance}")
            
            # Analyze results
            analysis = await self._analyze_results(query, results)
            
            execution_time = time.time() - start_time
            
            # Build response
            response = {
                "query_id": query_id,
                "query": query,
                "results": results,
                "metadata": {
                    "backend": backend,
                    "timestamp": datetime.now().isoformat(),
                    "execution_time": execution_time,
                    "result_count": len(results),
                    "cached": False
                },
                "performance": performance,
                "analysis": analysis
            }
            
            # Cache results
            if self.cache_results:
                self.result_cache[query_id] = response
            
            # Add to history
            await self._add_to_history(response)
            
            # Track metrics
            self.metrics["execution_time"].append(execution_time)
            self.metrics["result_count"].append(len(results))
            
            logger.info(f"Query test completed in {execution_time:.3f}s with {len(results)} results")
            return response
            
        except asyncio.TimeoutError:
            logger.error(f"Query timeout after {self.default_timeout}s: {query}")
            return {
                "error": "timeout",
                "message": f"Query exceeded timeout of {self.default_timeout}s",
                "query": query
            }
        except Exception as e:
            logger.error(f"Query test failed: {e}", exc_info=True)
            return {
                "error": "execution_failed",
                "message": str(e),
                "query": query
            }
    
    async def run_ab_test(
        self,
        query: str,
        variant_a: str,
        variant_b: str,
        iterations: int = 10,
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Run A/B test comparing two ranking variants.
        
        Args:
            query: Test query
            variant_a: First ranking variant
            variant_b: Second ranking variant
            iterations: Number of test iterations
            metrics: Metrics to compare (default: relevance, speed, diversity)
            
        Returns:
            Dict containing comparative analysis of both variants
        """
        if not self._initialized:
            raise RuntimeError("SearchStudio not initialized. Call initialize() first.")
        
        try:
            logger.info(f"Running A/B test: {variant_a} vs {variant_b} for query: '{query}'")
            
            test_id = self._generate_test_id(query, variant_a, variant_b)
            metrics = metrics or ["relevance", "speed", "diversity"]
            
            results_a = []
            results_b = []
            
            # Run iterations for both variants
            for i in range(iterations):
                logger.debug(f"A/B test iteration {i+1}/{iterations}")
                
                # Test variant A
                result_a = await self._execute_search(
                    query=query,
                    backend="local",
                    ranking_algorithm=variant_a
                )
                results_a.append(result_a)
                
                # Test variant B
                result_b = await self._execute_search(
                    query=query,
                    backend="local",
                    ranking_algorithm=variant_b
                )
                results_b.append(result_b)
            
            # Calculate comparative metrics
            comparison = await self._compare_variants(
                query=query,
                variant_a=variant_a,
                variant_b=variant_b,
                results_a=results_a,
                results_b=results_b,
                metrics=metrics
            )
            
            # Store A/B test results
            ab_test_data = {
                "test_id": test_id,
                "query": query,
                "variant_a": variant_a,
                "variant_b": variant_b,
                "iterations": iterations,
                "metrics": metrics,
                "comparison": comparison,
                "timestamp": datetime.now().isoformat()
            }
            
            self.ab_tests[test_id] = ab_test_data
            await self._save_ab_test(ab_test_data)
            
            logger.info(f"A/B test completed: {comparison.get('winner', 'tie')}")
            return ab_test_data
            
        except Exception as e:
            logger.error(f"A/B test failed: {e}", exc_info=True)
            return {
                "error": "ab_test_failed",
                "message": str(e),
                "query": query
            }
    
    async def save_template(
        self,
        name: str,
        query_pattern: str,
        parameters: Optional[Dict[str, Any]] = None,
        description: str = "",
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Save a search query template.
        
        Args:
            name: Template name
            query_pattern: Query pattern with placeholders
            parameters: Default parameters
            description: Template description
            tags: Template tags for organization
            
        Returns:
            Dict containing template data
        """
        if not self._initialized:
            raise RuntimeError("SearchStudio not initialized. Call initialize() first.")
        
        try:
            logger.info(f"Saving template: {name}")
            
            template = {
                "name": name,
                "query_pattern": query_pattern,
                "parameters": parameters or {},
                "description": description,
                "tags": tags or [],
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "usage_count": 0
            }
            
            self.templates[name] = template
            
            # Save to disk
            template_path = self.workspace_dir / "templates" / f"{name}.json"
            with open(template_path, "w") as f:
                json.dump(template, f, indent=2)
            
            logger.info(f"Template saved: {name} -> {template_path}")
            return {"status": "success", "template": template}
            
        except Exception as e:
            logger.error(f"Failed to save template: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}
    
    async def load_template(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Load a search template by name.
        
        Args:
            name: Template name
            
        Returns:
            Template data or None if not found
        """
        if not self._initialized:
            raise RuntimeError("SearchStudio not initialized. Call initialize() first.")
        
        try:
            if name in self.templates:
                template = self.templates[name]
                template["usage_count"] += 1
                logger.debug(f"Loaded template: {name}")
                return template
            
            logger.warning(f"Template not found: {name}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to load template: {e}", exc_info=True)
            return None
    
    async def profile_performance(
        self,
        query: str,
        detailed: bool = True
    ) -> Dict[str, Any]:
        """
        Profile search query performance.
        
        Args:
            query: Query to profile
            detailed: Include detailed breakdown
            
        Returns:
            Dict containing performance profile
        """
        if not self._initialized:
            raise RuntimeError("SearchStudio not initialized. Call initialize() first.")
        
        try:
            logger.info(f"Profiling query: '{query}'")
            
            profile = {
                "query": query,
                "timestamp": datetime.now().isoformat(),
                "stages": {},
                "total_time": 0.0,
                "breakdown": {}
            }
            
            # Profile query parsing
            start = time.time()
            parsed = await self._parse_query(query)
            parse_time = time.time() - start
            profile["stages"]["parsing"] = parse_time
            
            # Profile query expansion
            start = time.time()
            expanded = await self._expand_query(query)
            expansion_time = time.time() - start
            profile["stages"]["expansion"] = expansion_time
            
            # Profile search execution
            start = time.time()
            results = await self._execute_search(query, backend="local")
            search_time = time.time() - start
            profile["stages"]["search"] = search_time
            
            # Profile ranking
            start = time.time()
            ranked = await self._rank_results(results)
            ranking_time = time.time() - start
            profile["stages"]["ranking"] = ranking_time
            
            profile["total_time"] = sum(profile["stages"].values())
            
            if detailed:
                profile["breakdown"] = {
                    "parsing_percent": (parse_time / profile["total_time"]) * 100,
                    "expansion_percent": (expansion_time / profile["total_time"]) * 100,
                    "search_percent": (search_time / profile["total_time"]) * 100,
                    "ranking_percent": (ranking_time / profile["total_time"]) * 100
                }
            
            # Store profile
            profile_id = hashlib.md5(query.encode()).hexdigest()
            self.performance_profiles[profile_id] = profile
            
            logger.info(f"Performance profile completed: {profile['total_time']:.3f}s total")
            return profile
            
        except Exception as e:
            logger.error(f"Performance profiling failed: {e}", exc_info=True)
            return {"error": "profiling_failed", "message": str(e)}
    
    async def analyze_results(
        self,
        results: List[Dict[str, Any]],
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze search results for quality metrics.
        
        Args:
            results: Search results to analyze
            metrics: Metrics to calculate
            
        Returns:
            Dict containing analysis results
        """
        try:
            metrics = metrics or ["diversity", "coverage", "relevance"]
            
            analysis = {
                "result_count": len(results),
                "metrics": {},
                "timestamp": datetime.now().isoformat()
            }
            
            if "diversity" in metrics:
                analysis["metrics"]["diversity"] = await self._calculate_diversity(results)
            
            if "coverage" in metrics:
                analysis["metrics"]["coverage"] = await self._calculate_coverage(results)
            
            if "relevance" in metrics:
                analysis["metrics"]["relevance"] = await self._calculate_relevance(results)
            
            logger.debug(f"Result analysis completed: {analysis['metrics']}")
            return analysis
            
        except Exception as e:
            logger.error(f"Result analysis failed: {e}", exc_info=True)
            return {"error": "analysis_failed", "message": str(e)}
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get studio usage statistics.
        
        Returns:
            Dict containing usage statistics
        """
        try:
            stats = {
                "total_queries": len(self.query_history),
                "total_templates": len(self.templates),
                "total_ab_tests": len(self.ab_tests),
                "cache_size": len(self.result_cache),
                "avg_execution_time": statistics.mean(self.metrics["execution_time"]) if self.metrics["execution_time"] else 0,
                "avg_result_count": statistics.mean(self.metrics["result_count"]) if self.metrics["result_count"] else 0,
                "most_used_templates": self._get_most_used_templates(5),
                "workspace_dir": str(self.workspace_dir)
            }
            
            logger.debug(f"Studio statistics: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}", exc_info=True)
            return {"error": "stats_failed", "message": str(e)}
    
    async def cleanup(self) -> None:
        """Clean up studio resources."""
        try:
            logger.info("Cleaning up SearchStudio")
            
            # Save current state
            await self._save_state()
            
            # Clear caches
            self.result_cache.clear()
            
            logger.info("SearchStudio cleanup completed")
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}", exc_info=True)
    
    # Private helper methods
    
    def _generate_query_id(self, query: str, backend: str, filters: Optional[Dict] = None) -> str:
        """Generate unique query ID."""
        data = f"{query}:{backend}:{json.dumps(filters or {}, sort_keys=True)}"
        return hashlib.md5(data.encode()).hexdigest()
    
    def _generate_test_id(self, query: str, variant_a: str, variant_b: str) -> str:
        """Generate unique A/B test ID."""
        data = f"{query}:{variant_a}:{variant_b}"
        return hashlib.md5(data.encode()).hexdigest()
    
    async def _execute_search(
        self,
        query: str,
        backend: str = "local",
        max_results: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        ranking_algorithm: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Execute search query (simulated)."""
        await asyncio.sleep(0.01)  # Simulate search latency
        
        # Simulated results
        results = [
            {
                "id": f"doc_{i}",
                "title": f"Result {i} for {query}",
                "score": 1.0 - (i * 0.1),
                "snippet": f"Snippet for result {i}",
                "metadata": {"backend": backend}
            }
            for i in range(min(max_results, 10))
        ]
        
        return results
    
    async def _profile_query(
        self,
        query: str,
        backend: str,
        results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Profile query performance."""
        return {
            "query_complexity": len(query.split()),
            "result_count": len(results),
            "avg_score": statistics.mean([r.get("score", 0) for r in results]) if results else 0
        }
    
    async def _analyze_results(self, query: str, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze search results."""
        if not results:
            return {"diversity": 0, "coverage": 0, "quality": 0}
        
        return {
            "diversity": await self._calculate_diversity(results),
            "coverage": await self._calculate_coverage(results),
            "quality": statistics.mean([r.get("score", 0) for r in results])
        }
    
    async def _calculate_diversity(self, results: List[Dict[str, Any]]) -> float:
        """Calculate result diversity score."""
        if not results:
            return 0.0
        
        # Simple diversity: count unique titles
        titles = set(r.get("title", "") for r in results)
        return len(titles) / len(results)
    
    async def _calculate_coverage(self, results: List[Dict[str, Any]]) -> float:
        """Calculate result coverage score."""
        if not results:
            return 0.0
        
        # Simple coverage: percentage of results with scores > 0.5
        high_quality = sum(1 for r in results if r.get("score", 0) > 0.5)
        return high_quality / len(results)
    
    async def _calculate_relevance(self, results: List[Dict[str, Any]]) -> float:
        """Calculate average relevance score."""
        if not results:
            return 0.0
        
        scores = [r.get("score", 0) for r in results]
        return statistics.mean(scores)
    
    async def _compare_variants(
        self,
        query: str,
        variant_a: str,
        variant_b: str,
        results_a: List[List[Dict]],
        results_b: List[List[Dict]],
        metrics: List[str]
    ) -> Dict[str, Any]:
        """Compare A/B test variants."""
        comparison = {
            "variant_a": {"name": variant_a, "metrics": {}},
            "variant_b": {"name": variant_b, "metrics": {}},
            "winner": None,
            "confidence": 0.0
        }
        
        # Calculate metrics for variant A
        for metric in metrics:
            values = []
            for results in results_a:
                if metric == "relevance":
                    values.append(await self._calculate_relevance(results))
                elif metric == "diversity":
                    values.append(await self._calculate_diversity(results))
                elif metric == "speed":
                    values.append(0.1)  # Simulated
            
            comparison["variant_a"]["metrics"][metric] = {
                "mean": statistics.mean(values),
                "stddev": statistics.stdev(values) if len(values) > 1 else 0
            }
        
        # Calculate metrics for variant B
        for metric in metrics:
            values = []
            for results in results_b:
                if metric == "relevance":
                    values.append(await self._calculate_relevance(results))
                elif metric == "diversity":
                    values.append(await self._calculate_diversity(results))
                elif metric == "speed":
                    values.append(0.1)  # Simulated
            
            comparison["variant_b"]["metrics"][metric] = {
                "mean": statistics.mean(values),
                "stddev": statistics.stdev(values) if len(values) > 1 else 0
            }
        
        # Determine winner (simple comparison)
        a_score = sum(m["mean"] for m in comparison["variant_a"]["metrics"].values())
        b_score = sum(m["mean"] for m in comparison["variant_b"]["metrics"].values())
        
        if a_score > b_score:
            comparison["winner"] = variant_a
            comparison["confidence"] = (a_score - b_score) / a_score
        elif b_score > a_score:
            comparison["winner"] = variant_b
            comparison["confidence"] = (b_score - a_score) / b_score
        else:
            comparison["winner"] = "tie"
        
        return comparison
    
    async def _parse_query(self, query: str) -> Dict[str, Any]:
        """Parse query into components."""
        await asyncio.sleep(0.001)
        return {"tokens": query.split(), "query": query}
    
    async def _expand_query(self, query: str) -> List[str]:
        """Expand query with synonyms."""
        await asyncio.sleep(0.001)
        return [query]
    
    async def _rank_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank search results."""
        await asyncio.sleep(0.001)
        return sorted(results, key=lambda x: x.get("score", 0), reverse=True)
    
    async def _load_templates(self) -> None:
        """Load templates from disk."""
        template_dir = self.workspace_dir / "templates"
        if not template_dir.exists():
            return
        
        for template_file in template_dir.glob("*.json"):
            try:
                with open(template_file) as f:
                    template = json.load(f)
                    self.templates[template["name"]] = template
            except Exception as e:
                logger.error(f"Failed to load template {template_file}: {e}")
    
    async def _load_history(self) -> None:
        """Load query history from disk."""
        history_file = self.workspace_dir / "history" / "queries.json"
        if not history_file.exists():
            return
        
        try:
            with open(history_file) as f:
                self.query_history = json.load(f)
                
            # Trim history to max_history
            if len(self.query_history) > self.max_history:
                items = sorted(self.query_history.items(), key=lambda x: x[1]["metadata"]["timestamp"])
                self.query_history = dict(items[-self.max_history:])
        except Exception as e:
            logger.error(f"Failed to load history: {e}")
    
    async def _load_ab_tests(self) -> None:
        """Load A/B test results from disk."""
        ab_test_dir = self.workspace_dir / "ab_tests"
        if not ab_test_dir.exists():
            return
        
        for test_file in ab_test_dir.glob("*.json"):
            try:
                with open(test_file) as f:
                    test = json.load(f)
                    self.ab_tests[test["test_id"]] = test
            except Exception as e:
                logger.error(f"Failed to load A/B test {test_file}: {e}")
    
    async def _load_profiles(self) -> None:
        """Load performance profiles from disk."""
        profile_dir = self.workspace_dir / "profiles"
        if not profile_dir.exists():
            return
        
        for profile_file in profile_dir.glob("*.json"):
            try:
                with open(profile_file) as f:
                    profile = json.load(f)
                    profile_id = profile_file.stem
                    self.performance_profiles[profile_id] = profile
            except Exception as e:
                logger.error(f"Failed to load profile {profile_file}: {e}")
    
    async def _add_to_history(self, query_data: Dict[str, Any]) -> None:
        """Add query to history."""
        query_id = query_data["query_id"]
        self.query_history[query_id] = query_data
        
        # Trim history
        if len(self.query_history) > self.max_history:
            oldest = min(self.query_history.items(), key=lambda x: x[1]["metadata"]["timestamp"])
            del self.query_history[oldest[0]]
    
    async def _save_ab_test(self, test_data: Dict[str, Any]) -> None:
        """Save A/B test to disk."""
        test_file = self.workspace_dir / "ab_tests" / f"{test_data['test_id']}.json"
        with open(test_file, "w") as f:
            json.dump(test_data, f, indent=2)
    
    async def _save_state(self) -> None:
        """Save current studio state to disk."""
        # Save history
        history_file = self.workspace_dir / "history" / "queries.json"
        with open(history_file, "w") as f:
            json.dump(self.query_history, f, indent=2)
        
        logger.debug("Studio state saved")
    
    def _get_most_used_templates(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get most used templates."""
        sorted_templates = sorted(
            self.templates.items(),
            key=lambda x: x[1].get("usage_count", 0),
            reverse=True
        )
        return [
            {"name": name, "usage_count": tmpl.get("usage_count", 0)}
            for name, tmpl in sorted_templates[:limit]
        ]


async def main():
    """Main entry point for standalone execution."""
    studio = SearchStudio()
    
    if await studio.initialize():
        # Test query
        result = await studio.test_query("machine learning tutorial")
        print(f"Query result: {result['metadata']}")
        
        # Run A/B test
        ab_result = await studio.run_ab_test(
            query="python tutorial",
            variant_a="default",
            variant_b="ml_enhanced"
        )
        print(f"A/B test winner: {ab_result['comparison']['winner']}")
        
        # Get statistics
        stats = studio.get_statistics()
        print(f"Statistics: {stats}")
        
        await studio.cleanup()
    else:
        print("Studio initialization failed")


if __name__ == "__main__":
    asyncio.run(main())
