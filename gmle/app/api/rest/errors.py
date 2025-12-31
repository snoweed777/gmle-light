"""REST API error handling."""

from __future__ import annotations

from typing import NoReturn

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

from gmle.app.infra.errors import GMLEError


def _get_status_code_for_error(error: GMLEError) -> int:
    """Get appropriate HTTP status code for error."""
    code = error.code.upper()
    
    if "RATE_LIMIT" in code or "PREDICTIVE_LIMIT" in code:
        return status.HTTP_429_TOO_MANY_REQUESTS
    elif "CONFIG" in code:
        return status.HTTP_400_BAD_REQUEST
    elif "ANKI" in code:
        return status.HTTP_503_SERVICE_UNAVAILABLE
    elif "DEGRADE" in code:
        return status.HTTP_503_SERVICE_UNAVAILABLE
    else:
        return status.HTTP_500_INTERNAL_SERVER_ERROR


async def api_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle API exceptions with structured error support."""
    # Handle structured GMLEError (all custom exceptions inherit from this)
    if isinstance(exc, GMLEError):
        status_code = _get_status_code_for_error(exc)
        return JSONResponse(
            status_code=status_code,
            content=exc.to_dict(),
        )
    
    # Handle FastAPI HTTPException
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "code": f"HTTP_{exc.status_code}",
                "details": {},
                "retryable": exc.status_code >= 500,
            },
        )

    # Unknown error - log and return generic response
    from gmle.app.infra.logger import get_logger, log_exception
    logger = get_logger()
    log_exception(
        logger,
        "Unhandled exception in API",
        exc,
        path=request.url.path,
        method=request.method,
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "予期しないエラーが発生しました",
            "code": "INTERNAL_ERROR",
            "details": {"message": str(exc)},
            "retryable": False,
        },
    )


def raise_not_found(resource: str, identifier: str) -> NoReturn:
    """Raise 404 Not Found exception."""
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{resource} '{identifier}' not found",
    )


def raise_bad_request(message: str) -> None:
    """Raise 400 Bad Request exception."""
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=message,
    )

