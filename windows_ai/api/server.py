"""FastAPI server for Windows AI

Complete REST API server with all endpoints for plugin management,
agent orchestration, and system monitoring.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
import time

from windows_ai.api.routes import router, set_plugin_manager
from windows_ai.api.chat_routes import router as chat_router
from windows_ai.api.frontend_routes import router as frontend_router
from windows_ai.api.setup_routes import router as setup_router
from windows_ai.api.credentials_routes import router as credentials_router
from windows_ai.api.health_routes import router as health_router
from windows_ai.api.marketplace_routes import router as marketplace_router
from windows_ai.api.agent_routes import router as agent_router
from windows_ai.api.sse_routes import router as sse_router
from windows_ai.api.websocket_routes import router as websocket_router
from windows_ai.api.workflow_routes import router as workflow_router
from windows_ai.api.middleware import setup_middleware
from windows_ai.api.rate_limiter import RateLimitMiddleware
from windows_ai.core.plugin_manager import PluginManager
from windows_ai.frameworks.unified_llm import UnifiedLLMProvider
from windows_ai.core.credential_manager import CredentialManager
from windows_ai.config.unified_config import get_config
import os
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def load_credentials_to_env():
    """Load credentials from storage into environment variables"""
    try:
        manager = CredentialManager()
        
        # Mapping of (service_id, key_name) -> env_var
        mappings = [
            ("openai", "openai_api_key", "OPENAI_API_KEY"),
            ("anthropic", "anthropic_api_key", "ANTHROPIC_API_KEY"),
            ("google", "google_api_key", "GOOGLE_API_KEY"),
            ("azure", "azure_api_key", "AZURE_OPENAI_API_KEY"),
            ("mistral", "mistral_api_key", "MISTRAL_API_KEY"),
            ("groq", "groq_api_key", "GROQ_API_KEY"),
            # Fallback for standard naming
            ("openai", "api_key", "OPENAI_API_KEY"),
            ("anthropic", "api_key", "ANTHROPIC_API_KEY"),
            ("google", "api_key", "GOOGLE_API_KEY"),
        ]
        
        count = 0
        for service, key, env_var in mappings:
            value = await manager.get_credential(service, key)
            if value:
                os.environ[env_var] = value
                count += 1
                
        logger.info(f"Loaded {count} credentials into environment")
        
    except Exception as e:
        logger.error(f"Failed to load credentials: {e}")

# Load global config
_config = get_config()

# Create FastAPI app with config-driven settings
app = FastAPI(
    title=_config.get_nested('api.title', 'Windows AI API'),
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
    version=_config.version,
    docs_url=_config.get_nested('api.docs_url', '/docs'),
    redoc_url=_config.get_nested('api.redoc_url', '/redoc'),
    openapi_url=_config.get_nested('api.openapi_url', '/openapi.json')
)

# Setup CORS from config
if _config.server and hasattr(_config.server, 'cors_origins') and _config.server.cors_origins:
    logger.info(f"Setting up CORS with origins: {_config.server.cors_origins}")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_config.server.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )
else:
    logger.info("No CORS origins configured, CORS disabled")

# Setup additional middleware
setup_middleware(app)

# Include API routes
app.include_router(router, prefix="/api/v1")

# Include chat routes (for GUI) - at root level for GUI compatibility
app.include_router(chat_router, tags=["chat"])

# Include frontend routes (plugins, models) - at root level for GUI compatibility
app.include_router(frontend_router, tags=["frontend"])

# Include setup routes (first-run wizard)
app.include_router(setup_router, tags=["setup"])

# Include credentials routes (API key management)
app.include_router(credentials_router, tags=["credentials"])

# Include health check routes
app.include_router(health_router, tags=["health"])

# Include marketplace routes
app.include_router(marketplace_router, tags=["marketplace"])

# Include agent routes (agent orchestration)
app.include_router(agent_router, tags=["agents"])

# Include SSE routes (server-sent events for streaming)
app.include_router(sse_router, tags=["sse"])

# Include WebSocket routes (real-time communication)
app.include_router(websocket_router, tags=["websocket"])

# Include workflow routes (DAG workflow engine)
app.include_router(workflow_router, tags=["workflows"])

# Add rate limiting middleware
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=int(os.environ.get("RATE_LIMIT_RPM", "120")),
    burst_size=int(os.environ.get("RATE_LIMIT_BURST", "20")),
)

# Global plugin manager
_plugin_manager: PluginManager = None

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    global _plugin_manager

    logger.info("Starting Windows AI API server...")

    # Initialize Sentry error tracking (if DSN provided)
    sentry_dsn = os.environ.get("SENTRY_DSN")
    if sentry_dsn:
        try:
            import sentry_sdk
            from sentry_sdk.integrations.fastapi import FastApiIntegration
            from sentry_sdk.integrations.starlette import StarletteIntegration
            
            sentry_sdk.init(
                dsn=sentry_dsn,
                environment=os.environ.get("ENVIRONMENT", "development"),
                traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
                profiles_sample_rate=float(os.environ.get("SENTRY_PROFILES_SAMPLE_RATE", "0.1")),
                integrations=[
                    FastApiIntegration(transaction_style="endpoint"),
                    StarletteIntegration(transaction_style="endpoint"),
                ],
                # Don't send PII by default
                send_default_pii=False,
                # Attach stack traces to messages
                attach_stacktrace=True,
                # Release tracking
                release=os.environ.get("RELEASE_VERSION", "2.0.0-alpha"),
            )
            logger.info("✅ Sentry error tracking initialized")
        except ImportError:
            logger.warning("⚠️ Sentry SDK not installed - error tracking disabled")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Sentry: {e}")
    else:
        logger.info("ℹ️ Sentry DSN not configured - error tracking disabled")

    # Load credentials first
    await load_credentials_to_env()

    # Initialize plugin manager
    try:
        _plugin_manager = PluginManager()
        await _plugin_manager.initialize()
        _plugin_manager.start_time = time.time()

        # Set plugin manager for routes
        set_plugin_manager(_plugin_manager)

        # Initialize Unified LLM Provider with config
        llm_provider = UnifiedLLMProvider()
        await llm_provider.initialize(config=_config)
        
        # Store in app state for routes to access
        if not hasattr(app.state, "components"):
            app.state.components = {}
        app.state.components["llm"] = llm_provider
        app.state.components["config"] = _config  # Store config for routes
        logger.info("Unified LLM Provider initialized and attached to app state")

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
                <span class="badge">v""" + _config.version + """</span>
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

@app.get("/health")
async def health_check_root():
    """Root-level health check for GUI"""
    return {
        "status": "healthy",
        "message": "Windows AI backend is running",
        "version": _config.version,
        "timestamp": time.time()
    }

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

def create_app(components: dict = None):
    """Create and configure the FastAPI app

    Args:
        components: Optional dictionary of initialized components

    Returns:
        FastAPI application instance
    """
    if components:
        # Store components for use by the app
        app.state.components = components

    return app

def start_server(host: str = None, port: int = None, reload: bool = False):
    """Start the API server
    
    Args:
        host: Server host (uses config.server.host if not provided)
        port: Server port (uses config.server.port if not provided)
        reload: Enable auto-reload on code changes
    """
    # Use config values if not explicitly provided
    if host is None:
        host = _config.server.host if _config.server and hasattr(_config.server, 'host') else "0.0.0.0"
    if port is None:
        port = _config.server.port if _config.server and hasattr(_config.server, 'port') else 8010
    
    logger.info(f"Starting server on {host}:{port} (from config)")
    
    # Get workers from config if available
    workers = None
    if _config.server and hasattr(_config.server, 'workers'):
        workers = _config.server.workers
        logger.info(f"Using {workers} workers from config")
    
    uvicorn.run(
        "windows_ai.api.server:app",
        host=host,
        port=port,
        reload=reload,
        workers=workers if not reload else None,  # workers incompatible with reload
        log_level="info"
    )

if __name__ == "__main__":
    start_server(reload=True)
