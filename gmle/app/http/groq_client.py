"""Groq API client (OpenAI-compatible)."""

from __future__ import annotations

import os
import time
from typing import Any, Dict, cast

from dotenv import load_dotenv

from gmle.app.config.getter import get_llm_config
from gmle.app.http.base import request
from gmle.app.infra.errors import InfraError

# Load .env file
load_dotenv()

# Cache for API key validation results
# Format: {api_key_hash: {"result": {...}, "timestamp": float}}
_api_key_check_cache: Dict[str, Dict[str, Any]] = {}
_API_KEY_CHECK_CACHE_TTL = 300  # 5 minutes


def _check_api_key_status_impl(config: Dict[str, Any] | None = None, force_check: bool = False) -> Dict[str, Any]:
    """Internal implementation of API key check (without rate limiting)."""
    llm_config = get_llm_config(config)
    provider_config = llm_config.get("provider_config", {})
    api_url_base = provider_config.get("api_url") or "https://api.groq.com/openai/v1"
    default_model = provider_config.get("default_model") or "llama-3.1-8b-instant"
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return {
            "valid": False,
            "error": "GROQ_API_KEY not set",
            "key_type": None,
            "has_quota": False,
        }
    
    # Check cache if not forcing a fresh check
    if not force_check:
        import hashlib
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        cached = _api_key_check_cache.get(api_key_hash)
        if cached:
            cache_age = time.time() - cached["timestamp"]
            if cache_age < _API_KEY_CHECK_CACHE_TTL:
                return cast(Dict[str, Any], cached["result"])
    
    # Helper function to cache result
    import hashlib
    api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    def cache_result(result: Dict[str, Any]) -> Dict[str, Any]:
        """Cache the result and return it."""
        _api_key_check_cache[api_key_hash] = {
            "result": result,
            "timestamp": time.time(),
        }
        return result
    
    # Make a minimal test request
    import httpx
    client = httpx.Client(timeout=10.0)
    try:
        api_url = f"{api_url_base}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        # Groq API requires specific format
        resp = client.post(
            api_url,
            headers=headers,
            json={
                "model": default_model,
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 5,
            },
        )
        
        if resp.status_code == 200:
            return cache_result({
                "valid": True,
                "error": None,
                "key_type": "free",  # Groq free tier
                "has_quota": True,
            })
        elif resp.status_code == 401:
            return cache_result({
                "valid": False,
                "error": "Invalid API key",
                "key_type": None,
                "has_quota": False,
            })
        elif resp.status_code == 429:
            return cache_result({
                "valid": True,
                "error": "Rate limit exceeded",
                "key_type": "free",
                "has_quota": False,
            })
        else:
            # Get error details from response
            error_detail = f"API error: {resp.status_code}"
            try:
                error_body = resp.json()
                if "error" in error_body:
                    error_detail = f"{error_detail} - {error_body['error']}"
            except Exception:
                error_detail = f"{error_detail} - {resp.text[:200]}"
            
            return cache_result({
                "valid": False,
                "error": error_detail,
                "key_type": None,
                "has_quota": False,
            })
    except Exception as e:
        return cache_result({
            "valid": False,
            "error": str(e),
            "key_type": None,
            "has_quota": False,
        })
    finally:
        client.close()


def check_api_key_status(config: Dict[str, Any] | None = None, force_check: bool = False) -> Dict[str, Any]:
    """Check Groq API key status.
    
    NOTE: This function bypasses rate limiting and uses caching (5 min TTL) to avoid
    unnecessary API calls. Use force_check=True to force a fresh check.
    
    Args:
        config: Configuration dictionary
        force_check: If True, bypass cache and make a fresh API call
        
    Returns:
        Dict with keys: valid, error, key_type, has_quota
    """
    # Always call implementation directly with caching
    # This avoids unnecessary rate limit consumption
    return _check_api_key_status_impl(config, force_check=force_check)


def _chat_completions_impl(payload: Dict[str, Any], config: Dict[str, Any] | None = None) -> Any:
    """Internal implementation of Groq API call (without rate limiting)."""
    llm_config = get_llm_config(config)
    provider_config = llm_config.get("provider_config", {})
    api_url_base = provider_config.get("api_url") or "https://api.groq.com/openai/v1"
    default_model = provider_config.get("default_model") or "llama-3.1-8b-instant"
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise InfraError("GROQ_API_KEY not set")
    
    # Extract messages from payload
    messages = payload.get("messages", [])
    if not messages:
        raise InfraError("messages array is required")
    
    # Extract model from payload or use config default
    model = payload.get("model", default_model)
    
    # Groq API format (OpenAI-compatible)
    api_url = f"{api_url_base}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    groq_payload = {
        "model": model,
        "messages": messages,
        "temperature": payload.get("temperature", 0.7),
        "max_tokens": payload.get("max_tokens", 1024),
    }
    
    # Add optional parameters
    if "top_p" in payload:
        groq_payload["top_p"] = payload["top_p"]
    if "stream" in payload:
        groq_payload["stream"] = payload["stream"]
    
    response = request("POST", api_url, headers=headers, json=groq_payload, config=config)
    
    # Groq API response format (OpenAI-compatible)
    from gmle.app.http.json_parser import parse_llm_response
    parsed = parse_llm_response(response)
    
    # Preserve model and usage info if available
    if isinstance(response, dict) and "model" in response:
        parsed["model"] = response.get("model", model)
        parsed["usage"] = response.get("usage", {})
    
    return parsed


def chat_completions(payload: Dict[str, Any], config: Dict[str, Any] | None = None) -> Any:
    """Call Groq API chat completions through unified gate."""
    from gmle.app.http.api_gate import get_unified_api_gate
    
    llm_config = get_llm_config(config)
    provider = llm_config.get("active_provider", "groq")
    
    gate = get_unified_api_gate()
    return gate.call(
        call_type="mcq_generation",
        provider=provider,
        func=_chat_completions_impl,
        payload=payload,
        config=config,
    )

