"""Cohere API client."""

from __future__ import annotations

import os
from typing import Any, Dict

from dotenv import load_dotenv

from gmle.app.config.getter import get_api_config
from gmle.app.http.base import request
from gmle.app.infra.errors import InfraError

# Load .env file
load_dotenv()


def _check_api_key_status_impl(config: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Internal implementation of API key check (without rate limiting)."""
    api_config = get_api_config(config)
    cohere_config = api_config["cohere"]
    api_url = cohere_config["api_url"]
    
    api_key = os.getenv("COHERE_API_KEY")
    if not api_key:
        return {
            "valid": False,
            "error": "COHERE_API_KEY not set",
            "key_type": None,
            "has_quota": False,
        }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    # Make a minimal test request
    import httpx
    client = httpx.Client(timeout=10.0)
    try:
        resp = client.post(
            api_url,
            headers=headers,
            json={"model": "command-a-03-2025", "message": "test"},
        )
        
        if resp.status_code == 200:
            return {
                "valid": True,
                "error": None,
                "key_type": "production",  # Production keys work
                "has_quota": True,
            }
        elif resp.status_code == 429:
            # Check if it's monthly limit
            error_text = resp.text.lower()
            if "month" in error_text or "1000" in error_text or "trial" in error_text:
                return {
                    "valid": True,
                    "error": "Monthly limit reached",
                    "key_type": "trial",
                    "has_quota": False,
                    "error_detail": resp.text[:200],
                }
            else:
                # Short-term rate limit
                return {
                    "valid": True,
                    "error": "Rate limit (short-term)",
                    "key_type": "unknown",
                    "has_quota": True,
                    "error_detail": resp.text[:200],
                }
        elif resp.status_code in (401, 403):
            return {
                "valid": False,
                "error": f"Authentication failed: {resp.status_code}",
                "key_type": None,
                "has_quota": False,
            }
        else:
            return {
                "valid": False,
                "error": f"Unexpected status: {resp.status_code}",
                "key_type": None,
                "has_quota": False,
                "error_detail": resp.text[:200],
            }
    except Exception as e:
        return {
            "valid": False,
            "error": f"Failed to check API key: {str(e)}",
            "key_type": None,
            "has_quota": False,
        }
    finally:
        client.close()


def check_api_key_status(config: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Check Cohere API key status through unified gate."""
    from gmle.app.http.api_gate import get_unified_api_gate
    from gmle.app.config.getter import get_llm_config
    
    llm_config = get_llm_config(config)
    provider = llm_config.get("active_provider", "cohere")
    
    # Check if we can make the call (but don't block if we can't)
    gate = get_unified_api_gate()
    try:
        result: Any = gate.call(
            call_type="api_key_check",
            provider=provider,
            func=_check_api_key_status_impl,
            config=config,
        )
        return result  # type: ignore[no-any-return]
    except InfraError as e:
        # If blocked by rate limit, return error status
        if "blocked" in str(e).lower() or "limit" in str(e).lower():
            return {
                "valid": True,
                "error": f"Rate limit check blocked: {str(e)}",
                "key_type": "trial",
                "has_quota": False,
            }
        # Otherwise, try without gate (fallback)
        return _check_api_key_status_impl(config)


def _chat_completions_impl(payload: Dict[str, Any], config: Dict[str, Any] | None = None) -> Any:
    """Internal implementation of Cohere API call (without rate limiting)."""
    api_config = get_api_config(config)
    cohere_config = api_config["cohere"]
    api_url = cohere_config["api_url"]
    default_model = cohere_config["model"]
    
    api_key = os.getenv("COHERE_API_KEY")
    if not api_key:
        raise InfraError("COHERE_API_KEY not set")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    # Cohere v1 API format: extract message from messages array
    messages = payload.get("messages", [])
    if not messages:
        raise InfraError("messages array is required")
    
    # Get the last user message content
    message_content = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            message_content = msg.get("content", "")
            break
    
    if not message_content:
        raise InfraError("No user message found in messages array")
    
    # Extract model from payload or use config default
    model = payload.get("model", default_model)
    
    # Cohere v1 API payload format
    cohere_payload = {
        "model": model,
        "message": message_content,
    }
    response = request("POST", api_url, headers=headers, json=cohere_payload)
    
    # Cohere v1 API response format: response.text contains the message content
    from gmle.app.http.json_parser import parse_llm_response
    return parse_llm_response(response)


def chat_completions(payload: Dict[str, Any], config: Dict[str, Any] | None = None) -> Any:
    """Call Cohere v1 chat completions through unified gate."""
    from gmle.app.http.api_gate import get_unified_api_gate
    from gmle.app.config.getter import get_llm_config
    
    llm_config = get_llm_config(config)
    provider = llm_config.get("active_provider", "cohere")
    
    gate = get_unified_api_gate()
    return gate.call(
        call_type="mcq_generation",
        provider=provider,
        func=_chat_completions_impl,
        payload=payload,
        config=config,
    )

