"""Error handling utilities (small independent module)."""

from __future__ import annotations

from typing import Any, Dict

from .errors import GMLEError, InfraError


def create_structured_error(
    message: str,
    *,
    code: str = "UNKNOWN_ERROR",
    user_message: str | None = None,
    details: Dict[str, Any] | None = None,
    retryable: bool = False,
) -> InfraError:
    """Create structured error with user-friendly message.
    
    Args:
        message: Technical error message
        code: Error code
        user_message: User-friendly message (defaults to message)
        details: Additional error details
        retryable: Whether the error is retryable
    
    Returns:
        InfraError instance
    """
    return InfraError(
        message,
        code=code,
        user_message=user_message or message,
        details=details or {},
        retryable=retryable,
    )


def to_error_dict(error: Exception) -> Dict[str, Any]:
    """Convert exception to error dictionary.
    
    Args:
        error: Exception instance
    
    Returns:
        Dictionary with error information
    """
    if isinstance(error, GMLEError):
        return error.to_dict()
    
    return {
        "error": str(error),
        "code": type(error).__name__,
        "details": {},
        "retryable": False,
    }

