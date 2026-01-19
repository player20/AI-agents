"""
Admin authentication for self-improvement features.
Lean implementation: simple token-based auth via ADMIN_API_KEY.
"""

import os
import secrets
from functools import wraps
from typing import Callable, TypeVar, ParamSpec

P = ParamSpec('P')
T = TypeVar('T')


def is_admin(token: str = None) -> bool:
    """
    Check if the provided token matches ADMIN_API_KEY.

    Args:
        token: The admin token to validate

    Returns:
        True if token matches ADMIN_API_KEY, False otherwise
    """
    admin_key = os.getenv("ADMIN_API_KEY")
    if not admin_key:
        return False
    if token is None:
        return False
    # Use constant-time comparison to prevent timing attacks
    return secrets.compare_digest(token, admin_key)


def require_admin(func: Callable[P, T]) -> Callable[P, T]:
    """
    Decorator to gate functions behind admin authentication.

    The decorated function must accept an `admin_token` keyword argument.
    Raises PermissionError if the token is invalid or missing.

    Usage:
        @require_admin
        def sensitive_operation(data, admin_token=None):
            # Only runs if admin_token is valid
            pass
    """
    @wraps(func)
    def wrapper(*args, admin_token: str = None, **kwargs):
        if not is_admin(admin_token):
            raise PermissionError(
                "Admin access required for self-improvement. "
                "Provide a valid admin_token parameter."
            )
        return func(*args, admin_token=admin_token, **kwargs)
    return wrapper


def generate_admin_key() -> str:
    """
    Generate a secure 32-character admin key.
    Use this to create a new ADMIN_API_KEY for .env file.

    Returns:
        A cryptographically secure random key
    """
    return secrets.token_urlsafe(32)
