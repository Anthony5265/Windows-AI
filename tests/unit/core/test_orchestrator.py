"""
Comprehensive unit tests for WindowsAI Orchestrator

Tests the main orchestrator that manages all 2500+ AI capabilities
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from windows_ai.core.orchestrator import WindowsAI, get_windows_ai, quick_start


@pytest.fixture
def mock_config():
    """Create a mock configuration"""
    config = Mock()
    config.environment = "test"
    config.version = "1.0.0"
    config.model_dump = Mock(return_value={})
    config.set_nested = Mock()
    return config


@pytest.fixture
def orchestrator(mock_config):
    """Create orchestrator instance for testing"""
    with patch('windows_ai.core.orchestrator.get_config', return_value=mock_config):
        return WindowsAI(config=mock_config)


class TestOrchestratorInit:
    """Test orchestrator initialization"""

    def test_init_creates_instance(self, mock_config):
        """Test that WindowsAI can be instantiated"""
        with patch('windows_ai.core.orchestrator.get_config', return_value=mock_config):
            ai = WindowsAI()
            assert ai is not None
            assert ai._initialized is False
            assert isinstance(ai._managers, dict)
            assert len(ai._managers) == 0

    def test_init_with_custom_config(self, mock_config):
        """Test initialization with custom config"""
        ai = WindowsAI(config=mock_config)
        assert ai._config == mock_config

    def test_init_loads_default_config(self):
        """Test that default config is loaded if not provided"""
        mock_cfg = Mock()
        with patch('windows_ai.core.orchestrator.get_config', return_value=mock_cfg):
            ai = WindowsAI()
            assert ai._config == mock_cfg


class TestOrchestratorInitialization:
    """Test async initialization process"""

    @pytest.mark.asyncio
    async def test_initialize_success(self, orchestrator):
        """Test successful initialization"""
        with patch.object(orchestrator, '_init_all_managers', new_callable=AsyncMock) as mock_init:
            result = await orchestrator.initialize()
            assert result is True
            assert orchestrator._initialized is True
            mock_init.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_idempotent(self, orchestrator):
        """Test that multiple initialize calls are safe"""
        with patch.object(orchestrator, '_init_all_managers', new_callable=AsyncMock) as mock_init:
            await orchestrator.initialize()
            await orchestrator.initialize()
            # Should only initialize once
            assert mock_init.call_count == 1

    @pytest.mark.asyncio
    async def test_initialize_with_config_override(self, orchestrator):
        """Test initialization with config overrides"""
        overrides = {"llm.temperature": 0.8, "llm.model": "gpt-4"}

        with patch.object(orchestrator, '_init_all_managers', new_callable=AsyncMock):
            await orchestrator.initialize(config_override=overrides)
            # Should apply each override
            assert orchestrator._config.set_nested.call_count == 2

    @pytest.mark.asyncio
    async def test_initialize_with_sentry(self, orchestrator):
        """Test Sentry initialization if DSN provided"""
        with patch.dict('os.environ', {'SENTRY_DSN': 'https://test@sentry.io/123'}):
            with patch('windows_ai.core.orchestrator.sentry_sdk') as mock_sentry:
                mock_sentry.init = Mock()
                with patch.object(orchestrator, '_init_all_managers', new_callable=AsyncMock):
                    await orchestrator.initialize()
                    mock_sentry.init.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_handles_sentry_import_error(self, orchestrator):
        """Test graceful handling of missing Sentry SDK"""
        with patch.dict('os.environ', {'SENTRY_DSN': 'https://test@sentry.io/123'}):
            with patch('windows_ai.core.orchestrator.sentry_sdk', side_effect=ImportError):
                with patch.object(orchestrator, '_init_all_managers', new_callable=AsyncMock):
                    # Should not raise exception
                    result = await orchestrator.initialize()
                    assert result is True


class TestManagerInitialization:
    """Test initialization of individual managers"""

    @pytest.mark.asyncio
    async def test_init_all_managers(self, orchestrator):
        """Test that all managers are initialized"""
        mock_manager = Mock()
        mock_manager.initialize = AsyncMock(return_value=True)

        with patch('windows_ai.core.orchestrator.AIProvidersManager', return_value=mock_manager):
            with patch('windows_ai.core.orchestrator.ImageGenerationManager', return_value=mock_manager):
                with patch('windows_ai.core.orchestrator.AudioSpeechManager', return_value=mock_manager):
                    with patch('windows_ai.core.orchestrator.VideoGenerationManager', return_value=mock_manager):
                        await orchestrator._init_all_managers()
                        # Check that managers were added
                        assert len(orchestrator._managers) > 0

    @pytest.mark.asyncio
    async def test_init_single_manager_success(self, orchestrator):
        """Test successful initialization of a single manager"""
        mock_manager = Mock()
        mock_manager.initialize = AsyncMock(return_value=True)

        await orchestrator._init_single_manager("test", mock_manager)
        assert "test" in orchestrator._managers
        assert orchestrator._managers["test"] == mock_manager
        mock_manager.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_init_single_manager_graceful_degradation(self, orchestrator):
        """Test that manager initialization failures are handled gracefully"""
        mock_manager = Mock()
        mock_manager.initialize = AsyncMock(side_effect=RuntimeError("Init failed"))

        # Should not raise exception
        await orchestrator._init_single_manager("failing_manager", mock_manager)
        # Manager should still be added for graceful degradation
        assert "failing_manager" in orchestrator._managers


class TestChatInterface:
    """Test unified chat interface"""

    @pytest.mark.asyncio
    async def test_chat_success(self, orchestrator):
        """Test successful chat interaction"""
        mock_ai_manager = Mock()
        mock_ai_manager.chat = AsyncMock(return_value="Hello! How can I help?")
        orchestrator._managers["ai"] = mock_ai_manager
        orchestrator._initialized = True

        response = await orchestrator.chat("Hello", provider="openai")
        assert response == "Hello! How can I help?"
        mock_ai_manager.chat.assert_called_once_with("Hello", "openai")

    @pytest.mark.asyncio
    async def test_chat_auto_initializes(self, orchestrator):
        """Test that chat auto-initializes if not initialized"""
        mock_ai_manager = Mock()
        mock_ai_manager.chat = AsyncMock(return_value="Response")
        orchestrator._managers["ai"] = mock_ai_manager

        with patch.object(orchestrator, 'initialize', new_callable=AsyncMock) as mock_init:
            response = await orchestrator.chat("Test")
            mock_init.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_handles_errors(self, orchestrator):
        """Test that chat handles errors gracefully"""
        mock_ai_manager = Mock()
        mock_ai_manager.chat = AsyncMock(side_effect=RuntimeError("API Error"))
        orchestrator._managers["ai"] = mock_ai_manager
        orchestrator._initialized = True

        response = await orchestrator.chat("Test")
        assert "Error:" in response


class TestImageGeneration:
    """Test image generation interface"""

    @pytest.mark.asyncio
    async def test_generate_image(self, orchestrator):
        """Test image generation"""
        mock_image_manager = Mock()
        mock_image_manager.generate = AsyncMock(return_value=b"fake_image_data")
        orchestrator._managers["images"] = mock_image_manager

        result = await orchestrator.generate_image("A sunset")
        assert result == b"fake_image_data"
        mock_image_manager.generate.assert_called_once_with("A sunset")

    @pytest.mark.asyncio
    async def test_analyze_image(self, orchestrator):
        """Test image analysis"""
        mock_vision_manager = Mock()
        mock_vision_manager.analyze = AsyncMock(return_value={"description": "A cat"})
        orchestrator._managers["vision"] = mock_vision_manager

        result = await orchestrator.analyze_image("cat.jpg", task="describe")
        assert result["description"] == "A cat"
        mock_vision_manager.analyze.assert_called_once_with("cat.jpg", "describe")


class TestAudioProcessing:
    """Test audio processing interfaces"""

    @pytest.mark.asyncio
    async def test_transcribe(self, orchestrator):
        """Test audio transcription"""
        mock_audio_manager = Mock()
        mock_audio_manager.speech_to_text = AsyncMock(return_value="Transcribed text")
        orchestrator._managers["audio"] = mock_audio_manager

        result = await orchestrator.transcribe("audio.mp3")
        assert result == "Transcribed text"
        mock_audio_manager.speech_to_text.assert_called_once_with("audio.mp3")

    @pytest.mark.asyncio
    async def test_speak(self, orchestrator):
        """Test text-to-speech"""
        mock_audio_manager = Mock()
        mock_audio_manager.text_to_speech = AsyncMock(return_value=b"audio_data")
        orchestrator._managers["audio"] = mock_audio_manager

        result = await orchestrator.speak("Hello world")
        assert result == b"audio_data"
        mock_audio_manager.text_to_speech.assert_called_once_with("Hello world")


class TestOtherInterfaces:
    """Test other unified interfaces"""

    @pytest.mark.asyncio
    async def test_search_web(self, orchestrator):
        """Test web search interface"""
        mock_search_manager = Mock()
        mock_search_manager.search = AsyncMock(return_value=[{"title": "Result 1"}])
        orchestrator._managers["search"] = mock_search_manager

        result = await orchestrator.search_web("test query")
        assert len(result) == 1
        assert result[0]["title"] == "Result 1"

    @pytest.mark.asyncio
    async def test_send_email(self, orchestrator):
        """Test email sending interface"""
        mock_email_manager = Mock()
        mock_email_manager.send = AsyncMock(return_value=True)
        orchestrator._managers["email"] = mock_email_manager

        await orchestrator.send_email(
            ["test@example.com"],
            "Test Subject",
            "Test Body"
        )
        mock_email_manager.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_automate_task(self, orchestrator):
        """Test task automation interface"""
        mock_automation_manager = Mock()
        mock_automation_manager.run_task = AsyncMock(return_value={"status": "completed"})
        orchestrator._managers["automation"] = mock_automation_manager

        result = await orchestrator.automate_task("Open calculator")
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_analyze_data(self, orchestrator):
        """Test data analysis interface"""
        mock_data_manager = Mock()
        mock_data_manager.analyze = AsyncMock(return_value={"insights": []})
        orchestrator._managers["data"] = mock_data_manager

        result = await orchestrator.analyze_data([1, 2, 3], "auto")
        assert "insights" in result


class TestQuickAccessMethods:
    """Test quick access methods for managers"""

    def test_ai_accessor(self, orchestrator):
        """Test ai() quick access method"""
        mock_manager = Mock()
        orchestrator._managers["ai"] = mock_manager
        assert orchestrator.ai() == mock_manager

    def test_vision_accessor(self, orchestrator):
        """Test vision() quick access method"""
        mock_manager = Mock()
        orchestrator._managers["vision"] = mock_manager
        assert orchestrator.vision() == mock_manager

    def test_audio_accessor(self, orchestrator):
        """Test audio() quick access method"""
        mock_manager = Mock()
        orchestrator._managers["audio"] = mock_manager
        assert orchestrator.audio() == mock_manager

    def test_documents_accessor(self, orchestrator):
        """Test documents() quick access method"""
        mock_manager = Mock()
        orchestrator._managers["documents"] = mock_manager
        assert orchestrator.documents() == mock_manager

    def test_automation_accessor(self, orchestrator):
        """Test automation() quick access method"""
        mock_manager = Mock()
        orchestrator._managers["automation"] = mock_manager
        assert orchestrator.automation() == mock_manager


class TestUtilityMethods:
    """Test utility methods"""

    def test_detect_api_keys(self, orchestrator):
        """Test API key detection from environment"""
        with patch.dict('os.environ', {
            'OPENAI_API_KEY': 'sk-test123',
            'ANTHROPIC_API_KEY': 'ant-test456'
        }):
            detected = orchestrator._detect_api_keys()
            assert 'OPENAI_API_KEY' in detected
            assert 'ANTHROPIC_API_KEY' in detected
            assert detected['OPENAI_API_KEY'] == 'sk-test123'

    @pytest.mark.asyncio
    async def test_auto_configure(self, orchestrator):
        """Test auto-configuration based on environment"""
        with patch.dict('os.environ', {
            'OPENAI_API_KEY': 'sk-test',
            'ANTHROPIC_API_KEY': 'ant-test'
        }):
            config = await orchestrator._auto_configure()
            assert 'available_providers' in config
            assert 'openai' in config['available_providers']
            assert 'anthropic' in config['available_providers']

    def test_get_manager(self, orchestrator):
        """Test getting specific manager by name"""
        mock_manager = Mock()
        orchestrator._managers["test"] = mock_manager
        assert orchestrator.get_manager("test") == mock_manager
        assert orchestrator.get_manager("nonexistent") is None

    def test_list_capabilities(self, orchestrator):
        """Test listing all capabilities"""
        mock_manager = Mock()
        mock_manager.list_capabilities = Mock(return_value=["cap1", "cap2"])
        orchestrator._managers["test"] = mock_manager

        capabilities = orchestrator.list_capabilities()
        assert "test" in capabilities
        assert capabilities["test"] == ["cap1", "cap2"]


class TestHealthCheck:
    """Test health check functionality"""

    @pytest.mark.asyncio
    async def test_health_check_all_healthy(self, orchestrator):
        """Test health check when all managers are healthy"""
        mock_manager = Mock()
        mock_manager.health_check = AsyncMock(return_value={"status": "ok"})
        orchestrator._managers["test"] = mock_manager
        orchestrator._initialized = True

        health = await orchestrator.health_check()
        assert health["status"] == "healthy"
        assert health["initialized"] is True
        assert "test" in health["managers"]

    @pytest.mark.asyncio
    async def test_health_check_degraded(self, orchestrator):
        """Test health check with some failures"""
        mock_manager1 = Mock()
        mock_manager1.health_check = AsyncMock(return_value={"status": "ok"})
        mock_manager2 = Mock()
        mock_manager2.health_check = AsyncMock(side_effect=RuntimeError("Failed"))

        orchestrator._managers["healthy"] = mock_manager1
        orchestrator._managers["unhealthy"] = mock_manager2
        orchestrator._initialized = True

        health = await orchestrator.health_check()
        assert health["status"] == "degraded"
        assert len(health["errors"]) > 0

    @pytest.mark.asyncio
    async def test_health_check_basic_managers(self, orchestrator):
        """Test health check for managers without health_check method"""
        mock_manager = Mock(spec=[])  # No health_check method
        orchestrator._managers["basic"] = mock_manager
        orchestrator._initialized = True

        health = await orchestrator.health_check()
        assert "basic" in health["managers"]
        assert health["managers"]["basic"]["status"] == "ok"


class TestStatus:
    """Test status reporting"""

    def test_status(self, orchestrator):
        """Test status report"""
        mock_manager = Mock()
        mock_manager.list_capabilities = Mock(return_value=["cap1", "cap2"])
        orchestrator._managers["test"] = mock_manager
        orchestrator._initialized = True

        status = orchestrator.status()
        assert status["initialized"] is True
        assert status["managers_loaded"] == 1
        assert "config" in status


class TestCleanup:
    """Test cleanup functionality"""

    @pytest.mark.asyncio
    async def test_cleanup_all_managers(self, orchestrator):
        """Test cleanup of all managers"""
        mock_manager = Mock()
        mock_manager.cleanup = AsyncMock(return_value=True)
        orchestrator._managers["test"] = mock_manager
        orchestrator._initialized = True

        await orchestrator.cleanup()

        mock_manager.cleanup.assert_called_once()
        assert orchestrator._initialized is False
        assert len(orchestrator._managers) == 0

    @pytest.mark.asyncio
    async def test_cleanup_handles_errors(self, orchestrator):
        """Test that cleanup handles individual manager errors"""
        mock_manager = Mock()
        mock_manager.cleanup = AsyncMock(side_effect=RuntimeError("Cleanup failed"))
        orchestrator._managers["failing"] = mock_manager

        # Should not raise exception
        await orchestrator.cleanup()
        assert len(orchestrator._managers) == 0


class TestPluginIntegration:
    """Test plugin system integration"""

    @pytest.mark.asyncio
    async def test_execute_plugin(self, orchestrator):
        """Test plugin execution through orchestrator"""
        with patch('windows_ai.core.orchestrator.get_plugin_manager') as mock_get_pm:
            mock_pm = Mock()
            mock_pm.execute_plugin = AsyncMock(return_value={"status": "success"})
            mock_get_pm.return_value = mock_pm

            orchestrator._initialized = True
            result = await orchestrator.execute_plugin("test_plugin", param="value")

            assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_execute_plugin_error_handling(self, orchestrator):
        """Test plugin execution error handling"""
        with patch('windows_ai.core.orchestrator.get_plugin_manager') as mock_get_pm:
            mock_pm = Mock()
            mock_pm.execute_plugin = AsyncMock(side_effect=RuntimeError("Plugin error"))
            mock_get_pm.return_value = mock_pm

            orchestrator._initialized = True
            result = await orchestrator.execute_plugin("test_plugin")

            assert result["status"] == "error"
            assert "error" in result

    @pytest.mark.asyncio
    async def test_list_plugins(self, orchestrator):
        """Test listing plugins through orchestrator"""
        with patch('windows_ai.core.orchestrator.get_plugin_manager') as mock_get_pm:
            mock_pm = Mock()
            mock_pm.list_plugins = AsyncMock(return_value=[{"id": "plugin1"}])
            mock_get_pm.return_value = mock_pm

            result = await orchestrator.list_plugins()
            assert len(result) == 1
            assert result[0]["id"] == "plugin1"


class TestContextManager:
    """Test context manager support"""

    def test_sync_context_manager(self, orchestrator):
        """Test synchronous context manager"""
        with orchestrator as ai:
            assert ai is orchestrator

    @pytest.mark.asyncio
    async def test_async_context_manager(self, orchestrator):
        """Test asynchronous context manager"""
        with patch.object(orchestrator, 'initialize', new_callable=AsyncMock):
            with patch.object(orchestrator, 'cleanup', new_callable=AsyncMock) as mock_cleanup:
                async with orchestrator as ai:
                    assert ai is orchestrator
                mock_cleanup.assert_called_once()


class TestSingletonAndQuickStart:
    """Test singleton pattern and quick start"""

    def test_get_windows_ai_singleton(self):
        """Test that get_windows_ai returns singleton"""
        with patch('windows_ai.core.orchestrator.get_config'):
            ai1 = get_windows_ai()
            ai2 = get_windows_ai()
            assert ai1 is ai2

    @pytest.mark.asyncio
    async def test_quick_start(self):
        """Test quick_start helper function"""
        with patch('windows_ai.core.orchestrator.get_config'):
            with patch('windows_ai.core.orchestrator.get_windows_ai') as mock_get_ai:
                mock_ai = Mock()
                mock_ai.initialize = AsyncMock(return_value=True)
                mock_get_ai.return_value = mock_ai

                result = await quick_start()
                assert result == mock_ai
                mock_ai.initialize.assert_called_once()
