"""
IoT MQTT Client tests.
Tests MQTTClient from windows_ai/iot/.
"""

import pytest
from windows_ai.iot.mqtt_client import MQTTClient


def test_mqtt_client_creation():
    """Test MQTTClient can be created."""
    client = MQTTClient()
    assert client is not None


def test_mqtt_client_get_status():
    """Test MQTTClient status before connection."""
    client = MQTTClient()
    status = client.get_status()
    assert isinstance(status, dict)
    assert status["connected"] is False


def test_mqtt_client_has_connect_method():
    """Test MQTTClient has connection methods."""
    client = MQTTClient()
    assert hasattr(client, 'connect')
    assert hasattr(client, 'disconnect')
    assert hasattr(client, 'publish')
    assert hasattr(client, 'subscribe')
    assert hasattr(client, 'unsubscribe')


def test_mqtt_client_has_device_methods():
    """Test MQTTClient has device-specific convenience methods."""
    client = MQTTClient()
    assert hasattr(client, 'publish_sensor_data')
    assert hasattr(client, 'publish_device_status')
    assert hasattr(client, 'subscribe_device_commands')
