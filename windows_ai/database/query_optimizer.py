"""Database query optimization and performance analysis.

This module provides tools for profiling, analyzing, and optimizing database
queries using EXPLAIN plans, execution statistics, and caching strategies.
"""

import time
import asyncio
from typing import Any, Dict, List, Optional, Tuple, AsyncIterator
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import hashlib
from enum import Enum

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool, QueuePool
from sqlalchemy import text, event
from sqlalchemy.orm import sessionmaker
import logging

logger = logging.getLogger(__name__)


class QueryType(str, Enum):
    """Classification of SQL query types."""
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    JOIN = "JOIN"
    AGGREGATE = "AGGREGATE"
    SUBQUERY = "SUBQUERY"


@dataclass
class ExplainPlan:
    """EXPLAIN plan analysis result."""
    query: str
    plan_json: Dict[str, Any]
    execution_time_ms: float
    planning_time_ms: float
    total_cost: float
    rows: int
    node_type: str
    indexes_used: List[str]
    seq_scans: int
    index_scans: int
    recommendations: List[str]
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "query": self.query,
            "plan_json": self.plan_json,
            "execution_time_ms": self.execution_time_ms,
            "planning_time_ms": self.planning_time_ms,
            "total_cost": self.total_cost,
            "rows": self.rows,
            "node_type": self.node_type,
            "indexes_used": self.indexes_used,
            "seq_scans": self.seq_scans,
            "index_scans": self.index_scans,
            "recommendations": self.recommendations,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class QueryMetrics:
    """Query execution metrics."""
    query_hash: str
    query: str
    query_type: QueryType
    execution_count: int = 0
    total_time_ms: float = 0.0
    avg_time_ms: float = 0.0
    min_time_ms: float = 0.0
    max_time_ms: float = 0.0
    slow_count: int = 0  # Count of executions > 1000ms
    error_count: int = 0
    last_execution: datetime = None
    explain_plan: Optional[ExplainPlan] = None

    @property
    def slowness_ratio(self) -> float:
        """Ratio of slow executions to total executions."""
        if self.execution_count == 0:
            return 0.0
        return self.slow_count / self.execution_count

    def update(self, execution_time_ms: float, error: bool = False):
        """Update metrics with new execution."""
        self.execution_count += 1
        self.last_execution = datetime.now()

        if error:
            self.error_count += 1
            return

        self.total_time_ms += execution_time_ms
        self.avg_time_ms = self.total_time_ms / (self.execution_count - self.error_count)
        self.min_time_ms = min(self.min_time_ms or execution_time_ms, execution_time_ms)
        self.max_time_ms = max(self.max_time_ms or execution_time_ms, execution_time_ms)

        if execution_time_ms > 1000:
            self.slow_count += 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query_hash": self.query_hash,
            "query": self.query,
            "query_type": self.query_type.value,
            "execution_count": self.execution_count,
            "total_time_ms": self.total_time_ms,
            "avg_time_ms": self.avg_time_ms,
            "min_time_ms": self.min_time_ms,
            "max_time_ms": self.max_time_ms,
            "slow_count": self.slow_count,
            "error_count": self.error_count,
            "slowness_ratio": self.slowness_ratio,
            "last_execution": self.last_execution.isoformat() if self.last_execution else None,
        }


class QueryProfiler:
    """Profiles and analyzes database query performance."""

    def __init__(self, database_url: str):
        """Initialize query profiler.

        Args:
            database_url: SQLAlchemy database URL (e.g., postgresql+asyncpg://...)
        """
        self.database_url = database_url
        self.metrics: Dict[str, QueryMetrics] = {}
        self.slow_query_threshold_ms = 1000  # 1 second

    @staticmethod
    def _hash_query(query: str) -> str:
        """Create consistent hash for query."""
        normalized = " ".join(query.split())
        return hashlib.md5(normalized.encode()).hexdigest()

    @staticmethod
    def _classify_query(query: str) -> QueryType:
        """Classify query type from SQL statement."""
        query_upper = query.strip().upper()

        if "SELECT" in query_upper:
            if "JOIN" in query_upper:
                return QueryType.JOIN
            elif any(agg in query_upper for agg in ["COUNT", "SUM", "AVG", "MAX", "MIN"]):
                return QueryType.AGGREGATE
            elif "SELECT" in query_upper and "FROM" in query_upper:
                # Check for subqueries
                paren_count = query.count("(") - query.count(")")
                if paren_count > 0:
                    return QueryType.SUBQUERY
            return QueryType.SELECT
        elif "INSERT" in query_upper:
            return QueryType.INSERT
        elif "UPDATE" in query_upper:
            return QueryType.UPDATE
        elif "DELETE" in query_upper:
            return QueryType.DELETE
        return QueryType.SELECT

    async def create_engine(self):
        """Create async database engine."""
        return create_async_engine(
            self.database_url,
            echo=False,
            pool_size=10,
            max_overflow=20,
            poolclass=QueuePool,
        )

    async def analyze_query(
        self,
        query: str,
        session: AsyncSession,
    ) -> ExplainPlan:
        """Analyze query performance using EXPLAIN.

        Args:
            query: SQL query to analyze
            session: Active database session

        Returns:
            ExplainPlan with analysis results
        """
        try:
            # Run EXPLAIN ANALYZE
            explain_query = f"EXPLAIN (FORMAT JSON, ANALYZE, BUFFERS) {query}"
            result = await session.execute(text(explain_query))
            plan_json = json.loads(result.scalar())

            # Extract metrics from plan
            plan = plan_json[0]["Plan"]
            planning_time_ms = plan_json[0].get("Planning Time", 0)
            execution_time_ms = plan_json[0].get("Execution Time", 0)

            # Analyze plan for recommendations
            indexes_used, seq_scans, index_scans = self._analyze_plan_nodes(plan)
            recommendations = self._generate_recommendations(
                plan, seq_scans, index_scans, query
            )

            return ExplainPlan(
                query=query,
                plan_json=plan_json,
                execution_time_ms=execution_time_ms,
                planning_time_ms=planning_time_ms,
                total_cost=float(plan.get("Total Cost", 0)),
                rows=int(plan.get("Actual Rows", 0)),
                node_type=plan.get("Node Type", "Unknown"),
                indexes_used=indexes_used,
                seq_scans=seq_scans,
                index_scans=index_scans,
                recommendations=recommendations,
            )
        except Exception as e:
            logger.error(f"Error analyzing query: {e}")
            raise

    def _analyze_plan_nodes(self, node: Dict, depth: int = 0) -> Tuple[List[str], int, int]:
        """Recursively analyze plan nodes.

        Returns:
            Tuple of (indexes_used, seq_scans, index_scans)
        """
        indexes_used = []
        seq_scans = 0
        index_scans = 0

        node_type = node.get("Node Type", "")

        # Track index usage
        if "Index Name" in node:
            indexes_used.append(node["Index Name"])
            index_scans += 1
        elif node_type == "Seq Scan":
            seq_scans += 1

        # Recursively check child plans
        for child in node.get("Plans", []):
            child_indexes, child_seq, child_idx = self._analyze_plan_nodes(child, depth + 1)
            indexes_used.extend(child_indexes)
            seq_scans += child_seq
            index_scans += child_idx

        return indexes_used, seq_scans, index_scans

    def _generate_recommendations(
        self,
        plan: Dict,
        seq_scans: int,
        index_scans: int,
        query: str,
    ) -> List[str]:
        """Generate optimization recommendations based on plan."""
        recommendations = []

        # High sequential scans recommendation
        if seq_scans > 2:
            recommendations.append(
                f"High number of sequential scans ({seq_scans}). Consider adding indexes "
                "on frequently filtered columns."
            )

        # Expensive operations
        if plan.get("Node Type") in ["Sort", "Hash"]:
            recommendations.append(
                f"Query involves expensive {plan.get('Node Type')} operation. "
                "Consider adding indexes or restructuring query."
            )

        # Large row estimates
        if plan.get("Total Cost", 0) > 10000:
            recommendations.append(
                f"High estimated cost ({plan.get('Total Cost')}). Review query structure "
                "and consider optimization."
            )

        # Use LIMIT in queries
        if "LIMIT" not in query.upper() and "OFFSET" not in query.upper():
            if "SELECT *" in query.upper():
                recommendations.append(
                    "Query selects all columns without LIMIT. Consider SELECT * specific columns "
                    "and adding LIMIT for pagination."
                )

        return recommendations

    async def profile_query(
        self,
        query: str,
        session: AsyncSession,
        execute: bool = False,
    ) -> QueryMetrics:
        """Profile a single query.

        Args:
            query: SQL query to profile
            session: Active database session
            execute: Whether to actually execute the query

        Returns:
            Query metrics with performance data
        """
        query_hash = self._hash_query(query)
        query_type = self._classify_query(query)

        # Create metrics object
        if query_hash not in self.metrics:
            self.metrics[query_hash] = QueryMetrics(
                query_hash=query_hash,
                query=query,
                query_type=query_type,
            )

        metrics = self.metrics[query_hash]

        try:
            if execute:
                # Execute query and measure time
                start = time.time()
                await session.execute(text(query))
                execution_time_ms = (time.time() - start) * 1000
                metrics.update(execution_time_ms)
            else:
                # Just analyze without executing
                pass

            # Get EXPLAIN plan
            try:
                metrics.explain_plan = await self.analyze_query(query, session)
            except Exception as e:
                logger.warning(f"Could not generate EXPLAIN plan: {e}")

        except Exception as e:
            logger.error(f"Error profiling query: {e}")
            metrics.update(0, error=True)

        return metrics

    async def profile_slow_queries(
        self,
        session: AsyncSession,
        min_calls: int = 5,
        min_time_ms: float = 100,
    ) -> List[QueryMetrics]:
        """Get slow queries from profiled metrics.

        Args:
            session: Database session
            min_calls: Minimum execution count to consider
            min_time_ms: Minimum average execution time in ms

        Returns:
            List of slow query metrics, sorted by total time
        """
        slow_queries = [
            m for m in self.metrics.values()
            if m.execution_count >= min_calls and m.avg_time_ms >= min_time_ms
        ]
        return sorted(slow_queries, key=lambda m: m.total_time_ms, reverse=True)

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all profiled queries."""
        if not self.metrics:
            return {"message": "No queries profiled yet"}

        total_queries = len(self.metrics)
        total_executions = sum(m.execution_count for m in self.metrics.values())
        total_time_ms = sum(m.total_time_ms for m in self.metrics.values())
        slow_queries = sum(1 for m in self.metrics.values() if m.slow_count > 0)
        avg_time_ms = total_time_ms / total_executions if total_executions > 0 else 0

        return {
            "total_unique_queries": total_queries,
            "total_executions": total_executions,
            "total_time_ms": total_time_ms,
            "avg_time_ms": avg_time_ms,
            "slow_queries_count": slow_queries,
            "query_types": {
                qt.value: sum(1 for m in self.metrics.values() if m.query_type == qt)
                for qt in QueryType
            },
        }


class QueryOptimizer:
    """Provides query optimization suggestions and automatic optimizations."""

    # Common optimization patterns
    INDEX_PATTERNS = {
        "WHERE": "WHERE clause columns",
        "JOIN": "JOIN condition columns",
        "ORDER BY": "Sorting columns",
        "GROUP BY": "Grouping columns",
    }

    @staticmethod
    def suggest_indexes(query: str) -> List[str]:
        """Suggest indexes for a query.

        Args:
            query: SQL query to analyze

        Returns:
            List of suggested index definitions
        """
        suggestions = []
        query_upper = query.upper()

        # Simple WHERE clause detection
        if "WHERE" in query_upper:
            # Extract table names and conditions (simplified)
            suggestions.append("CREATE INDEX idx_where_conditions ON table_name (column_name);")

        # JOIN optimization
        if "JOIN" in query_upper:
            suggestions.append("CREATE INDEX idx_join_conditions ON table_name (join_column);")

        # ORDER BY optimization
        if "ORDER BY" in query_upper:
            suggestions.append("CREATE INDEX idx_order_by ON table_name (order_column);")

        return suggestions

    @staticmethod
    async def rewrite_query(query: str) -> str:
        """Suggest query rewrites for optimization.

        Args:
            query: Original query

        Returns:
            Optimized query suggestion
        """
        optimized = query

        # Remove unnecessary SELECT *
        if "SELECT *" in optimized.upper():
            optimized = optimized.replace("SELECT *", "SELECT column1, column2 /* add specific columns */")

        # Add LIMIT if missing
        if "LIMIT" not in optimized.upper() and "OFFSET" not in optimized.upper():
            if "SELECT" in optimized.upper():
                optimized = f"{optimized} LIMIT 1000"

        return optimized
