"""
Unit Tests for Individual Manager Methods
Tests specific functionality of each manager type
"""

import pytest
from windows_ai.integrations.ai_providers import AIProvidersManager
from windows_ai.integrations.image_generation import ImageGenerationManager
from windows_ai.integrations.audio_speech import AudioSpeechManager

@pytest.mark.unit
@pytest.mark.asyncio
async def test_ai_providers_manager_init():
    """Test AIProvidersManager initialization"""
    manager = AIProvidersManager()
    
    # initialize may return True or None - just verify no exception
    await manager.initialize()
    assert manager._initialized == True
    
    await manager.cleanup()

@pytest.mark.unit
@pytest.mark.asyncio
async def test_image_generation_manager_init():
    """Test ImageGenerationManager initialization"""
    manager = ImageGenerationManager()
    
    # initialize may return True or None - just verify no exception
    await manager.initialize()
    assert manager._initialized == True
    
    await manager.cleanup()

@pytest.mark.unit
@pytest.mark.asyncio
async def test_audio_speech_manager_init():
    """Test AudioSpeechManager initialization"""
    manager = AudioSpeechManager()
    
    # initialize may return True or None - just verify no exception
    await manager.initialize()
    assert manager._initialized == True
    
    await manager.cleanup()

@pytest.mark.unit
@pytest.mark.asyncio
async def test_manager_cleanup_idempotent():
    """Test that cleanup can be called multiple times safely"""
    manager = AIProvidersManager()
    
    await manager.initialize()
    await manager.cleanup()
    await manager.cleanup()  # Should not raise error
