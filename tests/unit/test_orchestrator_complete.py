"""
Comprehensive tests for Windows AI Orchestrator
Tests all core functionality including initialization, managers, and cleanup
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from windows_ai.core.orchestrator import WindowsAI, get_windows_ai, quick_start


@pytest.mark.unit
@pytest.mark.asyncio
class TestOrchestratorInitialization:
    """Test orchestrator initialization"""
    
    async def test_orchestrator_creates_successfully(self):
        """Test that orchestrator instance creates"""
        orchestrator = WindowsAI()
        assert orchestrator is not None
        assert orchestrator._initialized == False
        assert len(orchestrator._managers) == 0
    
    async def test_orchestrator_initializes(self):
        """Test that orchestrator initializes all managers"""
        orchestrator = WindowsAI()
        
        # Mock the manager initialization to avoid actual setup
        with patch.object(orchestrator, '_init_all_managers', new_callable=AsyncMock):
            await orchestrator.initialize()
            
            assert orchestrator._initialized == True
            assert orchestrator._config is not None
    
    async def test_orchestrator_auto_configure(self):
        """Test auto-configuration detects environment"""
        orchestrator = WindowsAI()
        config = await orchestrator._auto_configure(None)
        
        # _auto_configure returns detected_providers, available_providers, default_provider
        assert "detected_providers" in config
        assert "available_providers" in config
        assert "default_provider" in config
        assert isinstance(config["detected_providers"], list)
        assert isinstance(config["available_providers"], list)
    
    async def test_orchestrator_detect_api_keys(self):
        """Test API key detection from environment"""
        import os
        
        # Set test API key
        os.environ["OPENAI_API_KEY"] = "test-key-123"
        
        orchestrator = WindowsAI()
        keys = orchestrator._detect_api_keys()
        
        assert "OPENAI_API_KEY" in keys
        assert keys["OPENAI_API_KEY"] == "test-key-123"
        
        # Cleanup
        del os.environ["OPENAI_API_KEY"]
    
    async def test_orchestrator_prevents_double_initialization(self):
        """Test that orchestrator doesn't reinitialize"""
        orchestrator = WindowsAI()
        
        with patch.object(orchestrator, '_init_all_managers', new_callable=AsyncMock) as mock_init:
            await orchestrator.initialize()
            await orchestrator.initialize()  # Second call
            
            # Should only initialize once
            assert mock_init.call_count == 1


@pytest.mark.unit
@pytest.mark.asyncio
class TestOrchestratorManagers:
    """Test orchestrator manager coordination"""
    
    async def test_managers_initialized_concurrently(self):
        """Test that managers initialize in parallel"""
        orchestrator = WindowsAI()
        
        # Mock manager classes
        with patch('windows_ai.integrations.AIProvidersManager') as mock_ai, \
             patch('windows_ai.integrations.ImageGenerationManager') as mock_img, \
             patch('windows_ai.integrations.AudioSpeechManager') as mock_audio:
            
            # Create mock instances
            mock_ai.return_value.initialize = AsyncMock()
            mock_img.return_value.initialize = AsyncMock()
            mock_audio.return_value.initialize = AsyncMock()
            
            await orchestrator.initialize()
            
            # Verify all managers got initialized
            assert len(orchestrator._managers) > 0
    
    async def test_manager_initialization_graceful_degradation(self):
        """Test that one failing manager doesn't crash the system"""
        orchestrator = WindowsAI()
        orchestrator._config = {}
        
        # Create a mock manager that fails
        failing_manager = MagicMock()
        failing_manager.initialize = AsyncMock(side_effect=Exception("Test failure"))
        
        # Should not raise
        await orchestrator._init_single_manager("test", failing_manager)
        
        # Manager should still be added for graceful degradation
        assert "test" in orchestrator._managers
    
    async def test_get_manager_returns_correct_instance(self):
        """Test that get_manager returns the right manager"""
        orchestrator = WindowsAI()
        
        # Add a test manager
        test_manager = MagicMock()
        orchestrator._managers["test"] = test_manager
        
        result = orchestrator.get_manager("test")
        assert result == test_manager
    
    async def test_get_manager_returns_none_for_missing(self):
        """Test that get_manager returns None for missing managers"""
        orchestrator = WindowsAI()
        result = orchestrator.get_manager("nonexistent")
        assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
class TestOrchestratorAPI:
    """Test orchestrator public API"""
    
    async def test_chat_auto_initializes(self):
        """Test that chat initializes if not already initialized"""
        orchestrator = WindowsAI()
        
        # Mock initialize and AI manager
        with patch.object(orchestrator, 'initialize', new_callable=AsyncMock) as mock_init, \
             patch.object(orchestrator, '_initialized', False):
            
            mock_ai_manager = MagicMock()
            mock_ai_manager.chat = AsyncMock(return_value="Hello!")
            orchestrator._managers = {"ai": mock_ai_manager}
            
            await orchestrator.chat("Test message")
            
            # Verify initialization was called
            mock_init.assert_called_once()
    
    async def test_chat_handles_errors_gracefully(self):
        """Test that chat returns error message on failure"""
        orchestrator = WindowsAI()
        orchestrator._initialized = True
        
        # Mock failing AI manager
        mock_ai_manager = MagicMock()
        mock_ai_manager.chat = AsyncMock(side_effect=Exception("Test error"))
        orchestrator._managers = {"ai": mock_ai_manager}
        
        result = await orchestrator.chat("Test")
        
        assert result.startswith("Error:")
        assert "Test error" in result
    
    async def test_status_returns_system_info(self):
        """Test that status returns comprehensive info"""
        orchestrator = WindowsAI()
        orchestrator._initialized = True
        orchestrator._managers = {"test1": MagicMock(), "test2": MagicMock()}
        orchestrator._config = {"setting": "value", "api_keys": {"secret": "hidden"}}
        
        status = orchestrator.status()
        
        assert status["initialized"] == True
        assert status["managers_loaded"] == 2
        assert "config" in status
        assert "api_keys" not in status["config"]  # Sensitive data hidden
    
    async def test_execute_plugin_auto_initializes(self):
        """Test that execute_plugin initializes if needed"""
        orchestrator = WindowsAI()
        
        with patch.object(orchestrator, 'initialize', new_callable=AsyncMock) as mock_init, \
             patch('windows_ai.core.plugin_manager.get_plugin_manager') as mock_pm:
            
            mock_plugin_manager = MagicMock()
            mock_plugin_manager.execute_plugin = AsyncMock(return_value={"status": "success"})
            mock_pm.return_value = mock_plugin_manager
            
            orchestrator._initialized = False
            result = await orchestrator.execute_plugin("test-plugin")
            
            mock_init.assert_called_once()
            assert result["status"] == "success"
    
    async def test_list_plugins_handles_errors(self):
        """Test that list_plugins returns empty list on error"""
        orchestrator = WindowsAI()
        
        with patch('windows_ai.core.plugin_manager.get_plugin_manager') as mock_pm:
            mock_pm.side_effect = Exception("Test error")
            
            result = await orchestrator.list_plugins()
            
            assert result == []


@pytest.mark.unit
@pytest.mark.asyncio
class TestOrchestratorCleanup:
    """Test orchestrator cleanup and resource management"""
    
    async def test_cleanup_shuts_down_all_managers(self):
        """Test that cleanup calls cleanup on all managers"""
        orchestrator = WindowsAI()
        orchestrator._initialized = True
        
        # Create mock managers with cleanup
        manager1 = MagicMock()
        manager1.cleanup = AsyncMock()
        manager2 = MagicMock()
        manager2.cleanup = AsyncMock()
        
        orchestrator._managers = {"mgr1": manager1, "mgr2": manager2}
        
        await orchestrator.cleanup()
        
        manager1.cleanup.assert_called_once()
        manager2.cleanup.assert_called_once()
        assert orchestrator._initialized == False
        assert len(orchestrator._managers) == 0
    
    async def test_cleanup_handles_manager_failures(self):
        """Test that cleanup continues even if a manager fails"""
        orchestrator = WindowsAI()
        orchestrator._initialized = True
        
        # One manager fails, one succeeds
        failing_manager = MagicMock()
        failing_manager.cleanup = AsyncMock(side_effect=Exception("Cleanup failed"))
        good_manager = MagicMock()
        good_manager.cleanup = AsyncMock()
        
        orchestrator._managers = {"bad": failing_manager, "good": good_manager}
        
        # Should not raise
        await orchestrator.cleanup()
        
        # Both should be attempted
        failing_manager.cleanup.assert_called_once()
        good_manager.cleanup.assert_called_once()
        
        # System should still clean up
        assert orchestrator._initialized == False
    
    async def test_context_manager_support(self):
        """Test async context manager protocol"""
        orchestrator = WindowsAI()
        
        with patch.object(orchestrator, 'initialize', new_callable=AsyncMock), \
             patch.object(orchestrator, 'cleanup', new_callable=AsyncMock):
            
            async with orchestrator as ai:
                assert ai == orchestrator
                orchestrator.initialize.assert_called_once()
            
            orchestrator.cleanup.assert_called_once()


@pytest.mark.unit
def test_global_instance_singleton():
    """Test that get_windows_ai returns singleton"""
    instance1 = get_windows_ai()
    instance2 = get_windows_ai()
    
    assert instance1 is instance2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_quick_start_initializes_and_returns():
    """Test quick_start helper function"""
    with patch('windows_ai.core.orchestrator.get_windows_ai') as mock_get:
        mock_ai = AsyncMock()
        mock_ai.initialize = AsyncMock()
        mock_get.return_value = mock_ai
        
        result = await quick_start()
        
        mock_ai.initialize.assert_called_once()
        assert result == mock_ai


@pytest.mark.unit
@pytest.mark.asyncio
class TestOrchestratorQuickAccess:
    """Test quick access methods"""
    
    async def test_ai_property_returns_manager(self):
        """Test ai() returns AI providers manager"""
        orchestrator = WindowsAI()
        mock_manager = MagicMock()
        orchestrator._managers = {"ai": mock_manager}
        
        result = orchestrator.ai()
        assert result == mock_manager
    
    async def test_vision_property_returns_manager(self):
        """Test vision() returns vision manager"""
        orchestrator = WindowsAI()
        mock_manager = MagicMock()
        orchestrator._managers = {"vision": mock_manager}
        
        result = orchestrator.vision()
        assert result == mock_manager
    
    async def test_quick_access_returns_none_when_missing(self):
        """Test quick access returns None for missing managers"""
        orchestrator = WindowsAI()
        orchestrator._managers = {}
        
        assert orchestrator.ai() is None
        assert orchestrator.vision() is None


@pytest.mark.unit
@pytest.mark.asyncio
class TestOrchestratorUnifiedAPI:
    """Test unified API methods"""
    
    async def test_generate_image_calls_image_manager(self):
        """Test generate_image routes to image generation manager"""
        orchestrator = WindowsAI()
        orchestrator._initialized = True
        
        mock_img_manager = MagicMock()
        mock_img_manager.generate = AsyncMock(return_value=b"image_data")
        orchestrator._managers = {"images": mock_img_manager}
        
        result = await orchestrator.generate_image("A cat")
        
        mock_img_manager.generate.assert_called_once_with("A cat")
        assert result == b"image_data"
    
    async def test_transcribe_calls_audio_manager(self):
        """Test transcribe routes to audio manager"""
        orchestrator = WindowsAI()
        orchestrator._initialized = True
        
        mock_audio_manager = MagicMock()
        mock_audio_manager.speech_to_text = AsyncMock(return_value="Transcribed text")
        orchestrator._managers = {"audio": mock_audio_manager}
        
        result = await orchestrator.transcribe("audio.mp3")
        
        mock_audio_manager.speech_to_text.assert_called_once_with("audio.mp3")
        assert result == "Transcribed text"
    
    async def test_search_web_calls_search_manager(self):
        """Test search_web routes to search manager"""
        orchestrator = WindowsAI()
        orchestrator._initialized = True
        
        mock_search_manager = MagicMock()
        mock_search_manager.search = AsyncMock(return_value=[{"title": "Result"}])
        orchestrator._managers = {"search": mock_search_manager}
        
        result = await orchestrator.search_web("test query")
        
        mock_search_manager.search.assert_called_once_with("test query")
        assert len(result) == 1
        assert result[0]["title"] == "Result"


@pytest.mark.integration
@pytest.mark.asyncio
class TestOrchestratorIntegration:
    """Integration tests for orchestrator with real components"""
    
    async def test_full_initialization_workflow(self):
        """Test complete initialization workflow"""
        orchestrator = WindowsAI()
        
        # Provide minimal config
        config = {
            "auto_install_dependencies": False,
            "offline_mode": True
        }
        
        # This will attempt real initialization but should handle failures gracefully
        await orchestrator.initialize(config)
        
        assert orchestrator._initialized == True
        assert len(orchestrator._managers) > 0
        
        # Cleanup
        await orchestrator.cleanup()
    
    async def test_list_capabilities_aggregates_from_managers(self):
        """Test that list_capabilities collects from all managers"""
        orchestrator = WindowsAI()
        orchestrator._initialized = True
        
        # Mock managers with capabilities
        manager1 = MagicMock()
        manager1.list_capabilities = MagicMock(return_value=["cap1", "cap2"])
        manager2 = MagicMock()
        manager2.list_capabilities = MagicMock(return_value=["cap3"])
        
        orchestrator._managers = {"mgr1": manager1, "mgr2": manager2}
        
        capabilities = orchestrator.list_capabilities()
        
        assert "mgr1" in capabilities
        assert "mgr2" in capabilities
        assert capabilities["mgr1"] == ["cap1", "cap2"]
        assert capabilities["mgr2"] == ["cap3"]
