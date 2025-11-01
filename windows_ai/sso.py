"""Single Sign-On utilities using MSAL for Microsoft Entra ID."""

from __future__ import annotations

from typing import List, Optional

try:  # pragma: no cover - optional dependency
    import msal  # type: ignore
except Exception:  # pragma: no cover - environment specific
    msal = None  # type: ignore[assignment]

__all__ = ["SSOClient"]


class SSOClient:
    """Lightweight wrapper around ``msal`` for authentication flows."""

    def __init__(
        self, client_id: str, tenant_id: str, authority: Optional[str] = None
    ) -> None:
        if msal is None:
            raise RuntimeError("msal library is required for SSO support")
        base = "https://login.microsoftonline.com/"
        authority = authority or f"{base}{tenant_id}"
        self.app = msal.PublicClientApplication(client_id, authority=authority)

    def device_code_flow(self, scope: List[str]) -> dict:
        """Authenticate using the device code flow."""

        flow = self.app.initiate_device_flow(scopes=scope)
        if "user_code" not in flow:
            raise RuntimeError("Failed to create device flow")
        return self.app.acquire_token_by_device_flow(flow)

    def interactive_login(self, scope: List[str]) -> dict:
        """Authenticate using an interactive browser flow."""

        return self.app.acquire_token_interactive(scopes=scope)
