"""
Shared 2FA code fetching functionality.

This module provides a single fetch_2fa_code() function used by:
1. The MCP tool (for agent's interactive work)
2. The test_login_script runner (injected into script namespace)

Both use the same HTTP endpoint, keeping the implementation DRY.
"""

import os
import httpx


class TwoFAError(Exception):
    """Raised when 2FA code fetch fails."""
    pass


class TwoFATimeoutError(TwoFAError):
    """Raised when 2FA code fetch times out."""
    pass


class TwoFANotConfiguredError(TwoFAError):
    """Raised when account has no 2FA configured."""
    pass


def fetch_2fa_code(timeout_seconds: int = 60) -> str:
    """
    Fetch a 2FA code for the current session's account.

    This function calls the backend API to retrieve a 2FA code based on
    the account's configured method (SMS, email, or TOTP).

    For TOTP: Returns immediately (calculated locally by backend)
    For SMS: Polls Twilio until code arrives or timeout
    For Email: Polls Mailgun until code arrives or timeout

    Args:
        timeout_seconds: Max seconds to wait for SMS/email codes (default 60)

    Returns:
        The 2FA code as a string (e.g., "123456")

    Raises:
        TwoFAError: If SESSION_ID or BACKEND_URL not configured
        TwoFANotConfiguredError: If account has no 2FA set up
        TwoFATimeoutError: If code not received in time
    """
    session_id = os.environ.get("SESSION_ID")
    account_id = os.environ.get("ACCOUNT_ID")
    backend_url = (os.environ.get("BACKEND_URL") or "").strip().rstrip("/")
    agent_secret = os.environ.get("AGENT_CALLBACK_SECRET")

    if not session_id:
        raise TwoFAError("No SESSION_ID configured. Cannot determine which account to fetch 2FA for.")

    if not backend_url:
        raise TwoFAError("No BACKEND_URL configured. Cannot contact 2FA service.")

    if not agent_secret:
        raise TwoFAError("No AGENT_CALLBACK_SECRET configured. Cannot authenticate with backend.")

    # Call backend - it resolves session_id -> account_id internally
    try:
        with httpx.Client(timeout=float(timeout_seconds + 10)) as client:
            response = client.post(
                f"{backend_url}/auth/twofa/fetch-code",
                json={"session_id": session_id, "account_id": account_id, "timeout_seconds": timeout_seconds},
                headers={"X-Agent-Secret": agent_secret}
            )
    except httpx.TimeoutException:
        raise TwoFATimeoutError(
            f"2FA fetch timed out after {timeout_seconds}s. "
            "For SMS/email: The verification code may not have arrived yet."
        )
    except httpx.RequestError as e:
        raise TwoFAError(f"Network error fetching 2FA code: {e}")

    if response.status_code == 404:
        raise TwoFANotConfiguredError(
            "Session not found or account has no 2FA configured."
        )

    if response.status_code != 200:
        try:
            detail = response.json().get("detail", response.text[:200])
        except Exception:
            detail = response.text[:200]
        raise TwoFAError(f"2FA fetch failed: {detail}")

    # Success
    data = response.json()
    code = data.get("code")

    if not code:
        raise TwoFAError("2FA response missing 'code' field")

    return code
