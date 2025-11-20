"""FastAPI server for Windows AI

Complete REST API server with all endpoints for plugin management,
agent orchestration, and system monitoring.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.openapi.docs import get_swagger_ui_html
import uvicorn
import logging
import time

from windows_ai.api.routes import router, set_plugin_manager
from windows_ai.api.middleware import setup_middleware
from windows_ai.core.plugin_manager import PluginManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Windows AI API",
    description="""
    Complete REST API for Windows AI

    ## Features

    * **Plugin Management** - List, query, and manage 155+ AI integrations
    * **Plugin Execution** - Execute actions on any plugin with async support
    * **Agent Orchestration** - Create and manage AI agents (coming soon)
    * **System Monitoring** - Health checks, stats, and system information
    * **Authentication** - API key and bearer token support
    * **Rate Limiting** - Protect against abuse
    * **Full OpenAPI** - Complete API documentation

    ## Authentication

    Include your API key in requests using one of:
    - Header: `X-API-Key: your-api-key`
    - Bearer token: `Authorization: Bearer your-api-key`

    If no API key is configured, the API runs in development mode (no auth required).

    ## Categories

    - **Code Models** (15 plugins) - GitHub Copilot, CodeWhisperer, Tabnine, etc.
    - **Vision Models** (20 plugins) - GPT-4V, Gemini Vision, Claude Vision, etc.
    - **Audio Models** (25 plugins) - Whisper, ElevenLabs, Azure Speech, etc.
    - **Windows Integration** (30 plugins) - Windows Hello, Defender, WSL2, etc.
    - **Cloud Services** (40+ plugins) - AWS, Azure, GCP integrations
    - **And many more...**
    """,
    version="2.0.0-alpha",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Setup middleware
setup_middleware(app)

# Include API routes
app.include_router(router, prefix="/api/v1")

# Global plugin manager
_plugin_manager: PluginManager = None

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    global _plugin_manager

    logger.info("Starting Windows AI API server...")

    # Initialize plugin manager
    try:
        _plugin_manager = PluginManager()
        await _plugin_manager.initialize()
        _plugin_manager.start_time = time.time()

        # Set plugin manager for routes
        set_plugin_manager(_plugin_manager)

        plugins = _plugin_manager.get_all_plugins()
        logger.info(f"Loaded {len(plugins)} plugins")

        # Log categories
        categories = {}
        for p in plugins:
            for tag in p.get('tags', []):
                categories[tag] = categories.get(tag, 0) + 1

        logger.info(f"Plugin categories: {categories}")

    except Exception as e:
        logger.error(f"Failed to initialize plugin manager: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global _plugin_manager

    logger.info("Shutting down Windows AI API server...")

    if _plugin_manager:
        try:
            await _plugin_manager.shutdown()
            logger.info("Plugin manager shut down successfully")
        except Exception as e:
            logger.error(f"Error shutting down plugin manager: {e}")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with welcome message"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Windows AI API</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background: #f5f5f5;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #0078d4;
                margin-top: 0;
            }
            .badge {
                display: inline-block;
                padding: 5px 10px;
                background: #28a745;
                color: white;
                border-radius: 5px;
                font-size: 14px;
                margin-left: 10px;
            }
            .links {
                margin-top: 30px;
            }
            .links a {
                display: inline-block;
                margin-right: 20px;
                color: #0078d4;
                text-decoration: none;
                font-weight: bold;
            }
            .links a:hover {
                text-decoration: underline;
            }
            .stats {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 5px;
                margin-top: 20px;
            }
            .stat {
                margin: 10px 0;
            }
            .stat-label {
                font-weight: bold;
                color: #495057;
            }
            .stat-value {
                color: #0078d4;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>
                🪟 Windows AI API
                <span class="badge">v2.0.0-alpha</span>
            </h1>
            <p>
                Welcome to the Windows AI REST API! This API provides access to 155+ AI integrations
                including code models, vision models, audio models, and Windows integrations.
            </p>

            <div class="stats">
                <h3>Quick Stats</h3>
                <div class="stat">
                    <span class="stat-label">Total Plugins:</span>
                    <span class="stat-value">155+</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Categories:</span>
                    <span class="stat-value">Code, Vision, Audio, Windows, Cloud, and more</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Status:</span>
                    <span class="stat-value">Active Development</span>
                </div>
            </div>

            <div class="links">
                <a href="/docs">📚 API Documentation</a>
                <a href="/redoc">📖 ReDoc</a>
                <a href="/api/v1/system/health">🏥 Health Check</a>
                <a href="/api/v1/system/info">ℹ️ System Info</a>
            </div>

            <h3>Quick Start</h3>
            <pre><code># List all plugins
curl http://localhost:8000/api/v1/plugins/

# Execute a plugin
curl -X POST http://localhost:8000/api/v1/plugins/whisper/execute \\
  -H "Content-Type: application/json" \\
  -d '{"action": "transcribe", "params": {"audio_file": "audio.mp3"}}'

# Health check
curl http://localhost:8000/api/v1/system/health
</code></pre>
        </div>
    </body>
    </html>
    """

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "path": str(request.url)
        }
    )

def start_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Start the API server"""
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(
        "windows_ai.api.server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

if __name__ == "__main__":
    start_server(reload=True)
