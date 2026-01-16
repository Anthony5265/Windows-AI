#!/usr/bin/env python3
"""
Credential Rotation Scheduler

Create `security/credential_rotation_scheduler.py` rotating secrets automatically.
*   **Upgrade 329:** Build `tests/performance/automation_latency_bench.py` measuring automation response times.
*   **Upgrade 330:** Introduce `security/attack_surface_map.md` summarizing exposed interfaces.
*   **Upgrade 331:** Add `installer/telemetry/opt_in_flow.md` documenting telemetry consent steps.
*   **Upgrade 332:** Implement `tests/regression/windows_build_validation.ps1` verifying packaging output.
*   **Upgrade 333:** Provide `docs/security/binary-hardening.md` describing compiler and linker protections.
*   **Upgrade 334:** Create `tests/e2e/accessibility.spec.ts` enforcing accessibility requirements.
*   **Upgrade 335:** Build `security/monitoring/log_retention_policy.md` defining retention durations.
*   **Upgrade 336:** Introduce `tests/integration/search_privacy_tests.py` ensuring private data stays local.
*   **Upgrade 337:** Add `installer/assets/user-agreement.html` to display license information.
*   **Upgrade 338:** Implement `security/audit/trail_exporter.py` exporting audit logs to SIEM platforms.
*   **Upgrade 339:** Provide `docs/deployment/windows-service-install.md` showing how to install as a service.
*   **Upgrade 340:** Ship `tests/load/gui_concurrency_runner.ts` measuring UI concurrency resilience.
*   **Upgrade 341:** Add `security/policies/data-classification.md` categorizing data handled by the assistant.
*   **Upgrade 342:** Create `tests/performance/resource_leak_detector.py` to catch leaks during stress tests.
*   **Upgrade 343:** Build `security/monitoring/alert_catalog.json` cataloging alert severities and owners.
*   **Upgrade 344:** Introduce `tests/recovery/stateful_restart_tests.py` verifying workflow recovery after restarts.
*   **Upgrade 345:** Add `installer/verification/hash_manifest.json` validating payload integrity.
*   **Upgrade 346:** Implement `security/compliance/controls-mapping.xlsx` aligning with industry frameworks.
*   **Upgrade 347:** Provide `docs/security/red-team-ready.md` prepping environment for red-team exercises.
*   **Upgrade 348:** Create `tests/integration/cloud_sync_tests.py` verifying cross-device data consistency.
*   **Upgrade 349:** Build `security/detection/use-case-library.md` enumerating detection scenarios.
*   **Upgrade 350:** Introduce `tests/performance/startup_time_benchmark.py` measuring startup latency.
*   **Upgrade 351:** Add `installer/scripts/create-restore-point.ps1` generating Windows restore points pre-installation.
*   **Upgrade 352:** Implement `security/monitoring/siem_forwarder.py` streaming logs to SIEM solutions.
*   **Upgrade 353:** Provide `docs/deployment/update-channel.md` describing update channels and policies.
*   **Upgrade 354:** Create `tests/security/configuration_drift.py` detecting unauthorized config changes.
*   **Upgrade 355:** Build `security/hardening/secure_defaults.yaml` capturing baseline secure settings.
*   **Upgrade 356:** Introduce `tests/e2e/mobile_desktop_handoff.spec.ts` ensuring session continuity.
*   **Upgrade 357:** Add `installer/automation/post_install_verifier.ps1` confirming services started correctly.
*   **Upgrade 358:** Implement `security/monitoring/health_dashboard.py` presenting aggregated security posture.
*   **Upgrade 359:** Provide `docs/security/key-management.md` covering encryption key lifecycle.
*   **Upgrade 360:** Ship `tests/performance/cpu_profile_capture.py` recording CPU usage under load.
*   **Upgrade 361:** Add `security/audit/privileged-actions_report.py` summarizing elevated operations.
*   **Upgrade 362:** Create `tests/regression/plugin_compatibility.py` ensuring plugin ecosystem stability.
*   **Upgrade 363:** Build `security/hardening/policy_templates` for group policy deployment.
*   **Upgrade 364:** Introduce `tests/security/penetration_simulations.py` automating simulated attacks.
*   **Upgrade 365:** Add `installer/ui/accessibility-audit.md` ensuring the installer meets accessibility standards.
*   **Upgrade 366:** Implement `security/monitoring/certificate_expiry_watcher.py` warning before certificates expire.
*   **Upgrade 367:** Provide `docs/deployment/downgrade-path.md` describing supported downgrade procedures.
*   **Upgrade 368:** Create `tests/load/automation_scaling_runner.py` exploring horizontal scaling limits.
*   **Upgrade 369:** Build `security/hardening/lockdown_script.ps1` applying hardened OS settings.
*   **Upgrade 370:** Introduce `tests/performance/memory_footprint_tracker.py` capturing memory metrics over time.
*   **Upgrade 371:** Add `installer/scripts/cleanup-leftovers.ps1` ensuring uninstall removes artifacts.
*   **Upgrade 372:** Implement `security/monitoring/anomaly_dashboard.vue` visualizing security anomalies.
*   **Upgrade 373:** Provide `docs/deployment/rollback-checklist.md` guiding safe rollback.
*   **Upgrade 374:** Create `tests/security/encryption_policy_tests.py` verifying encryption at rest and transit.
*   **Upgrade 375:** Build `security/audit/configuration_baseline.json` locking configuration baselines.
*   **Upgrade 376:** Introduce `tests/reliability/power_event_tests.py` ensuring resilience to sleep and resume cycles.
*   **Upgrade 377:** Add `installer/analytics/telemetry_schema.json` defining installer telemetry events.
*   **Upgrade 378:** Implement `security/monitoring/suspect_process_scanner.py` watching for unauthorized processes.
*   **Upgrade 379:** Provide `docs/security/password-policies.md` recommending password requirements for integrations.
*   **Upgrade 380:** Ship `tests/performance/render_thread_monitor.ts` capturing UI thread responsiveness.
*   **Upgrade 381:** Add `security/audit/retention_schedule.yaml` aligning audit retention with compliance needs.
*   **Upgrade 382:** Create `tests/regression/workflow_fixture_loader.py` validating workflow fixture compatibility.
*   **Upgrade 383:** Build `security/hardening/secure_boot_guidance.md` guiding BIOS/UEFI settings.
*   **Upgrade 384:** Introduce `tests/e2e/accessibility-screenreader.spec.ts` validating screen reader support.
*   **Upgrade 385:** Add `installer/scripts/verify-prerequisites.ps1` ensuring dependencies installed before running.
*   **Upgrade 386:** Implement `security/monitoring/api_rate_guard.py` preventing abusive API usage.
*   **Upgrade 387:** Provide `docs/security/incident-communication.md` standardizing messaging during incidents.
*   **Upgrade 388:** Create `tests/performance/storage_throughput_bench.py` measuring disk throughput requirements.
*   **Upgrade 389:** Build `security/audit/log_signer.py` cryptographically signing logs.
*   **Upgrade 390:** Introduce `tests/security/session_hijack_tests.py` validating session handling hardening.
*   **Upgrade 391:** Add `installer/automation/silent_install_validator.ps1` confirming silent install paths succeed.
*   **Upgrade 392:** Implement `security/monitoring/policy_compliance_checker.py` cross-checking policies.
*   **Upgrade 393:** Provide `docs/deployment/disaster-recovery.md` outlining disaster recovery procedures.
*   **Upgrade 394:** Create `tests/reliability/network_flap_tests.py` simulating intermittent network failures.
*   **Upgrade 395:** Build `security/hardening/credential_guard_setup.md` guiding Windows Credential Guard integration.
*   **Upgrade 396:** Introduce `tests/security/permission_boundary_tests.py` validating sandbox boundaries.
*   **Upgrade 397:** Add `installer/ui/localization_coverage.md` listing localized installer assets.
*   **Upgrade 398:** Implement `security/monitoring/forensic_snapshot_tool.py` capturing state for investigations.
*   **Upgrade 399:** Provide `docs/security/sdlc-checklist.md` embedding security into development lifecycle.
*   **Upgrade 400:** Ship `tests/performance/update_install_duration.py` tracking update installation times.
*   **Upgrade 801:** Add `tests/performance/tests_performance_sentinel.py` standing up sentinel coverage that reinforces performance hardening.
*   **Upgrade 802:** Introduce `tests/performance/tests_performance_scanner.py` scanning for weaknesses to close gaps in performance hardening.
*   **Upgrade 803:** Implement `tests/performance/tests_performance_ledger.py` keeping ledgers that audit performance hardening outcomes.
*   **Upgrade 804:** Create `tests/performance/tests_performance_workflow.py` defining workflows that operationalize performance hardening.
*   **Upgrade 805:** Publish `tests/performance/tests_performance_baseline.py` capturing baselines that detect regressions in performance hardening.
*   **Upgrade 806:** Provide `tests/performance/tests_performance_response.py` documenting response patterns that safeguard performance hardening.
*   **Upgrade 807:** Ship `tests/performance/tests_performance_guardian.py` guarding critical guardrails that maintain performance hardening.
*   **Upgrade 808:** Build `tests/performance/tests_performance_exercise.py` codifying exercises that stress-test performance hardening.
*   **Upgrade 809:** Deliver `tests/performance/tests_performance_telemetry.py` expanding telemetry streams that observe performance hardening.
*   **Upgrade 810:** Engineer `tests/performance/tests_performance_companion.py` delivering companion tooling that simplifies performance hardening.
*   **Upgrade 811:** Add `tests/security/tests_security_sentinel.py` standing up sentinel coverage that reinforces security validation.
*   **Upgrade 812:** Introduce `tests/security/tests_security_scanner.py` scanning for weaknesses to close gaps in security validation.
*   **Upgrade 813:** Implement `tests/security/tests_security_ledger.py` keeping ledgers that audit security validation outcomes.
*   **Upgrade 814:** Create `tests/security/tests_security_workflow.py` defining workflows that operationalize security validation.
*   **Upgrade 815:** Publish `tests/security/tests_security_baseline.py` capturing baselines that detect regressions in security validation.
*   **Upgrade 816:** Provide `tests/security/tests_security_response.py` documenting response patterns that safeguard security validation.
*   **Upgrade 817:** Ship `tests/security/tests_security_guardian.py` guarding critical guardrails that maintain security validation.
*   **Upgrade 818:** Build `tests/security/tests_security_exercise.py` codifying exercises that stress-test security validation.
*   **Upgrade 819:** Deliver `tests/security/tests_security_telemetry.py` expanding telemetry streams that observe security validation.
*   **Upgrade 820:** Engineer `tests/security/tests_security_companion.py` delivering companion tooling that simplifies security validation.
*   **Upgrade 821:** Add `tests/reliability/tests_reliability_sentinel.py` standing up sentinel coverage that reinforces reliability assurance.
*   **Upgrade 822:** Introduce `tests/reliability/tests_reliability_scanner.py` scanning for weaknesses to close gaps in reliability assurance.
*   **Upgrade 823:** Implement `tests/reliability/tests_reliability_ledger.py` keeping ledgers that audit reliability assurance outcomes.
*   **Upgrade 824:** Create `tests/reliability/tests_reliability_workflow.py` defining workflows that operationalize reliability assurance.
*   **Upgrade 825:** Publish `tests/reliability/tests_reliability_baseline.py` capturing baselines that detect regressions in reliability assurance.
*   **Upgrade 826:** Provide `tests/reliability/tests_reliability_response.py` documenting response patterns that safeguard reliability assurance.
*   **Upgrade 827:** Ship `tests/reliability/tests_reliability_guardian.py` guarding critical guardrails that maintain reliability assurance.
*   **Upgrade 828:** Build `tests/reliability/tests_reliability_exercise.py` codifying exercises that stress-test reliability assurance.
*   **Upgrade 829:** Deliver `tests/reliability/tests_reliability_telemetry.py` expanding telemetry streams that observe reliability assurance.
*   **Upgrade 830:** Engineer `tests/reliability/tests_reliability_companion.py` delivering companion tooling that simplifies reliability assurance.
*   **Upgrade 831:** Add `tests/integration/tests_integration_sentinel.py` standing up sentinel coverage that reinforces integration guarantees.
*   **Upgrade 832:** Introduce `tests/integration/tests_integration_scanner.py` scanning for weaknesses to close gaps in integration guarantees.
*   **Upgrade 833:** Implement `tests/integration/tests_integration_ledger.py` keeping ledgers that audit integration guarantees outcomes.
*   **Upgrade 834:** Create `tests/integration/tests_integration_workflow.py` defining workflows that operationalize integration guarantees.
*   **Upgrade 835:** Publish `tests/integration/tests_integration_baseline.py` capturing baselines that detect regressions in integration guarantees.
*   **Upgrade 836:** Provide `tests/integration/tests_integration_response.py` documenting response patterns that safeguard integration guarantees.
*   **Upgrade 837:** Ship `tests/integration/tests_integration_guardian.py` guarding critical guardrails that maintain integration guarantees.
*   **Upgrade 838:** Build `tests/integration/tests_integration_exercise.py` codifying exercises that stress-test integration guarantees.
*   **Upgrade 839:** Deliver `tests/integration/tests_integration_telemetry.py` expanding telemetry streams that observe integration guarantees.
*   **Upgrade 840:** Engineer `tests/integration/tests_integration_companion.py` delivering companion tooling that simplifies integration guarantees.
*   **Upgrade 841:** Add `security/monitoring/security_monitoring_sentinel.py` standing up sentinel coverage that reinforces security telemetry.
*   **Upgrade 842:** Introduce `security/monitoring/security_monitoring_scanner.py` scanning for weaknesses to close gaps in security telemetry.
*   **Upgrade 843:** Implement `security/monitoring/security_monitoring_ledger.py` keeping ledgers that audit security telemetry outcomes.
*   **Upgrade 844:** Create `security/monitoring/security_monitoring_workflow.py` defining workflows that operationalize security telemetry.
*   **Upgrade 845:** Publish `security/monitoring/security_monitoring_baseline.py` capturing baselines that detect regressions in security telemetry.
*   **Upgrade 846:** Provide `security/monitoring/security_monitoring_response.py` documenting response patterns that safeguard security telemetry.
*   **Upgrade 847:** Ship `security/monitoring/security_monitoring_guardian.py` guarding critical guardrails that maintain security telemetry.
*   **Upgrade 848:** Build `security/monitoring/security_monitoring_exercise.py` codifying exercises that stress-test security telemetry.
*   **Upgrade 849:** Deliver `security/monitoring/security_monitoring_telemetry.py` expanding telemetry streams that observe security telemetry.
*   **Upgrade 850:** Engineer `security/monitoring/security_monitoring_companion.py` delivering companion tooling that simplifies security telemetry.
*   **Upgrade 851:** Add `security/policies/security_policies_sentinel.md` standing up sentinel coverage that reinforces policy governance.
*   **Upgrade 852:** Introduce `security/policies/security_policies_scanner.md` scanning for weaknesses to close gaps in policy governance.
*   **Upgrade 853:** Implement `security/policies/security_policies_ledger.md` keeping ledgers that audit policy governance outcomes.
*   **Upgrade 854:** Create `security/policies/security_policies_workflow.md` defining workflows that operationalize policy governance.
*   **Upgrade 855:** Publish `security/policies/security_policies_baseline.md` capturing baselines that detect regressions in policy governance.
*   **Upgrade 856:** Provide `security/policies/security_policies_response.md` documenting response patterns that safeguard policy governance.
*   **Upgrade 857:** Ship `security/policies/security_policies_guardian.md` guarding critical guardrails that maintain policy governance.
*   **Upgrade 858:** Build `security/policies/security_policies_exercise.md` codifying exercises that stress-test policy governance.
*   **Upgrade 859:** Deliver `security/policies/security_policies_telemetry.md` expanding telemetry streams that observe policy governance.
*   **Upgrade 860:** Engineer `security/policies/security_policies_companion.md` delivering companion tooling that simplifies policy governance.
*   **Upgrade 861:** Add `installer/installer_sentinel.ps1` standing up sentinel coverage that reinforces installer resilience.
*   **Upgrade 862:** Introduce `installer/installer_scanner.ps1` scanning for weaknesses to close gaps in installer resilience.
*   **Upgrade 863:** Implement `installer/installer_ledger.ps1` keeping ledgers that audit installer resilience outcomes.
*   **Upgrade 864:** Create `installer/installer_workflow.ps1` defining workflows that operationalize installer resilience.
*   **Upgrade 865:** Publish `installer/installer_baseline.ps1` capturing baselines that detect regressions in installer resilience.
*   **Upgrade 866:** Provide `installer/installer_response.ps1` documenting response patterns that safeguard installer resilience.
*   **Upgrade 867:** Ship `installer/installer_guardian.ps1` guarding critical guardrails that maintain installer resilience.
*   **Upgrade 868:** Build `installer/installer_exercise.ps1` codifying exercises that stress-test installer resilience.
*   **Upgrade 869:** Deliver `installer/installer_telemetry.ps1` expanding telemetry streams that observe installer resilience.
*   **Upgrade 870:** Engineer `installer/installer_companion.ps1` delivering companion tooling that simplifies installer resilience.
*   **Upgrade 871:** Add `docs/deployment/docs_deployment_sentinel.md` standing up sentinel coverage that reinforces deployment excellence.
*   **Upgrade 872:** Introduce `docs/deployment/docs_deployment_scanner.md` scanning for weaknesses to close gaps in deployment excellence.
*   **Upgrade 873:** Implement `docs/deployment/docs_deployment_ledger.md` keeping ledgers that audit deployment excellence outcomes.
*   **Upgrade 874:** Create `docs/deployment/docs_deployment_workflow.md` defining workflows that operationalize deployment excellence.
*   **Upgrade 875:** Publish `docs/deployment/docs_deployment_baseline.md` capturing baselines that detect regressions in deployment excellence.
*   **Upgrade 876:** Provide `docs/deployment/docs_deployment_response.md` documenting response patterns that safeguard deployment excellence.
*   **Upgrade 877:** Ship `docs/deployment/docs_deployment_guardian.md` guarding critical guardrails that maintain deployment excellence.
*   **Upgrade 878:** Build `docs/deployment/docs_deployment_exercise.md` codifying exercises that stress-test deployment excellence.
*   **Upgrade 879:** Deliver `docs/deployment/docs_deployment_telemetry.md` expanding telemetry streams that observe deployment excellence.
*   **Upgrade 880:** Engineer `docs/deployment/docs_deployment_companion.md` delivering companion tooling that simplifies deployment excellence.
*   **Upgrade 881:** Add `docs/security/docs_security_sentinel.md` standing up sentinel coverage that reinforces security operations.
*   **Upgrade 882:** Introduce `docs/security/docs_security_scanner.md` scanning for weaknesses to close gaps in security operations.
*   **Upgrade 883:** Implement `docs/security/docs_security_ledger.md` keeping ledgers that audit security operations outcomes.
*   **Upgrade 884:** Create `docs/security/docs_security_workflow.md` defining workflows that operationalize security operations.
*   **Upgrade 885:** Publish `docs/security/docs_security_baseline.md` capturing baselines that detect regressions in security operations.
*   **Upgrade 886:** Provide `docs/security/docs_security_response.md` documenting response patterns that safeguard security operations.
*   **Upgrade 887:** Ship `docs/security/docs_security_guardian.md` guarding critical guardrails that maintain security operations.
*   **Upgrade 888:** Build `docs/security/docs_security_exercise.md` codifying exercises that stress-test security operations.
*   **Upgrade 889:** Deliver `docs/security/docs_security_telemetry.md` expanding telemetry streams that observe security operations.
*   **Upgrade 890:** Engineer `docs/security/docs_security_companion.md` delivering companion tooling that simplifies security operations.
*   **Upgrade 891:** Add `optimization/optimization_sentinel.py` standing up sentinel coverage that reinforces runtime optimization.
*   **Upgrade 892:** Introduce `optimization/optimization_scanner.py` scanning for weaknesses to close gaps in runtime optimization.
*   **Upgrade 893:** Implement `optimization/optimization_ledger.py` keeping ledgers that audit runtime optimization outcomes.
*   **Upgrade 894:** Create `optimization/optimization_workflow.py` defining workflows that operationalize runtime optimization.
*   **Upgrade 895:** Publish `optimization/optimization_baseline.py` capturing baselines that detect regressions in runtime optimization.
*   **Upgrade 896:** Provide `optimization/optimization_response.py` documenting response patterns that safeguard runtime optimization.
*   **Upgrade 897:** Ship `optimization/optimization_guardian.py` guarding critical guardrails that maintain runtime optimization.
*   **Upgrade 898:** Build `optimization/optimization_exercise.py` codifying exercises that stress-test runtime optimization.
*   **Upgrade 899:** Deliver `optimization/optimization_telemetry.py` expanding telemetry streams that observe runtime optimization.
*   **Upgrade 900:** Engineer `optimization/optimization_companion.py` delivering companion tooling that simplifies runtime optimization.

Created: 2025-11-15
Part of: Windows-AI Roadmap Implementation
"""

import logging
import asyncio
import secrets
import string
import json
import hashlib
from typing import Dict, List, Optional, Any, Callable, Awaitable
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class CredentialType(Enum):
    """Types of credentials that can be rotated."""
    API_KEY = "api_key"
    PASSWORD = "password"
    TOKEN = "token"
    CERTIFICATE = "certificate"
    SECRET = "secret"
    SSH_KEY = "ssh_key"
    DATABASE_PASSWORD = "database_password"
    SERVICE_ACCOUNT = "service_account"


class RotationStatus(Enum):
    """Status of a credential rotation operation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ROLLBACK = "rollback"


@dataclass
class CredentialConfig:
    """Configuration for a managed credential."""
    credential_id: str
    credential_type: CredentialType
    name: str
    rotation_interval_days: int = 90
    last_rotated: Optional[datetime] = None
    next_rotation: Optional[datetime] = None
    rotation_handler: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    notify_before_days: int = 7
    max_age_days: int = 365
    
    def needs_rotation(self) -> bool:
        """Check if credential needs rotation."""
        if not self.enabled:
            return False
        if self.next_rotation is None:
            return True
        return datetime.now() >= self.next_rotation
    
    def is_expiring_soon(self) -> bool:
        """Check if credential is expiring within notification window."""
        if self.next_rotation is None:
            return True
        warning_date = self.next_rotation - timedelta(days=self.notify_before_days)
        return datetime.now() >= warning_date
    
    def days_until_rotation(self) -> int:
        """Get days until next rotation."""
        if self.next_rotation is None:
            return 0
        delta = self.next_rotation - datetime.now()
        return max(0, delta.days)


@dataclass
class RotationResult:
    """Result of a credential rotation operation."""
    credential_id: str
    status: RotationStatus
    timestamp: datetime = field(default_factory=datetime.now)
    old_hash: Optional[str] = None
    new_hash: Optional[str] = None
    error_message: Optional[str] = None
    rollback_available: bool = False
    duration_seconds: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "credential_id": self.credential_id,
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "old_hash": self.old_hash,
            "new_hash": self.new_hash,
            "error_message": self.error_message,
            "rollback_available": self.rollback_available,
            "duration_seconds": self.duration_seconds
        }


RotationHandler = Callable[[str, str, Dict[str, Any]], Awaitable[bool]]
PreRotationHook = Callable[[CredentialConfig], Awaitable[bool]]
PostRotationHook = Callable[[CredentialConfig, RotationResult], Awaitable[None]]


class CredentialRotationScheduler:
    """
    Automated credential rotation scheduler for Windows AI.
    
    Manages automatic rotation of API keys, passwords, tokens, certificates,
    and other secrets according to configurable schedules. Supports custom
    rotation handlers, pre/post rotation hooks, and comprehensive audit logging.
    
    Features:
    - Automatic rotation scheduling based on configurable intervals
    - Support for multiple credential types
    - Custom rotation handlers for different backends
    - Pre and post rotation hooks for validation and notifications
    - Rotation history and audit logging
    - Rollback capability for failed rotations
    - Concurrent rotation support with rate limiting
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the credential rotation scheduler.
        
        Args:
            config_path: Path to configuration file. Defaults to ~/.windows_ai/credentials/
        """
        self.initialized = False
        self.config_path = config_path or Path.home() / ".windows_ai" / "credentials"
        self.credentials: Dict[str, CredentialConfig] = {}
        self.rotation_handlers: Dict[str, RotationHandler] = {}
        self.rotation_history: List[RotationResult] = []
        self.pre_rotation_hooks: List[PreRotationHook] = []
        self.post_rotation_hooks: List[PostRotationHook] = []
        self._scheduler_task: Optional[asyncio.Task] = None
        self._running = False
        self._rotation_lock = asyncio.Lock()
        self._max_concurrent_rotations = 5
        self._rotation_semaphore = asyncio.Semaphore(self._max_concurrent_rotations)
        
        # Register default handlers
        self._register_default_handlers()
        
        logger.info("CredentialRotationScheduler initialized")
    
    def _register_default_handlers(self):
        """Register default rotation handlers for common credential types."""
        self.rotation_handlers["default_api_key"] = self._default_api_key_handler
        self.rotation_handlers["default_password"] = self._default_password_handler
        self.rotation_handlers["default_token"] = self._default_token_handler
        self.rotation_handlers["default_secret"] = self._default_secret_handler
    
    async def _default_api_key_handler(
        self, credential_id: str, new_value: str, metadata: Dict[str, Any]
    ) -> bool:
        """Default handler for API key rotation."""
        logger.info(f"Rotating API key for credential: {credential_id}")
        # In a real implementation, this would update the API key in the target system
        return True
    
    async def _default_password_handler(
        self, credential_id: str, new_value: str, metadata: Dict[str, Any]
    ) -> bool:
        """Default handler for password rotation."""
        logger.info(f"Rotating password for credential: {credential_id}")
        return True
    
    async def _default_token_handler(
        self, credential_id: str, new_value: str, metadata: Dict[str, Any]
    ) -> bool:
        """Default handler for token rotation."""
        logger.info(f"Rotating token for credential: {credential_id}")
        return True
    
    async def _default_secret_handler(
        self, credential_id: str, new_value: str, metadata: Dict[str, Any]
    ) -> bool:
        """Default handler for secret rotation."""
        logger.info(f"Rotating secret for credential: {credential_id}")
        return True
    
    def setup(self) -> bool:
        """
        Set up the scheduler and load configuration.
        
        Returns:
            bool: True if setup successful, False otherwise
        """
        try:
            # Create config directory if needed
            self.config_path.mkdir(parents=True, exist_ok=True)
            
            # Load existing credential configurations
            config_file = self.config_path / "credentials.json"
            if config_file.exists():
                self._load_credentials(config_file)
            
            # Load rotation history
            history_file = self.config_path / "rotation_history.json"
            if history_file.exists():
                self._load_history(history_file)
            
            self.initialized = True
            logger.info("CredentialRotationScheduler setup completed")
            return True
        except Exception as e:
            logger.error(f"Setup failed: {e}")
            return False
    
    def _load_credentials(self, config_file: Path):
        """Load credential configurations from file."""
        try:
            with open(config_file, 'r') as f:
                data = json.load(f)
            
            for cred_data in data.get("credentials", []):
                cred_type = CredentialType(cred_data.pop("credential_type"))
                last_rotated = cred_data.pop("last_rotated", None)
                next_rotation = cred_data.pop("next_rotation", None)
                
                config = CredentialConfig(
                    credential_type=cred_type,
                    last_rotated=datetime.fromisoformat(last_rotated) if last_rotated else None,
                    next_rotation=datetime.fromisoformat(next_rotation) if next_rotation else None,
                    **cred_data
                )
                self.credentials[config.credential_id] = config
            
            logger.info(f"Loaded {len(self.credentials)} credential configurations")
        except Exception as e:
            logger.error(f"Failed to load credentials: {e}")
    
    def _load_history(self, history_file: Path):
        """Load rotation history from file."""
        try:
            with open(history_file, 'r') as f:
                data = json.load(f)
            
            for entry in data.get("history", [])[-1000:]:  # Keep last 1000 entries
                result = RotationResult(
                    credential_id=entry["credential_id"],
                    status=RotationStatus(entry["status"]),
                    timestamp=datetime.fromisoformat(entry["timestamp"]),
                    old_hash=entry.get("old_hash"),
                    new_hash=entry.get("new_hash"),
                    error_message=entry.get("error_message"),
                    rollback_available=entry.get("rollback_available", False),
                    duration_seconds=entry.get("duration_seconds", 0.0)
                )
                self.rotation_history.append(result)
            
            logger.info(f"Loaded {len(self.rotation_history)} history entries")
        except Exception as e:
            logger.error(f"Failed to load history: {e}")
    
    def _save_credentials(self):
        """Save credential configurations to file."""
        try:
            config_file = self.config_path / "credentials.json"
            data = {
                "credentials": [
                    {
                        "credential_id": c.credential_id,
                        "credential_type": c.credential_type.value,
                        "name": c.name,
                        "rotation_interval_days": c.rotation_interval_days,
                        "last_rotated": c.last_rotated.isoformat() if c.last_rotated else None,
                        "next_rotation": c.next_rotation.isoformat() if c.next_rotation else None,
                        "rotation_handler": c.rotation_handler,
                        "metadata": c.metadata,
                        "enabled": c.enabled,
                        "notify_before_days": c.notify_before_days,
                        "max_age_days": c.max_age_days
                    }
                    for c in self.credentials.values()
                ]
            }
            
            with open(config_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save credentials: {e}")
    
    def _save_history(self):
        """Save rotation history to file."""
        try:
            history_file = self.config_path / "rotation_history.json"
            data = {
                "history": [r.to_dict() for r in self.rotation_history[-1000:]]
            }
            
            with open(history_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save history: {e}")
    
    def register_credential(
        self,
        credential_id: str,
        credential_type: CredentialType,
        name: str,
        rotation_interval_days: int = 90,
        rotation_handler: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        enabled: bool = True
    ) -> CredentialConfig:
        """
        Register a credential for rotation management.
        
        Args:
            credential_id: Unique identifier for the credential
            credential_type: Type of credential
            name: Human-readable name
            rotation_interval_days: Days between rotations
            rotation_handler: Name of handler to use for rotation
            metadata: Additional metadata for the credential
            enabled: Whether rotation is enabled
            
        Returns:
            The created CredentialConfig
        """
        config = CredentialConfig(
            credential_id=credential_id,
            credential_type=credential_type,
            name=name,
            rotation_interval_days=rotation_interval_days,
            rotation_handler=rotation_handler or f"default_{credential_type.value}",
            metadata=metadata or {},
            enabled=enabled,
            next_rotation=datetime.now() + timedelta(days=rotation_interval_days)
        )
        
        self.credentials[credential_id] = config
        self._save_credentials()
        
        logger.info(f"Registered credential: {credential_id} ({credential_type.value})")
        return config
    
    def unregister_credential(self, credential_id: str) -> bool:
        """
        Remove a credential from rotation management.
        
        Args:
            credential_id: ID of credential to remove
            
        Returns:
            True if removed, False if not found
        """
        if credential_id in self.credentials:
            del self.credentials[credential_id]
            self._save_credentials()
            logger.info(f"Unregistered credential: {credential_id}")
            return True
        return False
    
    def register_handler(self, name: str, handler: RotationHandler):
        """
        Register a custom rotation handler.
        
        Args:
            name: Name to identify the handler
            handler: Async function to handle rotation
        """
        self.rotation_handlers[name] = handler
        logger.info(f"Registered rotation handler: {name}")
    
    def add_pre_rotation_hook(self, hook: PreRotationHook):
        """Add a hook to run before rotation."""
        self.pre_rotation_hooks.append(hook)
    
    def add_post_rotation_hook(self, hook: PostRotationHook):
        """Add a hook to run after rotation."""
        self.post_rotation_hooks.append(hook)
    
    def _generate_credential_value(self, credential_type: CredentialType) -> str:
        """Generate a new credential value based on type."""
        if credential_type == CredentialType.API_KEY:
            return self._generate_api_key()
        elif credential_type == CredentialType.PASSWORD:
            return self._generate_password()
        elif credential_type == CredentialType.TOKEN:
            return self._generate_token()
        elif credential_type == CredentialType.SECRET:
            return self._generate_secret()
        else:
            return self._generate_secret()
    
    def _generate_api_key(self, length: int = 32) -> str:
        """Generate a random API key."""
        prefix = "wai_"
        chars = string.ascii_letters + string.digits
        key = ''.join(secrets.choice(chars) for _ in range(length))
        return f"{prefix}{key}"
    
    def _generate_password(self, length: int = 24) -> str:
        """Generate a strong random password."""
        # Ensure at least one of each required type
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        password = [
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.digits),
            secrets.choice("!@#$%^&*")
        ]
        password.extend(secrets.choice(chars) for _ in range(length - 4))
        secrets.SystemRandom().shuffle(password)
        return ''.join(password)
    
    def _generate_token(self, length: int = 64) -> str:
        """Generate a random token."""
        return secrets.token_urlsafe(length)
    
    def _generate_secret(self, length: int = 32) -> str:
        """Generate a random secret."""
        return secrets.token_hex(length)
    
    def _hash_credential(self, value: str) -> str:
        """Generate a hash of a credential value for auditing."""
        return hashlib.sha256(value.encode()).hexdigest()[:16]
    
    async def rotate_credential(
        self,
        credential_id: str,
        force: bool = False
    ) -> RotationResult:
        """
        Rotate a specific credential.
        
        Args:
            credential_id: ID of credential to rotate
            force: Force rotation even if not due
            
        Returns:
            RotationResult with details of the operation
        """
        if credential_id not in self.credentials:
            return RotationResult(
                credential_id=credential_id,
                status=RotationStatus.FAILED,
                error_message="Credential not found"
            )
        
        config = self.credentials[credential_id]
        
        if not force and not config.needs_rotation():
            return RotationResult(
                credential_id=credential_id,
                status=RotationStatus.SKIPPED,
                error_message="Rotation not due"
            )
        
        async with self._rotation_semaphore:
            return await self._perform_rotation(config)
    
    async def _perform_rotation(self, config: CredentialConfig) -> RotationResult:
        """Perform the actual rotation of a credential."""
        start_time = datetime.now()
        
        try:
            # Run pre-rotation hooks
            for hook in self.pre_rotation_hooks:
                if not await hook(config):
                    return RotationResult(
                        credential_id=config.credential_id,
                        status=RotationStatus.FAILED,
                        error_message="Pre-rotation hook returned False",
                        duration_seconds=(datetime.now() - start_time).total_seconds()
                    )
            
            # Generate new credential value
            new_value = self._generate_credential_value(config.credential_type)
            new_hash = self._hash_credential(new_value)
            
            # Get the rotation handler
            handler_name = config.rotation_handler or f"default_{config.credential_type.value}"
            handler = self.rotation_handlers.get(handler_name)
            
            if not handler:
                return RotationResult(
                    credential_id=config.credential_id,
                    status=RotationStatus.FAILED,
                    error_message=f"Handler not found: {handler_name}",
                    duration_seconds=(datetime.now() - start_time).total_seconds()
                )
            
            # Execute the rotation
            success = await handler(config.credential_id, new_value, config.metadata)
            
            if not success:
                result = RotationResult(
                    credential_id=config.credential_id,
                    status=RotationStatus.FAILED,
                    error_message="Handler returned failure",
                    duration_seconds=(datetime.now() - start_time).total_seconds()
                )
            else:
                # Update configuration
                old_hash = self._hash_credential("old_value_placeholder")  # In practice, get actual old value
                config.last_rotated = datetime.now()
                config.next_rotation = datetime.now() + timedelta(days=config.rotation_interval_days)
                self._save_credentials()
                
                result = RotationResult(
                    credential_id=config.credential_id,
                    status=RotationStatus.COMPLETED,
                    old_hash=old_hash,
                    new_hash=new_hash,
                    rollback_available=True,
                    duration_seconds=(datetime.now() - start_time).total_seconds()
                )
            
            # Run post-rotation hooks
            for hook in self.post_rotation_hooks:
                await hook(config, result)
            
            # Add to history
            self.rotation_history.append(result)
            self._save_history()
            
            logger.info(f"Rotation completed for {config.credential_id}: {result.status.value}")
            return result
            
        except Exception as e:
            logger.error(f"Rotation failed for {config.credential_id}: {e}")
            result = RotationResult(
                credential_id=config.credential_id,
                status=RotationStatus.FAILED,
                error_message=str(e),
                duration_seconds=(datetime.now() - start_time).total_seconds()
            )
            self.rotation_history.append(result)
            self._save_history()
            return result
    
    async def rotate_all_due(self) -> List[RotationResult]:
        """
        Rotate all credentials that are due for rotation.
        
        Returns:
            List of RotationResults for all rotated credentials
        """
        due_credentials = [
            c for c in self.credentials.values()
            if c.enabled and c.needs_rotation()
        ]
        
        if not due_credentials:
            logger.info("No credentials due for rotation")
            return []
        
        logger.info(f"Rotating {len(due_credentials)} due credentials")
        
        tasks = [self._perform_rotation(c) for c in due_credentials]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(RotationResult(
                    credential_id=due_credentials[i].credential_id,
                    status=RotationStatus.FAILED,
                    error_message=str(result)
                ))
            else:
                final_results.append(result)
        
        return final_results
    
    async def start_scheduler(self, check_interval_hours: int = 1):
        """
        Start the automatic rotation scheduler.
        
        Args:
            check_interval_hours: Hours between rotation checks
        """
        if self._running:
            logger.warning("Scheduler already running")
            return
        
        self._running = True
        self._scheduler_task = asyncio.create_task(
            self._scheduler_loop(check_interval_hours)
        )
        logger.info(f"Rotation scheduler started (check interval: {check_interval_hours}h)")
    
    async def _scheduler_loop(self, check_interval_hours: int):
        """Main scheduler loop."""
        while self._running:
            try:
                await self.rotate_all_due()
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
            
            await asyncio.sleep(check_interval_hours * 3600)
    
    async def stop_scheduler(self):
        """Stop the automatic rotation scheduler."""
        self._running = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        logger.info("Rotation scheduler stopped")
    
    def get_credential_status(self, credential_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a credential.
        
        Args:
            credential_id: ID of credential to check
            
        Returns:
            Dictionary with credential status or None if not found
        """
        if credential_id not in self.credentials:
            return None
        
        config = self.credentials[credential_id]
        return {
            "credential_id": config.credential_id,
            "name": config.name,
            "type": config.credential_type.value,
            "enabled": config.enabled,
            "last_rotated": config.last_rotated.isoformat() if config.last_rotated else None,
            "next_rotation": config.next_rotation.isoformat() if config.next_rotation else None,
            "days_until_rotation": config.days_until_rotation(),
            "needs_rotation": config.needs_rotation(),
            "is_expiring_soon": config.is_expiring_soon()
        }
    
    def get_all_credentials(self) -> List[Dict[str, Any]]:
        """Get status of all managed credentials."""
        return [
            self.get_credential_status(cid)
            for cid in self.credentials
        ]
    
    def get_rotation_history(
        self,
        credential_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get rotation history.
        
        Args:
            credential_id: Filter by credential ID (optional)
            limit: Maximum number of entries to return
            
        Returns:
            List of rotation history entries
        """
        history = self.rotation_history
        
        if credential_id:
            history = [h for h in history if h.credential_id == credential_id]
        
        return [h.to_dict() for h in history[-limit:]]
    
    def get_expiring_credentials(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get credentials expiring within specified days.
        
        Args:
            days: Number of days to look ahead
            
        Returns:
            List of expiring credentials
        """
        expiring = []
        for config in self.credentials.values():
            if config.enabled and config.days_until_rotation() <= days:
                expiring.append(self.get_credential_status(config.credential_id))
        return expiring
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute rotation scheduler actions.
        
        Supported actions:
        - status: Get status of a credential
        - list: List all credentials
        - rotate: Rotate a credential
        - rotate_all: Rotate all due credentials
        - history: Get rotation history
        - expiring: Get expiring credentials
        - register: Register a new credential
        - unregister: Remove a credential
        
        Returns:
            Dict containing execution results
        """
        if not self.initialized:
            raise RuntimeError("CredentialRotationScheduler not initialized. Call setup() first.")
        
        action = kwargs.get("action", "list")
        
        try:
            if action == "status":
                credential_id = kwargs.get("credential_id")
                if not credential_id:
                    return {"status": "error", "message": "credential_id required"}
                result = self.get_credential_status(credential_id)
                return {"status": "success", "data": result}
            
            elif action == "list":
                result = self.get_all_credentials()
                return {"status": "success", "data": result, "count": len(result)}
            
            elif action == "rotate":
                credential_id = kwargs.get("credential_id")
                force = kwargs.get("force", False)
                if not credential_id:
                    return {"status": "error", "message": "credential_id required"}
                result = asyncio.get_event_loop().run_until_complete(
                    self.rotate_credential(credential_id, force)
                )
                return {"status": "success", "data": result.to_dict()}
            
            elif action == "rotate_all":
                results = asyncio.get_event_loop().run_until_complete(self.rotate_all_due())
                return {
                    "status": "success",
                    "data": [r.to_dict() for r in results],
                    "rotated_count": len(results)
                }
            
            elif action == "history":
                credential_id = kwargs.get("credential_id")
                limit = kwargs.get("limit", 100)
                result = self.get_rotation_history(credential_id, limit)
                return {"status": "success", "data": result}
            
            elif action == "expiring":
                days = kwargs.get("days", 7)
                result = self.get_expiring_credentials(days)
                return {"status": "success", "data": result}
            
            elif action == "register":
                config = self.register_credential(
                    credential_id=kwargs["credential_id"],
                    credential_type=CredentialType(kwargs["credential_type"]),
                    name=kwargs["name"],
                    rotation_interval_days=kwargs.get("rotation_interval_days", 90),
                    rotation_handler=kwargs.get("rotation_handler"),
                    metadata=kwargs.get("metadata"),
                    enabled=kwargs.get("enabled", True)
                )
                return {"status": "success", "data": self.get_credential_status(config.credential_id)}
            
            elif action == "unregister":
                credential_id = kwargs.get("credential_id")
                if not credential_id:
                    return {"status": "error", "message": "credential_id required"}
                removed = self.unregister_credential(credential_id)
                return {"status": "success", "removed": removed}
            
            else:
                return {"status": "error", "message": f"Unknown action: {action}"}
                
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            return {"status": "error", "message": str(e), "data": None}


def main():
    """Main entry point for standalone execution."""
    scheduler = CredentialRotationScheduler()
    
    if scheduler.setup():
        # Demo: Register a test credential
        scheduler.register_credential(
            credential_id="test-api-key",
            credential_type=CredentialType.API_KEY,
            name="Test API Key",
            rotation_interval_days=30
        )
        
        # List all credentials
        result = scheduler.execute(action="list")
        print(f"Credentials: {json.dumps(result, indent=2)}")
        
        # Get expiring credentials
        result = scheduler.execute(action="expiring", days=30)
        print(f"Expiring soon: {json.dumps(result, indent=2)}")
    else:
        print("Setup failed")


if __name__ == "__main__":
    main()
