"""REST API error handling."""

from __future__ import annotations

from typing import NoReturn

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

from gmle.app.infra.error_utils import to_error_dict
from gmle.app.infra.errors import (
    AnkiError,
    ConfigError,
    DegradeTrigger,
    GMLEError,
    InfraError,
    SOTError,
)


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
    # Handle structured GMLEError
    if isinstance(exc, GMLEError):
        status_code = _get_status_code_for_error(exc)
        return JSONResponse(
            status_code=status_code,
            content=exc.to_dict(),
        )
    
    # Fallback for non-structured exceptions
    if isinstance(exc, ConfigError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "設定エラーが発生しました",
                "code": "CONFIG_ERROR",
                "details": {"message": str(exc)},
                "retryable": False,
            },
        )

    if isinstance(exc, InfraError):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "インフラエラーが発生しました",
                "code": "INFRA_ERROR",
                "details": {"message": str(exc)},
                "retryable": True,
            },
        )

    if isinstance(exc, AnkiError):
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": "Ankiサービスエラーが発生しました",
                "code": "ANKI_ERROR",
                "details": {"message": str(exc)},
                "retryable": True,
            },
        )

    if isinstance(exc, SOTError):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "データエラーが発生しました",
                "code": "SOT_ERROR",
                "details": {"message": str(exc)},
                "retryable": False,
            },
        )

    if isinstance(exc, DegradeTrigger):
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": "Degradeモードがトリガーされました",
                "code": "DEGRADE_TRIGGER",
                "details": {"message": str(exc)},
                "retryable": False,
            },
        )

    # Unknown error
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

