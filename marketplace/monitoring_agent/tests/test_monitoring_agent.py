"""Tests for monitoring_agent plugin."""

import pytest
from marketplace.monitoring_agent import MonitoringAgentPlugin


class TestMonitoringAgentPlugin:
    """Test cases for MonitoringAgentPlugin."""
    
    def test_initialization(self):
        """Test plugin initialization."""
        plugin = MonitoringAgentPlugin()
        assert plugin is not None
        assert plugin.enabled is True
    
    def test_validation(self):
        """Test plugin validation."""
        plugin = MonitoringAgentPlugin()
        assert plugin.validate() is True
    
    def test_lifecycle(self):
        """Test plugin lifecycle."""
        plugin = MonitoringAgentPlugin()
        plugin.initialize()
        plugin.shutdown()
        assert True  # No exceptions


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
