"""
Setup API for Electron GUI Integration

Provides REST API endpoints for first-run setup wizard
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/setup", tags=["setup"])


class SetupStatusResponse(BaseModel):
    """Setup status response"""
    is_complete: bool
    current_step: Optional[str]
    total_steps: int
    completed_steps: int
    failed_steps: int
    progress_percent: int
    steps: List[Dict[str, Any]]


class APIKeyRequest(BaseModel):
    """API key configuration request"""
    service: str
    api_key: str
    description: Optional[str] = None


class SetupStepUpdate(BaseModel):
    """Setup step update for WebSocket"""
    step_id: str
    name: str
    description: str
    progress: int
    completed: bool
    error: Optional[str] = None


# Store active websocket connections
active_connections: List[WebSocket] = []


async def broadcast_step_update(step_data: Dict[str, Any]):
    """Broadcast step update to all connected clients"""
    if not active_connections:
        return
    
    update = SetupStepUpdate(**step_data)
    
    for connection in active_connections[:]:  # Copy list to avoid modification issues
        try:
            await connection.send_json(update.dict())
        except Exception as e:
            logger.error(f"Failed to send update to client: {e}")
            active_connections.remove(connection)


def get_orchestrator():
    """Get setup orchestrator instance (dependency injection)"""
    from windows_ai.core.setup_orchestrator import SetupOrchestrator
    from windows_ai.core.credential_manager import CredentialManager
    from windows_ai.core.app_database import ApplicationDatabase
    from pathlib import Path
    
    credential_manager = CredentialManager()
    db_path = Path.home() / ".windows_ai" / "windows_ai.db"
    app_database = ApplicationDatabase(str(db_path))
    
    return SetupOrchestrator(credential_manager, app_database)


@router.get("/status", response_model=SetupStatusResponse)
async def get_setup_status():
    """
    Get current setup status
    
    Returns information about setup progress and completed steps
    """
    try:
        orchestrator = get_orchestrator()
        status = orchestrator.get_setup_status()
        return SetupStatusResponse(**status)
    
    except Exception as e:
        logger.error(f"Failed to get setup status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start")
async def start_setup():
    """
    Start the setup process
    
    Initiates first-run setup and returns immediately.
    Use WebSocket endpoint for progress updates.
    """
    try:
        orchestrator = get_orchestrator()
        
        if orchestrator.is_setup_complete():
            raise HTTPException(
                status_code=400,
                detail="Setup has already been completed"
            )
        
        # Run setup in background task
        asyncio.create_task(
            orchestrator.run_setup(progress_callback=broadcast_step_update)
        )
        
        return {"status": "started", "message": "Setup process initiated"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start setup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
async def reset_setup():
    """
    Reset setup progress
    
    Clears all setup progress and allows re-running setup
    """
    try:
        orchestrator = get_orchestrator()
        await orchestrator.reset_setup()
        
        return {"status": "reset", "message": "Setup progress has been reset"}
    
    except Exception as e:
        logger.error(f"Failed to reset setup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api-key")
async def add_api_key(request: APIKeyRequest):
    """
    Add an API key for a service
    
    Args:
        request: Service name, API key, and optional description
    """
    try:
        from windows_ai.core.credential_manager import CredentialManager
        
        credential_manager = CredentialManager()
        
        await credential_manager.store_credential(
            service=request.service,
            key='api_key',
            value=request.api_key,
            description=request.description or f"API key for {request.service}"
        )
        
        return {
            "status": "success",
            "message": f"API key saved for {request.service}"
        }
    
    except Exception as e:
        logger.error(f"Failed to save API key: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api-keys")
async def list_api_keys():
    """
    List configured API keys
    
    Returns list of services with API keys (keys are not included)
    """
    try:
        from windows_ai.core.credential_manager import CredentialManager
        
        credential_manager = CredentialManager()
        credentials = await credential_manager.list_credentials()
        
        # Group by service and filter for api_key entries
        services = {}
        for cred in credentials:
            if cred.get('key') == 'api_key':
                service = cred.get('service')
                services[service] = {
                    'service': service,
                    'configured': True,
                    'description': cred.get('description', '')
                }
        
        return {
            "services": list(services.values())
        }
    
    except Exception as e:
        logger.error(f"Failed to list API keys: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api-key/{service}")
async def delete_api_key(service: str):
    """
    Delete an API key for a service
    
    Args:
        service: Service name
    """
    try:
        from windows_ai.core.credential_manager import CredentialManager
        
        credential_manager = CredentialManager()
        deleted = await credential_manager.delete_credential(service, 'api_key')
        
        if not deleted:
            raise HTTPException(
                status_code=404,
                detail=f"No API key found for {service}"
            )
        
        return {
            "status": "success",
            "message": f"API key deleted for {service}"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete API key: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws")
async def setup_progress_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time setup progress updates
    
    Clients connect to receive live updates during setup process
    """
    await websocket.accept()
    active_connections.append(websocket)
    
    logger.info("Setup WebSocket client connected")
    
    try:
        # Send current status immediately
        orchestrator = get_orchestrator()
        status = orchestrator.get_setup_status()
        await websocket.send_json(status)
        
        # Keep connection alive
        while True:
            # Wait for client messages (ping/pong)
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )
                
                # Handle ping
                if data == "ping":
                    await websocket.send_text("pong")
                
            except asyncio.TimeoutError:
                # Send periodic status updates
                status = orchestrator.get_setup_status()
                await websocket.send_json(status)
    
    except WebSocketDisconnect:
        logger.info("Setup WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)


@router.get("/recommended-services")
async def get_recommended_services():
    """
    Get list of recommended AI services for API key configuration
    
    Returns service metadata including name, description, and setup priority
    """
    services = [
        {
            'id': 'openai',
            'name': 'OpenAI',
            'description': 'GPT-4, GPT-3.5, DALL-E, Whisper',
            'priority': 1,
            'features': ['chat', 'completion', 'embedding', 'image', 'audio'],
            'documentation': 'https://platform.openai.com/docs/api-reference',
            'signup_url': 'https://platform.openai.com/signup'
        },
        {
            'id': 'anthropic',
            'name': 'Anthropic',
            'description': 'Claude 3 (Opus, Sonnet, Haiku)',
            'priority': 2,
            'features': ['chat', 'completion', 'analysis'],
            'documentation': 'https://docs.anthropic.com/claude/reference',
            'signup_url': 'https://console.anthropic.com/signup'
        },
        {
            'id': 'google',
            'name': 'Google AI',
            'description': 'Gemini Pro, Gemini Vision',
            'priority': 3,
            'features': ['chat', 'completion', 'vision', 'embedding'],
            'documentation': 'https://ai.google.dev/docs',
            'signup_url': 'https://makersuite.google.com/app/apikey'
        },
        {
            'id': 'cohere',
            'name': 'Cohere',
            'description': 'Command, Embed, Rerank',
            'priority': 4,
            'features': ['chat', 'embedding', 'classification', 'search'],
            'documentation': 'https://docs.cohere.com/reference/about',
            'signup_url': 'https://dashboard.cohere.com/register'
        },
        {
            'id': 'azure_openai',
            'name': 'Azure OpenAI',
            'description': 'Enterprise OpenAI via Microsoft Azure',
            'priority': 5,
            'features': ['chat', 'completion', 'embedding'],
            'documentation': 'https://learn.microsoft.com/en-us/azure/ai-services/openai/',
            'signup_url': 'https://azure.microsoft.com/en-us/products/ai-services/openai-service'
        },
        {
            'id': 'huggingface',
            'name': 'Hugging Face',
            'description': 'Open-source models and inference API',
            'priority': 6,
            'features': ['chat', 'completion', 'embedding', 'image', 'audio'],
            'documentation': 'https://huggingface.co/docs/api-inference/index',
            'signup_url': 'https://huggingface.co/join'
        }
    ]
    
    return {"services": services}


@router.get("/system-requirements")
async def check_system_requirements():
    """
    Check system requirements and compatibility
    
    Returns information about system specs and compatibility
    """
    import platform
    import sys
    
    requirements = {
        'python_version': {
            'current': sys.version,
            'required': '3.8+',
            'compatible': sys.version_info >= (3, 8)
        },
        'operating_system': {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'compatible': platform.system() == 'Windows'
        },
        'architecture': {
            'current': platform.machine(),
            'compatible': platform.machine() in ['AMD64', 'x86_64']
        }
    }
    
    # Check disk space
    try:
        from pathlib import Path
        import shutil
        
        home = Path.home()
        stat = shutil.disk_usage(home)
        
        requirements['disk_space'] = {
            'free_gb': stat.free / (1024**3),
            'total_gb': stat.total / (1024**3),
            'required_gb': 5.0,
            'compatible': stat.free / (1024**3) >= 5.0
        }
    except Exception as e:
        logger.warning(f"Could not check disk space: {e}")
        requirements['disk_space'] = {'error': str(e)}
    
    # Overall compatibility
    requirements['overall_compatible'] = all([
        requirements['python_version']['compatible'],
        requirements['operating_system']['compatible'],
        requirements['architecture']['compatible']
    ])
    
    return requirements
