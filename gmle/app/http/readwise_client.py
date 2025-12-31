"""Readwise API client."""

from __future__ import annotations

import os
from typing import Any, Dict

from gmle.app.http.base import request
from gmle.app.infra.error_utils import create_structured_error
from gmle.app.infra.errors import InfraError


READWISE_API_URL = "https://readwise.io/api/v2/highlights/"


def fetch_highlights(params: Dict[str, Any] | None = None, config: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Fetch highlights from Readwise with improved error handling.
    
    Args:
        params: Query parameters
        config: Optional config dict (for API URL override)
    
    Returns:
        Dict with highlights data
    
    Raises:
        InfraError: If API call fails
    """
    token = os.getenv("READWISE_TOKEN")
    if not token:
        raise create_structured_error(
            "READWISE_TOKEN environment variable is not set",
            code="READWISE_TOKEN_MISSING",
            user_message="Readwise APIトークンが設定されていません。.envファイルを確認してください。",
        )
    
    # Get API URL from config or use default
    api_url = (config or {}).get("api", {}).get("readwise", {}).get("api_url", READWISE_API_URL)
    headers = {"Authorization": f"Token {token}"}
    params = params or {}
    
    try:
        result = request("GET", api_url, headers=headers, json=params, config=config)
        if isinstance(result, dict):
            return result
        return {}
    except InfraError:
        # Re-raise InfraError as-is (already structured)
        raise
    except Exception as exc:
        error_type = type(exc).__name__
        raise create_structured_error(
            f"Readwise API request failed ({error_type}): {exc}",
            code="READWISE_API_ERROR",
            user_message="Readwise APIへのリクエストに失敗しました",
            details={"error_type": error_type, "original_error": str(exc)},
            retryable=True,
        ) from exc
