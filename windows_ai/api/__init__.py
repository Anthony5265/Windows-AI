"""Windows AI REST API

Complete REST API for Windows AI with FastAPI.
Provides endpoints for plugin management, execution, and monitoring.
"""

from windows_ai.api.server import app, start_server

__all__ = ['app', 'start_server']
