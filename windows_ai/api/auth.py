"""
Authentication and authorization for API

NOTE: Authentication is OPTIONAL and OFF by default.
      If WINDOWS_AI_API_KEY is not set, ALL requests are allowed.
      This provides maximum freedom - users can enable auth if desired.
"""

from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import os
import secrets

# API Key authentication
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Bearer token authentication
bearer_scheme = HTTPBearer(auto_error=False)

def get_api_key() -> str:
    """Get API key from environment or generate one"""
    api_key = os.getenv("WINDOWS_AI_API_KEY")
    if not api_key:
        # Generate a secure random API key
        api_key = secrets.token_urlsafe(32)
        print(f"Generated API key: {api_key}")
        print("Set WINDOWS_AI_API_KEY environment variable to persist this key")
    return api_key

async def verify_api_key(api_key: Optional[str] = Security(api_key_header)) -> bool:
    """Verify API key for requests"""
    # If no API key is configured, allow all requests (development mode)
    expected_key = os.getenv("WINDOWS_AI_API_KEY")
    if not expected_key:
        return True

    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")

    if api_key != expected_key:
        raise HTTPException(status_code=403, detail="Invalid API key")

    return True

async def verify_bearer_token(credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme)) -> bool:
    """Verify bearer token for requests"""
    # If no API key is configured, allow all requests (development mode)
    expected_key = os.getenv("WINDOWS_AI_API_KEY")
    if not expected_key:
        return True

    if not credentials:
        raise HTTPException(status_code=401, detail="Bearer token required")

    if credentials.credentials != expected_key:
        raise HTTPException(status_code=403, detail="Invalid bearer token")

    return True

async def get_current_user(
    api_key_valid: bool = Depends(verify_api_key),
) -> dict:
    """Get current authenticated user"""
    return {"authenticated": api_key_valid}
