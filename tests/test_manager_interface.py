"""Test that all managers have required methods"""

import asyncio
import inspect
from windows_ai.integrations import (
    AIProvidersManager, ImageGenerationManager, AudioSpeechManager,
    VideoGenerationManager, DocumentProcessingManager, WindowsAutomationManager,
    BrowserAutomationManager, ProductivityManager, DataAnalysisManager,
    CodeAssistantsManager, TranslationManager, SearchEnginesManager,
    KnowledgeGraphManager, ThreeDGenerationManager, MusicGenerationManager,
    EmbeddingsManager, VectorStoresManager, WorkflowAutomationManager,
    EmailServicesManager, NotificationsManager, CloudStorageManager,
    DatabaseManager, MonitoringManager, AIAgentsManager,
    SecurityScanningManager, ContentModerationManager, RAGPipelineManager,
    MLOpsManager, PaymentsManager, SocialMediaManager, SchedulingManager,
    CRMManager, IoTHardwareManager, ComputerVisionManager,
    HealthcareAIManager, LegalAIManager, EducationAIManager,
    FinanceAIManager, ScientificAIManager, AccessibilityAIManager,
    RealEstateAIManager, GamingAIManager, ConversationalAIManager,
    AutomationRoboticsManager, BiometricsIdentityManager
)

MANAGERS = [
    AIProvidersManager, ImageGenerationManager, AudioSpeechManager,
    VideoGenerationManager, DocumentProcessingManager, WindowsAutomationManager,
    BrowserAutomationManager, ProductivityManager, DataAnalysisManager,
    CodeAssistantsManager, TranslationManager, SearchEnginesManager,
    KnowledgeGraphManager, ThreeDGenerationManager, MusicGenerationManager,
    EmbeddingsManager, VectorStoresManager, WorkflowAutomationManager,
    EmailServicesManager, NotificationsManager, CloudStorageManager,
    DatabaseManager, MonitoringManager, AIAgentsManager,
    SecurityScanningManager, ContentModerationManager, RAGPipelineManager,
    MLOpsManager, PaymentsManager, SocialMediaManager, SchedulingManager,
    CRMManager, IoTHardwareManager, ComputerVisionManager,
    HealthcareAIManager, LegalAIManager, EducationAIManager,
    FinanceAIManager, ScientificAIManager, AccessibilityAIManager,
    RealEstateAIManager, GamingAIManager, ConversationalAIManager,
    AutomationRoboticsManager, BiometricsIdentityManager
]

def test_manager_interface():
    """Verify all managers have required async methods"""
    
    print(f"Testing {len(MANAGERS)} integration managers...\n")
    
    missing_initialize = []
    missing_cleanup = []
    non_async_initialize = []
    non_async_cleanup = []
    
    for ManagerClass in MANAGERS:
        manager_name = ManagerClass.__name__
        
        # Check for initialize method
        if not hasattr(ManagerClass, 'initialize'):
            missing_initialize.append(manager_name)
        elif not asyncio.iscoroutinefunction(ManagerClass.initialize):
            non_async_initialize.append(manager_name)
        
        # Check for cleanup method
        if not hasattr(ManagerClass, 'cleanup'):
            missing_cleanup.append(manager_name)
        elif not asyncio.iscoroutinefunction(ManagerClass.cleanup):
            non_async_cleanup.append(manager_name)
    
    # Report results
    print(f"✅ Managers with initialize(): {len(MANAGERS) - len(missing_initialize)}/{len(MANAGERS)}")
    print(f"✅ Managers with cleanup():    {len(MANAGERS) - len(missing_cleanup)}/{len(MANAGERS)}")
    print(f"✅ Async initialize():         {len(MANAGERS) - len(non_async_initialize)}/{len(MANAGERS)}")
    print(f"✅ Async cleanup():            {len(MANAGERS) - len(non_async_cleanup)}/{len(MANAGERS)}")
    
    if missing_initialize:
        print(f"\n❌ Missing initialize(): {missing_initialize}")
    
    if missing_cleanup:
        print(f"\n❌ Missing cleanup(): {missing_cleanup}")
    
    if non_async_initialize:
        print(f"\n⚠️  Non-async initialize(): {non_async_initialize}")
    
    if non_async_cleanup:
        print(f"\n⚠️  Non-async cleanup(): {non_async_cleanup}")
    
    # Summary
    all_good = (
        len(missing_initialize) == 0 and
        len(missing_cleanup) == 0 and
        len(non_async_initialize) == 0 and
        len(non_async_cleanup) == 0
    )
    
    print("\n" + "="*60)
    if all_good:
        print("✅ ALL MANAGERS PASS - Ready for production!")
    else:
        print("⚠️  SOME ISSUES FOUND - See details above")
    print("="*60)
    
    return all_good

if __name__ == "__main__":
    success = test_manager_interface()
    exit(0 if success else 1)
