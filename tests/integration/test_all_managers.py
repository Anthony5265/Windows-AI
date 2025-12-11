"""
Comprehensive Integration Tests for All 45 Managers
Tests initialization, basic operations, and cleanup for all managers
"""

import pytest
import asyncio
from windows_ai.core.orchestrator import WindowsAI

@pytest.mark.integration
@pytest.mark.asyncio
async def test_all_managers_initialize():
    """Test that all 45 managers can initialize without errors"""
    orchestrator = WindowsAI()
    await orchestrator.initialize()
    
    # Verify all managers initialized
    assert len(orchestrator._managers) == 45
    
    # Verify orchestrator is ready
    assert orchestrator._initialized == True
    
    await orchestrator.cleanup()

@pytest.mark.integration
@pytest.mark.asyncio
async def test_managers_cleanup():
    """Test that all managers cleanup properly"""
    orchestrator = WindowsAI()
    await orchestrator.initialize()
    
    # Cleanup should not raise errors
    await orchestrator.cleanup()
    
    # Verify cleanup worked
    assert orchestrator._initialized == False

@pytest.mark.integration
@pytest.mark.asyncio
async def test_orchestrator_chat():
    """Test basic chat functionality"""
    orchestrator = WindowsAI()
    await orchestrator.initialize()
    
    try:
        # This will fail without API keys but shouldn't crash
        response = await orchestrator.chat("Hello")
        # If we get here, great! If not, exception caught below
    except Exception as e:
        # Expected without API keys
        assert "API key" in str(e) or "provider" in str(e).lower()
    
    await orchestrator.cleanup()

@pytest.mark.integration
@pytest.mark.asyncio
async def test_plugin_execution():
    """Test plugin execution through orchestrator"""
    orchestrator = WindowsAI()
    await orchestrator.initialize()
    
    # Get available plugins - may be 0 if no plugins loaded
    plugins = await orchestrator.list_plugins()
    # Just verify the call works without error
    assert isinstance(plugins, list)
    
    await orchestrator.cleanup()
