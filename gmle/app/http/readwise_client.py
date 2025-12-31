"""Readwise API client."""

from __future__ import annotations

import os
from typing import Any, Dict

from gmle.app.http.base import request
from gmle.app.infra.errors import InfraError


READWISE_API_URL = "https://readwise.io/api/v2/highlights/"


def fetch_highlights(params: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Fetch highlights from Readwise."""
    token = os.getenv("READWISE_TOKEN")
    if not token:
        raise InfraError("READWISE_TOKEN not set")
    headers = {"Authorization": f"Token {token}"}
    params = params or {}
    try:
        result = request("GET", READWISE_API_URL, headers=headers, json=params)
        if isinstance(result, dict):
            return result
        return {}
    except Exception as exc:
        raise InfraError(f"Readwise API failed: {exc}") from exc
