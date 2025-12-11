"""
Credentials API Routes

Provides REST endpoints for managing API keys and credentials
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/credentials", tags=["credentials"])


class CredentialRequest(BaseModel):
    """Request to store a credential"""
    provider: str = Field(..., description="Provider name (openai, anthropic, google, azure)")
    api_key: str = Field(..., description="API key value")


class CredentialStatusResponse(BaseModel):
    """Response with credential configuration status"""
    openai: bool = False
    anthropic: bool = False
    google: bool = False
    azure: bool = False


class AzureEndpointRequest(BaseModel):
    """Request to set Azure endpoint"""
    endpoint: str


class TestResult(BaseModel):
    """Result of testing a credential"""
    valid: bool
    error: Optional[str] = None


def get_credential_manager():
    """Get credential manager instance"""
    from windows_ai.core.credential_manager import CredentialManager
    return CredentialManager()


@router.post("")
async def store_credential(request: CredentialRequest, fastapi_req: Request):
    """
    Store an API credential
    
    Securely stores an API key for a provider
    """
    try:
        credential_manager = get_credential_manager()
        
        # Map provider names to storage keys
        key_mapping = {
            'openai': 'openai_api_key',
            'anthropic': 'anthropic_api_key',
            'google': 'google_api_key',
            'azure': 'azure_api_key'
        }
        
        storage_key = key_mapping.get(request.provider.lower())
        if not storage_key:
            raise HTTPException(status_code=400, detail=f"Unknown provider: {request.provider}")
        
        # Store the credential
        await credential_manager.store_credential(
            service_id=request.provider.lower(),
            key_name=storage_key,
            key_value=request.api_key
        )
        
        # Update environment variable immediately so it's available without restart
        env_var_mapping = {
            'openai_api_key': 'OPENAI_API_KEY',
            'anthropic_api_key': 'ANTHROPIC_API_KEY',
            'google_api_key': 'GOOGLE_API_KEY',
            'azure_api_key': 'AZURE_OPENAI_API_KEY'
        }
        
        if storage_key in env_var_mapping:
            import os
            os.environ[env_var_mapping[storage_key]] = request.api_key
            logger.info(f"Updated environment variable {env_var_mapping[storage_key]}")
            
            # Reset LLM client if available to force recreation with new key
            try:
                if hasattr(fastapi_req.app.state, "components") and "llm" in fastapi_req.app.state.components:
                    llm = fastapi_req.app.state.components["llm"]
                    llm.reset_client(request.provider.lower())
                    logger.info(f"Reset LLM client for {request.provider}")
            except Exception as e:
                logger.warning(f"Could not reset LLM client: {e}")
        
        logger.info(f"Stored credential for {request.provider}")
        return {"status": "success", "provider": request.provider}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to store credential: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=CredentialStatusResponse)
async def get_credential_status():
    """
    Get configuration status for all providers
    
    Returns which providers have API keys configured
    """
    try:
        credential_manager = get_credential_manager()
        
        status = CredentialStatusResponse()
        
        # Check each provider
        providers = ['openai', 'anthropic', 'google', 'azure']
        
        for provider in providers:
            key = await credential_manager.get_credential(provider, f"{provider}_api_key")
            setattr(status, provider, key is not None and len(key) > 0)
        
        return status
        
    except Exception as e:
        logger.error(f"Failed to get credential status: {e}")
        # Return empty status on error
        return CredentialStatusResponse()


@router.delete("/{provider}")
async def delete_credential(provider: str):
    """
    Delete a stored credential
    
    Args:
        provider: Provider name (openai, anthropic, google, azure)
    """
    try:
        credential_manager = get_credential_manager()
        
        key_mapping = {
            'openai': 'openai_api_key',
            'anthropic': 'anthropic_api_key',
            'google': 'google_api_key',
            'azure': 'azure_api_key'
        }
        
        storage_key = key_mapping.get(provider.lower())
        if not storage_key:
            raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")
        
        await credential_manager.delete_credential(provider.lower(), storage_key)
        
        return {"status": "deleted", "provider": provider}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete credential: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/azure/endpoint")
async def set_azure_endpoint(request: AzureEndpointRequest):
    """
    Set Azure OpenAI endpoint URL
    """
    try:
        credential_manager = get_credential_manager()
        
        await credential_manager.store_credential(
            service='azure',
            key='azure_endpoint',
            value=request.endpoint
        )
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Failed to set Azure endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test")
async def test_credentials() -> Dict[str, TestResult]:
    """
    Test all configured API credentials
    
    Returns validation status for each configured provider
    """
    results = {}
    credential_manager = get_credential_manager()
    
    # Test OpenAI
    try:
        openai_key = await credential_manager.get_credential('openai', 'openai_api_key')
        if openai_key:
            valid = await _test_openai(openai_key)
            results['openai'] = TestResult(valid=valid)
        else:
            results['openai'] = TestResult(valid=False, error="Not configured")
    except Exception as e:
        results['openai'] = TestResult(valid=False, error=str(e))
    
    # Test Anthropic
    try:
        anthropic_key = await credential_manager.get_credential('anthropic', 'anthropic_api_key')
        if anthropic_key:
            valid = await _test_anthropic(anthropic_key)
            results['anthropic'] = TestResult(valid=valid)
        else:
            results['anthropic'] = TestResult(valid=False, error="Not configured")
    except Exception as e:
        results['anthropic'] = TestResult(valid=False, error=str(e))
    
    # Test Google
    try:
        google_key = await credential_manager.get_credential('google', 'google_api_key')
        if google_key:
            valid = await _test_google(google_key)
            results['google'] = TestResult(valid=valid)
        else:
            results['google'] = TestResult(valid=False, error="Not configured")
    except Exception as e:
        results['google'] = TestResult(valid=False, error=str(e))
    
    # Test Azure
    try:
        azure_key = await credential_manager.get_credential('azure', 'azure_api_key')
        azure_endpoint = await credential_manager.get_credential('azure', 'azure_endpoint')
        if azure_key and azure_endpoint:
            valid = await _test_azure(azure_key, azure_endpoint)
            results['azure'] = TestResult(valid=valid)
        else:
            results['azure'] = TestResult(valid=False, error="Not configured")
    except Exception as e:
        results['azure'] = TestResult(valid=False, error=str(e))
    
    return results


async def _test_openai(api_key: str) -> bool:
    """Test OpenAI API key"""
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10.0
            )
            return response.status_code == 200
    except Exception:
        return False


async def _test_anthropic(api_key: str) -> bool:
    """Test Anthropic API key"""
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            # Anthropic uses x-api-key header
            response = await client.get(
                "https://api.anthropic.com/v1/models",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01"
                },
                timeout=10.0
            )
            # Anthropic may return 200 or 401
            return response.status_code in [200, 404]  # 404 means key valid but endpoint doesn't exist
    except Exception:
        return False


async def _test_google(api_key: str) -> bool:
    """Test Google AI API key"""
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://generativelanguage.googleapis.com/v1/models?key={api_key}",
                timeout=10.0
            )
            return response.status_code == 200
    except Exception:
        return False


async def _test_azure(api_key: str, endpoint: str) -> bool:
    """Test Azure OpenAI API key"""
    try:
        import httpx
        # Normalize endpoint
        if not endpoint.endswith('/'):
            endpoint += '/'
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{endpoint}openai/deployments?api-version=2024-02-01",
                headers={"api-key": api_key},
                timeout=10.0
            )
            return response.status_code == 200
    except Exception:
        return False
