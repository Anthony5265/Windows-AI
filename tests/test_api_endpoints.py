import pytest
from unittest.mock import Mock, patch, AsyncMock
from windows_ai.api.server import app
import json

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

class TestAPIEndpoints:
    def test_health_check(self, client):
        response = client.get('/api/health')
        assert response.status_code == 200
        assert 'status' in response.json
        
    def test_plugin_list(self, client):
        response = client.get('/api/plugins')
        assert response.status_code == 200
        assert isinstance(response.json.get('plugins'), list)
        
    def test_plugin_load(self, client):
        response = client.post('/api/plugins/load', json={'name': 'test_plugin'})
        assert response.status_code in [200, 404]
        
    def test_query_endpoint(self, client):
        response = client.post('/api/query', json={'query': 'test'})
        assert response.status_code in [200, 400]
