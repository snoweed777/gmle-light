"""REST API error handling."""

from __future__ import annotations

from typing import NoReturn

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

from gmle.app.infra.errors import (
    AnkiError,
    ConfigError,
    InfraError,
    SOTError,
)


async def api_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle API exceptions."""
    if isinstance(exc, ConfigError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "Configuration error",
                "detail": str(exc),
                "code": "CONFIG_ERROR",
            },
        )

    if isinstance(exc, InfraError):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Infrastructure error",
                "detail": str(exc),
                "code": "INFRA_ERROR",
            },
        )

    if isinstance(exc, AnkiError):
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": "Anki service error",
                "detail": str(exc),
                "code": "ANKI_ERROR",
            },
        )

    if isinstance(exc, SOTError):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Source of truth error",
                "detail": str(exc),
                "code": "SOT_ERROR",
            },
        )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "code": "INTERNAL_ERROR",
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

