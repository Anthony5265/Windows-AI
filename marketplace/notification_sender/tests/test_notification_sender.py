"""Tests for notification_sender plugin."""

import pytest
from marketplace.notification_sender import NotificationSenderPlugin


class TestNotificationSenderPlugin:
    """Test cases for NotificationSenderPlugin."""
    
    def test_initialization(self):
        """Test plugin initialization."""
        plugin = NotificationSenderPlugin()
        assert plugin is not None
        assert plugin.enabled is True
    
    def test_validation(self):
        """Test plugin validation."""
        plugin = NotificationSenderPlugin()
        assert plugin.validate() is True
    
    def test_lifecycle(self):
        """Test plugin lifecycle."""
        plugin = NotificationSenderPlugin()
        plugin.initialize()
        plugin.shutdown()
        assert True  # No exceptions


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
