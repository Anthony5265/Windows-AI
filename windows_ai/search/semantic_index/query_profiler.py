#!/usr/bin/env python3
"""
Query Profiler - Analyze Query Performance Metrics

This module provides comprehensive query performance profiling for semantic search operations.
Tracks execution time, embedding generation, vector similarity searches, and identifies bottlenecks.

Features:
- Real-time query performance monitoring
- Detailed execution breakdown by phase
- Query complexity analysis
- Performance trend tracking
- Bottleneck identification
- Cache hit/miss ratios
- Query optimization recommendations

Example:
    profiler = QueryProfiler()
    await profiler.initialize()
    
    # Profile a query
    async with profiler.profile_query("my search query") as session:
        results = await search_engine.search(session.query)
    
    # Get performance stats
    stats = await profiler.get_statistics(time_range="1h")
"""

import asyncio
import json
import logging
import statistics
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class QueryPhase:
    """Represents a single phase of query execution"""
    name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def complete(self) -> float:
        """Mark phase as complete and calculate duration"""
        self.end_time = time.perf_counter()
        self.duration = self.end_time - self.start_time
        return self.duration


@dataclass
class QueryProfile:
    """Complete profile of a single query execution"""
    query_id: str
    query_text: str
    start_time: float
    timestamp: datetime = field(default_factory=datetime.now)
    end_time: Optional[float] = None
    total_duration: Optional[float] = None
    phases: List[QueryPhase] = field(default_factory=list)
    cache_hit: bool = False
    result_count: int = 0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_phase(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> QueryPhase:
        """Add a new execution phase"""
        phase = QueryPhase(
            name=name,
            start_time=time.perf_counter(),
            metadata=metadata or {}
        )
        self.phases.append(phase)
        return phase
    
    def complete(self, result_count: int = 0, error: Optional[str] = None):
        """Mark query as complete"""
        self.end_time = time.perf_counter()
        self.total_duration = self.end_time - self.start_time
        self.result_count = result_count
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "query_id": self.query_id,
            "query_text": self.query_text,
            "timestamp": self.timestamp.isoformat(),
            "total_duration": self.total_duration,
            "cache_hit": self.cache_hit,
            "result_count": self.result_count,
            "error": self.error,
            "phases": [
                {
                    "name": p.name,
                    "duration": p.duration,
                    "metadata": p.metadata
                }
                for p in self.phases
            ],
            "metadata": self.metadata
        }


@dataclass
class PerformanceStatistics:
    """Aggregated performance statistics"""
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    avg_duration: float = 0.0
    median_duration: float = 0.0
    p95_duration: float = 0.0
    p99_duration: float = 0.0
    min_duration: float = 0.0
    max_duration: float = 0.0
    phase_stats: Dict[str, Dict[str, float]] = field(default_factory=dict)
    error_types: Dict[str, int] = field(default_factory=dict)
    queries_per_second: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class QueryProfiler:
    """
    Query performance profiler for semantic search operations
    
    Tracks and analyzes query execution metrics, identifying bottlenecks
    and providing optimization recommendations.
    """
    
    def __init__(self, max_history: int = 10000):
        """
        Initialize query profiler
        
        Args:
            max_history: Maximum number of query profiles to keep in memory
        """
        self.max_history = max_history
        self._initialized = False
        self._profiles: deque = deque(maxlen=max_history)
        self._active_profiles: Dict[str, QueryProfile] = {}
        self._query_counter = 0
        self._lock = asyncio.Lock()
        
        # Performance tracking
        self._durations: deque = deque(maxlen=max_history)
        self._phase_durations: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self._error_counts: Dict[str, int] = defaultdict(int)
        
        logger.info("QueryProfiler created")
    
    async def initialize(self) -> bool:
        """
        Initialize profiler
        
        Returns:
            True if initialization successful
        """
        if self._initialized:
            logger.warning("QueryProfiler already initialized")
            return True
        
        try:
            # Initialize data structures
            self._profiles.clear()
            self._active_profiles.clear()
            self._query_counter = 0
            
            self._initialized = True
            logger.info("QueryProfiler initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"QueryProfiler initialization failed: {e}")
            return False
    
    @asynccontextmanager
    async def profile_query(self, query_text: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Context manager for profiling a query
        
        Args:
            query_text: The search query text
            metadata: Additional metadata to track
        
        Yields:
            QueryProfile instance for tracking phases
        
        Example:
            async with profiler.profile_query("search term") as profile:
                # Profile embedding generation
                phase = profile.add_phase("embedding")
                embedding = await generate_embedding(profile.query_text)
                phase.complete()
                
                # Profile vector search
                phase = profile.add_phase("vector_search")
                results = await vector_search(embedding)
                phase.complete()
                
                profile.complete(result_count=len(results))
        """
        async with self._lock:
            self._query_counter += 1
            query_id = f"q_{self._query_counter}_{int(time.time())}"
        
        profile = QueryProfile(
            query_id=query_id,
            query_text=query_text,
            start_time=time.perf_counter(),
            metadata=metadata or {}
        )
        
        self._active_profiles[query_id] = profile
        
        try:
            yield profile
        except Exception as e:
            profile.error = str(e)
            logger.error(f"Query {query_id} failed: {e}")
            raise
        finally:
            # Ensure profile is completed
            if profile.end_time is None:
                profile.complete()
            
            # Complete any unfinished phases
            for phase in profile.phases:
                if phase.end_time is None:
                    phase.complete()
            
            # Store profile
            await self._store_profile(profile)
            
            # Remove from active
            self._active_profiles.pop(query_id, None)
    
    async def _store_profile(self, profile: QueryProfile):
        """Store completed profile and update statistics"""
        async with self._lock:
            self._profiles.append(profile)
            
            # Update duration tracking
            if profile.total_duration is not None:
                self._durations.append(profile.total_duration)
            
            # Update phase duration tracking
            for phase in profile.phases:
                if phase.duration is not None:
                    self._phase_durations[phase.name].append(phase.duration)
            
            # Update error tracking
            if profile.error:
                error_type = profile.error.split(":")[0] if ":" in profile.error else "Unknown"
                self._error_counts[error_type] += 1
    
    async def get_profile(self, query_id: str) -> Optional[QueryProfile]:
        """
        Get specific query profile
        
        Args:
            query_id: Query identifier
        
        Returns:
            QueryProfile if found, None otherwise
        """
        async with self._lock:
            # Check active profiles first
            if query_id in self._active_profiles:
                return self._active_profiles[query_id]
            
            # Search historical profiles
            for profile in reversed(self._profiles):
                if profile.query_id == query_id:
                    return profile
        
        return None
    
    async def get_recent_profiles(self, count: int = 100) -> List[QueryProfile]:
        """
        Get most recent query profiles
        
        Args:
            count: Number of profiles to return
        
        Returns:
            List of recent QueryProfile instances
        """
        async with self._lock:
            recent = list(self._profiles)[-count:]
            return list(reversed(recent))
    
    async def get_statistics(
        self,
        time_range: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> PerformanceStatistics:
        """
        Get performance statistics
        
        Args:
            time_range: Time range string (e.g., "1h", "24h", "7d")
            start_time: Start of time range (alternative to time_range)
            end_time: End of time range (defaults to now)
        
        Returns:
            PerformanceStatistics instance
        """
        # Parse time range
        if time_range:
            end_time = datetime.now()
            if time_range.endswith("h"):
                hours = int(time_range[:-1])
                start_time = end_time - timedelta(hours=hours)
            elif time_range.endswith("d"):
                days = int(time_range[:-1])
                start_time = end_time - timedelta(days=days)
            elif time_range.endswith("m"):
                minutes = int(time_range[:-1])
                start_time = end_time - timedelta(minutes=minutes)
            else:
                start_time = end_time - timedelta(hours=1)
        
        async with self._lock:
            # Filter profiles by time range
            if start_time or end_time:
                profiles = [
                    p for p in self._profiles
                    if (not start_time or p.timestamp >= start_time) and
                       (not end_time or p.timestamp <= end_time)
                ]
            else:
                profiles = list(self._profiles)
            
            if not profiles:
                return PerformanceStatistics()
            
            # Calculate statistics
            stats = PerformanceStatistics()
            stats.total_queries = len(profiles)
            
            successful = [p for p in profiles if not p.error]
            failed = [p for p in profiles if p.error]
            
            stats.successful_queries = len(successful)
            stats.failed_queries = len(failed)
            
            stats.cache_hits = sum(1 for p in profiles if p.cache_hit)
            stats.cache_misses = stats.total_queries - stats.cache_hits
            
            # Duration statistics
            durations = [p.total_duration for p in profiles if p.total_duration is not None]
            if durations:
                stats.avg_duration = statistics.mean(durations)
                stats.median_duration = statistics.median(durations)
                stats.min_duration = min(durations)
                stats.max_duration = max(durations)
                
                # Percentiles
                sorted_durations = sorted(durations)
                stats.p95_duration = sorted_durations[int(len(sorted_durations) * 0.95)] if len(sorted_durations) > 0 else 0.0
                stats.p99_duration = sorted_durations[int(len(sorted_durations) * 0.99)] if len(sorted_durations) > 0 else 0.0
            
            # Phase statistics
            phase_names: Set[str] = set()
            for p in profiles:
                phase_names.update(phase.name for phase in p.phases)
            
            for phase_name in phase_names:
                phase_durations = []
                for p in profiles:
                    for phase in p.phases:
                        if phase.name == phase_name and phase.duration is not None:
                            phase_durations.append(phase.duration)
                
                if phase_durations:
                    stats.phase_stats[phase_name] = {
                        "avg": statistics.mean(phase_durations),
                        "median": statistics.median(phase_durations),
                        "min": min(phase_durations),
                        "max": max(phase_durations),
                        "count": len(phase_durations)
                    }
            
            # Error statistics
            stats.error_types = dict(self._error_counts)
            
            # Queries per second
            if start_time and end_time:
                time_span = (end_time - start_time).total_seconds()
                if time_span > 0:
                    stats.queries_per_second = stats.total_queries / time_span
            
            return stats
    
    async def get_slow_queries(
        self,
        threshold: float = 1.0,
        count: int = 10
    ) -> List[QueryProfile]:
        """
        Get slowest queries
        
        Args:
            threshold: Minimum duration in seconds
            count: Maximum number of queries to return
        
        Returns:
            List of slow QueryProfile instances
        """
        async with self._lock:
            slow_queries = [
                p for p in self._profiles
                if p.total_duration is not None and p.total_duration >= threshold
            ]
            
            # Sort by duration descending
            slow_queries.sort(key=lambda p: p.total_duration or 0, reverse=True)
            
            return slow_queries[:count]
    
    async def get_bottlenecks(
        self,
        time_range: str = "1h"
    ) -> Dict[str, Any]:
        """
        Identify performance bottlenecks
        
        Args:
            time_range: Time range to analyze
        
        Returns:
            Dictionary with bottleneck analysis
        """
        stats = await self.get_statistics(time_range=time_range)
        
        bottlenecks = {
            "slow_phases": [],
            "high_error_rate": False,
            "low_cache_hit_rate": False,
            "recommendations": []
        }
        
        # Identify slow phases
        if stats.phase_stats:
            for phase_name, phase_stat in stats.phase_stats.items():
                if phase_stat["avg"] > 0.5:  # More than 500ms average
                    bottlenecks["slow_phases"].append({
                        "phase": phase_name,
                        "avg_duration": phase_stat["avg"],
                        "max_duration": phase_stat["max"]
                    })
        
        # Check error rate
        if stats.total_queries > 0:
            error_rate = stats.failed_queries / stats.total_queries
            if error_rate > 0.05:  # More than 5% errors
                bottlenecks["high_error_rate"] = True
                bottlenecks["recommendations"].append(
                    f"High error rate: {error_rate*100:.1f}%. Investigate error types: {stats.error_types}"
                )
        
        # Check cache hit rate
        if stats.total_queries > 0:
            cache_hit_rate = stats.cache_hits / stats.total_queries
            if cache_hit_rate < 0.3:  # Less than 30% cache hits
                bottlenecks["low_cache_hit_rate"] = True
                bottlenecks["recommendations"].append(
                    f"Low cache hit rate: {cache_hit_rate*100:.1f}%. Consider increasing cache size or TTL."
                )
        
        # Recommendations for slow phases
        for slow_phase in bottlenecks["slow_phases"]:
            phase_name = slow_phase["phase"]
            if "embedding" in phase_name.lower():
                bottlenecks["recommendations"].append(
                    f"Phase '{phase_name}' is slow. Consider caching embeddings or using a faster model."
                )
            elif "vector" in phase_name.lower() or "search" in phase_name.lower():
                bottlenecks["recommendations"].append(
                    f"Phase '{phase_name}' is slow. Consider optimizing index or using approximate search."
                )
            else:
                bottlenecks["recommendations"].append(
                    f"Phase '{phase_name}' is slow. Profile this phase for optimization opportunities."
                )
        
        return bottlenecks
    
    async def export_profiles(
        self,
        filepath: str,
        time_range: Optional[str] = None,
        format: str = "json"
    ) -> bool:
        """
        Export query profiles to file
        
        Args:
            filepath: Output file path
            time_range: Optional time range filter
            format: Output format ("json" or "csv")
        
        Returns:
            True if export successful
        """
        try:
            profiles = await self.get_recent_profiles(count=self.max_history)
            
            if format == "json":
                data = {
                    "exported_at": datetime.now().isoformat(),
                    "total_profiles": len(profiles),
                    "profiles": [p.to_dict() for p in profiles]
                }
                
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2)
            
            elif format == "csv":
                import csv
                with open(filepath, 'w', newline='') as f:
                    if profiles:
                        writer = csv.DictWriter(f, fieldnames=[
                            'query_id', 'query_text', 'timestamp', 'total_duration',
                            'cache_hit', 'result_count', 'error'
                        ])
                        writer.writeheader()
                        for p in profiles:
                            writer.writerow({
                                'query_id': p.query_id,
                                'query_text': p.query_text,
                                'timestamp': p.timestamp.isoformat(),
                                'total_duration': p.total_duration,
                                'cache_hit': p.cache_hit,
                                'result_count': p.result_count,
                                'error': p.error or ''
                            })
            
            logger.info(f"Exported {len(profiles)} profiles to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export profiles: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup profiler resources"""
        async with self._lock:
            self._profiles.clear()
            self._active_profiles.clear()
            self._durations.clear()
            self._phase_durations.clear()
            self._error_counts.clear()
        
        self._initialized = False
        logger.info("QueryProfiler cleaned up")
