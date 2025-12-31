"""Groq API client (OpenAI-compatible)."""

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
            return {
                "valid": True,
                "error": None,
                "key_type": "free",  # Groq free tier
                "has_quota": True,
            }
        elif resp.status_code == 401:
            return {
                "valid": False,
                "error": "Invalid API key",
                "key_type": None,
                "has_quota": False,
            }
        elif resp.status_code == 429:
            return {
                "valid": True,
                "error": "Rate limit exceeded",
                "key_type": "free",
                "has_quota": False,
            }
        else:
            # Get error details from response
            error_detail = f"API error: {resp.status_code}"
            try:
                error_body = resp.json()
                if "error" in error_body:
                    error_detail = f"{error_detail} - {error_body['error']}"
            except Exception:
                error_detail = f"{error_detail} - {resp.text[:200]}"
            
            return {
                "valid": False,
                "error": error_detail,
                "key_type": None,
                "has_quota": False,
            }
    except Exception as e:
        return {
            "valid": False,
            "error": str(e),
            "key_type": None,
            "has_quota": False,
        }
    finally:
        client.close()


def check_api_key_status(config: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Check Groq API key status through unified gate."""
    from gmle.app.http.api_gate import get_unified_api_gate
    
    llm_config = get_llm_config(config)
    provider = llm_config.get("active_provider", "groq")
    
    # Only use gate if Groq is the active provider
    if provider == "groq":
        gate = get_unified_api_gate()
        result: Any = gate.call(
            call_type="api_key_check",
            provider=provider,
            func=_check_api_key_status_impl,
            config=config,
        )
        return result  # type: ignore[no-any-return]
    # Otherwise, try without gate (fallback)
    return _check_api_key_status_impl(config)


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

