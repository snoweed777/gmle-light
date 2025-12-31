"""HTTP base client with retry."""

from __future__ import annotations

import time
from typing import Any, Dict

import httpx

from gmle.app.config.getter import get_http_config
from gmle.app.infra.errors import InfraError
from gmle.app.infra.logger import get_logger


def _is_monthly_limit_error(status_code: int, error_text: str) -> bool:
    """Check if error indicates monthly/quota limit (non-retryable)."""
    if status_code != 429:
        return False
    error_lower = error_text.lower()
    return any(
        keyword in error_lower
        for keyword in ["month", "1000", "trial", "monthly", "quota exceeded"]
    )


def _calculate_retry_wait(attempt: int, retry_backoff_base: float, retry_after: str | None = None) -> float:
    """Calculate wait time before retry.
    
    Args:
        attempt: Current attempt number (0-indexed)
        retry_backoff_base: Base for exponential backoff
        retry_after: Optional Retry-After header value
        
    Returns:
        Wait time in seconds
    """
    if retry_after:
        try:
            return float(retry_after)
        except ValueError:
            pass
    
    # Exponential backoff: base^attempt seconds
    return retry_backoff_base ** attempt


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
    """Perform HTTP request with exponential backoff retry.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        url: Request URL
        headers: Optional request headers
        json: Optional JSON payload
        timeout: Request timeout in seconds
        max_retries: Maximum number of retries
        config: Optional config dict
        
    Returns:
        Response JSON (if content-type is application/json) or text
        
    Raises:
        InfraError: For non-retryable errors or after max retries
    """
    http_config = get_http_config(config)
    timeout = timeout or http_config["timeout"]
    max_retries = max_retries if max_retries is not None else http_config["max_retries"]
    retry_backoff_base = http_config["retry_backoff_base"]
    
    logger = get_logger()
    
    client = httpx.Client(timeout=timeout)
    last_exception: Exception | None = None
    
    try:
        for attempt in range(max_retries + 1):
            try:
                resp = client.request(method, url, headers=headers, json=json)
                
                # Non-retryable errors (auth failures)
                if resp.status_code in (401, 403):
                    raise InfraError(
                        f"Authentication failed: {resp.status_code}",
                        code="AUTH_ERROR",
                        user_message=f"認証エラーが発生しました: {resp.status_code}",
                        retryable=False,
                    )
                
                # Rate limit handling
                if resp.status_code == 429:
                    error_text = resp.text[:500] if resp.text else ""
                    
                    # Check for monthly/quota limit (non-retryable)
                    if _is_monthly_limit_error(resp.status_code, error_text):
                        raise InfraError(
                            f"Monthly API limit reached (429): {error_text}",
                            code="MONTHLY_LIMIT",
                            user_message="月次API制限に達しました",
                            retryable=False,
                        )
                    
                    # Short-term rate limit (retryable)
                    if attempt < max_retries:
                        retry_after = resp.headers.get("Retry-After")
                        wait = _calculate_retry_wait(attempt, retry_backoff_base, retry_after)
                        
                        logger.warning(
                            f"Rate limit (429) - retrying in {wait:.1f}s",
                            extra={
                                "extra_fields": {
                                    "url": url,
                                    "attempt": attempt + 1,
                                    "max_retries": max_retries,
                                    "retry_after": retry_after,
                                }
                            },
                        )
                        time.sleep(wait)
                        continue
                    
                    # Max retries reached
                    raise InfraError(
                        f"Rate limit exceeded after {max_retries} retries: {error_text}",
                        code="RATE_LIMIT",
                        user_message="レート制限に達しました。しばらく待ってから再試行してください。",
                        retryable=True,
                    )
                
                # Server errors (retryable)
                if resp.status_code >= 500:
                    if attempt < max_retries:
                        wait = _calculate_retry_wait(attempt, retry_backoff_base)
                        logger.warning(
                            f"Server error {resp.status_code} - retrying in {wait:.1f}s",
                            extra={
                                "extra_fields": {
                                    "url": url,
                                    "status_code": resp.status_code,
                                    "attempt": attempt + 1,
                                    "max_retries": max_retries,
                                }
                            },
                        )
                        time.sleep(wait)
                        continue
                    
                    raise InfraError(
                        f"Server error after {max_retries} retries: {resp.status_code}",
                        code="SERVER_ERROR",
                        user_message=f"サーバーエラーが発生しました: {resp.status_code}",
                        retryable=True,
                    )
                
                # Success - check for HTTP errors and parse response
                resp.raise_for_status()
                
                content_type = resp.headers.get("content-type", "")
                if content_type.startswith("application/json"):
                    return resp.json()
                return resp.text
                
            except httpx.RequestError as exc:
                last_exception = exc
                if attempt < max_retries:
                    wait = _calculate_retry_wait(attempt, retry_backoff_base)
                    logger.warning(
                        f"Request error - retrying in {wait:.1f}s",
                        extra={
                            "extra_fields": {
                                "url": url,
                                "error": str(exc),
                                "attempt": attempt + 1,
                                "max_retries": max_retries,
                            }
                        },
                    )
                    time.sleep(wait)
                    continue
                
                # Max retries reached
                raise InfraError(
                    f"Request failed after {max_retries} retries: {url}",
                    code="REQUEST_ERROR",
                    user_message="リクエストが失敗しました。ネットワーク接続を確認してください。",
                    retryable=True,
                ) from exc
                
    finally:
        client.close()
    
    # Should never reach here, but type checker needs it
    if last_exception:
        raise InfraError(f"Unexpected error: {url}") from last_exception
    raise InfraError(f"Request failed: {url}")
