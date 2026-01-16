"""Transaction optimization and deadlock detection.

Analyzes transaction patterns, detects deadlocks,
and recommends optimization strategies.
"""

import re
import asyncio
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TransactionIsolation(str, Enum):
    """PostgreSQL transaction isolation levels."""
    READ_UNCOMMITTED = "read_uncommitted"
    READ_COMMITTED = "read_committed"
    REPEATABLE_READ = "repeatable_read"
    SERIALIZABLE = "serializable"


class DeadlockSeverity(str, Enum):
    """Severity levels for deadlock detection."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class TransactionMetric:
    """Individual transaction metric."""
    transaction_id: int
    start_time: datetime
    query: str
    isolation_level: TransactionIsolation
    duration_ms: float
    rows_affected: int
    locks_held: List[str] = field(default_factory=list)
    success: bool = True
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "transaction_id": self.transaction_id,
            "start_time": self.start_time.isoformat(),
            "duration_ms": self.duration_ms,
            "rows_affected": self.rows_affected,
            "isolation_level": self.isolation_level.value,
            "locks_held": self.locks_held,
            "success": self.success,
            "error_message": self.error_message,
        }


@dataclass
class DeadlockEvent:
    """Deadlock event details."""
    detected_at: datetime
    table_names: List[str]
    transaction_ids: List[int]
    severity: DeadlockSeverity
    query_patterns: List[str]
    suggested_fix: str
    resolution_time_ms: Optional[float] = None
    rollback_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "detected_at": self.detected_at.isoformat(),
            "tables": self.table_names,
            "transactions": self.transaction_ids,
            "severity": self.severity.value,
            "patterns": self.query_patterns,
            "fix": self.suggested_fix,
            "resolution_time_ms": self.resolution_time_ms,
            "rollbacks": self.rollback_count,
        }


@dataclass
class LockWaitEvent:
    """Lock wait event details."""
    waiting_transaction_id: int
    blocking_transaction_id: int
    table_name: str
    lock_type: str
    wait_duration_ms: float
    query: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "waiting_xid": self.waiting_transaction_id,
            "blocking_xid": self.blocking_transaction_id,
            "table": self.table_name,
            "lock_type": self.lock_type,
            "wait_duration_ms": self.wait_duration_ms,
            "query": self.query,
        }


class DeadlockDetector:
    """Detects and analyzes deadlock patterns."""

    def __init__(self):
        """Initialize deadlock detector."""
        self.deadlock_events: List[DeadlockEvent] = []
        self.lock_wait_events: List[LockWaitEvent] = []
        self.detected_at_last_check = datetime.now()

    def analyze_deadlock_log(self, deadlock_text: str) -> Optional[DeadlockEvent]:
        """Parse and analyze PostgreSQL deadlock log.

        Args:
            deadlock_text: Raw deadlock log text

        Returns:
            DeadlockEvent if deadlock detected, None otherwise
        """
        # Extract table names
        table_matches = re.findall(
            r'relation "([^"]+)"',
            deadlock_text
        )
        table_names = list(set(table_matches))

        # Extract transaction IDs
        xid_matches = re.findall(
            r'process \d+ acquires (?:ExclusiveLock|ShareLock).*on ([0-9]+)',
            deadlock_text
        )
        transaction_ids = [int(xid) for xid in xid_matches[:2]]

        # Extract query patterns
        query_patterns = re.findall(
            r'(INSERT|UPDATE|DELETE|SELECT).*(?:INTO|FROM|ON).*(\w+)',
            deadlock_text,
            re.IGNORECASE
        )

        if not transaction_ids or not table_names:
            return None

        # Determine severity based on patterns
        if len(table_names) > 2:
            severity = DeadlockSeverity.CRITICAL
        elif len(transaction_ids) > 1 and query_patterns:
            severity = DeadlockSeverity.HIGH
        else:
            severity = DeadlockSeverity.MEDIUM

        # Generate suggested fix
        suggested_fix = self._generate_deadlock_fix(
            query_patterns, table_names, transaction_ids
        )

        event = DeadlockEvent(
            detected_at=datetime.now(),
            table_names=table_names,
            transaction_ids=transaction_ids,
            severity=severity,
            query_patterns=[f"{op} on {table}" for op, table in query_patterns],
            suggested_fix=suggested_fix,
        )

        self.deadlock_events.append(event)
        return event

    def _generate_deadlock_fix(
        self,
        patterns: List[Tuple[str, str]],
        tables: List[str],
        xids: List[int],
    ) -> str:
        """Generate deadlock fix recommendation.

        Args:
            patterns: Query operation patterns
            tables: Affected tables
            xids: Transaction IDs

        Returns:
            Suggested fix string
        """
        fixes = []

        # Analyze access patterns
        update_count = sum(1 for op, _ in patterns if op.upper() == "UPDATE")
        if update_count > 1:
            fixes.append("Serialize UPDATE operations on same tables")
            fixes.append("Use explicit LOCK TABLE IN EXCLUSIVE MODE at transaction start")

        if len(tables) > 1:
            fixes.append(f"Ensure consistent lock ordering across {len(tables)} tables")
            fixes.append("Access tables in same order in all transactions")

        if not fixes:
            fixes.append("Reduce transaction scope")
            fixes.append("Use READ COMMITTED isolation level if possible")

        return " | ".join(fixes)

    async def detect_lock_waits(
        self,
        query_func: callable,
    ) -> List[LockWaitEvent]:
        """Detect current lock wait events.

        Args:
            query_func: Async function to query lock waits

        Returns:
            List of detected lock wait events
        """
        try:
            lock_waits = await query_func(
                """
                SELECT waiting_pid, blocking_pid, relation::regclass, locktype, 
                       EXTRACT(EPOCH FROM (now() - backend_xmin_xid))::int as wait_ms,
                       query
                FROM pg_locks l1 
                JOIN pg_locks l2 ON l1.locktype = l2.locktype AND l1.database = l2.database
                WHERE l1.granted = false AND l2.granted = true
                """
            )

            events = []
            for lock in lock_waits:
                event = LockWaitEvent(
                    waiting_transaction_id=lock.get("waiting_pid", 0),
                    blocking_transaction_id=lock.get("blocking_pid", 0),
                    table_name=lock.get("relation", "unknown"),
                    lock_type=lock.get("locktype", "unknown"),
                    wait_duration_ms=lock.get("wait_ms", 0),
                    query=lock.get("query", ""),
                )
                events.append(event)
                self.lock_wait_events.append(event)

            return events
        except Exception as e:
            logger.error(f"Error detecting lock waits: {e}")
            return []

    async def get_deadlock_report(self) -> Dict[str, Any]:
        """Generate deadlock analysis report.

        Returns:
            Deadlock metrics and recommendations
        """
        if not self.deadlock_events:
            return {"deadlock_count": 0, "events": []}

        total_critical = sum(
            1 for e in self.deadlock_events
            if e.severity == DeadlockSeverity.CRITICAL
        )
        total_high = sum(
            1 for e in self.deadlock_events
            if e.severity == DeadlockSeverity.HIGH
        )

        return {
            "total_deadlocks": len(self.deadlock_events),
            "critical": total_critical,
            "high": total_high,
            "recent_events": [
                e.to_dict() for e in self.deadlock_events[-10:]
            ],
        }


class TransactionOptimizer:
    """Analyzes and optimizes transaction patterns."""

    def __init__(self):
        """Initialize transaction optimizer."""
        self.transactions: Dict[int, TransactionMetric] = {}
        self.deadlock_detector = DeadlockDetector()

    async def record_transaction(
        self,
        transaction_id: int,
        query: str,
        start_time: datetime,
        duration_ms: float,
        rows_affected: int,
        isolation_level: TransactionIsolation = TransactionIsolation.READ_COMMITTED,
        success: bool = True,
        error_message: Optional[str] = None,
    ):
        """Record a transaction for analysis.

        Args:
            transaction_id: Transaction ID
            query: SQL query
            start_time: Transaction start time
            duration_ms: Transaction duration
            rows_affected: Number of rows affected
            isolation_level: Transaction isolation level
            success: Whether transaction succeeded
            error_message: Error message if failed
        """
        metric = TransactionMetric(
            transaction_id=transaction_id,
            start_time=start_time,
            query=query,
            isolation_level=isolation_level,
            duration_ms=duration_ms,
            rows_affected=rows_affected,
            success=success,
            error_message=error_message,
        )
        self.transactions[transaction_id] = metric

    async def analyze_transaction_pattern(self, query: str) -> Dict[str, Any]:
        """Analyze transaction query patterns.

        Args:
            query: SQL query

        Returns:
            Pattern analysis results
        """
        # Extract operations
        operations = re.findall(
            r'\b(INSERT|UPDATE|DELETE|SELECT|BEGIN|COMMIT|ROLLBACK)\b',
            query,
            re.IGNORECASE
        )

        # Extract tables
        tables = re.findall(
            r'(?:FROM|INTO|UPDATE)\s+(\w+)',
            query,
            re.IGNORECASE
        )

        # Extract joins
        joins = re.findall(
            r'(?:INNER|LEFT|RIGHT|FULL)?\s+JOIN\s+(\w+)',
            query,
            re.IGNORECASE
        )

        # Detect potential issues
        issues = []
        if "SELECT" in [op.upper() for op in operations]:
            if len(tables) > 3:
                issues.append("Complex multi-table join - consider query simplification")
            if "FOR UPDATE" not in query.upper():
                issues.append("Consider row-level locking with FOR UPDATE if updating selected rows")

        if "UPDATE" in [op.upper() for op in operations] and len(tables) > 1:
            issues.append("Multi-table UPDATE - may cause deadlock with other transactions")

        return {
            "operations": operations,
            "tables": tables,
            "joins": joins,
            "complexity": len(operations) + len(tables),
            "issues": issues,
        }

    async def detect_n_plus_one(
        self,
        query_log: List[str],
        threshold: int = 5,
    ) -> List[Dict[str, Any]]:
        """Detect N+1 query patterns.

        Args:
            query_log: List of executed queries
            threshold: Minimum repetitions to flag

        Returns:
            Detected N+1 patterns
        """
        query_patterns: Dict[str, int] = {}

        for query in query_log:
            # Normalize query (remove specific values)
            normalized = re.sub(r'\d+', '?', query)
            normalized = re.sub(r"'[^']*'", "'?'", normalized)
            query_patterns[normalized] = query_patterns.get(normalized, 0) + 1

        # Find patterns exceeding threshold
        n_plus_one = [
            {
                "pattern": pattern,
                "count": count,
                "example": query_log[[
                    re.sub(r'\d+', '?', q).replace("'", "'?'") for q in query_log
                ].index(pattern)],
            }
            for pattern, count in query_patterns.items()
            if count >= threshold
        ]

        return n_plus_one

    async def suggest_optimizations(self) -> List[Dict[str, str]]:
        """Generate transaction optimization suggestions.

        Returns:
            List of optimization recommendations
        """
        suggestions = []

        # Analyze transaction durations
        if self.transactions:
            durations = [t.duration_ms for t in self.transactions.values()]
            avg_duration = sum(durations) / len(durations)
            max_duration = max(durations)

            if max_duration > avg_duration * 3:
                suggestions.append({
                    "type": "high_latency",
                    "issue": f"Max transaction duration ({max_duration:.0f}ms) is {max_duration/avg_duration:.1f}x average",
                    "fix": "Investigate slow queries within transactions, consider query optimization or indexing"
                })

        # Check isolation level recommendations
        serializable_count = sum(
            1 for t in self.transactions.values()
            if t.isolation_level == TransactionIsolation.SERIALIZABLE
        )
        if serializable_count > len(self.transactions) * 0.1:
            suggestions.append({
                "type": "isolation_level",
                "issue": f"{serializable_count} transactions using SERIALIZABLE isolation",
                "fix": "Consider READ_COMMITTED for non-critical transactions to reduce lock contention"
            })

        # Check transaction sizes
        large_transactions = [
            t for t in self.transactions.values()
            if t.rows_affected > 1000
        ]
        if large_transactions:
            suggestions.append({
                "type": "batch_size",
                "issue": f"{len(large_transactions)} transactions affecting >1000 rows",
                "fix": "Break large transactions into smaller batches to reduce lock hold times"
            })

        return suggestions

    async def get_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive optimization report.

        Returns:
            Complete optimization analysis
        """
        if not self.transactions:
            return {"transaction_count": 0, "transactions": []}

        durations = [t.duration_ms for t in self.transactions.values()]
        success_count = sum(1 for t in self.transactions.values() if t.success)

        return {
            "total_transactions": len(self.transactions),
            "successful": success_count,
            "failed": len(self.transactions) - success_count,
            "success_rate": f"{success_count / len(self.transactions) * 100:.1f}%",
            "duration_stats": {
                "min_ms": min(durations),
                "max_ms": max(durations),
                "avg_ms": sum(durations) / len(durations),
                "p95_ms": sorted(durations)[int(len(durations) * 0.95)],
            },
            "deadlock_analysis": await self.deadlock_detector.get_deadlock_report(),
            "suggestions": await self.suggest_optimizations(),
            "recent_transactions": [
                t.to_dict() for t in list(self.transactions.values())[-20:]
            ],
        }
