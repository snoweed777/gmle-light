"""HTTP base client with retry."""

from __future__ import annotations

import time
from typing import Any, Dict

import httpx

from gmle.app.config.getter import get_http_config
from gmle.app.infra.errors import InfraError


def request(
    method: str,
    url: str,
    *,
    headers: Dict[str, str] | None = None,
    json: Any | None = None,
    timeout: float | None = None,
    max_retries: int | None = None,
    config: Dict[str, Any] | None = None,
) -> Any:
    """Perform HTTP request with exponential backoff retry."""
    http_config = get_http_config(config)
    timeout = timeout or http_config["timeout"]
    max_retries = max_retries if max_retries is not None else http_config["max_retries"]
    retry_backoff_base = http_config["retry_backoff_base"]
    
    client = httpx.Client(timeout=timeout)
    try:
        for attempt in range(max_retries + 1):
            try:
                resp = client.request(method, url, headers=headers, json=json)
                if resp.status_code in (401, 403):
                    raise InfraError(f"auth error: {resp.status_code} {resp.text}")
                if resp.status_code == 429:
                    # Check if it's a monthly limit (don't retry)
                    error_text = resp.text.lower()
                    is_monthly_limit = (
                        "month" in error_text
                        or "1000" in error_text
                        or "trial" in error_text
                        or "monthly" in error_text
                    )
                    
                    if is_monthly_limit:
                        # Monthly limit reached - fail immediately, no retry
                        raise InfraError(
                            f"Monthly API limit reached (429): {resp.text[:500]}"
                        )
                    
                    # Short-term rate limit - retry with backoff
                    if attempt < max_retries:
                        # Check for Retry-After header
                        retry_after = resp.headers.get("Retry-After")
                        if retry_after:
                            try:
                                wait = int(retry_after)
                            except ValueError:
                                wait = retry_backoff_base ** attempt * 60  # Default to minutes
                        else:
                            # Exponential backoff with longer wait for rate limits
                            wait = retry_backoff_base ** attempt * 60  # Wait in seconds
                        time.sleep(wait)
                        continue
                    raise InfraError(f"rate limit error after retries: {resp.status_code} {resp.text}")
                if resp.status_code >= 500:
                    if attempt < max_retries:
                        wait = retry_backoff_base ** attempt
                        time.sleep(wait)
                        continue
                    raise InfraError(f"server error after retries: {resp.status_code}")
                resp.raise_for_status()
                return resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text
            except httpx.RequestError as exc:
                if attempt < max_retries:
                    wait = retry_backoff_base ** attempt
                    time.sleep(wait)
                    continue
                raise InfraError(f"request failed after retries: {url}") from exc
    finally:
        client.close()
