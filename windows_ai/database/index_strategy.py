"""Database index strategy and optimization module.

Analyzes query patterns, recommends indexes, and implements
optimized index strategies for PostgreSQL databases.
"""

import asyncio
import hashlib
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class IndexType(str, Enum):
    """Types of database indexes."""
    BTREE = "btree"  # Default, general purpose
    HASH = "hash"  # Equality operators
    GIST = "gist"  # Geometric types, text search
    GIN = "gin"  # Arrays, full-text search
    BRIN = "brin"  # Large tables, sequential access
    PARTIAL = "partial"  # Conditional indexes


class IndexStrategy(str, Enum):
    """Index optimization strategies."""
    SINGLE_COLUMN = "single_column"  # Simple column index
    COMPOSITE = "composite"  # Multi-column index
    COVERING = "covering"  # Includes non-key columns
    PARTIAL = "partial"  # Conditional index
    EXPRESSION = "expression"  # Index on expression


@dataclass
class IndexRecommendation:
    """Recommendation to create an index."""
    table_name: str
    index_name: str
    columns: List[str]
    index_type: IndexType = IndexType.BTREE
    strategy: IndexStrategy = IndexStrategy.SINGLE_COLUMN
    where_clause: Optional[str] = None
    included_columns: List[str] = field(default_factory=list)
    priority: int = 1  # 1-10, higher = more important
    estimated_benefit_percent: float = 0.0
    reason: str = ""
    query_patterns: List[str] = field(default_factory=list)

    @property
    def create_statement(self) -> str:
        """Generate CREATE INDEX statement."""
        col_list = ", ".join(self.columns)
        included = f" INCLUDE ({', '.join(self.included_columns)})" if self.included_columns else ""
        where = f" WHERE {self.where_clause}" if self.where_clause else ""

        return (
            f"CREATE INDEX CONCURRENTLY {self.index_name}\n"
            f"ON {self.table_name} USING {self.index_type.value}\n"
            f"({col_list}){included}{where};"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "table": self.table_name,
            "index_name": self.index_name,
            "columns": self.columns,
            "type": self.index_type.value,
            "strategy": self.strategy.value,
            "priority": self.priority,
            "estimated_benefit": f"{self.estimated_benefit_percent:.1f}%",
            "reason": self.reason,
            "query_patterns": self.query_patterns,
            "create_statement": self.create_statement,
        }


@dataclass
class IndexUsageStats:
    """Statistics on index usage."""
    index_name: str
    table_name: str
    scans: int = 0
    rows_read: int = 0
    rows_returned: int = 0
    size_mb: float = 0.0
    idx_tup_read: int = 0
    idx_tup_fetch: int = 0
    last_scan: Optional[datetime] = None

    @property
    def efficiency(self) -> float:
        """Calculate index efficiency (0-100)."""
        if self.idx_tup_read == 0:
            return 0.0
        # Ratio of fetches to reads
        return (self.idx_tup_fetch / self.idx_tup_read * 100) if self.idx_tup_read > 0 else 0.0

    @property
    def is_unused(self) -> bool:
        """Check if index is unused."""
        return self.scans == 0

    @property
    def is_bloated(self) -> bool:
        """Check if index is bloated (rarely used relative to size)."""
        if self.size_mb < 10:  # Small indexes are OK
            return False
        return self.scans < 10 and self.size_mb > 50

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "index": self.index_name,
            "table": self.table_name,
            "scans": self.scans,
            "rows_read": self.rows_read,
            "rows_returned": self.rows_returned,
            "size_mb": self.size_mb,
            "efficiency": f"{self.efficiency:.1f}%",
            "unused": self.is_unused,
            "bloated": self.is_bloated,
            "last_scan": self.last_scan.isoformat() if self.last_scan else None,
        }


@dataclass
class TableStatistics:
    """Statistics for a database table."""
    table_name: str
    row_count: int = 0
    table_size_mb: float = 0.0
    indexes: List[IndexUsageStats] = field(default_factory=list)
    sequential_scans: int = 0
    index_scans: int = 0
    last_vacuum: Optional[datetime] = None
    last_analyze: Optional[datetime] = None

    @property
    def index_scan_ratio(self) -> float:
        """Calculate ratio of index scans to total scans."""
        total = self.sequential_scans + self.index_scans
        if total == 0:
            return 0.0
        return (self.index_scans / total) * 100

    @property
    def vacuum_needed(self) -> bool:
        """Check if table needs vacuum."""
        if not self.last_vacuum:
            return True
        days_since = (datetime.now() - self.last_vacuum).days
        return days_since > 7

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "table": self.table_name,
            "row_count": self.row_count,
            "table_size_mb": self.table_size_mb,
            "indexes": len(self.indexes),
            "sequential_scans": self.sequential_scans,
            "index_scans": self.index_scans,
            "index_scan_ratio": f"{self.index_scan_ratio:.1f}%",
            "vacuum_needed": self.vacuum_needed,
            "last_vacuum": self.last_vacuum.isoformat() if self.last_vacuum else None,
            "last_analyze": self.last_analyze.isoformat() if self.last_analyze else None,
        }


class IndexStrategy:
    """Analyzes and recommends index strategies."""

    def __init__(self):
        """Initialize index strategy analyzer."""
        self.recommendations: Dict[str, List[IndexRecommendation]] = {}
        self.index_usage: Dict[str, IndexUsageStats] = {}
        self.table_stats: Dict[str, TableStatistics] = {}

    def analyze_query_pattern(self, query: str) -> Dict[str, Any]:
        """Analyze a query to identify index opportunities.

        Args:
            query: SQL query string

        Returns:
            Analysis results including columns used and operations
        """
        # Parse WHERE clause
        where_cols = self._extract_where_columns(query)

        # Parse JOIN clause
        join_cols = self._extract_join_columns(query)

        # Parse ORDER BY
        order_cols = self._extract_order_by_columns(query)

        # Parse GROUP BY
        group_cols = self._extract_group_by_columns(query)

        return {
            "where_columns": where_cols,
            "join_columns": join_cols,
            "order_columns": order_cols,
            "group_columns": group_cols,
            "index_candidates": where_cols + join_cols + order_cols,
        }

    def recommend_indexes(
        self,
        table_name: str,
        where_columns: List[str],
        join_columns: List[str],
        order_columns: List[str],
        group_columns: List[str],
    ) -> List[IndexRecommendation]:
        """Generate index recommendations based on query patterns.

        Args:
            table_name: Name of the table
            where_columns: Columns in WHERE clause
            join_columns: Columns in JOIN conditions
            order_columns: Columns in ORDER BY
            group_columns: Columns in GROUP BY

        Returns:
            List of index recommendations
        """
        recommendations = []

        # 1. Single column indexes for high-frequency filters
        for col in where_columns[:3]:  # Top 3 where columns
            idx_name = f"idx_{table_name}_{col}"
            rec = IndexRecommendation(
                table_name=table_name,
                index_name=idx_name,
                columns=[col],
                strategy=IndexStrategy.SINGLE_COLUMN,
                priority=8,
                estimated_benefit_percent=25.0,
                reason=f"Frequent filter on {col} in WHERE clause",
                query_patterns=["SELECT * FROM ... WHERE " + col],
            )
            recommendations.append(rec)

        # 2. Composite index for WHERE + ORDER BY
        if where_columns and order_columns:
            composite_cols = where_columns + order_columns
            idx_name = f"idx_{table_name}_{'_'.join(composite_cols)}"
            rec = IndexRecommendation(
                table_name=table_name,
                index_name=idx_name,
                columns=composite_cols,
                strategy=IndexStrategy.COMPOSITE,
                priority=9,
                estimated_benefit_percent=40.0,
                reason="Composite index for WHERE + ORDER BY (enables index-only scan)",
                query_patterns=["SELECT * FROM ... WHERE ... ORDER BY ..."],
            )
            recommendations.append(rec)

        # 3. Covering index for SELECT with specific columns
        if where_columns:
            idx_name = f"idx_{table_name}_covering"
            rec = IndexRecommendation(
                table_name=table_name,
                index_name=idx_name,
                columns=where_columns,
                included_columns=order_columns[:3],  # Include ORDER BY cols
                strategy=IndexStrategy.COVERING,
                priority=9,
                estimated_benefit_percent=45.0,
                reason="Covering index for index-only scans (no table access)",
                query_patterns=["Index-only scans enable fast queries"],
            )
            recommendations.append(rec)

        # 4. Partial index for active records
        idx_name = f"idx_{table_name}_active"
        rec = IndexRecommendation(
            table_name=table_name,
            index_name=idx_name,
            columns=where_columns if where_columns else ["id"],
            strategy=IndexStrategy.PARTIAL,
            where_clause="active = true",
            priority=6,
            estimated_benefit_percent=15.0,
            reason="Partial index for frequently accessed active records",
            query_patterns=["SELECT * FROM ... WHERE active = true"],
        )
        recommendations.append(rec)

        # 5. JOIN indexes
        for col in join_columns:
            idx_name = f"idx_{table_name}_{col}_fk"
            rec = IndexRecommendation(
                table_name=table_name,
                index_name=idx_name,
                columns=[col],
                strategy=IndexStrategy.SINGLE_COLUMN,
                priority=7,
                estimated_benefit_percent=20.0,
                reason=f"Foreign key/JOIN index on {col}",
                query_patterns=[f"... JOIN ... ON .{col} = ..."],
            )
            recommendations.append(rec)

        return recommendations

    def suggest_unused_index_drops(self) -> List[str]:
        """Suggest indexes that should be dropped.

        Returns:
            List of DROP INDEX statements
        """
        drop_statements = []

        for idx_name, stats in self.index_usage.items():
            if stats.is_unused:
                drop_statements.append(f"DROP INDEX CONCURRENTLY {idx_name};")
            elif stats.is_bloated:
                # Suggest reindex
                drop_statements.append(f"-- {idx_name} is bloated, consider REINDEX")
                drop_statements.append(f"-- REINDEX INDEX CONCURRENTLY {idx_name};")

        return drop_statements

    def get_index_maintenance_recommendations(self) -> List[str]:
        """Get recommendations for index maintenance.

        Returns:
            List of recommended maintenance statements
        """
        recommendations = []

        # Suggest REINDEX for fragmented indexes
        for idx_name, stats in self.index_usage.items():
            if stats.efficiency < 50:  # Low efficiency = fragmentation
                recommendations.append(
                    f"REINDEX INDEX CONCURRENTLY {idx_name}; -- Efficiency: {stats.efficiency:.1f}%"
                )

        # Suggest ANALYZE for outdated statistics
        for table, stats in self.table_stats.items():
            if stats.last_analyze is None or \
               (datetime.now() - stats.last_analyze).days > 7:
                recommendations.append(f"ANALYZE {table};")

        # Suggest VACUUM
        for table, stats in self.table_stats.items():
            if stats.vacuum_needed:
                recommendations.append(f"VACUUM ANALYZE {table};")

        return recommendations

    def _extract_where_columns(self, query: str) -> List[str]:
        """Extract columns used in WHERE clause."""
        # Simplified extraction - in production would use proper SQL parsing
        import re
        where_match = re.search(r'WHERE\s+(.+?)(?:ORDER|GROUP|LIMIT|HAVING|;|$)', query, re.IGNORECASE)
        if where_match:
            where_clause = where_match.group(1)
            # Extract column names (simplified)
            cols = re.findall(r'\b(\w+)\s*=', where_clause)
            return list(set(cols))
        return []

    def _extract_join_columns(self, query: str) -> List[str]:
        """Extract columns used in JOIN conditions."""
        import re
        join_matches = re.findall(r'ON\s+(.+?)(?:WHERE|LIMIT|;|$)', query, re.IGNORECASE)
        cols = []
        for join_clause in join_matches:
            found = re.findall(r'\.(\w+)\s*=', join_clause)
            cols.extend(found)
        return list(set(cols))

    def _extract_order_by_columns(self, query: str) -> List[str]:
        """Extract columns used in ORDER BY."""
        import re
        order_match = re.search(r'ORDER\s+BY\s+(.+?)(?:LIMIT|;|$)', query, re.IGNORECASE)
        if order_match:
            order_clause = order_match.group(1)
            cols = re.findall(r'\b(\w+)(?:\s+ASC|\s+DESC)?', order_clause)
            return list(set(cols))
        return []

    def _extract_group_by_columns(self, query: str) -> List[str]:
        """Extract columns used in GROUP BY."""
        import re
        group_match = re.search(r'GROUP\s+BY\s+(.+?)(?:HAVING|ORDER|LIMIT|;|$)', query, re.IGNORECASE)
        if group_match:
            group_clause = group_match.group(1)
            cols = re.findall(r'\b(\w+)', group_clause)
            return list(set(cols))
        return []

    def get_strategy_report(self) -> Dict[str, Any]:
        """Generate comprehensive index strategy report.

        Returns:
            Detailed report with recommendations and statistics
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "total_recommendations": sum(len(recs) for recs in self.recommendations.values()),
            "recommendations_by_table": {
                table: [rec.to_dict() for rec in recs]
                for table, recs in self.recommendations.items()
            },
            "index_usage": {
                idx_name: stats.to_dict()
                for idx_name, stats in self.index_usage.items()
            },
            "table_statistics": {
                table: stats.to_dict()
                for table, stats in self.table_stats.items()
            },
            "unused_indexes": [
                stats.index_name
                for stats in self.index_usage.values()
                if stats.is_unused
            ],
            "bloated_indexes": [
                stats.index_name
                for stats in self.index_usage.values()
                if stats.is_bloated
            ],
            "maintenance_recommendations": self.get_index_maintenance_recommendations(),
        }
