"""Tests for log_aggregator plugin."""

import pytest
from marketplace.log_aggregator import LogAggregatorPlugin


class TestLogAggregatorPlugin:
    """Test cases for LogAggregatorPlugin."""
    
    def test_initialization(self):
        """Test plugin initialization."""
        plugin = LogAggregatorPlugin()
        assert plugin is not None
        assert plugin.enabled is True
    
    def test_validation(self):
        """Test plugin validation."""
        plugin = LogAggregatorPlugin()
        assert plugin.validate() is True
    
    def test_lifecycle(self):
        """Test plugin lifecycle."""
        plugin = LogAggregatorPlugin()
        plugin.initialize()
        plugin.shutdown()
        assert True  # No exceptions


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
