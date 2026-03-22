"""Tests for fine-tuning pipeline, edge inference, security audit, and additional coverage."""
import pytest
import asyncio
import time


# ========================================================================
# Fine-Tuning Pipeline
# ========================================================================

class TestFineTunePipeline:
    """Test on-device fine-tuning pipeline."""

    def test_import(self):
        from windows_ai.core.fine_tuning import FineTunePipeline
        assert FineTunePipeline is not None

    def test_method_enum(self):
        from windows_ai.core.fine_tuning import FineTuneMethod
        assert FineTuneMethod.LORA.value == "lora"
        assert FineTuneMethod.QLORA.value == "qlora"
        assert FineTuneMethod.FULL.value == "full"

    def test_status_enum(self):
        from windows_ai.core.fine_tuning import FineTuneStatus
        assert FineTuneStatus.PENDING.value == "pending"
        assert FineTuneStatus.COMPLETED.value == "completed"

    def test_config(self):
        from windows_ai.core.fine_tuning import FineTuneConfig, FineTuneMethod
        config = FineTuneConfig(model_name="phi-2", method=FineTuneMethod.LORA)
        d = config.to_dict()
        assert d["model_name"] == "phi-2"
        assert d["method"] == "lora"

    def test_create_job(self):
        from windows_ai.core.fine_tuning import FineTunePipeline, FineTuneConfig
        pipeline = FineTunePipeline()
        config = FineTuneConfig(model_name="test-model")
        job = pipeline.create_job(config)
        assert job.job_id == "ft-0001"
        assert job.status.value == "pending"

    @pytest.mark.asyncio
    async def test_start_job(self):
        from windows_ai.core.fine_tuning import FineTunePipeline, FineTuneConfig
        pipeline = FineTunePipeline()
        config = FineTuneConfig(model_name="test-model")
        job = await pipeline.start_job(config)
        assert job.status.value == "training"
        assert job.total_steps > 0

    def test_update_progress(self):
        from windows_ai.core.fine_tuning import FineTunePipeline, FineTuneConfig
        pipeline = FineTunePipeline()
        job = pipeline.create_job(FineTuneConfig(model_name="test"))
        job.total_steps = 100
        assert pipeline.update_progress(job.job_id, step=50, loss=0.5)
        assert job.progress == 0.5
        assert job.train_loss == 0.5

    def test_complete_job(self):
        from windows_ai.core.fine_tuning import FineTunePipeline, FineTuneConfig
        pipeline = FineTunePipeline()
        job = pipeline.create_job(FineTuneConfig(model_name="test"))
        assert pipeline.complete_job(job.job_id, eval_loss=0.3)
        assert job.status.value == "completed"
        assert job.eval_loss == 0.3

    def test_fail_job(self):
        from windows_ai.core.fine_tuning import FineTunePipeline, FineTuneConfig
        pipeline = FineTunePipeline()
        job = pipeline.create_job(FineTuneConfig(model_name="test"))
        assert pipeline.fail_job(job.job_id, "OOM")
        assert job.status.value == "failed"
        assert job.error == "OOM"

    def test_cancel_job(self):
        from windows_ai.core.fine_tuning import FineTunePipeline, FineTuneConfig
        pipeline = FineTunePipeline()
        job = pipeline.create_job(FineTuneConfig(model_name="test"))
        assert pipeline.cancel_job(job.job_id)
        assert job.status.value == "cancelled"

    def test_list_jobs(self):
        from windows_ai.core.fine_tuning import FineTunePipeline, FineTuneConfig
        pipeline = FineTunePipeline()
        pipeline.create_job(FineTuneConfig(model_name="m1"))
        pipeline.create_job(FineTuneConfig(model_name="m2"))
        jobs = pipeline.list_jobs()
        assert len(jobs) == 2

    def test_supported_models(self):
        from windows_ai.core.fine_tuning import FineTunePipeline
        pipeline = FineTunePipeline()
        models = pipeline.get_supported_models()
        assert len(models) > 0
        assert any("phi" in m["name"] for m in models)

    def test_stats(self):
        from windows_ai.core.fine_tuning import FineTunePipeline
        pipeline = FineTunePipeline()
        stats = pipeline.get_stats()
        assert stats["total_jobs"] == 0

    def test_dataset_validator(self):
        from windows_ai.core.fine_tuning import DatasetValidator
        validator = DatasetValidator()
        result = validator.validate("/nonexistent/file.json")
        assert result["valid"] is False

    def test_progress_callback(self):
        from windows_ai.core.fine_tuning import FineTunePipeline, FineTuneConfig
        pipeline = FineTunePipeline()
        called = []
        pipeline.on_progress(lambda j: called.append(j.job_id))
        job = pipeline.create_job(FineTuneConfig(model_name="test"))
        job.total_steps = 10
        pipeline.update_progress(job.job_id, step=5, loss=0.5)
        assert len(called) == 1


# ========================================================================
# Edge Inference
# ========================================================================

class TestEdgeInference:
    """Test IoT edge inference manager."""

    def test_import(self):
        from windows_ai.iot.edge_inference import EdgeInferenceManager
        assert EdgeInferenceManager is not None

    def test_device_types(self):
        from windows_ai.iot.edge_inference import EdgeDeviceType
        assert EdgeDeviceType.RASPBERRY_PI.value == "raspberry_pi"
        assert EdgeDeviceType.JETSON_NANO.value == "jetson_nano"
        assert EdgeDeviceType.ESP32.value == "esp32"

    def test_model_formats(self):
        from windows_ai.iot.edge_inference import ModelFormat
        assert ModelFormat.ONNX.value == "onnx"
        assert ModelFormat.TFLITE.value == "tflite"
        assert ModelFormat.TENSORRT.value == "tensorrt"

    def test_register_node(self):
        from windows_ai.iot.edge_inference import EdgeInferenceManager, EdgeDeviceType
        mgr = EdgeInferenceManager()
        node = mgr.register_node("n1", EdgeDeviceType.RASPBERRY_PI, "raspi.local")
        assert node.node_id == "n1"
        assert node.status.value == "idle"

    def test_unregister_node(self):
        from windows_ai.iot.edge_inference import EdgeInferenceManager, EdgeDeviceType
        mgr = EdgeInferenceManager()
        mgr.register_node("n1", EdgeDeviceType.RASPBERRY_PI, "raspi.local")
        assert mgr.unregister_node("n1") is True
        assert mgr.unregister_node("n1") is False

    def test_list_nodes(self):
        from windows_ai.iot.edge_inference import EdgeInferenceManager, EdgeDeviceType
        mgr = EdgeInferenceManager()
        mgr.register_node("n1", EdgeDeviceType.RASPBERRY_PI, "r1.local")
        mgr.register_node("n2", EdgeDeviceType.JETSON_NANO, "j1.local")
        nodes = mgr.list_nodes()
        assert len(nodes) == 2

    def test_heartbeat(self):
        from windows_ai.iot.edge_inference import EdgeInferenceManager, EdgeDeviceType
        mgr = EdgeInferenceManager()
        mgr.register_node("n1", EdgeDeviceType.RASPBERRY_PI, "raspi.local")
        assert mgr.heartbeat("n1") is True
        assert mgr.heartbeat("nonexistent") is False

    def test_deploy_model(self):
        from windows_ai.iot.edge_inference import (
            EdgeInferenceManager, EdgeDeviceType, EdgeModel, ModelFormat
        )
        mgr = EdgeInferenceManager()
        mgr.register_node("n1", EdgeDeviceType.RASPBERRY_PI, "raspi.local")
        model = EdgeModel("m1", "Test Model", ModelFormat.ONNX, size_mb=50.0, task="classification")
        result = mgr.deploy_model("n1", model)
        assert result["status"] == "success"

    def test_deploy_incompatible(self):
        from windows_ai.iot.edge_inference import (
            EdgeInferenceManager, EdgeDeviceType, EdgeModel, ModelFormat
        )
        mgr = EdgeInferenceManager()
        mgr.register_node("n1", EdgeDeviceType.ESP32, "esp.local")
        model = EdgeModel("m1", "Big Model", ModelFormat.ONNX, size_mb=100.0, task="nlp")
        result = mgr.deploy_model("n1", model)
        assert result["status"] == "error"  # ESP32 only supports TFLite

    def test_undeploy_model(self):
        from windows_ai.iot.edge_inference import (
            EdgeInferenceManager, EdgeDeviceType, EdgeModel, ModelFormat
        )
        mgr = EdgeInferenceManager()
        mgr.register_node("n1", EdgeDeviceType.RASPBERRY_PI, "raspi.local")
        model = EdgeModel("m1", "Test", ModelFormat.ONNX, size_mb=10, task="cls")
        mgr.deploy_model("n1", model)
        result = mgr.undeploy_model("n1", "m1")
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_infer(self):
        from windows_ai.iot.edge_inference import (
            EdgeInferenceManager, EdgeDeviceType, EdgeModel, ModelFormat
        )
        mgr = EdgeInferenceManager()
        mgr.register_node("n1", EdgeDeviceType.RASPBERRY_PI, "raspi.local")
        model = EdgeModel("m1", "Test", ModelFormat.ONNX, size_mb=10, task="cls")
        mgr.deploy_model("n1", model)
        result = await mgr.infer("n1", "m1", {"image": "test.jpg"})
        assert result.success is True
        assert result.latency_ms >= 0

    @pytest.mark.asyncio
    async def test_infer_unknown_node(self):
        from windows_ai.iot.edge_inference import EdgeInferenceManager
        mgr = EdgeInferenceManager()
        result = await mgr.infer("unknown", "m1", {})
        assert result.success is False

    @pytest.mark.asyncio
    async def test_infer_best_node(self):
        from windows_ai.iot.edge_inference import (
            EdgeInferenceManager, EdgeDeviceType, EdgeModel, ModelFormat
        )
        mgr = EdgeInferenceManager()
        mgr.register_node("n1", EdgeDeviceType.RASPBERRY_PI, "r1.local")
        model = EdgeModel("m1", "Test", ModelFormat.ONNX, size_mb=10, task="cls")
        mgr.deploy_model("n1", model)
        result = await mgr.infer_best_node("m1", {"data": "test"})
        assert result.success is True

    def test_get_stats(self):
        from windows_ai.iot.edge_inference import EdgeInferenceManager
        mgr = EdgeInferenceManager()
        stats = mgr.get_stats()
        assert stats["total_nodes"] == 0

    def test_supported_formats(self):
        from windows_ai.iot.edge_inference import EdgeInferenceManager
        mgr = EdgeInferenceManager()
        formats = mgr.get_available_formats()
        assert "onnx" in formats
        assert "tflite" in formats

    def test_supported_devices(self):
        from windows_ai.iot.edge_inference import EdgeInferenceManager
        mgr = EdgeInferenceManager()
        devices = mgr.get_supported_devices()
        assert "raspberry_pi" in devices


# ========================================================================
# Security Audit
# ========================================================================

class TestSecurityAudit:
    """Test security penetration test simulations."""

    def test_import(self):
        from windows_ai.security.security_audit import SecurityAuditor
        assert SecurityAuditor is not None

    def test_severity_enum(self):
        from windows_ai.security.security_audit import SeverityLevel
        assert SeverityLevel.CRITICAL.value == "critical"
        assert SeverityLevel.INFO.value == "info"

    def test_category_enum(self):
        from windows_ai.security.security_audit import TestCategory
        assert TestCategory.INJECTION.value == "injection"
        assert TestCategory.AUTHENTICATION.value == "authentication"

    def test_run_full_audit(self):
        from windows_ai.security.security_audit import SecurityAuditor
        auditor = SecurityAuditor()
        report = auditor.run_full_audit()
        assert report.tests_run > 0
        assert report.tests_passed > 0
        assert report.pass_rate > 0

    def test_audit_report_dict(self):
        from windows_ai.security.security_audit import SecurityAuditor
        auditor = SecurityAuditor()
        report = auditor.run_full_audit()
        d = report.to_dict()
        assert "audit_id" in d
        assert "findings" in d
        assert "pass_rate" in d

    def test_sql_injection_tests(self):
        from windows_ai.security.security_audit import SecurityAuditor, TestCategory
        auditor = SecurityAuditor()
        findings = auditor.run_category(TestCategory.INJECTION)
        assert len(findings) > 0
        assert all(f.category.value == "injection" for f in findings)

    def test_xss_tests(self):
        from windows_ai.security.security_audit import SecurityAuditor, TestCategory
        auditor = SecurityAuditor()
        findings = auditor.run_category(TestCategory.INPUT_VALIDATION)
        assert len(findings) > 0

    def test_auth_tests(self):
        from windows_ai.security.security_audit import SecurityAuditor, TestCategory
        auditor = SecurityAuditor()
        findings = auditor.run_category(TestCategory.AUTHENTICATION)
        assert len(findings) >= 3

    def test_sanitize_input(self):
        from windows_ai.security.security_audit import SecurityAuditor
        result = SecurityAuditor._sanitize_input("' OR '1'='1")
        assert "'" not in result
        assert "OR" not in result

    def test_sanitize_html(self):
        from windows_ai.security.security_audit import SecurityAuditor
        result = SecurityAuditor._sanitize_html("<script>alert('xss')</script>")
        assert "<script>" not in result

    def test_validate_path(self):
        from windows_ai.security.security_audit import SecurityAuditor
        assert SecurityAuditor._validate_path("/safe/path") is True
        assert SecurityAuditor._validate_path("../../etc/passwd") is False

    def test_get_last_report(self):
        from windows_ai.security.security_audit import SecurityAuditor
        auditor = SecurityAuditor()
        assert auditor.get_last_report() is None
        auditor.run_full_audit()
        report = auditor.get_last_report()
        assert report is not None
        assert "audit_id" in report


# ========================================================================
# Additional Coverage: Home Assistant Adapter
# ========================================================================

class TestHomeAssistantAdapter:
    """Test Home Assistant adapter."""

    def test_import(self):
        from iot.adapters.homeassistant_adapter import HomeAssistantAdapter
        assert HomeAssistantAdapter is not None

    def test_create(self):
        from iot.adapters.homeassistant_adapter import HomeAssistantAdapter
        adapter = HomeAssistantAdapter("http://localhost:8123", "test-token")
        assert adapter.base_url == "http://localhost:8123"


class TestEnhancedHAAdapter:
    """Test Enhanced HA adapter."""

    def test_import(self):
        from iot.adapters.enhanced_ha_adapter import EnhancedHAAdapter
        assert EnhancedHAAdapter is not None


# ========================================================================
# Additional Coverage: Transfer Learning
# ========================================================================

class TestTransferLearning:
    """Test transfer learning module."""

    def test_import(self):
        import importlib
        spec = importlib.util.find_spec("windows_ai.transfer_learning")
        assert spec is not None
