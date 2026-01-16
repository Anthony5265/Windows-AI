"""Backup and Disaster Recovery Module.

Automated backup management, replication, and recovery procedures.
"""

from typing import Any, Dict, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class BackupStatus(str, Enum):
    """Backup job status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BackupFrequency(str, Enum):
    """Backup frequency."""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


@dataclass
class BackupPolicy:
    """Backup policy."""
    policy_id: str
    name: str
    frequency: BackupFrequency
    retention_days: int
    target_locations: List[str]  # e.g., ["s3", "local", "azure"]
    incremental: bool = True
    compression: bool = True
    encryption: bool = True
    verify_integrity: bool = True
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "policy_id": self.policy_id,
            "name": self.name,
            "frequency": self.frequency.value,
            "retention_days": self.retention_days,
            "target_locations": self.target_locations,
            "incremental": self.incremental,
            "compression": self.compression,
            "encryption": self.encryption,
            "enabled": self.enabled,
        }


@dataclass
class BackupJob:
    """Backup job."""
    job_id: str
    policy_id: str
    status: BackupStatus
    backup_type: str  # "full" or "incremental"
    started_at: datetime
    completed_at: Optional[datetime]
    size_bytes: int
    files_count: int
    checksum: str
    destination: str
    error_message: Optional[str] = None
    retention_until: datetime = field(default_factory=lambda: datetime.now() + timedelta(days=30))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "job_id": self.job_id,
            "policy_id": self.policy_id,
            "status": self.status.value,
            "backup_type": self.backup_type,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "size_bytes": self.size_bytes,
            "files_count": self.files_count,
            "checksum": self.checksum,
            "destination": self.destination,
            "error_message": self.error_message,
        }


@dataclass
class RecoveryPoint:
    """Recovery point."""
    point_id: str
    backup_job_id: str
    timestamp: datetime
    rpo_minutes: int  # Recovery Point Objective
    rto_minutes: int  # Recovery Time Objective
    size_bytes: int
    data_integrity: float  # 0-100%
    metadata: Dict[str, Any] = field(default_factory=dict)


class DisasterRecoveryManager:
    """Disaster recovery manager."""

    def __init__(self):
        """Initialize DR manager."""
        self.policies: Dict[str, BackupPolicy] = {}
        self.jobs: Dict[str, BackupJob] = {}
        self.recovery_points: Dict[str, RecoveryPoint] = {}
        self.last_full_backup: Optional[datetime] = None

    async def create_backup_policy(
        self,
        name: str,
        frequency: BackupFrequency,
        retention_days: int,
        target_locations: List[str],
        incremental: bool = True,
        compression: bool = True,
        encryption: bool = True,
    ) -> BackupPolicy:
        """Create backup policy.

        Args:
            name: Policy name
            frequency: Backup frequency
            retention_days: Retention in days
            target_locations: Target storage locations
            incremental: Enable incremental backups
            compression: Enable compression
            encryption: Enable encryption

        Returns:
            Backup policy
        """
        policy_id = f"policy_{int(datetime.now().timestamp())}"

        policy = BackupPolicy(
            policy_id=policy_id,
            name=name,
            frequency=frequency,
            retention_days=retention_days,
            target_locations=target_locations,
            incremental=incremental,
            compression=compression,
            encryption=encryption,
        )

        self.policies[policy_id] = policy
        logger.info(f"Created backup policy: {name}")

        return policy

    async def schedule_backup(
        self,
        policy_id: str,
    ) -> Optional[BackupJob]:
        """Schedule backup job.

        Args:
            policy_id: Policy ID

        Returns:
            Backup job or None
        """
        policy = self.policies.get(policy_id)

        if not policy or not policy.enabled:
            return None

        # Determine backup type
        backup_type = "full"
        if policy.incremental and self.last_full_backup:
            # Use incremental if not first backup
            if (datetime.now() - self.last_full_backup).days < 7:
                backup_type = "incremental"

        job_id = f"backup_job_{int(datetime.now().timestamp())}"
        destination = policy.target_locations[0] if policy.target_locations else "local"

        job = BackupJob(
            job_id=job_id,
            policy_id=policy_id,
            status=BackupStatus.PENDING,
            backup_type=backup_type,
            started_at=datetime.now(),
            completed_at=None,
            size_bytes=0,
            files_count=0,
            checksum="",
            destination=destination,
            retention_until=datetime.now() + timedelta(days=policy.retention_days),
        )

        self.jobs[job_id] = job
        logger.info(f"Scheduled backup job: {job_id}")

        return job

    async def start_backup_job(self, job_id: str) -> Optional[BackupJob]:
        """Start backup job.

        Args:
            job_id: Job ID

        Returns:
            Updated backup job or None
        """
        job = self.jobs.get(job_id)

        if not job:
            return None

        job.status = BackupStatus.RUNNING
        logger.info(f"Started backup job: {job_id}")

        return job

    async def complete_backup_job(
        self,
        job_id: str,
        size_bytes: int,
        files_count: int,
        checksum: str,
    ) -> Optional[BackupJob]:
        """Complete backup job.

        Args:
            job_id: Job ID
            size_bytes: Backup size in bytes
            files_count: Number of files backed up
            checksum: Backup checksum

        Returns:
            Updated backup job or None
        """
        job = self.jobs.get(job_id)

        if not job:
            return None

        job.status = BackupStatus.COMPLETED
        job.completed_at = datetime.now()
        job.size_bytes = size_bytes
        job.files_count = files_count
        job.checksum = checksum

        if job.backup_type == "full":
            self.last_full_backup = datetime.now()

        # Create recovery point
        recovery_point = RecoveryPoint(
            point_id=f"rp_{job_id}",
            backup_job_id=job_id,
            timestamp=job.completed_at,
            rpo_minutes=self._calculate_rpo(job),
            rto_minutes=self._calculate_rto(job),
            size_bytes=size_bytes,
            data_integrity=100.0,
        )

        self.recovery_points[recovery_point.point_id] = recovery_point
        logger.info(f"Completed backup job: {job_id}")

        return job

    async def fail_backup_job(
        self,
        job_id: str,
        error_message: str,
    ) -> Optional[BackupJob]:
        """Mark backup job as failed.

        Args:
            job_id: Job ID
            error_message: Error message

        Returns:
            Updated backup job or None
        """
        job = self.jobs.get(job_id)

        if not job:
            return None

        job.status = BackupStatus.FAILED
        job.error_message = error_message
        logger.error(f"Backup job failed: {job_id} - {error_message}")

        return job

    async def restore_from_backup(
        self,
        recovery_point_id: str,
        target_location: str,
    ) -> bool:
        """Restore from backup.

        Args:
            recovery_point_id: Recovery point ID
            target_location: Target restore location

        Returns:
            Success status
        """
        recovery_point = self.recovery_points.get(recovery_point_id)

        if not recovery_point:
            return False

        logger.info(
            f"Restoring from backup: {recovery_point_id} to {target_location}"
        )

        # Simulate restore operation
        return True

    async def get_recovery_points(self) -> List[RecoveryPoint]:
        """Get all recovery points.

        Returns:
            List of recovery points
        """
        return list(self.recovery_points.values())

    async def get_backup_jobs(
        self,
        policy_id: Optional[str] = None,
        status: Optional[BackupStatus] = None,
    ) -> List[BackupJob]:
        """Get backup jobs.

        Args:
            policy_id: Filter by policy ID
            status: Filter by status

        Returns:
            List of backup jobs
        """
        jobs = list(self.jobs.values())

        if policy_id:
            jobs = [j for j in jobs if j.policy_id == policy_id]

        if status:
            jobs = [j for j in jobs if j.status == status]

        return jobs

    async def cleanup_expired_backups(self) -> int:
        """Clean up expired backups.

        Returns:
            Number of backups deleted
        """
        now = datetime.now()
        deleted_count = 0

        # Clean backup jobs
        expired_jobs = [
            job_id for job_id, job in self.jobs.items()
            if job.completed_at and job.completed_at < (now - timedelta(days=365))
        ]

        for job_id in expired_jobs:
            del self.jobs[job_id]
            deleted_count += 1

        # Clean recovery points
        expired_rps = [
            rp_id for rp_id, rp in self.recovery_points.items()
            if rp.timestamp < (now - timedelta(days=365))
        ]

        for rp_id in expired_rps:
            del self.recovery_points[rp_id]
            deleted_count += 1

        logger.info(f"Cleaned up {deleted_count} expired backups")
        return deleted_count

    async def get_dr_status(self) -> Dict[str, Any]:
        """Get disaster recovery status.

        Returns:
            DR status summary
        """
        completed_jobs = [
            j for j in self.jobs.values()
            if j.status == BackupStatus.COMPLETED
        ]

        total_backup_size = sum(j.size_bytes for j in completed_jobs)

        last_completed = None
        if completed_jobs:
            last_completed = max(j.completed_at for j in completed_jobs)

        return {
            "policies_count": len(self.policies),
            "enabled_policies": sum(1 for p in self.policies.values() if p.enabled),
            "total_backup_jobs": len(self.jobs),
            "completed_jobs": len(completed_jobs),
            "failed_jobs": sum(1 for j in self.jobs.values() if j.status == BackupStatus.FAILED),
            "running_jobs": sum(1 for j in self.jobs.values() if j.status == BackupStatus.RUNNING),
            "total_backup_size_bytes": total_backup_size,
            "recovery_points": len(self.recovery_points),
            "last_backup": last_completed.isoformat() if last_completed else None,
            "average_backup_size_bytes": (
                total_backup_size // len(completed_jobs) if completed_jobs else 0
            ),
        }

    async def get_rto_rpo_metrics(self) -> Dict[str, Any]:
        """Get RTO/RPO metrics.

        Returns:
            RTO/RPO metrics
        """
        recovery_points = list(self.recovery_points.values())

        if not recovery_points:
            return {
                "average_rto_minutes": 0,
                "average_rpo_minutes": 0,
                "best_rto_minutes": 0,
                "best_rpo_minutes": 0,
            }

        return {
            "average_rto_minutes": sum(rp.rto_minutes for rp in recovery_points) // len(recovery_points),
            "average_rpo_minutes": sum(rp.rpo_minutes for rp in recovery_points) // len(recovery_points),
            "best_rto_minutes": min(rp.rto_minutes for rp in recovery_points),
            "best_rpo_minutes": min(rp.rpo_minutes for rp in recovery_points),
            "total_recovery_points": len(recovery_points),
        }

    def _calculate_rto(self, job: BackupJob) -> int:
        """Calculate Recovery Time Objective.

        Args:
            job: Backup job

        Returns:
            RTO in minutes
        """
        # Estimate based on backup size (assuming 100MB/min restore speed)
        restore_duration = max(10, job.size_bytes // (100 * 1024 * 1024))
        return restore_duration + 5  # Add 5 min for verification

    def _calculate_rpo(self, job: BackupJob) -> int:
        """Calculate Recovery Point Objective.

        Args:
            job: Backup job

        Returns:
            RPO in minutes
        """
        # RPO is backup frequency
        return 60 if job.backup_type == "incremental" else 1440  # 1 hour for incremental, 1 day for full
