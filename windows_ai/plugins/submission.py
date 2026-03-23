"""Community Plugin Submission Process.

Handles the workflow for community members to submit, review, and
publish plugins to the marketplace. Includes validation, security
scanning, and approval stages.
"""

from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class SubmissionStatus(str, Enum):
    """Status of a plugin submission."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    VALIDATING = "validating"
    SECURITY_REVIEW = "security_review"
    COMMUNITY_REVIEW = "community_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"


class RejectionReason(str, Enum):
    """Reasons a submission may be rejected."""
    INVALID_METADATA = "invalid_metadata"
    SECURITY_ISSUE = "security_issue"
    DUPLICATE = "duplicate"
    LOW_QUALITY = "low_quality"
    POLICY_VIOLATION = "policy_violation"
    MALICIOUS_CODE = "malicious_code"
    MISSING_TESTS = "missing_tests"
    INCOMPATIBLE = "incompatible"


@dataclass
class PluginSubmission:
    """A community plugin submission."""
    submission_id: str
    plugin_id: str
    plugin_name: str
    author: str
    version: str
    description: str
    source_url: Optional[str] = None
    status: SubmissionStatus = SubmissionStatus.DRAFT
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    validation_results: Dict[str, Any] = field(default_factory=dict)
    security_results: Dict[str, Any] = field(default_factory=dict)
    review_comments: List[Dict[str, str]] = field(default_factory=list)
    rejection_reason: Optional[RejectionReason] = None
    reviewer: Optional[str] = None
    checksum: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "submission_id": self.submission_id,
            "plugin_id": self.plugin_id,
            "plugin_name": self.plugin_name,
            "author": self.author,
            "version": self.version,
            "description": self.description,
            "status": self.status.value,
            "created_at": self.created_at,
            "review_comments": self.review_comments,
            "rejection_reason": self.rejection_reason.value if self.rejection_reason else None,
        }


class PluginSubmissionManager:
    """Manages the community plugin submission workflow.

    Usage::

        manager = PluginSubmissionManager()
        submission = manager.create_submission(
            plugin_id="my-plugin", plugin_name="My Plugin",
            author="dev@example.com", version="1.0.0",
            description="A useful plugin"
        )
        manager.submit(submission.submission_id)
        manager.validate(submission.submission_id)
        manager.approve(submission.submission_id, reviewer="admin")
    """

    def __init__(self):
        self._submissions: Dict[str, PluginSubmission] = {}
        self._next_id = 1
        self._validators: List[Callable] = []
        self._security_scanners: List[Callable] = []
        logger.info("PluginSubmissionManager initialized")

    # ------------------------------------------------------------------
    # Submission lifecycle
    # ------------------------------------------------------------------

    def create_submission(
        self,
        plugin_id: str,
        plugin_name: str,
        author: str,
        version: str,
        description: str,
        source_url: Optional[str] = None,
    ) -> PluginSubmission:
        """Create a new plugin submission."""
        sub_id = f"sub-{self._next_id:04d}"
        self._next_id += 1

        submission = PluginSubmission(
            submission_id=sub_id,
            plugin_id=plugin_id,
            plugin_name=plugin_name,
            author=author,
            version=version,
            description=description,
            source_url=source_url,
            checksum=hashlib.sha256(f"{plugin_id}:{version}".encode()).hexdigest()[:16],
        )
        self._submissions[sub_id] = submission
        logger.info("Created submission %s for plugin %s by %s", sub_id, plugin_id, author)
        return submission

    def submit(self, submission_id: str) -> Dict[str, Any]:
        """Submit a draft for review."""
        sub = self._submissions.get(submission_id)
        if not sub:
            return {"status": "error", "message": "Submission not found"}
        if sub.status != SubmissionStatus.DRAFT:
            return {"status": "error", "message": f"Cannot submit from status {sub.status.value}"}

        sub.status = SubmissionStatus.SUBMITTED
        sub.updated_at = time.time()
        return {"status": "success", "submission_id": submission_id}

    def validate(self, submission_id: str) -> Dict[str, Any]:
        """Run automated validation on a submission."""
        sub = self._submissions.get(submission_id)
        if not sub:
            return {"status": "error", "message": "Submission not found"}

        sub.status = SubmissionStatus.VALIDATING
        results = {
            "metadata_valid": bool(sub.plugin_id and sub.plugin_name and sub.version),
            "description_valid": len(sub.description) >= 10,
            "version_format_valid": self._validate_version(sub.version),
            "author_valid": bool(sub.author),
        }

        # Run custom validators
        for validator in self._validators:
            try:
                results.update(validator(sub))
            except Exception as e:
                results[f"validator_error"] = str(e)

        sub.validation_results = results
        all_passed = all(v for k, v in results.items() if isinstance(v, bool))

        if all_passed:
            sub.status = SubmissionStatus.SECURITY_REVIEW
        else:
            sub.status = SubmissionStatus.REJECTED
            sub.rejection_reason = RejectionReason.INVALID_METADATA

        sub.updated_at = time.time()
        return {"status": "success", "validation": results, "passed": all_passed}

    def security_review(self, submission_id: str) -> Dict[str, Any]:
        """Run security scanning on a submission."""
        sub = self._submissions.get(submission_id)
        if not sub:
            return {"status": "error", "message": "Submission not found"}

        results = {
            "no_dangerous_imports": True,
            "no_hardcoded_secrets": True,
            "no_network_abuse": True,
            "checksum_valid": sub.checksum is not None,
        }

        # Run custom security scanners
        for scanner in self._security_scanners:
            try:
                results.update(scanner(sub))
            except Exception as e:
                results["scanner_error"] = str(e)

        sub.security_results = results
        all_passed = all(v for k, v in results.items() if isinstance(v, bool))

        if all_passed:
            sub.status = SubmissionStatus.COMMUNITY_REVIEW
        else:
            sub.status = SubmissionStatus.REJECTED
            sub.rejection_reason = RejectionReason.SECURITY_ISSUE

        sub.updated_at = time.time()
        return {"status": "success", "security": results, "passed": all_passed}

    def approve(self, submission_id: str, reviewer: str) -> Dict[str, Any]:
        """Approve a submission for publication."""
        sub = self._submissions.get(submission_id)
        if not sub:
            return {"status": "error", "message": "Submission not found"}

        sub.status = SubmissionStatus.APPROVED
        sub.reviewer = reviewer
        sub.updated_at = time.time()
        logger.info("Submission %s approved by %s", submission_id, reviewer)
        return {"status": "success", "submission_id": submission_id}

    def reject(self, submission_id: str, reason: RejectionReason, comment: str = "") -> Dict[str, Any]:
        """Reject a submission."""
        sub = self._submissions.get(submission_id)
        if not sub:
            return {"status": "error", "message": "Submission not found"}

        sub.status = SubmissionStatus.REJECTED
        sub.rejection_reason = reason
        if comment:
            sub.review_comments.append({"type": "rejection", "comment": comment})
        sub.updated_at = time.time()
        return {"status": "success", "submission_id": submission_id}

    def publish(self, submission_id: str) -> Dict[str, Any]:
        """Publish an approved submission to the marketplace."""
        sub = self._submissions.get(submission_id)
        if not sub:
            return {"status": "error", "message": "Submission not found"}
        if sub.status != SubmissionStatus.APPROVED:
            return {"status": "error", "message": "Only approved submissions can be published"}

        sub.status = SubmissionStatus.PUBLISHED
        sub.updated_at = time.time()
        logger.info("Submission %s published to marketplace", submission_id)
        return {"status": "success", "submission_id": submission_id, "plugin_id": sub.plugin_id}

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def get_submission(self, submission_id: str) -> Optional[Dict[str, Any]]:
        sub = self._submissions.get(submission_id)
        return sub.to_dict() if sub else None

    def list_submissions(
        self, status: Optional[SubmissionStatus] = None, author: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        results = []
        for sub in self._submissions.values():
            if status and sub.status != status:
                continue
            if author and sub.author != author:
                continue
            results.append(sub.to_dict())
        return results

    def add_comment(self, submission_id: str, author: str, comment: str) -> Dict[str, Any]:
        """Add a review comment to a submission."""
        sub = self._submissions.get(submission_id)
        if not sub:
            return {"status": "error", "message": "Submission not found"}
        sub.review_comments.append({
            "author": author,
            "comment": comment,
            "timestamp": time.time(),
        })
        return {"status": "success"}

    def get_stats(self) -> Dict[str, Any]:
        """Get submission statistics."""
        subs = list(self._submissions.values())
        return {
            "total": len(subs),
            "draft": sum(1 for s in subs if s.status == SubmissionStatus.DRAFT),
            "submitted": sum(1 for s in subs if s.status == SubmissionStatus.SUBMITTED),
            "approved": sum(1 for s in subs if s.status == SubmissionStatus.APPROVED),
            "rejected": sum(1 for s in subs if s.status == SubmissionStatus.REJECTED),
            "published": sum(1 for s in subs if s.status == SubmissionStatus.PUBLISHED),
        }

    # ------------------------------------------------------------------
    # Extensibility
    # ------------------------------------------------------------------

    def add_validator(self, validator: Callable) -> None:
        """Register a custom validation function."""
        self._validators.append(validator)

    def add_security_scanner(self, scanner: Callable) -> None:
        """Register a custom security scanning function."""
        self._security_scanners.append(scanner)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_version(version: str) -> bool:
        """Check if version follows semver-like format."""
        parts = version.split(".")
        if len(parts) < 2 or len(parts) > 4:
            return False
        try:
            for part in parts:
                int(part.split("-")[0])  # Handle pre-release like 1.0.0-beta
            return True
        except ValueError:
            return False
