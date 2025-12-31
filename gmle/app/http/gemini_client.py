"""Google AI Studio (Gemini) API client."""

from __future__ import annotations

import os
from typing import Any, Dict

from dotenv import load_dotenv

from gmle.app.config.getter import get_llm_config
from gmle.app.http.base import request
from gmle.app.infra.errors import InfraError

# Load .env file
load_dotenv()


def _check_api_key_status_impl(config: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Internal implementation of API key check (without rate limiting)."""
    llm_config = get_llm_config(config)
    provider_config = llm_config.get("provider_config", {})
    api_url_base = provider_config.get("api_url") or "https://generativelanguage.googleapis.com/v1beta"
    default_model = provider_config.get("default_model") or "gemini-1.5-flash"
    
    api_key = os.getenv("GOOGLE_AI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {
            "valid": False,
            "error": "GOOGLE_AI_API_KEY or GEMINI_API_KEY not set",
            "key_type": None,
            "has_quota": False,
        }
    
    # Make a minimal test request
    import httpx
    client = httpx.Client(timeout=10.0)
    try:
        api_url = f"{api_url_base}/models/{default_model}:generateContent?key={api_key}"
        resp = client.post(
            api_url,
            json={"contents": [{"parts": [{"text": "test"}]}]},
        )
        
        if resp.status_code == 200:
            return {
                "valid": True,
                "error": None,
                "key_type": "free",  # Google AI Studio free tier
                "has_quota": True,
            }
        elif resp.status_code == 429:
            # Rate limit - check if daily limit
            error_text = resp.text.lower()
            if "quota" in error_text or "limit" in error_text:
                return {
                    "valid": True,
                    "error": "Daily quota limit reached",
                    "key_type": "free",
                    "has_quota": False,
                    "error_detail": resp.text[:200],
                }
            else:
                return {
                    "valid": True,
                    "error": "Rate limit (short-term)",
                    "key_type": "free",
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
    """Check Gemini API key status through unified gate."""
    from gmle.app.http.api_gate import get_unified_api_gate
    from gmle.app.config.getter import get_llm_config
    
    llm_config = get_llm_config(config)
    provider = llm_config.get("active_provider", "gemini")
    
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
                "key_type": "free",
                "has_quota": False,
            }
        # Otherwise, try without gate (fallback)
        return _check_api_key_status_impl(config)


def _chat_completions_impl(payload: Dict[str, Any], config: Dict[str, Any] | None = None) -> Any:
    """Internal implementation of Gemini API call (without rate limiting)."""
    llm_config = get_llm_config(config)
    provider_config = llm_config.get("provider_config", {})
    api_url_base = provider_config.get("api_url") or "https://generativelanguage.googleapis.com/v1beta"
    default_model = provider_config.get("default_model") or "gemini-1.5-flash"
    
    api_key = os.getenv("GOOGLE_AI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise InfraError("GOOGLE_AI_API_KEY or GEMINI_API_KEY not set")
    
    # Extract message from payload
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
    
    # Gemini API format
    api_url = f"{api_url_base}/models/{model}:generateContent?key={api_key}"
    gemini_payload = {
        "contents": [{
            "parts": [{"text": message_content}]
        }]
    }
    
    response = request("POST", api_url, json=gemini_payload, config=config)
    
    # Gemini API response format
    from gmle.app.http.json_parser import parse_llm_response
    return parse_llm_response(response)


def chat_completions(payload: Dict[str, Any], config: Dict[str, Any] | None = None) -> Any:
    """Call Gemini API generateContent through unified gate."""
    from gmle.app.http.api_gate import get_unified_api_gate
    from gmle.app.config.getter import get_llm_config
    
    llm_config = get_llm_config(config)
    provider = llm_config.get("active_provider", "gemini")
    
    gate = get_unified_api_gate()
    return gate.call(
        call_type="mcq_generation",
        provider=provider,
        func=_chat_completions_impl,
        payload=payload,
        config=config,
    )

