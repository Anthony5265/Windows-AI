"""FastAPI server for Windows AI.

The canonical runtime is initialized here as the application composition
root while existing route modules remain available during the convergence
period described by AI_BLUEPRINT.md.
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
import time
import os

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
from windows_ai.api.observability_routes import router as observability_router
from windows_ai.api.mesh_routes import router as mesh_router
from windows_ai.api.canonical_routes import router as canonical_router
from windows_ai.api.middleware import setup_middleware
from windows_ai.api.rate_limiter import RateLimitMiddleware
from windows_ai.core.plugin_manager import PluginManager
from windows_ai.frameworks.unified_llm import UnifiedLLMProvider
from windows_ai.core.credential_manager import CredentialManager
from windows_ai.config.unified_config import get_config
from windows_ai.canonical_runtime import CanonicalRuntime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def load_credentials_to_env():
    """Load credentials from storage into environment variables."""
    try:
        manager = CredentialManager()
        mappings = [
            ("openai", "openai_api_key", "OPENAI_API_KEY"),
            ("anthropic", "anthropic_api_key", "ANTHROPIC_API_KEY"),
            ("google", "google_api_key", "GOOGLE_API_KEY"),
            ("azure", "azure_api_key", "AZURE_OPENAI_API_KEY"),
            ("mistral", "mistral_api_key", "MISTRAL_API_KEY"),
            ("groq", "groq_api_key", "GROQ_API_KEY"),
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
        logger.info("Loaded %s credentials into environment", count)
    except Exception as e:
        logger.error("Failed to load credentials: %s", e)

_config = get_config()
app = FastAPI(
    title=_config.get_nested('api.title', 'Windows AI API'),
    description="Canonical Windows-AI API plus the existing compatibility routes.",
    version=_config.version,
    docs_url=_config.get_nested('api.docs_url', '/docs'),
    redoc_url=_config.get_nested('api.redoc_url', '/redoc'),
    openapi_url=_config.get_nested('api.openapi_url', '/openapi.json')
)

if _config.server and hasattr(_config.server, 'cors_origins') and _config.server.cors_origins:
    app.add_middleware(CORSMiddleware, allow_origins=_config.server.cors_origins,
                       allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

setup_middleware(app)
app.include_router(router, prefix="/api/v1")
app.include_router(chat_router, tags=["chat"])
app.include_router(frontend_router, tags=["frontend"])
app.include_router(setup_router, tags=["setup"])
app.include_router(credentials_router, tags=["credentials"])
app.include_router(health_router, tags=["health"])
app.include_router(marketplace_router, tags=["marketplace"])
app.include_router(agent_router, tags=["agents"])
app.include_router(sse_router, tags=["sse"])
app.include_router(websocket_router, tags=["websocket"])
app.include_router(workflow_router, tags=["workflows"])
app.include_router(observability_router, tags=["observability"])
app.include_router(mesh_router, tags=["mesh"])
app.include_router(canonical_router)

app.add_middleware(RateLimitMiddleware,
                   requests_per_minute=int(os.environ.get("RATE_LIMIT_RPM", "120")),
                   burst_size=int(os.environ.get("RATE_LIMIT_BURST", "20")))

_plugin_manager: PluginManager = None

@app.on_event("startup")
async def startup_event():
    """Initialize the canonical runtime and existing platform services."""
    global _plugin_manager
    logger.info("Starting Windows AI API server...")
    runtime = CanonicalRuntime().start()
    app.state.canonical_runtime = runtime

    try:
        _plugin_manager = PluginManager()
        app.state.plugin_manager = _plugin_manager
        set_plugin_manager(_plugin_manager)
        runtime.register_service("plugin_manager", _plugin_manager)
    except Exception as exc:
        logger.warning("Plugin manager initialization deferred: %s", exc)

    try:
        await load_credentials_to_env()
    except Exception:
        logger.exception("Credential initialization failed")

@app.on_event("shutdown")
async def shutdown_event():
    """Stop the canonical runtime cleanly."""
    runtime = getattr(app.state, "canonical_runtime", None)
    if runtime is not None:
        runtime.stop()

@app.get("/", response_class=HTMLResponse)
async def root():
    return "<h1>Windows AI</h1><p>Canonical runtime is available at /api/v1/runtime.</p>"

@app.get("/openapi.json")
async def openapi_json():
    return app.openapi()

def create_app(components: dict = None):
    """Return the configured application and optionally attach legacy components."""
    if components:
        app.state.components = components
    return app

if __name__ == "__main__":
    uvicorn.run("windows_ai.api.server:app", host="0.0.0.0", port=int(os.environ.get("PORT", "8000")), reload=False)
