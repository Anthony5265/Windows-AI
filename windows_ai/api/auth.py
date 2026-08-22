"""Authentication and authorization for the Windows AI API."""

import os
import secrets
from typing import Optional

from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer


api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)


def get_api_key() -> str:
    """Return the configured API key without generating or logging credentials."""
    return os.getenv("WINDOWS_AI_API_KEY", "")


def _require_configured_key() -> str:
    key = get_api_key()
    if not key:
        raise HTTPException(
            status_code=503,
            detail="API authentication is not configured",
        )
    return key


async def verify_api_key(
    api_key: Optional[str] = Security(api_key_header),
) -> bool:
    """Verify an X-API-Key credential."""
    expected_key = _require_configured_key()
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")
    if not secrets.compare_digest(api_key, expected_key):
        raise HTTPException(status_code=403, detail="Invalid API key")
    return True


async def verify_bearer_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> bool:
    """Verify a bearer token using the configured API credential."""
    expected_key = _require_configured_key()
    if not credentials:
        raise HTTPException(status_code=401, detail="Bearer token required")
    if not secrets.compare_digest(credentials.credentials, expected_key):
        raise HTTPException(status_code=403, detail="Invalid bearer token")
    return True


async def get_current_user(
    api_key_valid: bool = Depends(verify_api_key),
) -> dict:
    """Return the minimal authenticated-user representation."""
    return {"authenticated": api_key_valid}
