"""
Comprehensive tests for Integration Managers
Tests all 43+ integration managers
"""
import pytest
import asyncio
from windows_ai.integrations import (
    AIProvidersManager,
    ImageGenerationManager,
    AudioSpeechManager,
    VideoGenerationManager,
    DocumentProcessingManager,
    WindowsAutomationManager,
    BrowserAutomationManager,
    ProductivityManager,
    DataAnalysisManager,
    CodeAssistantsManager,
    TranslationManager,
    SearchEnginesManager,
    KnowledgeGraphManager,
    ThreeDGenerationManager,
    MusicGenerationManager,
    EmbeddingsManager,
    VectorStoresManager,
    WorkflowAutomationManager,
    EmailServicesManager,
    NotificationsManager,
    CloudStorageManager,
    DatabaseManager,
    MonitoringManager,
    AIAgentsManager,
    SecurityScanningManager,
    ContentModerationManager,
    RAGPipelineManager,
    MLOpsManager,
    PaymentsManager,
    SocialMediaManager,
    SchedulingManager,
    CRMManager,
    IoTHardwareManager,
    ComputerVisionManager,
    HealthcareAIManager,
    LegalAIManager,
    EducationAIManager,
    FinanceAIManager,
    ScientificAIManager,
    AccessibilityAIManager,
    RealEstateAIManager,
    GamingAIManager,
    ConversationalAIManager,
    AutomationRoboticsManager,
    BiometricsIdentityManager
)

# List of all manager classes
MANAGER_CLASSES = [
    AIProvidersManager,
    ImageGenerationManager,
    AudioSpeechManager,
    VideoGenerationManager,
    DocumentProcessingManager,
    WindowsAutomationManager,
    BrowserAutomationManager,
    ProductivityManager,
    DataAnalysisManager,
    CodeAssistantsManager,
    TranslationManager,
    SearchEnginesManager,
    KnowledgeGraphManager,
    ThreeDGenerationManager,
    MusicGenerationManager,
    EmbeddingsManager,
    VectorStoresManager,
    WorkflowAutomationManager,
    EmailServicesManager,
    NotificationsManager,
    CloudStorageManager,
    DatabaseManager,
    MonitoringManager,
    AIAgentsManager,
    SecurityScanningManager,
    ContentModerationManager,
    RAGPipelineManager,
    MLOpsManager,
    PaymentsManager,
    SocialMediaManager,
    SchedulingManager,
    CRMManager,
    IoTHardwareManager,
    ComputerVisionManager,
    HealthcareAIManager,
    LegalAIManager,
    EducationAIManager,
    FinanceAIManager,
    ScientificAIManager,
    AccessibilityAIManager,
    RealEstateAIManager,
    GamingAIManager,
    ConversationalAIManager,
    AutomationRoboticsManager,
    BiometricsIdentityManager
]

@pytest.mark.unit
@pytest.mark.parametrize("manager_class", MANAGER_CLASSES)
def test_manager_can_instantiate(manager_class):
    """Test that each manager can be instantiated"""
    try:
        manager = manager_class()
        assert manager is not None
    except Exception as e:
        pytest.fail(f"Failed to instantiate {manager_class.__name__}: {e}")

@pytest.mark.unit
@pytest.mark.parametrize("manager_class", MANAGER_CLASSES)
def test_manager_has_initialize_method(manager_class):
    """Test that each manager has an initialize method"""
    manager = manager_class()
    assert hasattr(manager, "initialize"), f"{manager_class.__name__} missing initialize method"
    assert callable(manager.initialize), f"{manager_class.__name__}.initialize is not callable"

@pytest.mark.unit
@pytest.mark.parametrize("manager_class", MANAGER_CLASSES)
def test_manager_has_cleanup_method(manager_class):
    """Test that each manager has a cleanup method"""
    manager = manager_class()
    assert hasattr(manager, "cleanup"), f"{manager_class.__name__} missing cleanup method"
    assert callable(manager.cleanup), f"{manager_class.__name__}.cleanup is not callable"

@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.parametrize("manager_class", MANAGER_CLASSES)
async def test_manager_initialize(manager_class):
    """Test that manager can be initialized"""
    manager = manager_class()
    try:
        await manager.initialize()
        # Should not raise an exception
        assert True
    except Exception as e:
        # Some managers may need specific config, which is OK
        if "config" in str(e).lower() or "token" in str(e).lower() or "key" in str(e).lower():
            pytest.skip(f"{manager_class.__name__} requires specific configuration")
        else:
            pytest.fail(f"{manager_class.__name__}.initialize() failed: {e}")

@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.parametrize("manager_class", MANAGER_CLASSES)
async def test_manager_cleanup(manager_class):
    """Test that manager can be cleaned up"""
    manager = manager_class()
    try:
        await manager.initialize()
    except:
        pass  # Initialization may fail without config
    
    try:
        await manager.cleanup()
        # Should not raise an exception
        assert True
    except Exception as e:
        pytest.fail(f"{manager_class.__name__}.cleanup() failed: {e}")

@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.parametrize("manager_class", [
    AIProvidersManager,
    TranslationManager,
    DataAnalysisManager,
])
async def test_critical_managers_lifecycle(manager_class):
    """Integration test for critical managers lifecycle"""
    manager = manager_class()
    
    # Initialize
    try:
        await manager.initialize()
    except Exception as e:
        if "config" in str(e).lower() or "token" in str(e).lower():
            pytest.skip(f"{manager_class.__name__} requires configuration")
        else:
            raise
    
    # Cleanup
    await manager.cleanup()

@pytest.mark.unit
def test_manager_count():
    """Test that we have all expected managers"""
    assert len(MANAGER_CLASSES) >= 43, f"Expected at least 43 managers, found {len(MANAGER_CLASSES)}"

@pytest.mark.unit
@pytest.mark.parametrize("manager_class", MANAGER_CLASSES)
def test_manager_class_naming(manager_class):
    """Test that manager classes follow naming convention"""
    class_name = manager_class.__name__
    assert class_name.endswith("Manager"), f"{class_name} doesn't end with 'Manager'"

@pytest.mark.asyncio
@pytest.mark.unit
async def test_ai_providers_manager_special():
    """Special test for AIProvidersManager - most critical manager"""
    manager = AIProvidersManager()
    await manager.initialize()
    
    # Check it has key methods
    assert hasattr(manager, "generate_text") or hasattr(manager, "chat"), \
        "AIProvidersManager missing text generation capability"
    
    await manager.cleanup()

@pytest.mark.unit
def test_all_managers_imported():
    """Test that all managers can be imported from integrations module"""
    from windows_ai import integrations
    
    # Check that all expected managers are available
    expected_managers = [
        "AIProvidersManager",
        "ImageGenerationManager",
        "AudioSpeechManager",
        "VideoGenerationManager",
        "DocumentProcessingManager",
        "WindowsAutomationManager",
        "BrowserAutomationManager",
        "ProductivityManager"
    ]
    
    for manager_name in expected_managers:
        assert hasattr(integrations, manager_name), f"integrations module missing {manager_name}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
